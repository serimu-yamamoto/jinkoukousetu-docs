"""Cycle 91. Hypothetical elastic/capillary and cost comparison, no experiment.
Uses no measured 50 C modulus, friction coefficient or rain result.
Run python reproduce.py; --check compares recomputed objects without rewriting.
"""
from pathlib import Path
import json, math, itertools, sys
P=Path(__file__).resolve().parent
I=json.loads((P/"inputs.json").read_text(encoding="utf-8"))
R=I["reference"];W=I["wet"];C=I["cost"]
checks=[]
def ck(name,ok):
 if not ok:raise AssertionError(name)
 checks.append({"name":name,"passed":True})
def near(a,b):return math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-15)
def simpson(f,a,b,n=200):
 h=(b-a)/n
 return h/3*(f(a)+f(b)+sum((4 if j%2 else 2)*f(a+j*h) for j in range(1,n)))
def section(layers,n=400):
 D=sum(e*(hi**3-lo**3)/3 for lo,hi,e in layers)
 def Q(z):return sum(e*(hi*hi-max(z,lo)**2)/2 for lo,hi,e in layers if hi>z)
 v=sum(simpson(lambda z:Q(z)**2/(e/(2*(1+R["poisson_ratio_assumed"]))),lo,hi,n) for lo,hi,e in layers)
 return D,D*D/v
t0=R["initial_thickness_m"];phi=R["porosity"];d=R["initial_dense_depth_m"]
tc=t0-2*d;ts=(1-phi)*d;tf=tc+2*ts;tm=t0*(1-phi);E=R["skin_modulus_Pa_assumed"];rho=R["solid_density_kg_m3_assumed"]
layers=[(-tf/2,-tc/2,E),(-tc/2,tc/2,E*R["core_modulus_ratio_assumed"]),(tc/2,tf/2,E)]
D0,K0=section(layers);D0fine,K0fine=section(layers,800)
span=R["span_m"];b=R["arm_width_m"];l=R["arm_length_m"];hole=R["hole_m"]
area=2*span*b-b*b-math.pi*hole*hole/4
particle0=rho*tm*area;yield_geo=area/R["tile_area_m2"];y=yield_geo*C["quality_yield_assumed"]
F=R["nominal_pressure_Pa_assumed"]*R["tile_area_m2"]
tau=1-W["temperature_K"]/W["critical_temperature_K"]
gamma=W["B_N_m"]*tau**W["exponent"]*(1+W["b"]*tau)
def mechanics(D,K,t):
 db=F*l**3/(3*b*D);ds=F*l/(b*K)
 return {"tip_load_N_assumed":F,"bending_deflection_um":db*1e6,"shear_deflection_um":ds*1e6,"total_deflection_um":(db+ds)*1e6,
 "root_outer_strain_linear":F*l*t/(2*b*D),"D_per_width_N_m":D,"K_per_width_N_m":K}
base_m=mechanics(D0,K0,tf)
def wet(D,K):
 A=gamma*W["cos_angle_assumed"]*(l**4/(2*D)+2*l*l/K)
 rows=[]
 for gap in W["gaps_m_assumed"]:
  lam=A/gap**2;cl=2*lam/(1+math.sqrt(1-4*lam)) if lam<=.25 else None
  rows.append({"gap_um_assumed":gap*1e6,"lambda":lam,"closure_fraction":cl,"has_small_equilibrium_in_model":lam<=.25})
 return {"rows":rows,"critical_gap_um_in_model":2*math.sqrt(A)*1e6,
 "gap_for_diagnostic_closure_limit_um":math.sqrt(A/(W["closure_fraction_diagnostic_limit"]*(1-W["closure_fraction_diagnostic_limit"])))*1e6,
 "actual_rain_result":None}
mass0=C["reference_area_m2"]*C["reference_depth_m"]*C["reference_bed_density_kg_m3_assumed"]
count=mass0/particle0
def production(mass,t,rho1):
 gross=mass/y;virgin=gross*(1-C["reject_recovery_assumed"]*(1-y))
 web=gross/(t*rho1*C["web_width_m_assumed"]*C["campaign_h_assumed"]*60)
 return {"finished_kg_same_particle_inventory":mass,"gross_processed_kg":gross,"virgin_kg_assuming_reject_recovery":virgin,
 "web_speed_m_min_assuming_yield":web,"actual_packing_density":None}
# Baseline sheet mass per area is rho * tm, not rho * tf.
p0=production(mass0,tm,rho)
rows=[{"id":"porous_reference","mode":"reference","density_kg_m3":rho,"modulus_ratio_assumed":1,"thickness_um":tf*1e6,
 "mass_ratio":1,"bending_stiffness_ratio":1,"tip_compliance_ratio":1,**base_m,"wet":wet(D0,K0),"production":p0}]
for mode,r,rhod in itertools.product(["equal_mass","equal_bending"],I["comparison"]["dense_to_skin_modulus_ratios_assumed"],I["comparison"]["density_cases_kg_m3"]):
 Ed=E*r;t=tm*rho/rhod if mode=="equal_mass" else (12*D0/Ed)**(1/3)
 D,K=section([(-t/2,t/2,Ed)])
 m=mechanics(D,K,t);mass_ratio=rhod*t/(rho*tm)
 rows.append({"id":f"dense_{mode}_r{r}_rho{rhod}","mode":mode,"density_kg_m3":rhod,"density_status":"930 is common-density diagnostic; 963/969 are typical grade values, not measured lots",
 "modulus_ratio_assumed":r,"actual_50C_modulus":None,"thickness_um":t*1e6,
 "mass_ratio":mass_ratio,"bending_stiffness_ratio":D/D0,"tip_compliance_ratio":m["total_deflection_um"]/base_m["total_deflection_um"],
 **m,"wet":wet(D,K),"production":production(mass0*mass_ratio,t,rhod)})
def row(mode,r=1,rhod=930):return next(x for x in rows if x["mode"]==mode and x["modulus_ratio_assumed"]==r and x["density_kg_m3"]==rhod)
costs=[]
for x,pd,qp in itertools.product(rows,C["dense_price_yen_kg_ex_tax_assumed"],C["powder_all_conversion_yen_per_processed_kg_ex_tax_assumed"]):
 if x["mode"]=="reference":continue
 cp=p0["virgin_kg_assuming_reject_recovery"]*C["powder_price_yen_kg_ex_tax_assumed"]+p0["gross_processed_kg"]*qp
 prod=x["production"];raw=prod["virgin_kg_assuming_reject_recovery"]*pd
 qmax=(cp-raw)/prod["gross_processed_kg"]
 costs.append({"geometry_id":x["id"],"powder_conversion_yen_per_processed_kg_assumed":qp,"dense_price_yen_kg_assumed":pd,
 "reference_material_plus_all_conversion_yen_ex_tax_assumed":cp,"dense_virgin_material_yen_ex_tax_assumed":raw,
 "maximum_dense_conversion_yen_per_processed_kg_to_break_even":qmax,"even_zero_conversion_breaks_even":qmax>=0,
 "includes_site_groomer":False,"actual_quote":None})
powders=[{**x,"base_thickness_over_mean_particle_size":200/x["mean_size_um"],"original_skin_depth_over_mean_particle_size":25/x["mean_size_um"],
 "final_skin_thickness_over_mean_particle_size":15/x["mean_size_um"],"uniform_skin_proven":False} for x in I["powders"]]
ck("base_layers_conserve_solid_volume",near(tc*(1-phi)+2*ts,tm))
ck("base_final_thickness_180um",near(tf,180e-6))
ck("base_D_matches_cycle86",near(D0,5e8*.0002**3/12*.459))
ck("layer_quadrature_converges",near(K0,K0fine))
Dh,Kh=section([(-tm/2,tm/2,E)])
ck("dense_bending_closed_form",near(Dh,E*tm**3/12))
ck("dense_shear_closed_form",near(Kh,(5/6)*(E/(2*(1+R["poisson_ratio_assumed"])))*tm))
ck("equal_mass_constant_rho_stiffness_ratio",near(row("equal_mass")["bending_stiffness_ratio"],8/17))
ck("equal_mass_all_density_cases",all(near(x["mass_ratio"],1) for x in rows if x["mode"]=="equal_mass"))
ck("equal_bending_all_moduli",all(near(x["bending_stiffness_ratio"],1) for x in rows if x["mode"]=="equal_bending"))
ck("equal_bending_thickness_cube_relation",near(row("equal_bending")["thickness_um"]**3,120**3*17/8))
ck("two_equalities_require_specific_E",near(row("equal_mass",1,930)["bending_stiffness_ratio"]*2.125,1))
ck("inverse_modulus_compliance_equal_mass",near(row("equal_mass",.5)["tip_compliance_ratio"],2*row("equal_mass",1)["tip_compliance_ratio"]))
ck("surface_tension_matches_50C",math.isclose(gamma,.06794,rel_tol=1e-4))
wetrows=[w for x in rows for w in x["wet"]["rows"]]
ck("wet_equilibrium_satisfies_quadratic",all(near(w["closure_fraction"]*(1-w["closure_fraction"]),w["lambda"]) for w in wetrows if w["closure_fraction"] is not None))
ck("wet_gap_inverse_square",all(near(x["wet"]["rows"][0]["lambda"]/x["wet"]["rows"][1]["lambda"],6.25) for x in rows))
ck("baseline_20um_has_equilibrium",rows[0]["wet"]["rows"][0]["has_small_equilibrium_in_model"])
ck("dense_equalmass_20um_counterexample",not row("equal_mass")["wet"]["rows"][0]["has_small_equilibrium_in_model"])
ck("dense_equalmass_50um_below_10percent",row("equal_mass")["wet"]["rows"][1]["closure_fraction"]<.1)
ck("softer_dense_50um_exceeds_10percent",row("equal_mass",.5)["wet"]["rows"][1]["closure_fraction"]>.1)
ck("critical_gap_reproduces_fold",all(near(x["wet"]["rows"][0]["lambda"]*(20/x["wet"]["critical_gap_um_in_model"])**2,.25) for x in rows))
ck("10percent_gap_above_fold",all(x["wet"]["gap_for_diagnostic_closure_limit_um"]>x["wet"]["critical_gap_um_in_model"] for x in rows))
ck("mass_reference_135t",near(mass0,135000))
ck("same_inventory_particle_number_preserved",all(near(x["production"]["finished_kg_same_particle_inventory"]/(x["mass_ratio"]*particle0),count) for x in rows))
ck("gross_yield_balance",all(near(x["production"]["gross_processed_kg"]*y,x["production"]["finished_kg_same_particle_inventory"]) for x in rows))
ck("same_inventory_web_speed_preserved",all(near(x["production"]["web_speed_m_min_assuming_yield"],p0["web_speed_m_min_assuming_yield"]) for x in rows))
for mode in ["equal_mass","equal_bending"]:
 x=row(mode);cs=next(q for q in costs if q["geometry_id"]==x["id"] and q["dense_price_yen_kg_assumed"]==800 and q["powder_conversion_yen_per_processed_kg_assumed"]==300)
 ck("cost_balance_identity_"+mode,near(cs["dense_virgin_material_yen_ex_tax_assumed"]+cs["maximum_dense_conversion_yen_per_processed_kg_to_break_even"]*x["production"]["gross_processed_kg"],cs["reference_material_plus_all_conversion_yen_ex_tax_assumed"]))
ck("equal_bending_more_material_at_same_E_rho",row("equal_bending")["mass_ratio"]>1)
ck("fine_powder_not_uniform_skin_evidence",all(not x["uniform_skin_proven"] for x in powders))
ck("unmeasured_success",I["physical_experiments"]==0 and I["success_probability"] is None)
frontier=[]
for rhod in I['comparison']['density_cases_kg_m3']:
 t=tm*rho/rhod;required_ratio=12*D0/(E*t**3)
 D,K=section([(-t/2,t/2,E*required_ratio)])
 ck('mass_stiffness_frontier_'+str(rhod),near(D,D0) and near(rhod*t,rho*tm))
 frontier.append({'dense_density_kg_m3':rhod,'equal_mass_thickness_um':t*1e6,'minimum_modulus_ratio_to_preserve_bending':required_ratio,'required_dense_modulus_MPa_if_reference500':required_ratio*500,'actual_50C_modulus':None})
price_limits=[]
for mode in ['equal_mass','equal_bending']:
 x=row(mode);pd=x['production'];total=p0['virgin_kg_assuming_reject_recovery']*500+p0['gross_processed_kg']*300
 price=(total-pd['gross_processed_kg']*100)/pd['virgin_kg_assuming_reject_recovery']
 ck('price_limit_balance_'+mode,near(pd['virgin_kg_assuming_reject_recovery']*price+pd['gross_processed_kg']*100,total))
 price_limits.append({'mode':mode,'modulus_ratio_assumed':1,'density_kg_m3_assumed':930,'powder_price_assumed':500,'powder_conversion_assumed':300,'dense_conversion_assumed':100,'maximum_dense_price_yen_kg_ex_tax':price,'quote':None})
result={"cycle":91,"physical_experiments":0,"success_probability":None,"all_50C_moduli_assumed":True,"surface_tension_N_m":gamma,
 "geometric_yield":yield_geo,"total_yield_assumed":y,"reference_particle_mass_kg":particle0,"reference_particle_count":count,
 "equal_mass_bending_frontier":frontier,"inverse_price_limits":price_limits,"comparison_rows":rows,"powder_resolution":powders,"cost_rows":costs,"chosen_material":None,"actual_total_project_cost_yen":None}
validation={"count":len(checks),"all_passed":all(c["passed"] for c in checks),"checks":checks,"scope":"Arithmetic, conservation, inverse and counterexample checks; not physical validation"}
out={"results.json":result,"validation.json":validation}
for name,obj in out.items():
 if "--check" in sys.argv:assert json.loads((P/name).read_text(encoding="utf-8"))==obj,name
 else:(P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"numeric_checks":len(checks),"comparison_rows":len(rows),"wet_rows":len(wetrows),"cost_rows":len(costs),"physical_trials":0,"mode":"check" if "--check" in sys.argv else "write"}))
