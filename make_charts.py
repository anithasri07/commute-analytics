"""Create the README charts from commute.db."""
import sqlite3, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
con=sqlite3.connect("commute.db")
plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
BLUE,GREY,RED="#1F4E79","#B0B7C3","#C0392B"

# 1. Vendor share of trips vs share of wrong no-show marks
rows=con.execute("""SELECT v.vendor_name,
  100.0*COUNT(*)/(SELECT COUNT(*) FROM trips),
  100.0*(SELECT COUNT(*) FROM disputes d JOIN trips t2 ON t2.trip_id=d.trip_id WHERE d.outcome='ACCEPTED' AND t2.vendor_id=v.vendor_id)
       /(SELECT COUNT(*) FROM disputes WHERE outcome='ACCEPTED')
  FROM trips t JOIN vendors v ON v.vendor_id=t.vendor_id GROUP BY v.vendor_id ORDER BY 3 DESC""").fetchall()
names=[r[0] for r in rows]; x=range(len(names)); w=0.38
fig,ax=plt.subplots(figsize=(7,3.6))
ax.bar([i-w/2 for i in x],[r[1] for r in rows],w,color=GREY,label="Share of trips")
ax.bar([i+w/2 for i in x],[r[2] for r in rows],w,color=BLUE,label="Share of wrong no-show marks")
for i,r in enumerate(rows): ax.text(i+w/2,r[2]+1,f"{r[2]:.0f}%",ha="center",fontsize=9)
ax.set_xticks(list(x)); ax.set_xticklabels(names); ax.set_ylabel("%"); ax.legend(frameon=False)
ax.set_title("CityWheels: 33% of trips, 57% of wrong no-show marks",loc="left",fontweight="bold")
fig.tight_layout(); fig.savefig("vendor_wrong_marks.png",dpi=150)

# 2. Delay vs rating
rows=con.execute("""SELECT CASE WHEN t.cab_delay_min<=0 THEN 'On time/early' WHEN t.cab_delay_min<=5 THEN '1-5 min'
  WHEN t.cab_delay_min<=10 THEN '6-10 min' WHEN t.cab_delay_min<=20 THEN '11-20 min' ELSE '20+ min' END b,
  AVG(f.rating), MIN(t.cab_delay_min) FROM feedback f JOIN trips t ON t.trip_id=f.trip_id GROUP BY b ORDER BY 3""").fetchall()
fig,ax=plt.subplots(figsize=(7,3.6))
cols=[BLUE if r[1]>=4 else RED for r in rows]
ax.bar([r[0] for r in rows],[r[1] for r in rows],color=cols)
for i,r in enumerate(rows): ax.text(i,r[1]+0.05,f"{r[1]:.2f}",ha="center",fontsize=9)
ax.set_ylim(0,5); ax.set_ylabel("Average rating (1-5)"); ax.set_xlabel("How late the cab arrived")
ax.set_title("Ratings fall sharply once a cab is more than 10 minutes late",loc="left",fontweight="bold")
fig.tight_layout(); fig.savefig("delay_vs_rating.png",dpi=150)

# 3. No-show rate by shift
rows=con.execute("""SELECT shift_time,100.0*SUM(status='NO_SHOW')/COUNT(*) FROM trips GROUP BY shift_time
  ORDER BY CASE shift_time WHEN '02:00' THEN 0 ELSE 1 END, shift_time""").fetchall()
order=["06:00","09:00","14:00","18:00","22:00","02:00"]; d=dict(rows)
fig,ax=plt.subplots(figsize=(7,3.4))
ax.bar(order,[d[s] for s in order],color=[BLUE if s in("22:00","02:00") else GREY for s in order])
for i,s in enumerate(order): ax.text(i,d[s]+0.05,f"{d[s]:.1f}%",ha="center",fontsize=9)
ax.set_ylabel("No-show rate"); ax.set_xlabel("Shift start")
ax.set_title("Night shifts have ~60% higher no-show rates",loc="left",fontweight="bold")
fig.tight_layout(); fig.savefig("no_show_by_shift.png",dpi=150)
print("charts done")
