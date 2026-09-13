from pathlib import Path
import re

p = Path("app/rbf_router.py")
text = p.read_text(encoding="utf-8")

original = '''_COMPLEXITY_KEYWORDS = (
    "architecture", "algorithm", "proof", "kubernetes", "microservices",
    "design", "optimize", "distributed", "concurrency", "security",
    "analyze", "explain in detail", "compare", "derive", "theorem",
)'''

# Replace both possible current states (split or expanded) with the original
text = re.sub(r"_MEDIUM_KEYWORDS = \([^)]*\)\s*\n\s*_FRONTIER_KEYWORDS = \([^)]*\)", original, text, count=1, flags=re.DOTALL)
text = re.sub(r"_COMPLEXITY_KEYWORDS = \([^)]*\)", original, text, count=1, flags=re.DOTALL)

# Fix the feature builder back to one keyword_hits
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
print("[OK] rbf_router.py restored to original single-list keywords")
