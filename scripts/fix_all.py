import re
from pathlib import Path

# ---- 1. rbf_router.py: split keywords into medium + frontier ----
p = Path("app/rbf_router.py")
text = p.read_text(encoding="utf-8")

new_keywords = '''_MEDIUM_KEYWORDS = (
    "difference between", "graphql", "regex", "cors", "jwt",
    "authentication", "normalization", "garbage collection",
    "unit test", "refactor", "debug", "sql query", "hash map",
)

_FRONTIER_KEYWORDS = (
    "architecture", "algorithm", "proof", "prove", "kubernetes",
    "microservices", "distributed", "concurrency", "analyze", "derive",
    "theorem", "compare", "implement", "scalable", "benchmark",
    "trade-off", "rate limiter", "consensus", "multi-tenant",
    "event-sourcing", "lock-free", "quicksort", "saas", "isolation",
    "memory ordering", "complexity", "fault-tolerant", "byzantine",
    "closed-form", "design a", "design an", "optimize",
    "horizontally scalable", "mathematical", "formal", "correctness",
    "multi-region", "globally consistent", "zero downtime",
)'''

text = re.sub(r"_COMPLEXITY_KEYWORDS = \([^)]*\)", new_keywords, text, count=1, flags=re.DOTALL)

text = text.replace(
    "    keyword_hits = sum(1 for kw in _COMPLEXITY_KEYWORDS if kw in q_lower)",
    "    medium_hits = sum(1 for kw in _MEDIUM_KEYWORDS if kw in q_lower)\n"
    "    frontier_hits = sum(1 for kw in _FRONTIER_KEYWORDS if kw in q_lower)"
)

text = text.replace(
    "        sentence_count, keyword_hits, code_hits, unique_ratio,",
    "        sentence_count, medium_hits, frontier_hits, code_hits, unique_ratio,"
)

p.write_text(text, encoding="utf-8")
print("[OK] rbf_router.py: keywords split into medium + frontier")

# ---- 2. test_api.py: send 11 feedbacks instead of 5 ----
p = Path("tests/test_api.py")
text = p.read_text(encoding="utf-8")

text = text.replace(
    '"""Send 5 feedbacks; expect at least one retrain."""\n    retrained = False\n    for i in range(5):',
    '"""Send 11 feedbacks; expect at least one retrain (threshold is 10/10)."""\n    retrained = False\n    for i in range(11):'
)

p.write_text(text, encoding="utf-8")
print("[OK] test_api.py: 5 -> 11 feedbacks")
