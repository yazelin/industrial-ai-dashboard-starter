import math, random, time
START=time.time()
def simulated_snapshot():
    t=time.time()-START
    agvs=[]
    for i in range(1,4):
        b=max(5,90-(t*(i+1)%70))
        agvs.append({"id":f"AGV-{i}","x":round(50+35*math.sin(t/8+i),1),"y":round(50+35*math.cos(t/10+i),1),"battery":round(b,1),"status":"charging" if b<20 else random.choice(["idle","moving","loading"])})
    machines=[{"id":"AOI-1","status":random.choice(["run","run","warn"]),"ng_rate":round(random.random()*3,2)},{"id":"PLC-Press-2","status":random.choice(["run","run","stop"]),"temperature":round(45+random.random()*20,1)}]
    alerts=[{"level":"warning","message":a["id"]+" low battery"} for a in agvs if a["battery"]<20]
    return {"timestamp":time.time(),"agvs":agvs,"machines":machines,"alerts":alerts}
