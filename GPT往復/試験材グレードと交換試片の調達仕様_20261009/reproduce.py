"""Cycle 83: procurement arithmetic and material substitution diagnostics.
Only standard library; no physical observations or success probabilities generated.
Run after retaining the sibling cycle 82 allocation file.
"""
from pathlib import Path
import json, math
P=Path(__file__).resolve().parent
R=P.parents[1]
def read(name): return json.loads((P/name).read_text(encoding="utf8"))
def write(name,value): (P/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf8",newline="\n")
I=read("inputs.json"); M=read("materials.json"); g=I["geometry"]
checks=[]
def ck(name,condition):
    if not condition: raise AssertionError(name)
    checks.append({"name":name,"passed":True})
# A retained allocation, not a new set of observations.
prior=json.loads((R/I["previous_folder"]/"main_run_plan.json").read_text(encoding="utf8"))
mapping={"unfilled_UHMWPE_grade_TBD":"M1","unfilled_PEEK_grade_TBD":"M2","unfilled_hydrolysis_suitable_elastomer_grade_TBD":"M3"}
runs=[]
for m in I["main"]["materials"]:
    for j,orientation in enumerate(I["pilots"]["orientations"],1):
        runs.append({"run_id":f"P83-{m}-{j}","type":"orientation_pilot","material":m,"state":"dry","orientation":orientation,
                     "candidate_coupon_id":f"CP83-{m}-{j}","counterface_id":f"SK83-{m}-{j}",
                     "status":"not_run","data":None,"eligibility":"conditional_composition_and_facility_confirmation"})
for p in prior:
    runs.append({"run_id":p["run_id"],"type":"main","material":mapping[p["material"]],"state":p["state"],
                 "orientation":I["main"]["orientation_assumption"],"candidate_coupon_id":p["candidate_coupon_id"],
                 "counterface_id":p["new_counterface_id"],"status":"not_run","data":None,
                 "eligibility":"conditional_composition_and_facility_confirmation"})
ck("24 independent pairs retain 18 prior IDs",len(runs)==24 and {r["run_id"] for r in runs if r["type"]=="main"}=={r["run_id"] for r in prior})
ck("all sample identities unique",len({r["candidate_coupon_id"] for r in runs})==len({r["counterface_id"] for r in runs})==24)
ck("balanced main blocks",all(sum(r["type"]=="main" and r["material"]==m and r["state"]==s for r in runs)==3 for m in mapping.values() for s in I["main"]["states"]))
ck("all runs explicitly unperformed",all(r["status"]=="not_run" and r["data"] is None for r in runs))
bom=[]
Vpin=math.pi*(g["pin_diameter_mm"]/2)**2*g["pin_finished_length_mm"]/1000
Vdisk=math.pi*(g["disk_diameter_mm"]/2)**2*g["disk_finished_thickness_mm"]/1000
for m in M["candidates"]:
    rr=[r for r in runs if r["material"]==m["id"]]
    pins=sum(r["orientation"]=="candidate_pin_ski_disk" for r in rr); disks=len(rr)-pins
    xp=I["purchase_extras_per_material"]
    for label,core,blank,spare,v in [
        ("candidate_pin",pins,xp["candidate_pin_environmental_blanks"],xp["candidate_pin_spares"],Vpin),
        ("candidate_disk",disks,xp["candidate_disk_environmental_blanks"],xp["candidate_disk_spares"],Vdisk)]:
        bom.append({"material":m["id"],"item":label,"active_core":core,"environmental_blanks":blank,"spares":spare,
                    "extended_count":core+blank+spare,"single_finished_volume_cm3":v,
                    "extended_finished_mass_g":(core+blank+spare)*v*m["density_g_cm3"],
                    "status":"not_procured","price_yen":None})
for label,count,extra,diam in [
    ("ski_disk",sum(r["orientation"]=="candidate_pin_ski_disk" for r in runs),I["counterface_extras"]["ski_disks_spares"],g["disk_diameter_mm"]),
    ("ski_cap",sum(r["orientation"]=="ski_cap_candidate_disk" for r in runs),I["counterface_extras"]["ski_caps_spares"],g["pin_diameter_mm"])]:
    v=math.pi*(diam/2)**2*g["skin_assumed_thickness_mm"]/1000
    bom.append({"material":"SKI","item":label,"active_core":count,"environmental_blanks":0,"spares":extra,
                "extended_count":count+extra,"single_finished_volume_cm3":v,
                "extended_finished_mass_g":(count+extra)*v*M["counterface"]["density_g_cm3"],
                "status":"not_procured","price_yen":None,"note":"film on holder; thickness provisional, holders excluded"})
ck("core coupon conservation per orientation",sum(b["active_core"] for b in bom if b["material"]!="SKI")==24 and sum(b["active_core"] for b in bom if b["material"]=="SKI")==24)
ck("36 pins and 9 disks are extended stock not replicate count",sum(b["extended_count"] for b in bom if b["item"]=="candidate_pin")==36 and sum(b["extended_count"] for b in bom if b["item"]=="candidate_disk")==9)
# Conservative rectangular machining blanks, not an optimized nesting algorithm.
rects=[{"id":"disk_blank_1","x_mm":3,"y_mm":3,"w_mm":64,"h_mm":64}]
for row in range(6):
    for col in range(2):
        rects.append({"id":f"pin_blank_{row*2+col+1}","x_mm":73+11*col,"y_mm":3+11*row,"w_mm":8,"h_mm":8})
def gap(a,b):
    dx=max(b["x_mm"]-a["x_mm"]-a["w_mm"],a["x_mm"]-b["x_mm"]-b["w_mm"],0)
    dy=max(b["y_mm"]-a["y_mm"]-a["h_mm"],a["y_mm"]-b["y_mm"]-b["h_mm"],0)
    return math.hypot(dx,dy)
mingap=min(gap(a,b) for i,a in enumerate(rects) for b in rects[i+1:])
ck("blanks inside slab with 3 mm edge allowance",all(r["x_mm"]>=3 and r["y_mm"]>=3 and r["x_mm"]+r["w_mm"]<=97 and r["y_mm"]+r["h_mm"]<=97 for r in rects))
ck("blank separation includes 3 mm kerf",mingap>=g["min_kerf_clearance_mm"])
ck("finished dimensions fit machining blanks",g["pin_diameter_mm"]<=8 and g["pin_finished_length_mm"]<=10 and g["disk_diameter_mm"]<=64 and g["disk_finished_thickness_mm"]<=10)
layout={"stock_mm":g["stock_mm"],"rectangles":rects,"minimum_gap_mm":mingap,
        "finished_disk_center_mm":[35,35],"finished_disk_diameter_mm":60,
        "first_stock_yields":{"candidate_disk":1,"candidate_pins":12},
        "extended_stock_count_per_material":3,
        "extended_layout_note":"Two more stocks each supply only one disk; unused offcuts kept as unallocated material.",
        "scope":"2D collision and allowance check only; supplier must approve fixturing, shrinkage, tolerance, finish and kerf."}
scales=[]
for m in M["candidates"]:
    E=m["room_reference_tensile_E_MPa"]
    scales.append({"material":m["id"],"source_reference_E_MPa":E,"reference_temperature":"room/reference test, not 50 C",
                   "compliance_relative_to_assumed_30MPa":I["mechanical_scaling"]["reference_assumed_E_MPa"]/E if E else None,
                   "stiffness_relative_to_assumed_30MPa":E/I["mechanical_scaling"]["reference_assumed_E_MPa"] if E else None,
                   "same_geometry_same_nu_required":True,"measured_50C_prediction":False})
ck("linear elastic diagnostic ratios",math.isclose(scales[0]["compliance_relative_to_assumed_30MPa"],1/25) and math.isclose(scales[1]["compliance_relative_to_assumed_30MPa"],1/140) and scales[2]["compliance_relative_to_assumed_30MPa"] is None)
cost=[]
for scenario,nrun,nstock in [("pilot_6_plus_one_PEEK_stock",6,1),("all_24_plus_one_PEEK_stock",24,1),("all_24_plus_three_PEEK_stocks",24,3)]:
    item=nrun*I["basic_test_tariff"]["yen_inc_tax_per_run"]
    stock=nstock*I["prices"]["peek_stock_yen_inc_tax"]
    cost.append({"scenario":scenario,"basic_test_item_yen_inc_tax":item,"PEEK_public_stock_item_yen_inc_tax":stock,
                 "selected_items_subtotal_yen_inc_tax":item+stock,"complete_trial_total_yen":None,
                 "quote":False,"grade_match_confirmed":False,"orders_placed":0})
ck("tax arithmetic and selected item sums",I["prices"]["peek_stock_yen_ex_tax"]*110==I["prices"]["peek_stock_yen_inc_tax"]*100 and all(x["selected_items_subtotal_yen_inc_tax"]==x["basic_test_item_yen_inc_tax"]+x["PEEK_public_stock_item_yen_inc_tax"] for x in cost))
ck("unknown prices and material responses not filled in",all(m["mu_50C_against_ski"] is None and m["E_50C_MPa"] is None and m["price_yen"] is None for m in M["candidates"]) and all(x["complete_trial_total_yen"] is None for x in cost))
summary={"physical_experiments":0,"success_probability":None,"provider_contacts_sent":0,"orders_placed":0,"quotes_received":0,
         "equipment_secured":False,"numeric_checks":len(checks),"planned_runs":len(runs),
         "core_candidate_pins":21,"core_candidate_disks":3,"core_ski_disks":21,"core_ski_caps":3,
         "extended_candidate_pins":36,"extended_candidate_disks":9,"extended_ski_disks":27,"extended_ski_caps":6,
         "calculation_rows":len(bom)+len(scales)+len(cost),"packing_rectangles":len(rects),
         "minimum_packing_gap_mm":mingap,"one_PEEK_public_stock_yen_inc_tax":16478,
         "three_PEEK_public_stocks_yen_inc_tax":49434,"complete_trial_total_yen":None,
         "drawing_or_fixture_accepted":False,"materials_adopted_as_final":False}
for name,value in [("trial_bindings.json",runs),("bom.json",bom),("cutting_layout.json",layout),
                   ("material_scale.json",scales),("cost_scenarios.json",cost),("checks.json",checks),("summary.json",summary)]:write(name,value)
print(json.dumps(summary,ensure_ascii=False))
