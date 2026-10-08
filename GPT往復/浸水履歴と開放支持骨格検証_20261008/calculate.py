"""Cycle 30. Pressure-history counterexamples and process inventory.
No material success probability is computed. Python 3 standard library.
"""
import json,math,heapq,itertools
from pathlib import Path
P=Path(__file__).resolve().parent
I=json.loads((P/"inputs.json").read_text(encoding="utf-8"))
def save(n,x): (P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def tension(t):
    if not .01<=t<=373.946: raise ValueError("IAPWS liquid-vapor temperature range")
    tau=1-(t+273.15)/647.096
    return .2358*tau**1.256*(1-.625*tau)
def threshold(gamma,angle,d_um):
    if d_um<=0: raise ValueError("positive diameter required")
    return -4*gamma*math.cos(math.radians(angle))/(d_um*1e-6)
def history(d,aa,ar,pressures,gamma):
    if ar>aa:raise ValueError("receding must not exceed advancing")
    pa,pr=threshold(gamma,aa,d),threshold(gamma,ar,d)
    wet=False; out=[]
    for p in pressures:
        if not wet and p>pa:wet=True
        elif wet and p<pr:wet=False
        out.append(dict(pressure_Pa=p,wet=wet))
    return dict(diameter_um=d,advancing_deg=aa,receding_deg=ar,
                advancing_threshold_Pa=pa,receding_threshold_Pa=pr,states=out)
audit=[]
for r in I["pe_observations"]["rows"]:
    aa=r["receding_deg"]+r["hysteresis_deg"]
    pred=threshold(I["scenarios"]["audit_surface_tension_N_m"],aa,r["diameter_um"])/1e5
    audit.append(dict(**r,outer_advancing_deg=aa,shortcut_bar=pred,
                     shortcut_to_observed=pred/r["entry_bar"]))
hist=[]
for t in I["scenarios"]["temperature_C"]:
    for d in I["scenarios"]["diameters_um"]:
        for ar in I["scenarios"]["receding_deg"]:
            v=history(d,I["scenarios"]["advancing_deg"],ar,[1000*x for x in I["scenarios"]["pressure_cycle_kPa"]],tension(t))
            hist.append(dict(temperature_C=t,**v))
def bottleneck(edges,start="in",end="out"):
    adj={}
    for a,b,w in edges:adj.setdefault(a,[]).append((b,w));adj.setdefault(b,[]).append((a,w))
    queue=[(0,start)];best={start:0}
    while queue:
        c,u=heapq.heappop(queue)
        if c!=best[u]:continue
        if u==end:return c
        for v,w in adj.get(u,[]):
            val=max(c,w)
            if val<best.get(v,float("inf")):best[v]=val;heapq.heappush(queue,(val,v))
    return float("inf")
def flood_reaches(edges,p):
    seen={"in"};changed=True
    while changed:
        changed=False
        for a,b,w in edges:
            if w<=p and ((a in seen)!=(b in seen)):
                seen.update([a,b]);changed=True
    return "out" in seen
net=[]
for name,ds in [("mixed",I["network"]["mixed_paths_um"]),("separated",I["network"]["separated_paths_um"])]:
    edges=[(a,b,threshold(tension(I["network"]["temperature_C"]),I["network"]["advancing_deg"],d)) for (a,b),d in zip(I["network"]["edge_pairs"],ds)]
    net.append(dict(name=name,diameters_um=ds,edges=edges,breakthrough_Pa=bottleneck(edges)))
def gas(phi,eps,kappa,p0=101325):
    if not 0<=eps<1-phi:raise ValueError("positive remaining gas volume required")
    v0=1-phi; v=v0-eps;ratio=v0/v
    p=p0*ratio**kappa
    e=(p0*v0*math.log(ratio) if kappa==1 else p0*v0*(ratio**(kappa-1)-1)/(kappa-1))-p0*(v0-v)
    return dict(gas_volume_per_initial_total_volume=v,absolute_pressure_Pa=p,
                excess_cell_pressure_Pa=p-p0,compression_work_J_per_initial_m3=e)
gasrows=[]
for phi,eps,kappa in itertools.product(I["scenarios"]["gas_solid_fractions"],I["scenarios"]["gas_compressive_strains"],I["scenarios"]["polytropic_exponents"]):
    gasrows.append(dict(solid_fraction=phi,compressive_strain=eps,kappa=kappa,**gas(phi,eps,kappa,I["scenarios"]["initial_gas_pressure_Pa"])))
F=I["factory"];factory=[]
for area,y in itertools.product(F["areas_m2"],F["good_yields"]):
    good_mass=area*F["bed_depth_m"]*F["assumed_bed_density_kg_m3"]
    good_rate=good_mass/(F["production_days"]*F["hours_per_day"])
    feed_rate=good_rate/y
    one_mass=feed_rate*F["source_S3_one_stage_saturation_h"];pre_mass=feed_rate*F["source_S3_pretreatment_saturation_h"];second_mass=feed_rate*F["source_S3_second_stage_saturation_h"]
    one_volume=one_mass/F["source_S3_solid_density_kg_m3"];pre_volume=pre_mass/F["source_S3_solid_density_kg_m3"];second_volume=second_mass/F["source_S3_prefoamed_density_kg_m3"]
    factory.append(dict(area_m2=area,yield_assumed=y,good_mass_kg=good_mass,good_rate_kg_h=good_rate,
      feed_rate_kg_h=feed_rate,one_stage_inventory_kg=one_mass,pretreatment_inventory_kg=pre_mass,
      second_stage_inventory_kg=second_mass,one_stage_occupied_m3=one_volume,
      pretreatment_occupied_m3=pre_volume,second_stage_occupied_m3=second_volume,
      two_stage_occupied_m3=pre_volume+second_volume,volume_ratio_two_to_one=(pre_volume+second_volume)/one_volume))
checks=[]
def ck(n,v,d):
    if not v:raise AssertionError(n)
    checks.append(dict(name=n,passed=True,detail=d))
ck("IAPWS 25C reference",abs(tension(25)-.07197)<.00005,"N/m table rounded reference")
ck("IAPWS 50C reference",abs(tension(50)-.06794)<.00005,"N/m table rounded reference")
ck("inverse diameter scaling",abs(threshold(.072,120,10)/threshold(.072,120,100)-10)<1e-12,"cylinder only")
ck("wetting sign",threshold(.072,85,10)<0<threshold(.072,95,10),"water minus air convention")
ck("90 degree neutral",abs(threshold(.072,90,10))<1e-8,"numerical trigonometric tolerance")
seq=[0,2000,20000,0,-5000,0]
h85=history(10,120,85,seq,tension(50))
h95=history(10,120,95,seq,tension(50))
ck("hysteresis retains wet state at zero",h85["states"][2]["wet"] and h85["states"][3]["wet"],"ideal thetaR 85")
ck("higher receding angle allows release",h95["states"][2]["wet"] and not h95["states"][3]["wet"],"ideal thetaR 95")
ck("sufficient negative pressure drains",not h85["states"][4]["wet"],"specified imposed liquid-side pressure")
ck("no-entry control",not any(x["wet"] for x in history(1,120,85,seq,tension(50))["states"]),"peak below threshold")
ck("same pore histogram",sorted(net[0]["diameters_um"])==sorted(net[1]["diameters_um"]),"different paths, same throat inventory")
ck("different topology different onset",abs(net[0]["breakthrough_Pa"]/net[1]["breakthrough_Pa"]-10)<1e-12,"exact diamond counterexample")
for r in net:
    ps=sorted(set(w for _,_,w in r["edges"]))
    brute=next(p for p in ps if flood_reaches(r["edges"],p))
    ck("independent flood vs minimax "+r["name"],abs(brute-r["breakthrough_Pa"])<1e-10,"connectivity search, no fitted inputs")
ck("sealed gas Boyle conservation",all(abs((gas(phi,e,1)["absolute_pressure_Pa"]*(1-phi-e))-101325*(1-phi))<1e-8 for phi,e in itertools.product([.03,.1,.2],[.1,.3,.5])),"isothermal")
ck("zero compression gas baseline",gas(.1,0,1)["absolute_pressure_Pa"]==101325 and gas(.1,0,1)["compression_work_J_per_initial_m3"]==0,"no initial prepressure")
for kap in [1,1.4]:
    h=1e-6;eps=.3
    deriv=(gas(.1,eps+h,kap)["compression_work_J_per_initial_m3"]-gas(.1,eps-h,kap)["compression_work_J_per_initial_m3"])/(2*h)
    ck("energy derivative k="+str(kap),abs(deriv-gas(.1,eps,kap)["excess_cell_pressure_Pa"])<.001,"constant area cell-volume path only; not real foam stress")
ck("gas scenario domain",all(e<1-phi for phi,e in itertools.product([.03,.1,.2],[.1,.3,.5])),"all evaluated inputs keep positive gas volume")
ck("factory 2000m2 good rate",any(r["area_m2"]==2000 and r["good_rate_kg_h"]==225 for r in factory),"108 t / 480 h")
ck("two-stage full accounting",all(abs(r["two_stage_occupied_m3"]-r["pretreatment_occupied_m3"]-r["second_stage_occupied_m3"])<1e-12 for r in factory),"12h pretreatment not omitted")
ck("yield mass conservation",all(abs(r["feed_rate_kg_h"]*r["yield_assumed"]-r["good_rate_kg_h"])<1e-9 for r in factory),"assumed yields 1 and .8")
ck("small area scales tenfold",abs(factory[2]["two_stage_occupied_m3"]/factory[0]["two_stage_occupied_m3"]-10)<1e-12,"same yield")
save("results.json",dict(cycle=30,physical_tests=0,physical_success_probability=None,
 surface_tension_N_m={str(t):tension(t) for t in [25,30,50]},membrane_shortcut_audit=audit,
 pressure_histories=hist,network_counterexamples=net,sealed_cell_scales=gasrows,factory=factory))
save("validation.json",dict(check_count=len(checks),checks=checks,physical_tests=0,
 scope="Arithmetic, conservation, topology and specified ideal constitutive examples only. No snow/material validation."))
print(json.dumps(dict(checks=len(checks),source_rows=len(audit),histories=len(hist),
 network_cases=len(net),sealed_cell_cases=len(gasrows),factory_cases=len(factory))))
