"""Cycle 84: identifiability of penetration hardness and lateral onset strength.
All outputs are mathematical comparisons. No measured material values are generated.
Python 3 standard library only.
"""
from pathlib import Path
import json,math,itertools
P=Path(__file__).resolve().parent
I=json.loads((P/"inputs.json").read_text(encoding="utf8"));R=I["reference"]
checks=[]
def ck(name,ok):
    if not ok:raise AssertionError(name)
    checks.append({"name":name,"passed":True})
def write(name,v):(P/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf8",newline="\n")
def volume(e,theta,L,W):
    t=math.radians(theta)
    if theta==0:return L*W*e
    if not 0<theta<90:raise ValueError("angle")
    if e<=W*math.sin(t):return L*e*e/(2*math.tan(t))
    return L*W*math.cos(t)*(e-W*math.sin(t)/2)
def depth(N,H,theta,L,W):
    if N<=0 or H<=0:raise ValueError("positive force and H")
    if theta==0:return N/(H*L*W),"flat"
    t=math.radians(theta)
    if not 0<theta<90:raise ValueError("angle")
    partial=math.sqrt(2*N*math.tan(t)/(H*L))
    if partial<W*math.sin(t):return partial,"partial_width"
    return N/(H*L*W*math.cos(t))+W*math.sin(t)/2,"full_width_extension"
def response(N,H,S,theta,L,W):
    e,domain=depth(N,H,theta,L,W)
    return {"penetration_mm":e,"geometry_domain":domain,"lateral_onset_N":S*L*e if domain=="partial_width" else None,
            "volume_mm3":volume(e,theta,L,W),
            "lateral_law_applicable_in_this_model":domain=="partial_width",
            "actual_artificial_material_validation":False}
L=R["tool_length_mm"];W=R["tool_width_mm"];N=R["normal_force_N"];theta=R["edge_angle_deg"];H=R["H_N_mm3"];S=R["S_N_mm2"]
base=response(N,H,S,theta,L,W)
ck("reference agrees with prior geometric comparison",math.isclose(base["penetration_mm"],math.sqrt(18.75),rel_tol=1e-12) and math.isclose(base["lateral_onset_N"],74.47818472546172,rel_tol=1e-10))
sweep=[]
for a,h,s in itertools.product(I["sweep"]["angles_deg"],I["sweep"]["H_factors"],I["sweep"]["S_factors"]):
    z=response(N,H*h,S*s,a,L,W)
    sweep.append({"angle_deg":a,"H_ratio":h,"S_ratio":s,**z})
ck("volume inversion across finite-width and flat domains",all(math.isclose(H*x["H_ratio"]*x["volume_mm3"],N,rel_tol=1e-10) for x in sweep))
ck("full width and flat do not extrapolate lateral law",all(x["lateral_onset_N"] is None for x in sweep if x["geometry_domain"]!="partial_width"))
ck("both edged geometric branches exercised",all(any(x["geometry_domain"]==g for x in sweep) for g in ["partial_width","full_width_extension"]))
# Numerical integration and continuity provide an independent geometric check.
err=0
for a in [2,15,45,60]:
    t=math.radians(a);b=W*math.sin(t)
    for e in [0.3*b,b,2*b]:
        n=20000;ds=W/n
        vint=L*math.cos(t)*sum(max(e-(k+0.5)*ds*math.sin(t),0)*ds for k in range(n))
        err=max(err,abs(vint-volume(e,a,L,W))/volume(e,a,L,W))
    v1=L*b*b/(2*math.tan(t));v2=L*W*math.cos(t)*(b-b/2)
    ck("geometric continuity at "+str(a)+"deg",math.isclose(v1,v2,rel_tol=1e-12))
ck("independent strip integration",err<1e-7)
states=[]
for q in I["states"]:
    z=response(N,H*q["H_ratio"],S*q["S_ratio"],theta,L,W)
    er=z["penetration_mm"]/base["penetration_mm"]
    fr=z["lateral_onset_N"]/base["lateral_onset_N"]
    states.append({**q,**z,"penetration_ratio":er,"constant_load_onset_ratio":fr,
                   "constant_depth_onset_N":S*q["S_ratio"]*L*base["penetration_mm"],
                   "constant_depth_onset_ratio":q["S_ratio"],
                   "inverse_H_ratio":1/(er*er),"inverse_S_ratio":fr/er})
ck("dual observations identify both assumed parameters",all(math.isclose(x["inverse_H_ratio"],x["H_ratio"],rel_tol=1e-12) and math.isclose(x["inverse_S_ratio"],x["S_ratio"],rel_tol=1e-12) for x in states))
ck("wet-like counterexample strengthened apparent holding",states[2]["S_ratio"]<1 and states[2]["constant_load_onset_ratio"]>1 and states[2]["constant_depth_onset_ratio"]<1)
ck("near recovered holding hides unrecovered hardness",abs(states[5]["constant_load_onset_ratio"]-1)<0.02 and states[5]["H_ratio"]==0.5 and states[5]["penetration_ratio"]>1.4)
ck("matched onset does not identify hardness",math.isclose(states[4]["constant_load_onset_ratio"],1) and math.isclose(states[4]["penetration_ratio"],0.5))
dynamic=[]
for a,mu in itertools.product(I["diagnostic"]["dynamic_angles_deg"],I["diagnostic"]["chip_friction_values"]):
    tau=math.degrees(math.atan(mu));valid=a>tau
    v=math.tan(math.radians(a)-math.atan(mu)) if valid else None
    dynamic.append({"angle_deg":a,"assumed_chip_friction":mu,"friction_angle_deg":tau,
                    "inside_positive_cutting_angle_domain":valid,"Fc_over_N":v,"Fc_N_at_300N":N*v if valid else None,
                    "material_prediction":False,"note":"orthogonal dynamic cutting idealization; not static Sf or measured ski glide friction"})
ck("invalid cutting-angle cases remain null",any(not x["inside_positive_cutting_angle_domain"] for x in dynamic) and all(x["Fc_over_N"] is None for x in dynamic if not x["inside_positive_cutting_angle_domain"]))
ck("zero chip-friction limit",all(math.isclose(x["Fc_over_N"],math.tan(math.radians(x["angle_deg"])),rel_tol=1e-12) for x in dynamic if x["assumed_chip_friction"]==0))
# Bounded-error illustrations; no probability distributions or confidence levels.
B=I["measurement_bounds"];bounds=[]
for hf in B["H_factors"]:
    z=response(N,H*hf,S,theta,L,W);e=z["penetration_mm"];F=z["lateral_onset_N"]
    elo=e-B["penetration_halfwidth_mm"];ehi=e+B["penetration_halfwidth_mm"]
    flo=F-B["force_halfwidth_N"];fhi=F+B["force_halfwidth_N"]
    llo=L-B["length_halfwidth_mm"];lhi=L+B["length_halfwidth_mm"]
    nlo=N-B["normal_force_halfwidth_N"];nhi=N+B["normal_force_halfwidth_N"]
    alo=theta-B["angle_halfwidth_deg"];ahi=theta+B["angle_halfwidth_deg"]
    if min(elo,flo,llo,nlo)<=0:raise ValueError("bounds exceed positive domain")
    hbounds=[2*nlo*math.tan(math.radians(alo))/(lhi*ehi*ehi),2*nhi*math.tan(math.radians(ahi))/(llo*elo*elo)]
    sbounds=[flo/(lhi*ehi),fhi/(llo*elo)]
    bounds.append({"assumed_H_N_mm3":H*hf,"assumed_S_N_mm2":S,"penetration_mm":e,"onset_N":F,
                   "H_bounded_interval_N_mm3":hbounds,"S_bounded_interval_N_mm2":sbounds,
                   "relative_depth_error_bound":B["penetration_halfwidth_mm"]/e,
                   "penetration_over_assumed_grain_scale":e/B["assumed_grain_scale_mm"],
                   "statistical_confidence_level":None,"instrument_secured":False})
ck("bounded inversions enclose assumed truth",all(x["H_bounded_interval_N_mm3"][0]<x["assumed_H_N_mm3"]<x["H_bounded_interval_N_mm3"][1] and x["S_bounded_interval_N_mm2"][0]<S<x["S_bounded_interval_N_mm2"][1] for x in bounds))
ck("grain-scale diagnostic exercises sub-grain indentation",bounds[-1]["penetration_over_assumed_grain_scale"]<1<bounds[0]["penetration_over_assumed_grain_scale"])
bed=I["beds"];V=bed["length_m"]*bed["width_m"]*bed["depth_m"]
plan=[]
for state in bed["conditions"]:
    for j in range(1,bed["independent_preparations_per_condition"]+1):
        plan.append({"bed_id":state+"-"+str(j),"condition":state,"independent_bed_replicate":j,
                     "fresh_tracks":[{"control":"constant_normal_load","data":None},{"control":"matched_penetration","data":None}],
                     "status":"not_run","material_route":"after_selection_not_fixed","mass_loss_g":None,"post_yield_curve":None})
cost=[]
for rho,price in itertools.product(bed["densities_kg_m3"],bed["assumed_finished_material_yen_kg_ex_tax"]):
    mass=V*rho
    cost.append({"assumed_density_kg_m3":rho,"assumed_finished_material_yen_kg_ex_tax":price,
                 "volume_per_preparation_L":1000*V,"mass_per_preparation_kg":mass,
                 "fresh_material_for_12_preparations_kg":len(plan)*mass,
                 "assumed_material_only_yen_ex_tax":len(plan)*mass*price,
                 "actual_total_test_cost_yen":None,"quote":False})
ck("bed allocation independent at preparation level",len(plan)==12 and len({x["bed_id"] for x in plan})==12 and sum(len(x["fresh_tracks"]) for x in plan)==24 and all(x["status"]=="not_run" for x in plan))
ck("bed volume units",math.isclose(V*1000,27) and math.isclose(V*len(plan)*1000,324))
ck("costs not fabricated quotes",all(not x["quote"] and x["actual_total_test_cost_yen"] is None for x in cost))
summary={"physical_experiments":0,"success_probability":None,"equipment_secured":False,"provider_contacts_sent":0,"orders_placed":0,
         "numeric_checks":len(checks),"calculation_rows":len(sweep)+len(states)+len(dynamic)+len(bounds)+len(cost),
         "sweep_rows":len(sweep),"paired_counterexamples":len(states),"dynamic_diagnostic_rows":len(dynamic),
         "bounded_measurement_examples":len(bounds),"material_cost_sensitivity_rows":len(cost),
         "planned_bed_preparations":len(plan),"planned_tracks":24,"integration_max_relative_error":err,
         "reference":base,"key_masked_recovery":states[5],"actual_total_test_cost_yen":None,
         "new_snow_target_calibrated":False,"full_450mm_bed_verified":False}
for name,v in [("parameter_sweep.json",sweep),("paired_states.json",states),("dynamic_domain.json",dynamic),
               ("measurement_bounds.json",bounds),("bed_plan.json",plan),("material_quantities.json",cost),
               ("checks.json",checks),("summary.json",summary)]:write(name,v)
print(json.dumps({k:summary[k] for k in ["numeric_checks","calculation_rows","planned_bed_preparations","planned_tracks","physical_experiments"]}))
