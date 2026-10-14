"""Run every query in 02_analysis.sql against commute.db and print the results."""
import sqlite3, re
con=sqlite3.connect("commute.db")
sql=open("02_analysis.sql").read()
for block in re.split(r"\n(?=-- Q\d+\.)", sql)[1:]:
    title=block.splitlines()[0]; print("\n"+title)
    cur=con.execute(block); cols=[c[0] for c in cur.description]
    rows=cur.fetchall(); print(" | ".join(cols))
    for r in rows: print(" | ".join(str(x) for x in r))
