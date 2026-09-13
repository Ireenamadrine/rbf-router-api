from pathlib import Path
import re

p = Path("app/rbf_router.py")
text = p.read_text(encoding="utf-8")

old_regex_marker = "_MEDIUM_KEYWORDS = ("
if old_regex_marker in text:
    text = re.sub(
        r"_MEDIUM_KEYWORDS = \([^)]*\)\s*\n\s*_FRONTIER_KEYWORDS = \([^)]*\)",
        '''_COMPLEXITY_KEYWORDS = (
    "architecture", "algorithm", "proof", "kubernetes", "microservices",
    "design", "optimize", "distributed", "concurrency", "security",
    "analyze", "compare", "derive", "theorem", "regex", "cors", "jwt",
    "authentication", "normalization", "graphql", "garbage collection",
    "difference between", "rate limiter", "consensus", "multi-tenant",
    "event-sourcing", "lock-free", "quicksort", "saas", "isolation",
    "memory ordering", "complexity",
)''',
        text, count=1, flags=re.DOTALL,
    )
    text = text.replace(
        "    medium_hits = sum(1 for kw in _MEDIUM_KEYWORDS if kw in q_lower)\n"
        "    frontier_hits = sum(1 for kw in _FRONTIER_KEYWORDS if kw in q_lower)",
        "    keyword_hits = sum(1 for kw in _COMPLEXITY_KEYWORDS if kw in q_lower)",
    )
    text = text.replace(
        "        sentence_count, medium_hits, frontier_hits, code_hits, unique_ratio,",
        "        sentence_count, keyword_hits, code_hits, unique_ratio,",
    )
    p.write_text(text, encoding="utf-8")
    print("[OK] keywords reverted to single list")
else:
    print("[SKIP] _MEDIUM_KEYWORDS not found - already reverted?")
