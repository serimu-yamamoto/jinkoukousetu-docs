"""Cycle 86: same-geometry mechanics, capillary screening and manufacturing.
Analytical diagnostics only. No material measurements or physical trial.
"""
from pathlib import Path
import json,math,itertools
P=Path(__file__).resolve().parent
I=json.loads((P/"inputs.json").read_text(encoding="utf8"));B=I["base"];M=I["mechanics"];W=I["wet"];C=I["production"]
checks=[]
def ck(name,ok):
 if not ok:raise AssertionError(name)
 checks.append({"name":name,"passed":True})
def write(name,obj):(P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf8",newline="\n")
def simpson(f,a,b,n=100):
 step=(b-a)/n
 return step/3*(f(a)+f(b)+sum((4 if k%2 else 2)*f(a+k*step) for k in range(1,n)))
def section(t0,e,d,Es,n=2,points=100):
 tc=t0-2*d;ts=(1-e)*d;tf=tc+2*ts
 layers=[(-tf/2,-tc/2,Es),(-tc/2,tc/2,Es*(1-e)**n),(tc/2,tf/2,Es)]
 D=sum(E*(z1**3-z0**3)/3 for z0,z1,E in layers)
 def Q(z):return sum(E*(z1*z1-max(z,z0)**2)/2 for z0,z1,E in layers if z1>z)
 integ=sum(simpson(lambda z:Q(z)**2/(E/(2*(1+M["poisson_ratio_assumed"]))),z0,z1,points) for z0,z1,E in layers)
 K=D*D/integ
 return {"core_thickness_m":tc,"skin_thickness_m":ts,"final_thickness_m":tf,"D_per_width_N_m":D,"K_shear_per_width_N_m":K}
tau=1-W["temperature_K"]/W["water_critical_temperature_K"]
gamma=W["surface_tension_B_N_m"]*tau**W["surface_tension_exponent"]*(1+W["surface_tension_b"]*tau)
ck("50C surface tension",math.isclose(gamma,.06794,rel_tol=1e-4))
geos=[]
for mode,s in itertools.product(I["modes"],I["scales"]):
 a=B["cell_size_mm"]*s;d=B["edge_inset_mm"]*s;hole=B["center_hole_mm"]*s
 span=3*a-2*d;w=a-2*d;length=(span-w)/2
 thickscale=s if mode=="uniform_3d" else 1
 t0=B["initial_thickness_mm"]*thickscale;depth=B["initial_densified_depth_each_side_mm"]*thickscale
 tf=t0-2*B["porosity"]*depth
 A=2*span*w-w*w-math.pi*hole*hole/4;tile=5*a*a
 mass=B["solid_density_kg_m3"]*(1-B["porosity"])*t0*A*1e-9
 geos.append({"id":f"{mode}_s{s}","mode":mode,"scale":s,"span_mm":span,"arm_width_mm":w,"arm_free_length_mm":length,
              "hole_mm":hole,"nominal_cut_gap_mm":2*d,"initial_thickness_mm":t0,"initial_dense_depth_mm":depth,
              "final_thickness_mm":tf,"plan_area_mm2":A,"tile_area_mm2":tile,"geometric_yield":A/tile,
              "particle_mass_kg":mass,"sheet_mass_kg_m2":B["solid_density_kg_m3"]*(1-B["porosity"])*t0*1e-3,
              "thickness_over_free_length":tf/length,"manufactured":False})
ck("H85 geometry recovered",math.isclose(geos[0]["particle_mass_kg"],3.233565564964844e-8,rel_tol=1e-12) and math.isclose(geos[0]["thickness_over_free_length"],.72))
ck("inplane area follows square scale",all(math.isclose(g["plan_area_mm2"]/geos[0]["plan_area_mm2"],g["scale"]**2) for g in geos))
ck("similar outline maintains theoretical material yield",all(math.isclose(g["geometric_yield"],.9271872587712815) for g in geos))
hom=section(.0002,0,.000025,5e8)
ck("homogeneous section bending",math.isclose(hom["D_per_width_N_m"],5e8*.0002**3/12,rel_tol=1e-12))
ck("energy shear recovers rectangular five-sixths",math.isclose(hom["K_shear_per_width_N_m"],(5/6)*(5e8/(2*1.4))*.0002,rel_tol=1e-8))
refsec=section(.0002,.4,.000025,5e8)
ck("H85 section stiffness recovered",math.isclose(refsec["D_per_width_N_m"],5e8*.0002**3/12*.459,rel_tol=1e-12))
refFine=section(.0002,.4,.000025,5e8,points=200)
ck("layerwise shear quadrature convergence",math.isclose(refsec["K_shear_per_width_N_m"],refFine["K_shear_per_width_N_m"],rel_tol=1e-8))
mech=[]
for g,E,p,active in itertools.product(geos,M["solid_moduli_MPa_assumed"],M["nominal_pressures_Pa"],M["active_support_fractions_assumed"]):
 sec=section(g["initial_thickness_mm"]*1e-3,B["porosity"],g["initial_dense_depth_mm"]*1e-3,E*1e6,n=M["core_power"])
 l=g["arm_free_length_mm"]*1e-3;b=g["arm_width_mm"]*1e-3
 F=p*g["tile_area_mm2"]*1e-6/active
 db=F*l**3/(3*b*sec["D_per_width_N_m"]);ds=F*l/(b*sec["K_shear_per_width_N_m"])
 strain=F*l*sec["final_thickness_m"]/(2*b*sec["D_per_width_N_m"])
 flags=[]
 if g["thickness_over_free_length"]>M["review_flags"]["thickness_over_free_length_above"]:flags.append("short_thick_arm_requires_3D_analysis")
 if (db+ds)/l>M["review_flags"]["tip_deflection_over_free_length_above"]:flags.append("large_displacement_requires_nonlinear_analysis")
 mech.append({"geometry":g["id"],"solid_modulus_MPa_assumed":E,"core_modulus_power":M["core_power"],"pressure_Pa_assumed":p,
              "active_support_fraction_assumed":active,"arm_tip_load_N":F,"bending_deflection_um":db*1e6,"shear_deflection_um":ds*1e6,
              "total_deflection_um":(db+ds)*1e6,"deflection_over_free_length":(db+ds)/l,"outer_fibre_strain_estimate":strain,
              "shear_to_bending_deflection":ds/db,"review_flags":flags,"actual_allowable_strain":None,"snowlike_performance":None})
def row(mode,s,E=500,p=2000,active=1):
 return next(x for x in mech if x["geometry"]==f"{mode}_s{s}" and x["solid_modulus_MPa_assumed"]==E and x["pressure_Pa_assumed"]==p and x["active_support_fraction_assumed"]==active)
for s in I["scales"]:
 ck(f"planar bending s4 and shear s2 scale {s}",math.isclose(row("planar_only",s)["bending_deflection_um"]/row("planar_only",1)["bending_deflection_um"],s**4) and math.isclose(row("planar_only",s)["shear_deflection_um"]/row("planar_only",1)["shear_deflection_um"],s**2))
ck("uniform 3D scaling does not change relative compliance",all(math.isclose(row("uniform_3d",s)["deflection_over_free_length"],row("uniform_3d",1)["deflection_over_free_length"]) for s in I["scales"]))
ck("load concentration changes force and deformation",math.isclose(row("planar_only",2,active=.1)["total_deflection_um"]/row("planar_only",2)["total_deflection_um"],10))
ck("tip compliance matches virtual work integral",math.isclose(simpson(lambda x:(.00025-x)**2/refsec["D_per_width_N_m"],0,.00025)/.00024,.00025**3/(3*.00024*refsec["D_per_width_N_m"]),rel_tol=1e-12))
wet=[]
for g,E,gap,angle in itertools.product(geos,M["solid_moduli_MPa_assumed"],W["gaps_um"],W["contact_angles_deg_assumed"]):
 sec=section(g["initial_thickness_mm"]*1e-3,B["porosity"],g["initial_dense_depth_mm"]*1e-3,E*1e6,n=M["core_power"])
 l=g["arm_free_length_mm"]*1e-3;c=math.cos(math.radians(angle));h=gap*1e-6
 lb=gamma*c*l**4/(2*sec["D_per_width_N_m"]*h*h)
 ls=gamma*c*2*l*l/(sec["K_shear_per_width_N_m"]*h*h);lam=lb+ls
 y=2*lam/(1+math.sqrt(1-4*lam)) if lam<=.25 else None
 wet.append({"geometry":g["id"],"solid_modulus_MPa_assumed":E,"gap_um_assumed":gap,"contact_angle_deg_assumed":angle,
             "lambda_bending":lb,"lambda_shear":ls,"lambda_total":lam,"small_branch_closure_fraction":y,
             "critical_initial_gap_um_in_this_model":2*math.sqrt(gamma*c*(l**4/(2*sec["D_per_width_N_m"])+2*l*l/sec["K_shear_per_width_N_m"]))*1e6,
             "uniform_gap_equilibrium_exists":lam<=.25,"actual_rain_performance":None,"free_particle_translation_included":False})
ck("wet equilibrium equation",all(math.isclose(x["small_branch_closure_fraction"]*(1-x["small_branch_closure_fraction"]),x["lambda_total"],rel_tol=1e-11) for x in wet if x["small_branch_closure_fraction"] is not None))
ck("wet critical gap formula",all(math.isclose(x["lambda_total"]*(x["gap_um_assumed"]/x["critical_initial_gap_um_in_this_model"])**2,.25,rel_tol=1e-12) for x in wet))
ck("homogeneous wet limit matches prior bending formula",math.isclose(gamma*(.00025)**4/(2*hom["D_per_width_N_m"]*(50e-6)**2),6*gamma*(.00025)**4/(5e8*(.0002)**3*(50e-6)**2),rel_tol=1e-12))
production=[]
for g,area in itertools.product(geos,C["areas_m2"]):
 mass=area*C["depth_m"]*C["bed_density_kg_m3_assumed"];y=g["geometric_yield"]*C["quality_yield_assumed"]
 gross=mass/y;virgin=gross*(1-C["reject_recovery_assumed"]*(1-y))
 goodcount=mass/g["particle_mass_kg"];cutline=(4*g["span_mm"]+math.pi*g["hole_mm"])*1e-3*goodcount/C["quality_yield_assumed"]
 speed=gross/C["campaign_h"]/g["sheet_mass_kg_m2"]/C["web_width_m"]/60
 heat=gross*C["polymer_heat_kWh_kg_ideal_assumed"]/C["thermal_efficiency_assumed"]
 thicknessratio=g["initial_thickness_mm"]/B["initial_thickness_mm"]
 production.append({"geometry":g["id"],"area_m2":area,"finished_mass_kg_assumed":mass,"good_particle_count":goodcount,
                    "gross_sheet_mass_kg":gross,"virgin_powder_kg":virgin,"processed_sheet_area_m2":gross/g["sheet_mass_kg_m2"],
                    "all_individual_contours_m":cutline,"individual_trace_equivalent_m_s":cutline/(C["campaign_h"]*3600),
                    "required_web_speed_m_min":speed,"hot_path_at_fixed_10min_m":speed*C["reference_hold_min"],
                    "diffusion_time_ratio_at_same_diffusivity":thicknessratio**2,
                    "hot_path_if_hold_scaled_only_by_thickness_squared_m":speed*C["reference_hold_min"]*thicknessratio**2,
                    "material_plus_selected_heat_yen_ex_tax_assumed":virgin*C["raw_powder_yen_kg_ex_tax_assumed"]+heat*C["electricity_yen_kWh_ex_tax_assumed"],
                    "actual_hold_time_min":None,"actual_machine_capacity":None,"actual_total_cost_yen":None})
def prod(mode,s,area=2000):return next(x for x in production if x["geometry"]==f"{mode}_s{s}" and x["area_m2"]==area)
ck("planar enlargement reduces count s2 and contour per batch s1",all(math.isclose(prod("planar_only",s)["good_particle_count"]*s*s,prod("planar_only",1)["good_particle_count"]) and math.isclose(prod("planar_only",s)["all_individual_contours_m"]*s,prod("planar_only",1)["all_individual_contours_m"]) for s in I["scales"]))
ck("uniform enlargement reduces count s3",all(math.isclose(prod("uniform_3d",s)["good_particle_count"]*s**3,prod("uniform_3d",1)["good_particle_count"]) for s in I["scales"]))
ck("equal mass and yield preserve selected raw heat subtotal",all(math.isclose(x["material_plus_selected_heat_yen_ex_tax_assumed"],70018623.91464323*(x["area_m2"]/2000),rel_tol=1e-12) for x in production))
ck("thicker sheet heat path cannot be shortened without dwell assumption",math.isclose(prod("uniform_3d",4)["hot_path_if_hold_scaled_only_by_thickness_squared_m"],4*prod("uniform_3d",1)["hot_path_at_fixed_10min_m"]))
core=[]
for n in M["core_power_sensitivity"]:
 sec=section(.0002,.4,.000025,5e8,n=n)
 core.append({"core_modulus_power_assumed":n,**sec,"actual_material":None})
plan=[]
for shape,condition,batch in itertools.product(["base_0_74mm","planar_1_48mm","planar_2_22mm","planar_2_96mm"],["dry_50C","once_wet_drained_50C"],range(1,4)):
 plan.append({"id":f"S86-{len(plan)+1:02d}","geometry":shape,"condition":condition,"independent_batch":batch,"status":"not_run","measurements":None})
ck("24 planned preparations are unperformed",len(plan)==24 and all(x["measurements"] is None and x["status"]=="not_run" for x in plan))
summary={"physical_experiments":0,"success_probability":None,"equipment_secured":False,"provider_contacts_sent":0,"orders_placed":0,
         "numeric_checks":len(checks),"calculation_rows":len(geos)+len(mech)+len(wet)+len(production)+len(core),
         "planned_preparations":len(plan),"surface_tension_N_m":gamma,
         "representative_mechanics":[row("planar_only",s) for s in I["scales"]],
         "actual_total_manufacturing_cost_yen":None,"snow_target_deflection_ratio":None,"adopted_geometry":None}
for name,obj in [("geometries.json",geos),("mechanical_screen.json",mech),("wet_screen.json",wet),("production_comparison.json",production),
                 ("core_sensitivity.json",core),("test_plan.json",plan),("checks.json",checks),("summary.json",summary)]:write(name,obj)
print(json.dumps({k:summary[k] for k in ["numeric_checks","calculation_rows","planned_preparations","physical_experiments"]}))
