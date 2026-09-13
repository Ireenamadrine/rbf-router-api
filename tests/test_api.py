"""Regression tests for the RBF-Router API."""
import os
import tempfile

# Point to throwaway files BEFORE importing app so lifespan uses them.
_tmp = tempfile.mkdtemp()
os.environ["ROUTER_PATH"] = os.path.join(_tmp, "test_router.joblib")
os.environ["DATABASE_PATH"] = os.path.join(_tmp, "test.db")

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["router_trained"] is True


def test_easy_vs_hard_separation(client):
    """The core value proposition: easy -> small, hard -> frontier."""
    easy = client.post("/optimize", json={"query": "What is 2 + 2?"}).json()
    hard = client.post("/optimize", json={
        "query": "Design a distributed consensus algorithm for a kubernetes cluster and prove its correctness"
    }).json()

    assert easy["recommended_tier"] == "small", \
        f"easy query got {easy['recommended_tier']} (probs={easy['alternatives']})"
    assert hard["recommended_tier"] == "frontier", \
        f"hard query got {hard['recommended_tier']} (probs={hard['alternatives']})"
    assert easy["confidence"] > 0.4, f"easy confidence too low: {easy['confidence']}"
    assert hard["confidence"] > 0.4, f"hard confidence too low: {hard['confidence']}"


def test_medium_query_lands_medium(client):
    """Medium queries shouldn't collapse to small or frontier."""
    r = client.post("/optimize", json={
        "query": "Explain the difference between REST and GraphQL APIs"
    }).json()
    assert r["recommended_tier"] == "medium", \
        f"medium query got {r['recommended_tier']} (probs={r['alternatives']})"


def test_feedback_triggers_retrain(client):
    """Send 11 feedbacks; expect at least one retrain (threshold is 10/10)."""
    retrained = False
    for i in range(11):
        route = client.post("/optimize", json={"query": f"sanity check {i}"}).json()
        fb = client.post("/feedback", json={
            "request_id": route["request_id"],
            "tier_used": route["recommended_tier"],
            "succeeded": True,
        }).json()
        if fb["router_updated"]:
            retrained = True

    assert retrained, "router never retrained after 5 feedbacks"


def test_stats_reflects_activity(client):
    r = client.get("/stats").json()
    assert r["total_routes"] >= 6
    assert r["total_feedback"] >= 5
    assert isinstance(r["accuracy_by_tier"], dict)