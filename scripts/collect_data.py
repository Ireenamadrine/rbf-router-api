"""Send 50 varied queries and their correct tier labels as feedback.
Watch /stats improve (or not) once the router retrains."""
import requests, time

BASE = "http://127.0.0.1:8000"

# 50 queries with the tier YOU believe is correct.
# Mix easy, medium, hard. Include realistic phrasing.
SAMPLES = [
    # --- small (16) ---
    ("What is 5 + 7?", "small"),
    ("Convert 100 USD to EUR", "small"),
    ("Who wrote Hamlet?", "small"),
    ("Say hello in French", "small"),
    ("What day is it today?", "small"),
    ("Reverse the word 'hello'", "small"),
    ("What is the boiling point of water?", "small"),
    ("List three primary colors", "small"),
    ("Translate 'thank you' to Spanish", "small"),
    ("What is 15% of 200?", "small"),
    ("Capital of Japan?", "small"),
    ("Print 'hi' in python", "small"),
    ("How many days in February?", "small"),
    ("What color is the sky?", "small"),
    ("Define 'cat'", "small"),
    ("Square root of 144?", "small"),

    # --- medium (18) ---
    ("Write a Python function to check if a string is a palindrome", "medium"),
    ("Explain the difference between a list and a tuple in Python", "medium"),
    ("Write a SQL query to find the second highest salary", "medium"),
    ("Explain how JWT authentication works", "medium"),
    ("Refactor this function to use list comprehension", "medium"),
    ("What is the time complexity of binary search?", "medium"),
    ("Write unit tests for a login function", "medium"),
    ("Explain the difference between HTTP and HTTPS", "medium"),
    ("How does garbage collection work in Python?", "medium"),
    ("Write a regex to match email addresses", "medium"),
    ("Explain CORS in one paragraph", "medium"),
    ("What is the difference between let and const in JavaScript?", "medium"),
    ("Write a bash script to rename files in a directory", "medium"),
    ("Explain the concept of dependency injection", "medium"),
    ("Debug: why is my async function not awaiting?", "medium"),
    ("Write a Dockerfile for a Node.js app", "medium"),
    ("Explain database normalization with an example", "medium"),
    ("How do you handle pagination in a REST API?", "medium"),

    # --- frontier (16) ---
    ("Design a distributed rate limiter that handles 1M req/sec across regions", "frontier"),
    ("Prove that quicksort has O(n log n) average case complexity", "frontier"),
    ("Architect a multi-tenant SaaS platform with data isolation guarantees", "frontier"),
    ("Explain the CAP theorem and how it applies to CockroachDB vs Spanner", "frontier"),
    ("Derive the closed-form solution for a Kalman filter update step", "frontier"),
    ("Design a globally consistent event-sourcing system with exactly-once delivery", "frontier"),
    ("Compare Raft, Paxos, and Zab consensus protocols with trade-offs", "frontier"),
    ("Implement a lock-free concurrent queue in C++ with memory ordering", "frontier"),
    ("Explain the mathematical foundations of transformer attention", "frontier"),
    ("Design a schema migration strategy for a 10TB Postgres database with zero downtime", "frontier"),
    ("Prove the correctness of a Byzantine fault-tolerant consensus algorithm", "frontier"),
    ("Architect a real-time ML feature store with sub-100ms serving latency", "frontier"),
    ("Analyze the security trade-offs of three homomorphic encryption schemes", "frontier"),
    ("Design a sharded, horizontally scalable time-series database", "frontier"),
    ("Derive the regret bound for Thompson sampling in multi-armed bandits", "frontier"),
    ("Design a cross-region active-active database with conflict resolution", "frontier"),
]


def main():
    print(f"Sending {len(SAMPLES)} samples to {BASE}\n")
    retrains = 0
    for i, (query, correct_tier) in enumerate(SAMPLES, 1):
        r = requests.post(f"{BASE}/optimize", json={"query": query}, timeout=10)
        r.raise_for_status()
        body = r.json()
        rid = body["request_id"]
        router_said = body["recommended_tier"]

        # Send feedback: use the tier WE believe is correct.
        # succeeded=True means "the tier we used worked."
        fb = requests.post(f"{BASE}/feedback", json={
            "request_id": rid,
            "tier_used": correct_tier,
            "succeeded": True,
        }, timeout=10).json()
        if fb["router_updated"]:
            retrains += 1

        match = "✓" if router_said == correct_tier else "✗"
        print(f"[{i:02d}] {match}  said={router_said:9s} truth={correct_tier:9s}")

    print(f"\n--- Retrains fired: {retrains} ---")
    s = requests.get(f"{BASE}/stats", timeout=10).json()
    print(f"Total routes:      {s['total_routes']}")
    print(f"Total feedback:    {s['total_feedback']}")
    print(f"Avg confidence:    {s['avg_confidence']:.3f}")
    print(f"Tier distribution: {s['tier_distribution']}")
    print(f"Accuracy by tier:  {s['accuracy_by_tier']}")


if __name__ == "__main__":
    main()