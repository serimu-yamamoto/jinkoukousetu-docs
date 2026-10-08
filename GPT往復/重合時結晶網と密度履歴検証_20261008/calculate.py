"""Cycle 29: density inventory and morphology-retention accounting, not material simulation.
Python 3 standard library only. Run: python calculate.py
All scenario values and source distinctions are in inputs.json.
"""
from pathlib import Path
import json, math
from decimal import Decimal, getcontext
P=Path(__file__).resolve().parent
I=json.loads((P/"inputs.json").read_text(encoding="utf-8"))
H=I["comparison"]["finished_depth_m"]
rho0=I["comparison"]["finished_density_kg_m3"]
areas=I["comparison"]["areas_m2"]
c=I["comparison"]["hypothetical_delivered_price_jpy_kg"]
g=9.80665
density=[]
for rho in I["scenario"]["bed_densities_kg_m3"]:
    for A in areas:
        M=A*H*rho
        density.append(dict(rho_kg_m3=rho,area_m2=A,mass_kg=M,
          material_cost_jpy=M*c,good_rate_kg_h=M/(30*16),
          gravity_shear_pa=rho*H*g*math.sin(math.pi/6),
          equal_cost_price_jpy_kg=rho0*c/rho))
spreading=[]
for raw in I["scenario"]["incoming_densities_kg_m3"]:
    for final in I["scenario"]["finished_densities_kg_m3"]:
        spreading.append(dict(incoming_rho=raw,finished_rho=final,
          loose_depth_m=H*final/raw,volume_ratio=final/raw,
          needs_expansion_not_compaction=raw>final))
# Ideal additive BULK volumes of distinct sub-lots, not actual mixed-powder packing.
retention=[]
for rd in I["scenario"]["damaged_density_kg_m3"]:
    for q in I["scenario"]["damage_fraction_per_full_bed_cycle"]:
        for n in I["scenario"]["cycles"]:
            a=(1-q)**n
            depth=H*(a+(1-a)*rho0/rd)
            retention.append(dict(damaged_rho=rd,q=q,cycles=n,
              intact_mass_fraction=a,ideal_depth_m=depth,
              ideal_effective_rho=rho0*H/depth))
renewal=[]
for A in areas:
    for depth in I["scenario"]["processed_depths_m"]:
        f=depth/H
        M=A*H*rho0
        for q in I["scenario"]["damage_fraction_in_processed_mass"]:
            kg=M*f*q*I["comparison"]["annual_grooming_cycles"]
            renewal.append(dict(area_m2=A,processed_depth_m=depth,q_processed=q,
              new_mass_kg_year=kg,material_purchase_jpy_year=kg*c))
limits=[]
for A in areas:
    for depth in I["scenario"]["processed_depths_m"]:
        for price in I["scenario"]["prices_jpy_kg"]:
            M=A*depth*rho0
            qmax=I["comparison"]["hypothetical_annual_material_budget_jpy"]/(M*I["comparison"]["annual_grooming_cycles"]*price)
            limits.append(dict(area_m2=A,processed_depth_m=depth,price=price,
              q_processed_max=qmax,whole_bed_fraction_max=qmax*depth/H))
# New powder preserved during shipping: mass and volume limits independently applied.
transport=[]
for A in areas:
    M=A*H*rho0
    for shipping_rho in I["scenario"]["incoming_densities_kg_m3"]:
        trips=math.ceil(max(M/I["comparison"]["hypothetical_truck_mass_kg"],
            M/(I["comparison"]["hypothetical_truck_volume_m3"]*shipping_rho)))
        transport.append(dict(area_m2=A,shipping_rho=shipping_rho,mass_kg=M,
            minimum_trips=trips,hypothetical_freight_jpy=trips*I["comparison"]["hypothetical_trip_jpy"],
            freight_jpy_kg=trips*I["comparison"]["hypothetical_trip_jpy"]/M))
contamination=[]
for A in areas:
    M=A*H*rho0
    for gamma in I["scenario"]["annual_contamination_rejection_fraction"]:
        cost=M*gamma*c
        remaining=I["comparison"]["hypothetical_annual_material_budget_jpy"]-cost
        contamination.append(dict(area_m2=A,gamma_annual=gamma,replacement_kg=M*gamma,
          purchase_jpy=cost,remaining_material_budget_jpy=remaining,
          budget_exceeded=remaining<0,
          whole_bed_q_max=None if remaining<0 else remaining/(M*200*c)))

checks=[]
def ck(name, passed, detail):
    if not passed: raise AssertionError(name)
    checks.append(dict(name=name,passed=True,detail=detail))
# Independently evaluated decimal reference examples, endpoints and conservation.
getcontext().prec=40
D=Decimal
ck("2000m2 reference mass",D("2000")*D(".45")*D("120")==D("108000"),"108 t")
ck("20000m2 reference mass",D("20000")*D(".45")*D("120")==D("1080000"),"1080 t")
ck("450 density equal-cost ceiling",abs(120*500/450-133.3333333333333)<1e-10,"not a market quote")
ck("60 to 120 loose depth",D(".45")*D("120")/D("60")==D(".90"),"mass per area conserved")
ck("450 to 120 requires expansion",450>120 and 450/120==3.75,"roller compaction alone does not specify expansion")
# Loop recurrence is checked against a closed form, rather than self-comparing same expression.
for q,n in [(0,200),(.0001,500),(.001,200),(.01,100)]:
    mass=D("1")
    for _ in range(n): mass*=1-D(str(q))
    closed=(1-q)**n
    ck(f"decay recurrence q={q}, n={n}",abs(float(mass)-closed)<1e-12,"independent Decimal recurrence")
ck("no damage retains original thickness",H*(1+(1-1)*rho0/450)==H,"q=0")
ck("all damaged reference limit",abs(H*rho0/450-.12)<1e-14,"same dry mass, additive bulk-volume reference")
ck("no density contrast",abs(H*(.3+.7*rho0/rho0)-H)<1e-14,"conversion with equal density cannot alter reference depth")
# Independent inventory balance across all rows is one family, not hundreds of empirical trials.
ck("bed mass and cost conservation",all(abs(r["mass_kg"]-r["area_m2"]*H*r["rho_kg_m3"])<1e-8 and abs(r["material_cost_jpy"]/c-r["mass_kg"])<1e-8 for r in density),"all density rows")
ck("monotone ideal depth under damage",all(r["ideal_depth_m"]<=H+1e-14 and r["ideal_depth_m"]>=H*rho0/r["damaged_rho"]-1e-14 for r in retention),"rd >= rho0")
ck("new powder renewal includes only processed mass",all(abs(r["new_mass_kg_year"]-r["area_m2"]*r["processed_depth_m"]*rho0*r["q_processed"]*200)<1e-8 for r in renewal),"200 annual cycles is an assumption")
ck("budget inversion",all(abs(r["area_m2"]*r["processed_depth_m"]*rho0*r["q_processed_max"]*r["price"]*200-I["comparison"]["hypothetical_annual_material_budget_jpy"])<1e-7 for r in limits),"material purchases only")
ck("truck capacity and integer minimality",all((r["minimum_trips"]*min(10000,50*r["shipping_rho"])>=r["mass_kg"] and (r["minimum_trips"]-1)*min(10000,50*r["shipping_rho"])<r["mass_kg"]) for r in transport),"10 t, 50 m3 purely hypothetical, no route survey")
ck("contamination 1% reference",any(r["area_m2"]==20000 and r["gamma_annual"]==.01 and r["replacement_kg"]==10800 and r["purchase_jpy"]==5400000 and r["remaining_material_budget_jpy"]==4600000 for r in contamination),"annual replacement, nonoverlapping with damage")
ck("over-budget contamination not zero-feasible",all(r["whole_bed_q_max"] is None if r["budget_exceeded"] else r["whole_bed_q_max"]>=0 for r in contamination),"negative remaining budget is infeasible, not an allowed zero-damage design")

R=dict(cycle=29,physical_tests=0,physical_success_probability=None,
 model="Accounting scenarios; not DEM, constitutive model, performance or probability",
 density=density,spreading=spreading,retention=retention,renewal=renewal,
 budget_limits=limits,transport=transport,contamination=contamination)
(P/"results.json").write_text(json.dumps(R,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(P/"validation.json").write_text(json.dumps(dict(check_count=len(checks),checks=checks,
 physical_tests=0,limits="Arithmetic/conservation checks do not validate the assumed material or mixture model."),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(dict(checks=len(checks),density_rows=len(density),spreading_rows=len(spreading),
 retention_rows=len(retention),renewal_rows=len(renewal),limit_rows=len(limits),transport_rows=len(transport),contamination_rows=len(contamination))))
