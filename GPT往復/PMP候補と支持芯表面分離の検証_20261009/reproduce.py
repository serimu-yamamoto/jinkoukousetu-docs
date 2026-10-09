"""Cycle 92: new PMP evidence and conditional PE-face/PMP-core mechanics.
No measured 50 C hybrid modulus, interface adhesion, ski friction or rain result.
Uses layer-energy equations from cycle 91. python reproduce.py [--check]
"""
from pathlib import Path
import json,math,itertools,sys
P=Path(__file__).resolve().parent;I=json.loads((P/"inputs.json").read_text(encoding="utf-8"))
R=I["reference"];H=I["hybrid"];C=I["cost"];W=I["wet"]
checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append({"name":n,"passed":True})
def near(a,b):return math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-14)
def simpson(f,a,b,n=400):
 h=(b-a)/n
 return h/3*(f(a)+f(b)+sum((4 if j%2 else 2)*f(a+j*h) for j in range(1,n)))
def section(layers):
 D=sum(e*(z1**3-z0**3)/3 for z0,z1,e in layers)
 def Q(z):return sum(e*(z1*z1-max(z,z0)**2)/2 for z0,z1,e in layers if z1>z)
 integ=sum(simpson(lambda z:Q(z)**2/(e/(2*(1+R["poisson_ratio_assumed"]))),z0,z1) for z0,z1,e in layers)
 K=D*D/integ
 Dsep=sum(e*(z1-z0)**3/12 for z0,z1,e in layers)
 return D,K,Dsep,Q
Es=R["skin_modulus_MPa_assumed"]*1e6;rho0=R["solid_density_kg_m3_assumed"]
areal=rho0*R["solid_equivalent_thickness_um"]*1e-6
tref=R["finished_thickness_um"]*1e-6;cref=R["core_thickness_um"]*1e-6
D0,K0,_,_=section([(-tref/2,-cref/2,Es),(-cref/2,cref/2,Es*R["porous_core_modulus_ratio_assumed"]),(cref/2,tref/2,Es)])
l=R["arm_length_mm"]*1e-3;b=R["arm_width_mm"]*1e-3
def delta(D,K,p=2000,active=1):
 F=p*R["tile_area_mm2"]*1e-6/active
 return F*l**3/(3*b*D)+F*l/(b*K)
def wet(D,K):
 A=W["gamma_N_m"]*W["cos_theta_assumed"]*(l**4/(2*D)+2*l*l/K)
 return [{"gap_um_assumed":g,"lambda":A/(g*1e-6)**2,"small_equilibrium_exists":A/(g*1e-6)**2<=.25} for g in W["gaps_um_assumed"]]
rows=[];frontiers=[];interfaces=[]
for skin in H["skin_thickness_each_um"]:
 ts=skin*1e-6;tc=(areal-2*H["skin_density_kg_m3_assumed"]*ts)/H["core_density_kg_m3_typical"];tt=tc+2*ts
 req=(12*D0-Es*(tt**3-tc**3))/tc**3
 frontiers.append({"skin_each_um":skin,"core_um":tc*1e6,"total_um":tt*1e6,"core_mass_fraction":H["core_density_kg_m3_typical"]*tc/areal,"core_modulus_MPa_required_to_match_D0":req/1e6,"actual_50C_value":None})
 for em in H["core_moduli_MPa_assumed"]:
  layers=[(-tt/2,-tc/2,Es),(-tc/2,tc/2,em*1e6),(tc/2,tt/2,Es)]
  D,K,Dsep,Q=section(layers);d=delta(D,K)
  rec={"id":f"S{skin}_E{em}","skin_each_um":skin,"core_modulus_MPa_assumed":em,"core_um":tc*1e6,"total_um":tt*1e6,
    "areal_mass_kg_m2":2*H["skin_density_kg_m3_assumed"]*ts+H["core_density_kg_m3_typical"]*tc,"D_per_width_N_m":D,"K_per_width_N_m":K,
    "D_ratio_to_porous_reference":D/D0,"tip_deflection_um":d*1e6,"tip_deflection_over_length":d/l,
    "independent_layer_D_ratio_to_bonded":Dsep/D,"wet_fixed_root":wet(D,K),"measured":False}
  rows.append(rec)
  for p,active in itertools.product(R["nominal_pressures_Pa_assumed"],R["active_fractions_assumed"]):
   F=p*R["tile_area_mm2"]*1e-6/active
   shear=F*Q(tc/2)/(b*D)
   interfaces.append({"geometry_id":rec["id"],"nominal_pressure_Pa_assumed":p,"active_fraction_assumed":active,
    "elastic_interface_shear_Pa":shear,"tip_deflection_over_length":delta(D,K,p,active)/l,
    "linear_geometry_flag":delta(D,K,p,active)/l>.1,"peel_or_fatigue_included":False,"allowable_measured_shear":None})
dense_t=areal/H["core_density_kg_m3_typical"]
dense_req=12*D0/(dense_t**3)
tp=I["film_probe"]["thickness_um"]*1e-6;Ep=I["film_probe"]["modulus_MPa_scenario"]*1e6
Dp,Kp,_,_=section([(-tp/2,tp/2,Ep)])
film={"thickness_um":tp*1e6,"modulus_MPa_scenario":Ep/1e6,"D_ratio":Dp/D0,"linear_predicted_tip_um":delta(Dp,Kp)*1e6,
 "linear_predicted_tip_over_length":delta(Dp,Kp)/l,"large_deflection_invalidates_linear_prediction":delta(Dp,Kp)/l>.1,
 "actual_deflection":None,"temperature_note":I["film_probe"]["temperature_label"],"wet_diagnostic":wet(Dp,Kp)}
fr=[]
for mus,muc in itertools.product(I["friction"]["skin_mu_assumed"],I["friction"]["exposed_core_mu_assumed"]):
 target=I["friction"]["diagnostic_mu_limit_assumed"];drag=I["friction"]["other_drag_assumed"]
 # Every chosen exposed-core value is >= skin value.
 if near(muc,mus):
  bound=1. if mus+drag<=target else None
 else:bound=(target-drag-mus)/(muc-mus)
 feasible=bound is not None and bound>=0
 fr.append({"skin_mu_assumed":mus,"core_mu_assumed":muc,"maximum_exposed_core_normal_load_fraction":min(1,bound) if feasible else None,
 "any_fraction_feasible":feasible,"actual_load_fraction":None,"actual_ski_pair_coefficients":None,"not_area_fraction":True})
mass=C["reference_area_m2"]*C["reference_depth_m"]*C["reference_bed_density_kg_m3_assumed"]
Y=C["geometric_yield_inherited"]*C["quality_yield_assumed"];gross=mass/Y;virgin=gross*(1-C["reject_recovery_assumed"]*(1-Y))
costs=[]
for x,pc,q in itertools.product(frontiers,C["core_raw_price_yen_kg_ex_tax_assumed"],C["additional_conversion_yen_per_gross_kg_assumed"]):
 f=x["core_mass_fraction"]
 raw=virgin*f*(pc-C["skin_raw_price_yen_kg_ex_tax_assumed"])
 costs.append({"skin_each_um":x["skin_each_um"],"core_raw_price_yen_kg_assumed":pc,"additional_conversion_yen_gross_kg_assumed":q,
 "virgin_core_kg_assuming_common_yield":virgin*f,"incremental_raw_cost_yen_ex_tax":raw,"incremental_conversion_cost_yen_ex_tax":gross*q,
 "incremental_total_yen_ex_tax":raw+gross*q,"actual_quote":None,"adhesive_mass_and_yield_change_included":False})
sc=I["source_checks"]
evidence={"RT18_tear_direction_ratio":sc["film_RT18_tear_MD_TD_N_cm"][1]/sc["film_RT18_tear_MD_TD_N_cm"][0],
 "RT18_film_to_molded_resin_tensile_modulus_ratio_not_matched_tests":sc["film_RT18_modulus_MD_TD_GPa"][0]*1000/sc["RT18_resin_tensile_modulus_23C_MPa"],
 "patent_mu_ratio":sc["patent_example1_mu"]/sc["patent_A1_mu"],"patent_wear_mass_ratio":sc["patent_example1_wear_mg"]/sc["patent_A1_wear_mg"],
 "patent_friction_not_used_in_model":True}
ck("reference_D_recovers_cycle91",near(D0,.000153))
ck("areal_mass_111_6_g_m2",near(areal,.1116))
ck("15_hybrid_comparisons",len(rows)==15)
ck("all_layer_mass_conserved",all(near(x["areal_mass_kg_m2"],areal) for x in rows))
ck("thicker_PE_skins_reduce_core_fraction",frontiers[0]["core_mass_fraction"]>frontiers[1]["core_mass_fraction"]>frontiers[2]["core_mass_fraction"])
ck("15um_skins_are_quarter_of_mass",near(frontiers[1]["core_mass_fraction"],.75))
ck("density_advantage_thicker_equalmass_PMP",dense_t>120e-6)
ck("homogeneous_PMP_frontier",near(dense_req/Es,2.125*(833/930)**3))
for x in frontiers:
 tc=x["core_um"]*1e-6;tt=x["total_um"]*1e-6;req=x["core_modulus_MPa_required_to_match_D0"]*1e6
 Dx,_,_,_=section([(-tt/2,-tc/2,Es),(-tc/2,tc/2,req),(tc/2,tt/2,Es)])
 ck("inverse_core_stiffness_S"+str(x["skin_each_um"]),near(Dx,D0))
ck("bond_loss_reduces_composite_D",all(0<x["independent_layer_D_ratio_to_bonded"]<1 for x in rows))
ck("bonded_D_monotonic_in_core_E",all(rows[j]["D_ratio_to_porous_reference"]<rows[j+1]["D_ratio_to_porous_reference"] for j in [0,1,2,3,5,6,7,8,10,11,12,13]))
ck("60_interface_load_conditions",len(interfaces)==60)
ck("load_concentration_shear_factor",near(interfaces[1]["elastic_interface_shear_Pa"]/interfaces[0]["elastic_interface_shear_Pa"],10))
ck("pressure_and_concentration_factor100",near(interfaces[3]["elastic_interface_shear_Pa"]/interfaces[0]["elastic_interface_shear_Pa"],100))
ck("high_load_linear_limits_flagged",any(x["linear_geometry_flag"] for x in interfaces))
ck("50um_uniform_D_closed_form",near(Dp,Ep*tp**3/12))
ck("50um_uniform_K_closed_form",near(Kp,5/6*Ep/(2*(1+R["poisson_ratio_assumed"]))*tp))
ck("thin_film_counterexample_flagged",film["large_deflection_invalidates_linear_prediction"] and film["actual_deflection"] is None)
ck("wet_inverse_square",all(near(x["wet_fixed_root"][0]["lambda"]/x["wet_fixed_root"][1]["lambda"],6.25) for x in rows))
sel=next(x for x in fr if x["skin_mu_assumed"]==.06 and x["core_mu_assumed"]==.2)
ck("friction_budget_one_seventh",near(sel["maximum_exposed_core_normal_load_fraction"],1/7))
ck("bad_base_cannot_meet_target",all(not x["any_fraction_feasible"] for x in fr if x["skin_mu_assumed"]==.1))
ck("friction_equal_value_edge_case",not next(x for x in fr if x["skin_mu_assumed"]==x["core_mu_assumed"]==.1)["any_fraction_feasible"])
ck("all_friction_bounds_reconstruct_budget",all(near((1-x["maximum_exposed_core_normal_load_fraction"])*x["skin_mu_assumed"]+x["maximum_exposed_core_normal_load_fraction"]*x["core_mu_assumed"],.08) for x in fr if x["any_fraction_feasible"] and x["maximum_exposed_core_normal_load_fraction"]<1))
ck("friction_primary_not_transferred",not I["friction"]["source_patent_friction_used_as_design_input"])
ck("reference_mass_135t",near(mass,135000))
ck("yield_mass_balance",near(gross*Y,mass))
ck("27_incremental_cost_cases",len(costs)==27)
ck("no_added_cost_when_prices_same_and_no_processing",all(near(x["incremental_total_yen_ex_tax"],0) for x in costs if x["core_raw_price_yen_kg_assumed"]==500 and x["additional_conversion_yen_gross_kg_assumed"]==0))
ck("cost_increments_add",all(near(x["incremental_total_yen_ex_tax"],x["incremental_raw_cost_yen_ex_tax"]+x["incremental_conversion_cost_yen_ex_tax"]) for x in costs))
ck("elastic_isotropy_not_tear_isotropy",near(sc["film_RT18_modulus_MD_TD_GPa"][0],sc["film_RT18_modulus_MD_TD_GPa"][1]) and evidence["RT18_tear_direction_ratio"]>5)
ck("patent_improvement_not_ski_validation",evidence["patent_mu_ratio"]<1 and sc["patent_example1_mu"]>.08)
ck("experiment_and_success_unmeasured",I["physical_experiments"]==0 and I["success_probability"] is None)
result={"cycle":92,"physical_experiments":0,"success_probability":None,"reference_D_N_m":D0,"reference_K_N_m":K0,
 "reference_areal_mass_kg_m2":areal,"equal_mass_PMP_thickness_um":dense_t*1e6,"homogeneous_PMP_modulus_MPa_required":dense_req/1e6,
 "frontiers":frontiers,"hybrid_rows":rows,"interface_rows":interfaces,"thin_film_diagnostic":film,
 "friction_budget_rows":fr,"cost_rows":costs,"evidence_ratios":evidence,"actual_material_selected":None,"actual_50C_interface_bond":None,
 "all_50C_moduli_are_scenarios":True,"physical_grain_bed_simulation":False}
validation={"count":len(checks),"all_passed":True,"checks":checks,"scope":"Mathematical identities, inverse conditions, transfer limits and explicit counterexamples; not physical validation"}
for name,obj in {"results.json":result,"validation.json":validation}.items():
 if "--check" in sys.argv:assert json.loads((P/name).read_text(encoding="utf-8"))==obj,name
 else:(P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"checks":len(checks),"hybrid_sections":len(rows),"interface_conditions":len(interfaces),"cost_cases":len(costs),"physical_trials":0}))
