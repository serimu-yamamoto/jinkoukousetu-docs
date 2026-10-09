from pathlib import Path
import json,sys,importlib.util
D=Path(__file__).resolve().parent;R=D.parents[1]
sp=importlib.util.spec_from_file_location("plan",R/"計算部品/blocked_thermal_screen.py")
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
i=json.loads((D/"inputs.json").read_text());p=m.allocate(i["histories"],i["preparation_batches"])
s=[m.schedule(len(i["histories"]),i["preparation_batches"],c,i["hold_hours"]) for c in i["capacity_sensitivities"]]
checks=[]
def ck(n,x):assert x,n;checks.append(n)
ids=[x[k] for x in p for k in ("baseline_dsc_aliquot","hotstage_then_dsc_aliquot")]
ck("18 physically distinct aliquot IDs",len(ids)==len(set(ids))==18)
ck("9 processing portions in 3 blocked preparation batches",len(p)==9 and len({x["preparation_batch"] for x in p})==3)
ck("three histories appear once per batch",all({x["history"] for x in p if x["preparation_batch"]==b}==set(i["histories"]) for b in ["B1","B2","B3"]))
ck("carrier position balanced across batches",all({x["joint_carrier_position"] for x in p if x["history"]==h}=={1,2,3} for h in i["histories"]))
ck("63 scheduled observations are repeated measures",sum(len(x["observed_timepoints"]) for x in p)==63)
ck("capacity scheduling respects batch boundaries",[x["cycles"] for x in s]==[9,6,3])
ck("hold-only times72_48_24",[x["hold_hours_only"] for x in s]==[72,48,24])
ck("no data, performance probability or confirmed quote invented",all(x["measurements"] is None for x in p) and all(x["total_quote_yen"] is None and not x["confirmed_capacity"] for x in s))
out=dict(cycle=135,physical_trials=0,success_probability=None,dependency_hashes={},
         plan=p,schedule_sensitivities=s,distinct_preparation_batches=3,
         process_portions=9,physical_aliquots=18,hotstage_aliquots=9,dsc_measurements_planned=18,
         planned_timepoint_observations=63,
         combined_capacity3_hold_hours_saved=48,
         overall_test_quote_yen=None,provider_contacts_sent=0,
         caveats=["Shared stage capacity and uniformity unconfirmed","three observations in one batch are not three independent formation batches","DSC baseline and after observation use different aliquots","18DSC measurements are not18independent batches","No recipe or free particles obtained"])
v=dict(count=len(checks),passed=True,checks=checks,meaning="allocation/data integrity checks;not experiments")
for name,data in [("results.json",out),("validation.json",v)]:
 t=json.dumps(data,ensure_ascii=False,indent=2)+"\n"
 if "--check" in sys.argv:assert (D/name).read_text()==t,name
 else:(D/name).write_text(t,encoding="utf-8",newline="\n")
print(json.dumps(dict(checks=len(checks),aliquots=18,dsc_measurements=18,physical_trials=0)))
