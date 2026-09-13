import re
from pathlib import Path


def patch(path, pattern, replacement, label):
    p = Path(path)
    if not p.exists():
        print(f"[SKIP] {label}: {path} not found")
        return False
    text = p.read_text(encoding="utf-8")
    new_text, n = re.subn(pattern, replacement, text, flags=re.DOTALL)
    if n == 0:
        print(f"[SKIP] {label}: pattern not matched")
        return False
    p.write_text(new_text, encoding="utf-8")
    print(f"[OK]   {label}: {n} replacement(s)")
    return True


# 1. db.py -- fix accuracy query
patch(
    "app/db.py",
    r'cur\.execute\("""[^"]*AVG\(succeeded\) AS acc[^"]*"""\)',
    'cur.execute("""\n'
    '                SELECT r.recommended_tier AS tier_used,\n'
    '                       AVG(CASE WHEN r.recommended_tier = f.tier_used THEN 1.0 ELSE 0.0 END) AS acc,\n'
    '                       COUNT(*) AS c\n'
    '                FROM routes r JOIN feedback f ON f.request_id = r.request_id\n'
    '                GROUP BY r.recommended_tier\n'
    '            """)',
    "db.py accuracy query",
)

# 2. main.py -- retrain thresholds 3/3 -> 10/10
patch(
    "app/main.py",
    r'min_feedback_to_retrain=3,\s*retrain_every_n_new=3',
    'min_feedback_to_retrain=10, retrain_every_n_new=10',
    "main.py retrain thresholds",
)

# 3. rbf_router.py -- expand complexity keywords
patch(
    "app/rbf_router.py",
    r'_COMPLEXITY_KEYWORDS = \([^)]*\)',
    '_COMPLEXITY_KEYWORDS = (\n'
    '    "architecture", "algorithm", "proof", "kubernetes", "microservices",\n'
    '    "design", "optimize", "distributed", "concurrency", "security",\n'
    '    "analyze", "explain in detail", "compare", "derive", "theorem",\n'
    '    "regex", "cors", "jwt", "authentication", "normalization", "graphql",\n'
    '    "garbage collection", "difference between", "rate limiter", "consensus",\n'
    '    "multi-tenant", "event-sourcing", "lock-free", "quicksort", "saas",\n'
    '    "isolation", "memory ordering", "complexity",\n'
    ')',
    "rbf_router.py keywords",
)

print()
print("Done. Now wipe state and restart uvicorn.")
