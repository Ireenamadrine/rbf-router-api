from pathlib import Path
import re

p = Path("app/db.py")
text = p.read_text(encoding="utf-8")

old = re.compile(
    r'cur\.execute\("""\s*SELECT f\.tier_used,\s*AVG\(f\.succeeded\) AS acc,\s*COUNT\(\*\) AS c\s*FROM feedback f\s*GROUP BY f\.tier_used\s*"""\)',
    re.DOTALL,
)
new = '''cur.execute("""
                SELECT r.recommended_tier AS tier_used,
                       AVG(CASE WHEN r.recommended_tier = f.tier_used THEN 1.0 ELSE 0.0 END) AS acc,
                       COUNT(*) AS c
                FROM routes r JOIN feedback f ON f.request_id = r.request_id
                GROUP BY r.recommended_tier
            """)'''

new_text, n = old.subn(new, text)
if n == 0:
    print("[SKIP] db.py: pattern not found -- paste get_stats() body, I will fix manually")
else:
    p.write_text(new_text, encoding="utf-8")
    print(f"[OK] db.py: stats query fixed ({n} replacement)")
