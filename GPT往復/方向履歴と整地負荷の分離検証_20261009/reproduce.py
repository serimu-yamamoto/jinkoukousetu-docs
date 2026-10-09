"""Cycle93: dimensionless counterexamples, not a wear or success predictor."""
from pathlib import Path
import math,json,sys
P=Path(__file__).resolve().parent
I=json.loads((P/"inputs.json").read_text(encoding="utf-8"))
checks=[]
def ck(name,v):
    checks.append({"name":name,"passed":bool(v)})
    if not v: raise AssertionError(name)
def close(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12)
def activity(r):
    if r<=0:raise ValueError("positive interval / unknown length required")
    return -math.expm1(-r)/r
def tensor(angles,weights):
    W=sum(weights)
    if W<=0:return None
    xx=sum(w*math.cos(math.radians(a))**2 for a,w in zip(angles,weights))/W
    xy=sum(w*math.sin(math.radians(a))*math.cos(math.radians(a)) for a,w in zip(angles,weights))/W
    yy=1-xx
    eig=(1-math.hypot(xx-yy,2*xy))/2
    return {"xx":xx,"xy":xy,"yy":yy,"min_eigenvalue":max(0,eig)}
rows=[]
for ell in I["hypothetical_decay_lengths_mm"]:
    for interval in I["intervals_mm"]:
        n=round(I["diagnostic_distance_mm"]/interval)
        rows.append({"ell_mm_assumed":ell,"interval_mm":interval,"segments":n,
                     "loaded_sliding_mm":interval*n,"orientation_min_eigenvalue":.5,
                     "normalized_activity":activity(interval/ell)})
q=tensor([0,90],[1,1]);rev=tensor([0,180],[1,1])
ck("orthogonal_half",close(q["min_eigenvalue"],.5))
ck("reciprocation_not_cross",close(rev["min_eigenvalue"],0))
ck("zero_work_undefined",tensor([0],[0]) is None)
ck("global_rotation_invariance",close(tensor([37,127],[1,1])["min_eigenvalue"],.5))
ck("loaded_intervals_even",all(r["segments"]%2==0 for r in rows))
ck("same_distance",all(close(r["loaded_sliding_mm"],1000) for r in rows))
ck("activity_bounded",all(0<r["normalized_activity"]<1 for r in rows))
ck("small_ratio_limit",close(activity(1e-10),1-5e-11))
ck("large_ratio_limit",close(activity(100),.01))
ck("r1",close(activity(1),1-math.exp(-1)))
ck("r10",close(activity(10),.09999546000702375))
# Numerical integral independently checks the exponential diagnostic kernel.
N=100000;r=3
integral=sum(math.exp(-(k+.5)*r/N) for k in range(N))/N
ck("kernel_midpoint_integral",abs(integral-activity(r))<2e-10)
ratio=activity(.1)/activity(10)
ck("same_tensor_different_history",ratio>9.5 and ratio<9.52)
ck("activity_decreases",all(activity(x)>activity(x*2) for x in [.001,.01,.1,1,10]))
low,high=1e-12,100
for _ in range(100):
    mid=(low+high)/2
    if activity(mid)>.1:low=mid
    else:high=mid
ck("inverse_budget",abs(activity(high)-.1)<1e-12)
v=I["test_assumptions"]["speed_m_s"];a=I["test_assumptions"]["acceleration_m_s2"]
d=I["test_assumptions"]["stroke_m"]
ck("trapezoid_possible",d>=v*v/a)
tstroke=d/v+v/a
const_fraction=1-v*v/(a*d)
strokes=round(I["test_assumptions"]["distance_m"]/d)
nruns=I["test_assumptions"]["pairs"]
motion=strokes*tstroke
event=strokes*I["test_assumptions"]["matched_stop_s"]
mount=I["test_assumptions"]["mount_h_per_pair"]
hours=nruns*((motion+event)/3600+mount)
ck("stroke_count",strokes==1000)
ck("motion_time",close(motion,25))
ck("constant_speed_fraction",close(const_fraction,.75))
ck("equal_stop_time",close(event,2000))
ck("planned_pair_count",nruns==2*3*3)
ck("test_hour_budget",close(hours,16.125))
ck("fast_ski_speed_not_reproduced",10*10/a>d)
costs=[{"rate_JPY_h_assumed":c,"partial_cost_JPY":c*hours} for c in I["test_assumptions"]["rates_JPY_h"]]
ck("partial_cost_arithmetic",all(close(x["partial_cost_JPY"]/x["rate_JPY_h_assumed"],hours) for x in costs))
# Separate lowering maintenance contact load from erasing a surface's prior orientation.
angles=[0,90];global_q=tensor(angles,[1,1]);local_q=tensor([0,0],[1,1])
ck("different_patches_not_one_history",global_q["min_eigenvalue"]>.49 and local_q["min_eigenvalue"]==0)
results={"physical_experiments":0,"success_probability":None,
"wear_volume_prediction":None,"actual_decay_length_mm":None,"wear_savings_fraction":None,
"diagnostic_rows":rows,
"equal_tensor_counterexample":{"short_r":.1,"long_r":10,"short_activity":activity(.1),"long_activity":activity(10),"ratio_not_wear":ratio},
"inverse_diagnostic_activity_0_1":{"required_interval_over_ell":high,"not_an_acceptance_standard":True},
"test_timing":{"pairs":nruns,"strokes_per_pair":strokes,"motion_s_per_pair":motion,
"matched_stops_s_per_pair":event,"constant_speed_distance_fraction":const_fraction,
"hours_18_pairs_partial":hours,"cost_scenarios_not_quotes":costs,
"excludes":["calibration","heating","materials","metrology","staff preparation","fixture development","tax","repeat tests"]}}
validation={"count":len(checks),"all_passed":all(x["passed"] for x in checks),"checks":checks,"validates":"arithmetic only"}
for name,data in [("results.json",results),("validation.json",validation)]:
    text=json.dumps(data,ensure_ascii=False,indent=2)+"\n"
    if "--check" in sys.argv:
        assert (P/name).read_text(encoding="utf-8")==text,name+" changed"
    else:(P/name).write_text(text,encoding="utf-8",newline="\n")
print(json.dumps({"checks":len(checks),"rows":len(rows),"test_hours_partial":hours,"physical_experiments":0}))
