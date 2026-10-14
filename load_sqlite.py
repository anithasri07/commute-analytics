"""Load the CSVs into a local SQLite database (commute.db)."""
import sqlite3, csv, os
if os.path.exists("commute.db"): os.remove("commute.db")
con=sqlite3.connect("commute.db"); con.executescript(open("01_schema.sql").read())
for t in ["sites","vendors","employees","trips","feedback","disputes"]:
    rows=list(csv.reader(open(f"{t}.csv"))); hdr,rows=rows[0],rows[1:]
    rows=[[None if v=="" else v for v in r] for r in rows]
    con.executemany(f"INSERT INTO {t} ({','.join(hdr)}) VALUES ({','.join('?'*len(hdr))})",rows)
con.commit(); print("loaded commute.db")
