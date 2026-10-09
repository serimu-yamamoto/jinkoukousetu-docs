"""Cycle 85 manufacturing mass balance and idealized skin densification.
No physical trial, material certificate, price quote or demonstrated production rate.
"""
from pathlib import Path
import json,math,itertools
P=Path(__file__).resolve().parent
I=json.loads((P/"inputs.json").read_text(encoding="utf8"))
G=I["geometry"];C=I["production"];T=I["thermal"];checks=[]
def ck(name,ok):
    if not ok:raise AssertionError(name)
    checks.append({"name":name,"passed":True})
def write(n,v):(P/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf8",newline="\n")
def skin(t,e,d,n):
    if t<=0 or not 0<=e<1 or not 0<=2*d<=t:raise ValueError("skin geometry")
    core=t-2*d;face=(1-e)*d;final=core+2*face
    er=(1-e)**n
    D_before=er*t**3/12
    D_after=(final**3-core**3+er*core**3)/12
    return {"initial_thickness_mm":t,"porosity":e,"initial_densified_depth_each_side_mm":d,
            "assumed_core_modulus_power":n,"core_thickness_mm":core,"dense_skin_thickness_each_side_mm":face,
            "final_thickness_mm":final,"thickness_loss_mm":t-final,"relative_bending_rigidity":D_after/D_before,
            "material_volume_per_unit_area_mm":core*(1-e)+2*face,"unperforated_strip_only":True,
            "manufactured":False,"modulus_measured_at_50C":False}
A=2*G["outer_span_mm"]*G["arm_width_mm"]-G["arm_width_mm"]**2-math.pi*(G["center_hole_diameter_mm"]/2)**2
pc=G["cut_pitch_mm"];cut=A/(pc*pc)
ma=G["solid_density_kg_m3"]*(1-G["initial_porosity"])*G["initial_sheet_thickness_mm"]*1e-3
mp=G["solid_density_kg_m3"]*(1-G["initial_porosity"])*G["initial_sheet_thickness_mm"]*A*1e-9
repr_skin=skin(G["initial_sheet_thickness_mm"],G["initial_porosity"],G["densified_depth_each_face_mm"],2)
geo={"cross_plan_area_mm2":A,"layout_cell_area_mm2":pc*pc,"first_pass_geometric_retention":cut,
     "initial_sheet_mass_kg_m2":ma,"mass_per_unrounded_cross_kg":mp,
     "mass_per_unrounded_cross_mg":mp*1e6,"parts_per_square_metre_of_web":1e6/(pc*pc),
     "representative_skin":repr_skin,"geometry_is_unmanufactured":True,"edge_rounding_included":False}
ck("cross fits pitch and center hole",0<G["center_hole_diameter_mm"]<G["arm_width_mm"]<G["outer_span_mm"]<pc and 0<cut<1)
ck("areal mass and individual part mass agree",math.isclose(ma*cut,mp*geo["parts_per_square_metre_of_web"],rel_tol=1e-12))
skins=[skin(t,e,d,n) for e,t,d,n in itertools.product(I["skin_sweep"]["porosities"],I["skin_sweep"]["initial_thicknesses_mm"],I["skin_sweep"]["initial_densified_depths_mm"],I["skin_sweep"]["core_modulus_powers"])]
ck("skin collapse conserves polymer volume",all(math.isclose(x["material_volume_per_unit_area_mm"],x["initial_thickness_mm"]*(1-x["porosity"]),rel_tol=1e-12) for x in skins))
ck("zero densification preserves bending",all(math.isclose(x["relative_bending_rigidity"],1,rel_tol=1e-12) for x in skins if x["initial_densified_depth_each_side_mm"]==0))
ck("zero porosity preserves bending",math.isclose(skin(.2,0,.025,2)["relative_bending_rigidity"],1,rel_tol=1e-12))
ck("representative thickness and stiffness",math.isclose(repr_skin["final_thickness_mm"],.18,abs_tol=1e-12) and math.isclose(repr_skin["relative_bending_rigidity"],1.275,rel_tol=1e-12))
ck("modulus assumption can change stiffness direction",skin(.2,.4,.025,1)["relative_bending_rigidity"]<1<skin(.2,.4,.025,3)["relative_bending_rigidity"])
sizes=[{"sheet_thickness_mm":t,"reference_powder_size_um":d,"thickness_over_reference_size":t*1000/d,
        "distribution_or_grade_equivalent":False,"is_layer_count_measurement":False}
       for t,d in itertools.product(I["skin_sweep"]["initial_thicknesses_mm"],I["raw_size_comparisons"]["nominal_powder_sizes_um"])]
ck("powder-to-thickness units",math.isclose(next(x["thickness_over_reference_size"] for x in sizes if x["sheet_thickness_mm"]==.2 and x["reference_powder_size_um"]==130),200/130))
y=cut*C["quality_yield"]
hours=C["planned_days"]*C["hours_per_day"]*C["uptime_fraction"]
inventory=[]
for area in C["areas_m2"]:
    mass=area*C["functional_depth_m"]*C["target_bulk_density_kg_m3"]
    inventory.append({"area_m2":area,"functional_depth_m":C["functional_depth_m"],"assumed_bulk_density_kg_m3":C["target_bulk_density_kg_m3"],
                      "finished_mass_kg":mass,"nominal_particle_count":mass/mp,"net_first_pass_yield":y,
                      "gross_web_mass_kg":mass/y,"active_campaign_h":hours,
                      "required_good_kg_h":mass/hours,"required_gross_kg_h":mass/y/hours,
                      "serial_handling_machine_h_at_10ms":mass/mp*C["sequential_handling_seconds_per_piece"]/3600,
                      "quote":False,"actual_production_capability":None})
ck("inventory dimensions and yield",inventory[0]["finished_mass_kg"]==135000 and inventory[1]["finished_mass_kg"]==1350000 and all(math.isclose(x["gross_web_mass_kg"]*y,x["finished_mass_kg"],rel_tol=1e-12) for x in inventory))
lines=[]
for inv in inventory:
    for width,hold in itertools.product(C["web_widths_m"],C["hold_times_min"]):
        speed=inv["required_gross_kg_h"]/ma/width/60
        lines.append({"area_m2":inv["area_m2"],"web_width_m":width,"assumed_hold_min":hold,"required_speed_m_min":speed,
                      "equivalent_hot_path_m":speed*hold,"heatup_cooling_path_included":False,
                      "hold_time_validated_for_thin_sheet":False,"actual_factory_size_m2":None})
ck("line length tracks residence time",all(math.isclose(x["equivalent_hot_path_m"],x["required_speed_m_min"]*x["assumed_hold_min"]) for x in lines))
qheat=(T["cp_kJ_kgK"]*(T["process_C"]-T["start_C"])+T["effective_fusion_kJ_kg"])/3600
cost=[]
for inv in inventory:
    gross=inv["gross_web_mass_kg"]
    for r,eff in itertools.product(C["trim_recovery_fractions"],T["system_efficiencies"]):
        recycled=gross*r*(1-y);virgin=gross-recycled;loss=gross*(1-y)*(1-r)
        energy=gross*qheat/eff
        cost.append({"area_m2":inv["area_m2"],"assumed_recovery_fraction_of_all_reject_mass":r,
                     "assumed_thermal_efficiency":eff,"gross_thermal_throughput_kg":gross,"virgin_powder_kg":virgin,
                     "recirculated_mass_kg":recycled,"unrecovered_factory_mass_kg":loss,
                     "virgin_kg_per_finished_kg":virgin/inv["finished_mass_kg"],
                     "heat_electricity_kWh":energy,"assumed_raw_material_cost_yen_ex_tax":virgin*T["assumed_raw_powder_yen_kg_ex_tax"],
                     "assumed_heat_cost_yen_ex_tax":energy*T["electricity_yen_kWh_ex_tax"],
                     "selected_material_plus_heat_yen_ex_tax":virgin*T["assumed_raw_powder_yen_kg_ex_tax"]+energy*T["electricity_yen_kWh_ex_tax"],
                     "total_manufacturing_cost_yen":None,"actual_quote":False,"recycled_properties_verified":False})
ck("closed-loop mass balance",all(math.isclose(x["virgin_powder_kg"]+x["recirculated_mass_kg"],x["gross_thermal_throughput_kg"],rel_tol=1e-12) and math.isclose(x["virgin_powder_kg"],next(v["finished_mass_kg"] for v in inventory if v["area_m2"]==x["area_m2"])+x["unrecovered_factory_mass_kg"],rel_tol=1e-12) for x in cost))
ck("recycling does not erase gross thermal throughput",all(len({round(x["gross_thermal_throughput_kg"],6) for x in cost if x["area_m2"]==a})==1 for a in C["areas_m2"]))
ck("thermal units",math.isclose(qheat,420/3600,rel_tol=1e-12))
lit=I["literature"]
bench={"source":"S3","test_speed_m_s":2*math.pi*(lit["track_radius_mm"]*1e-3)*lit["rotation_rpm"]/60,
       "is_ski_or_50C_measurement":False,"holding_only_ideal_lab_output_kg_h":lit["reference_charge_g"]/1000*60/lit["rotary_hold_min"],
       "total_cycle_output_kg_h":None,"release_agent_composition":None}
ck("literature speed conversion",math.isclose(bench["test_speed_m_s"],.16755160819145562,rel_tol=1e-12))
plan=[]
for variant,condition,batch in itertools.product(I["test_plan"]["variants"],I["test_plan"]["conditions"],range(1,I["test_plan"]["independent_batches_per_condition"]+1)):
    plan.append({"id":f"M85-{len(plan)+1:02d}","variant":variant,"condition":condition,"independent_batch":batch,"status":"not_run","data":None,"manufacturing_recipe_qualified":False})
ck("planned trials remain unperformed",len(plan)==24 and all(x["status"]=="not_run" and x["data"] is None for x in plan))

N=I["nesting"];a=N["cell_size_mm"];hole=N["center_hole_diameter_mm"]
nested=[]
for delta in N["edge_insets_mm"]:
    span=3*a-2*delta;arm=a-2*delta
    area=2*span*arm-arm*arm-math.pi*(hole/2)**2
    fraction=area/(5*a*a)
    nested.append({"edge_inset_mm":delta,"outer_span_mm":span,"arm_width_mm":arm,
                   "center_hole_diameter_mm":hole,"plan_area_mm2":area,"lattice_area_per_part_mm2":5*a*a,
                   "geometric_retention":fraction,"net_first_pass_yield":fraction*C["quality_yield"],
                   "mass_per_part_kg":area*ma*1e-6,"nominal_gap_between_outer_edges_mm":2*delta,
                   "cutting_process_validated":False,"rounded_corners_included":False})
nr=next(v for v in nested if math.isclose(v["edge_inset_mm"],N["representative_edge_inset_mm"]))
offsets=[(0,0),(1,0),(-1,0),(0,1),(0,-1)]
coverage=[]
for x,z in itertools.product(range(-30,31),repeat=2):
    coverage.append(sum(1 for dx,dz in offsets if ((x-dx)+2*(z-dz))%5==0))
ck("five-square cross lattice covers each unit cell once",all(v==1 for v in coverage))
ck("inset reduces usable area and retains hole ligament",all(v["arm_width_mm"]>hole and 0<v["geometric_retention"]<1 for v in nested) and all(nested[i]["geometric_retention"]>nested[i+1]["geometric_retention"] for i in range(len(nested)-1)))
ck("nested area matches independent polynomial",all(math.isclose(v["plan_area_mm2"],5*a*a-12*a*v["edge_inset_mm"]+4*v["edge_inset_mm"]**2-math.pi*(hole/2)**2,rel_tol=1e-12) for v in nested))
routes=[];cutting=[]
for inv in inventory:
    mass=inv["finished_mass_kg"];yn=nr["net_first_pass_yield"];gross=mass/yn
    for r in C["trim_recovery_fractions"]:
        fresh=gross*(1-r*(1-yn));loss=gross*(1-yn)*(1-r)
        energy=gross*qheat/.4
        routes.append({"area_m2":inv["area_m2"],"route":"nested_cross_representative","edge_inset_mm":nr["edge_inset_mm"],
                       "finished_mass_kg":mass,"net_first_pass_yield":yn,"gross_web_mass_kg":gross,
                       "recovery_fraction":r,"virgin_powder_kg":fresh,"unrecovered_factory_mass_kg":loss,
                       "heat_electricity_kWh_at_efficiency_0_4":energy,
                       "selected_material_plus_heat_yen_ex_tax":fresh*T["assumed_raw_powder_yen_kg_ex_tax"]+energy*T["electricity_yen_kWh_ex_tax"],
                       "required_web_speed_m_min_at_1m_width":gross/hours/ma/60,
                       "equivalent_10min_hot_path_m_at_1m_width":gross/hours/ma/60*10,
                       "nominal_good_particle_count":mass/nr["mass_per_part_kg"],
                       "total_manufacturing_cost_yen":None,"actual_quote":False})
    produced_count=mass/nr["mass_per_part_kg"]/C["quality_yield"]
    shared=(6*a+math.pi*hole)*1e-3
    full=(4*nr["outer_span_mm"]+math.pi*hole)*1e-3
    cutting.append({"area_m2":inv["area_m2"],"produced_piece_count_including_quality_rejects":produced_count,
                    "nominal_zero_inset_shared_boundary_reference_m":produced_count*shared,
                    "representative_all_individual_contours_m":produced_count*full,
                    "shared_reference_equivalent_trace_m_s":produced_count*shared/(hours*3600),
                    "individual_contours_equivalent_trace_m_s":produced_count*full/(hours*3600),
                    "serial_handling_machine_h_at_10ms":mass/nr["mass_per_part_kg"]*.01/3600,
                    "shared_reference_validated_cut_route":False,
                    "actual_machine_speed_m_s":None,"parallel_tool_capacity":None,
                    "note":"Nominal shared reference ignores positive-inset dual boundaries. Full contours trace each part separately. Neither is a demonstrated cutting process or strict lower bound."})
ck("nested route fresh mass equals product plus unrecovered mass",all(math.isclose(v["virgin_powder_kg"],v["finished_mass_kg"]+v["unrecovered_factory_mass_kg"],rel_tol=1e-12) for v in routes))
ck("nested route preserves gross mass and improves geometric yield",nr["geometric_retention"]>cut and all(math.isclose(v["gross_web_mass_kg"]*v["net_first_pass_yield"],v["finished_mass_kg"],rel_tol=1e-12) for v in routes))
ck("individual contour burden exceeds nominal shared reference",all(v["individual_contours_equivalent_trace_m_s"]>v["shared_reference_equivalent_trace_m_s"]>0 and v["actual_machine_speed_m_s"] is None for v in cutting))

summary={"physical_experiments":0,"success_probability":None,"equipment_secured":False,"provider_contacts_sent":0,"orders_placed":0,
         "numeric_checks":len(checks),"calculation_rows":1+len(skins)+len(sizes)+len(inventory)+len(lines)+len(cost)+1+len(nested)+len(routes)+len(cutting),
         "skin_rows":len(skins),"powder_size_rows":len(sizes),"inventory_rows":len(inventory),"line_rows":len(lines),"cost_rows":len(cost),
         "planned_trials":len(plan),"geometry":geo,"polymer_heat_kWh_kg_ideal":qheat,"total_manufacturing_cost_yen":None,
         "selected_route":"Factory sintered porous precursor, conditional skin densification, batch cutting; not proven",
         "qualified_50C_snowlike_structure":False,"factory_quote_received":False}
for n,v in [("nested_geometry.json",nested),("route_comparison.json",routes),("cutting_requirements.json",cutting),("geometry.json",geo),("skin_sweep.json",skins),("powder_scale.json",sizes),("inventory.json",inventory),
            ("line_requirements.json",lines),("material_heat_costs.json",cost),("literature_conversion.json",bench),
            ("manufacturing_test_plan.json",plan),("checks.json",checks),("summary.json",summary)]:write(n,v)
print(json.dumps({k:summary[k] for k in ["numeric_checks","calculation_rows","planned_trials","physical_experiments"]}))
