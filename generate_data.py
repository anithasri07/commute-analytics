"""Generate a synthetic dataset for a fictional corporate commute app (CommuteCo).
All data is made up. Patterns are planted so the analysis has something real to find."""
import random, csv, datetime as dt
random.seed(42)

SITES = [(1,"Site A - Tech Park","Bengaluru"),(2,"Site B - Business Bay","Bengaluru"),(3,"Site C - Riverside","Hyderabad")]
VENDORS = [(1,"SwiftRide"),(2,"MetroCabs"),(3,"CityWheels"),(4,"GreenFleet")]
DEPTS = ["Engineering","Operations","Support","Finance","HR","Sales"]
SHIFTS = ["06:00","09:00","14:00","18:00","22:00","02:00"]
START, END = dt.date(2026,7,1), dt.date(2026,9,30)

# vendor behaviour: (mean delay min, sd)
VDELAY = {1:(3,4),2:(5,5),3:(11,8),4:(4,4)}
# vendor share per site
VMIX = {1:[1,2,3],2:[2,3,4],3:[1,4,3]}

employees=[]
for e in range(1,2401):
    site=random.choices([1,2,3],[0.45,0.35,0.20])[0]
    dept=random.choice(DEPTS)
    shift=random.choices(SHIFTS,[0.10,0.40,0.15,0.10,0.15,0.10])[0]
    if dept=="Support": shift=random.choice(["22:00","02:00","14:00"])
    first=START+dt.timedelta(days=random.choices([0,random.randint(1,85)],[0.6,0.4])[0])
    rides=random.choices(["daily","frequent","occasional"],[0.45,0.35,0.20])[0]
    churn=random.random()<0.12   # some riders stop using the service
    employees.append(dict(employee_id=e,site_id=site,department=dept,shift_time=shift,
        first_ride_date=first,usage=rides,churn_date=first+dt.timedelta(days=random.randint(20,70)) if churn else None))

trips=[];feedback=[];disputes=[]
tid=fid=did=0
d=START
while d<=END:
    wd=d.weekday()
    for emp in employees:
        if d<emp["first_ride_date"] or (emp["churn_date"] and d>emp["churn_date"]): continue
        if wd>=5 and emp["department"]!="Support": continue
        p={"daily":0.85,"frequent":0.55,"occasional":0.2}[emp["usage"]]
        if random.random()>p: continue
        for ttype in ("LOGIN","LOGOUT"):
            if random.random()<0.08: continue
            tid+=1
            site=emp["site_id"]; vendor=random.choice(VMIX[site])
            m,sd=VDELAY[vendor]
            night=emp["shift_time"] in ("22:00","02:00")
            delay=max(-5,round(random.gauss(m+(2 if night else 0),sd)))
            dist=round(random.uniform(4,28),1)
            # status
            pn=0.015+(0.012 if night else 0)+(0.02 if delay>10 else 0)+(0.008 if site==2 else 0)
            pc=0.03+(0.03 if wd==0 else 0)
            r=random.random()
            if r<pn: status="NO_SHOW"
            elif r<pn+pc: status=random.choices(["CANCELLED","CANCELLED_LATE"],[0.75,0.25])[0]
            else: status="COMPLETED"
            trips.append(dict(trip_id=tid,employee_id=emp["employee_id"],site_id=site,vendor_id=vendor,
                trip_date=d.isoformat(),shift_time=emp["shift_time"],trip_type=ttype,
                cab_delay_min=delay if status!="CANCELLED" else "",distance_km=dist,status=status))
            if status=="COMPLETED" and random.random()<0.3:
                base=4.6-(0.08*max(0,delay-5))-(0.3 if vendor==3 else 0)
                rating=min(5,max(1,round(random.gauss(base,0.7))))
                cat=("DELAY" if delay>10 and random.random()<0.7 else random.choices(["DRIVER_BEHAVIOUR","CAB_CONDITION","ROUTE","NONE"],[0.15,0.15,0.15,0.55])[0]) if rating<=3 else "NONE"
                fid+=1; feedback.append(dict(feedback_id=fid,trip_id=tid,rating=rating,issue_category=cat))
            if status=="NO_SHOW":
                pd_=0.2+(0.25 if delay>10 else 0)+(0.15 if site==2 else 0)
                if random.random()<pd_:
                    pa=0.35+(0.35 if delay>10 else 0)+(0.2 if site==2 else 0)
                    acc=random.random()<min(pa,0.95)
                    did+=1
                    raised=dt.datetime.combine(d,dt.time(random.randint(0,23),random.randint(0,59)))
                    hrs=random.randint(8,120) if random.random()<0.8 else random.randint(120,240)
                    disputes.append(dict(dispute_id=did,trip_id=tid,raised_at=raised.isoformat(sep=" "),
                        resolved_at=(raised+dt.timedelta(hours=hrs)).isoformat(sep=" "),
                        outcome="ACCEPTED" if acc else "REJECTED"))
    d+=dt.timedelta(days=1)

def w(name,rows,cols):
    with open(f"{name}.csv","w",newline="") as f:
        wr=csv.DictWriter(f,fieldnames=cols); wr.writeheader()
        for r in rows: wr.writerow({c:r[c] for c in cols})
w("sites",[dict(site_id=a,site_name=b,city=c) for a,b,c in SITES],["site_id","site_name","city"])
w("vendors",[dict(vendor_id=a,vendor_name=b) for a,b in VENDORS],["vendor_id","vendor_name"])
for e in employees: e["first_ride_date"]=e["first_ride_date"].isoformat()
w("employees",employees,["employee_id","site_id","department","shift_time"])
w("trips",trips,["trip_id","employee_id","site_id","vendor_id","trip_date","shift_time","trip_type","cab_delay_min","distance_km","status"])
w("feedback",feedback,["feedback_id","trip_id","rating","issue_category"])
w("disputes",disputes,["dispute_id","trip_id","raised_at","resolved_at","outcome"])
print(len(employees),len(trips),len(feedback),len(disputes))
