from pathlib import Path
import sys,json,math,importlib.util
D=Path(__file__).resolve().parent;R=D.parents[1]
s=importlib.util.spec_from_file_location("thermal",R/"計算部品/crystal_thermal_ledger.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
i=json.loads((D/"inputs.json").read_text());checks=[]
def ck(name, value):
    assert value,name
    checks.append(name)
def eq(a,b):return math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-11)
rows=[]
for x in i["scenarios"]:
    r=m.ledger(i["initial_crystal_fraction"],x["events"]);r["name"]=x["name"];rows.append(r)
    ck(x["name"]+":phase mass",eq(r["original_crystal"]+r["new_crystal"]+r["amorphous"],1))
    ck(x["name"]+":net heat",eq(r["net_heat_normalized"],i["initial_crystal_fraction"]-r["final_crystal"]))
    ck(x["name"]+":gross transfer",eq(r["net_heat_normalized"],r["cumulative_melt"]-r["cumulative_recrystallization"]))
a,b,c=rows
ck("equal net heat does not identify original crystals",eq(a["net_heat_normalized"],b["net_heat_normalized"]) and not eq(a["original_crystal"],b["original_crystal"]))
ck("same total crystals do not identify original crystals",eq(a["final_crystal"],b["final_crystal"]))
ck("hidden turnover original fraction",eq(b["original_fraction_retained"],3/7))
ck("small net large turnover",eq(c["net_heat_normalized"],0.05) and eq(c["cumulative_melt"],0.3))
for label,initial,events in [
 ("negative initial",-0.1,[]),
 ("excess melting",0.35,[dict(melt_original=0.4,melt_new=0,recrystallize=0)]),
 ("excess crystallization",0.35,[dict(melt_original=0,melt_new=0,recrystallize=0.7)]),
 ("negative transfer",0.35,[dict(melt_original=-0.1,melt_new=0,recrystallize=0)])]:
    try:m.ledger(initial,events)
    except ValueError:ck(label,True)
    else:raise AssertionError(label)
heat=[dict(end_c=t,sensible_kwh_kg=m.sensible_heat(i["heat"]["cp_kj_kg_k"],i["heat"]["start_c"],t)) for t in i["heat"]["end_c"]]
ck("heat arithmetic80C",eq(heat[1]["sensible_kwh_kg"],1/36))
cost=[]
for rho in i["cost"]["density_kg_m3"]:
 for f in i["cost"]["fraction"]:
  for p in i["cost"]["increment_yen_kg"]:
   cost.append(dict(density_kg_m3=rho,fraction=f,increment_yen_kg=p,**m.treatment_inventory(rho,i["cost"]["bed_m"],f,p)))
ck("27 independent cost input combinations",len(cost)==27)
ck("inventory150",eq(m.treatment_inventory(150,0.45,1,100)["increment_yen_m2"],6750))
ck("local1percent sensitivity",eq(m.treatment_inventory(150,0.45,0.01,100)["increment_yen_m2"],67.5))
ck("zero local fraction",eq(m.treatment_inventory(150,0.45,0,100)["increment_yen_m2"],0))
out=dict(cycle=134,physical_trials=0,success_probability=None,dependency_hashes={},
         heat_counterexamples=rows,sensible_heat_sensitivities=heat,
         incremental_treatment_cost_sensitivities=cost,
         limitations=["No PBS rate or enthalpy fitted","No mapping from old crystals to load-bearing contacts","WAXS source index is not an absolute mass fraction","No friction, wear, strength, safety or winter performance measured"])
v=dict(count=len(checks),passed=True,checks=checks,meaning="implementation consistency only; not independent experiments")
for name,data in [("results.json",out),("validation.json",v)]:
 text=json.dumps(data,ensure_ascii=False,indent=2)+"\n"
 if "--check" in sys.argv:assert (D/name).read_text()==text,name
 else:(D/name).write_text(text,encoding="utf-8",newline="\n")
print(json.dumps(dict(checks=len(checks),scenarios=len(rows),cost_rows=len(cost),physical_trials=0)))
