"""H52 conditional mechanics. SI units; not a physical experiment or probability model.
Run: python -X utf8 model.py
Python standard library only. Figures are generated separately.
"""
import csv, json, math
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = "a6da338c378c3d5ae41f85daa9f7053db2d1dc49"
checks = []
def check(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append({"name": name, "passed": True})
def close(a, b, tol=1e-9):
    return math.isclose(a, b, rel_tol=tol, abs_tol=1e-18)
def save_json(name, data):
    (HERE/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
def save_csv(name, rows):
    with (HERE/name).open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader(); w.writerows(rows)

# H50 reference bridge: identical spherical contacts, pure water at 50 C.
R, gap, gamma = 15e-6, 20e-6, .06794390594
water_volume = .01*R**3
A=1.05*math.sqrt(R/water_volume)
B=2.5*R/water_volume
F0=2*math.pi*R*gamma
rupture=water_volume**(1/3)
def cap(s):
    return F0/(1+A*s+B*s*s)
def required(slack):
    G=gap-2*slack
    if G <= rupture:
        return None
    # Minimum denominator gives maximum force / remaining return displacement.
    # D'(s) = (A*G-1) + 2*(B*G-A)*s - 3*B*s*s.
    aa,bb,cc=-3*B,2*(B*G-A),A*G-1
    disc=bb*bb-4*aa*cc
    pts=[0,rupture]
    if disc>=0:
        for s in ((-bb+math.sqrt(disc))/(2*aa),(-bb-math.sqrt(disc))/(2*aa)):
            if 0<s<rupture: pts.append(s)
    return max(2*F0/((G-s)*(1+A*s+B*s*s)) for s in pts)
bridge=[]
for um in (0,1,2,3,4,5,7,9):
    d=um*1e-6; req=required(d)
    sampled=None if req is None else max(cap(rupture*i/20000)/((gap-rupture*i/20000)/2-d) for i in range(20001))
    bridge.append({"slack_um":um,"required_k_N_m":req,"grid_k_N_m":sampled,
                   "path_possible":req is not None,"design_k_N_m":1.1,
                   "minimum_uniform_E_fraction":None if req is None else req/1.1})
check("capillary extrema versus 20001-point independent path sampling",
      all(x["required_k_N_m"] is None or close(x["required_k_N_m"],x["grid_k_N_m"],2e-7) for x in bridge))
check("9 um slack prevents full water-bridge release", bridge[-1]["path_possible"] is False)
check("zero-slack contact end point reproduces 2F0/gap", close(required(0),2*F0/gap))

# Linear small-strain lower bound. Two ties + two compression return rails.
# One tie and one rail are active in either direction; k is their series stiffness.
k, delta, eps, SF=1.1,10e-6,.05,2
force=k*delta
mechanics=[]
for E_MPa in (1,2.66,10,100):
    E=E_MPa*1e6
    Lb=(108*k*delta**4/(E*math.pi*eps**4))**.2
    rb=eps*Lb**2/(3*delta)
    Vb=math.pi*rb**2*Lb
    for panels in (0,1,2,3):
        # panels=0: ideal, deliberately ignores buckling (not a buildable choice).
        kmin=0 if panels==0 else math.sqrt(4*E*SF*force/(math.pi*panels**2))
        q=max(2,kmin/k)
        kf=q*k; kt=k*q/(q-1)
        L=max(force/kt,force/kf)/eps
        At,Af=kt*L/E,kf*L/E
        rt,rf=math.sqrt(At/math.pi),math.sqrt(Af/math.pi)
        V=2*(At+Af)*L
        Pcr=None if panels==0 else math.pi**2*E*(math.pi*rf**4/4)/(L/panels)**2
        mechanics.append({"E_MPa":E_MPa,"effective_panels":panels,"q":q,
          "tie_k_N_m":kt,"rail_k_N_m":kf,"effective_k_N_m":kt*kf/(kt+kf),
          "member_length_um":L*1e6,"tie_radius_um":rt*1e6,"rail_radius_um":rf*1e6,
          "tie_strain":force/kt/L,"rail_strain":force/kf/L,
          "Euler_load_uN":None if Pcr is None else Pcr*1e6,
          "pair_volume_m3":V,"beam_length_um":Lb*1e6,"beam_radius_um":rb*1e6,
          "beam_volume_m3":Vb,"pair_to_beam_volume":V/Vb,
          "excluded_brace_joint_volume_m3":None,
          "maximum_extra_volume_before_losing_material_advantage_m3":max(0,Vb-V)})
check("all optimized members reproduce k and obey assumed strain budget",
      all(close(x["effective_k_N_m"],k) and max(x["tie_strain"],x["rail_strain"])<=eps*(1+1e-12) for x in mechanics))
check("round cantilever reconstruction by independent k and surface-strain equations",
      all(close(3*x["E_MPa"]*1e6*math.pi*(x["beam_radius_um"]*1e-6)**4/(4*(x["beam_length_um"]*1e-6)**3),k)
          and close(3*x["beam_radius_um"]*1e-6*delta/(x["beam_length_um"]*1e-6)**2,eps) for x in mechanics))
check("Euler capacity meets twice the active return force in panel scenarios",
      all(x["Euler_load_uN"] is None or x["Euler_load_uN"] >= SF*force*1e6*(1-1e-12) for x in mechanics))
# Exhaustive q comparison independent of dimensional objective implementation.
def normalized_volume(q):
    return 2*q*q/(q-1)*max((q-1)/q,1/q)**2
grid_ok=True
for x in mechanics:
    lo=1.00001 if x["effective_panels"]==0 else max(1.00001,math.sqrt(4*x["E_MPa"]*1e6*SF*force/(math.pi*x["effective_panels"]**2))/k)
    grid=[lo+(max(4,2*x["q"])-lo)*i/40000 for i in range(40001)]
    grid_ok &= normalized_volume(x["q"]) <= min(normalized_volume(q) for q in grid)*(1+1e-12)
check("analytical q optimum versus 40001-point constrained grid", grid_ok)
check("unbraced E2.66 case loses material advantage",
      next(x for x in mechanics if x["E_MPa"]==2.66 and x["effective_panels"]==1)["pair_to_beam_volume"]>1)
check("ideal ties plus rails equal one sixth of optimized cantilever volume",
      all(close(x["pair_to_beam_volume"],1/6) for x in mechanics if x["effective_panels"]==0))

# Independently published observations: do not fuse their recipes or temperatures.
source_values=[
 {"source":"WO2024261265A1","quantity":"dry_spun_Y_after_first_swelling","value":.71,"denominator":"initial dry length","scope":"Example 3; room-temperature water; not 50 C"},
 {"source":"WO2024261265A1","quantity":"dry_spun_Y_after_redrying","value":.68,"denominator":"initial dry length","scope":"Example 3; 72 h room-temperature drying"},
 {"source":"WO2024261265A1","quantity":"wet_spun_Y_after_first_swelling","value":.37,"denominator":"initial dry length","scope":"Example 3; room-temperature water"},
 {"source":"WO2024261265A1","quantity":"wet_spun_Y_after_redrying","value":.30,"denominator":"initial dry length","scope":"Example 3; 72 h room-temperature drying"},
 {"source":"10.1002/advs.202414339","quantity":"PVA15_AQ_E_MPa","value":1.00,"denominator":"engineering tensile strain","scope":"reported specimen; wet 50 C modulus not established"},
 {"source":"10.1002/advs.202414339","quantity":"PVA15_TPU5_AQ_E_MPa","value":1.47,"denominator":"engineering tensile strain","scope":"different material from patent"},
 {"source":"10.1002/advs.202414339","quantity":"PVA15_TPU8_AQ_E_MPa","value":2.66,"denominator":"engineering tensile strain","scope":"illustrative scale only; not H52 calibration"},
 {"source":"10.1016/j.mechmat.2021.103984","quantity":"incompletely_recovered_sample_mass_ratio","value":.70,"denominator":"initial fully hydrated specimen total mass","scope":"not 70 wt% water; still incomplete after 4 h rest"}
]
humidity=[]
Lh,dh=250e-6,10e-6
for label,wet,dry in (("dry_spun",.71,.68),("wet_spun",.37,.30)):
    ft=dry/wet
    frames=[("fixed",1.0),("matched",ft)]+[("offset_"+str(off),ft+off) for off in (-.02,-.01,-.005,.005,.01,.02)]
    for name,ff in frames:
        pre=ff/ft-1
        extension=max(0,(Lh*ff+dh)/(Lh*ft)-1)
        slack=max(0,Lh*(ft-ff))
        humidity.append({"source_example":label,"frame_case":name,"tie_length_factor":ft,
            "frame_length_factor":ff,"dry_tie_length_um":Lh*ft*1e6,
            "initial_mismatch_strain":pre,"maximum_tension_strain":extension,
            "slack_um":slack*1e6,"strain_le_5pct":extension<=.05,
            "slack_le_3um":slack<=3e-6,"screen_only_not_feasibility":True})
dry_matched=next(x for x in humidity if x["source_example"]=="dry_spun" and x["frame_case"]=="matched")
dry_fixed=next(x for x in humidity if x["source_example"]=="dry_spun" and x["frame_case"]=="fixed")
wet_fixed=next(x for x in humidity if x["source_example"]=="wet_spun" and x["frame_case"]=="fixed")
ft=.68/.71
allow_pre=eps-dh/(Lh*ft)
allow_positive_factor=ft*allow_pre
check("source Y values treated as remaining lengths, not contraction amounts",
      close(dry_fixed["initial_mismatch_strain"],.71/.68-1) and close(wet_fixed["initial_mismatch_strain"],.37/.30-1))
check("matched shrinkage removes preload but not stroke strain",
      close(dry_matched["initial_mismatch_strain"],0) and dry_matched["maximum_tension_strain"]>0)
check("fixed dry-spun frame exceeds illustrative 5 percent budget while matched frame fits",
      not dry_fixed["strain_le_5pct"] and dry_matched["strain_le_5pct"])
check("positive mismatch limit substitutes back into maximum strain equation",
      close((Lh*(ft+allow_positive_factor)+dh)/(Lh*ft)-1,eps))

# Constant reference particle count: do not use this as actual H52 density.
Vbase=6*math.pi*(30e-6)**2*150e-6
Ngrain=108000/(1200*Vbase)
Nports=6*Ngrain
ref={x["effective_panels"]:x for x in mechanics if x["E_MPa"]==2.66}
beam_volume=ref[2]["beam_volume_m3"]*Nports
pair_volume=ref[2]["pair_volume_m3"]*Nports
volume_saving=beam_volume-pair_volume
cost=[]
for unit in (200000,600000,1200000):
    cost.append({"reference_number_of_return_ports":Nports,"unit_JPY_per_m3":unit,
     "cantilever_members_m3":beam_volume,"two_panel_members_m3":pair_volume,
     "gross_member_cost_saving_JPY":volume_saving*unit,
     "brace_joint_making_and_life_cost_excluded":True,"quote":False})
check("gross cost difference recomputes from both member-volume costs",
      all(close((x["cantilever_members_m3"]-x["two_panel_members_m3"])*x["unit_JPY_per_m3"],x["gross_member_cost_saving_JPY"]) for x in cost))
results={
 "cycle":52,"base_commit":BASE,"physical_tests":0,"success_probability":None,
 "bridge":{"R_m":R,"gap_m":gap,"water_volume_m3":water_volume,"gamma_N_m":gamma,
           "rupture_m":rupture,"F0_N":F0,"required_k_slack3_N_m":required(3e-6),
           "minimum_E_retention_slack3":required(3e-6)/k},
 "mechanics":{"k_N_m":k,"stroke_m":delta,"strain_budget_assumed":eps,
              "active_return_force_N":force,"Euler_safety_factor_assumed":SF,
              "selected_reference_E_MPa":2.66,"two_panel_volume_ratio":ref[2]["pair_to_beam_volume"],
              "unbraced_volume_ratio":ref[1]["pair_to_beam_volume"],
              "two_panel_extra_volume_allowance_per_port_m3":ref[2]["maximum_extra_volume_before_losing_material_advantage_m3"],
              "complete_three_dimensional_design":False},
 "humidity":{"reference_wet_span_m":Lh,"stroke_m":dh,
             "fixed_dry_spun_max_strain":dry_fixed["maximum_tension_strain"],
             "matched_dry_spun_max_strain":dry_matched["maximum_tension_strain"],
             "allowable_positive_frame_factor_difference":allow_positive_factor,
             "allowable_negative_frame_factor_difference":3e-6/Lh,
             "patent_error_bars_not_probability_distribution":True},
 "cost":{"reference_grain_count":Ngrain,"reference_port_count":Nports,
         "gross_volume_saving_m3":volume_saving,"selected_material_mass_unknown":True,
         "whole_course_cost_not_estimated_here":True},
 "counts":{"mechanics_rows":len(mechanics),"bridge_rows":len(bridge),"humidity_rows":len(humidity),
           "cost_rows":len(cost),"source_value_rows":len(source_values),"numerical_checks":len(checks)},
 "limitations":["linear elastic members; no joint/slip/creep/contact friction calculation",
 "compression panel restraints require reactions in two transverse directions; braces not free",
 "Euler member buckling is not global frame or wet local buckling",
 "capillary reference does not represent flooded or contaminated particle beds",
 "source recipes and temperatures remain separate; no synthetic material property assigned",
 "not a ski-snow-equivalence or safety validation"]
}
for name,rows in (("bridge.csv",bridge),("members.csv",mechanics),("humidity.csv",humidity),("cost.csv",cost),("source-values.csv",source_values)):
    save_csv(name,rows)
save_json("results.json",results)
save_json("numerical-checks.json",checks)
print(json.dumps(results,ensure_ascii=False,indent=2))
