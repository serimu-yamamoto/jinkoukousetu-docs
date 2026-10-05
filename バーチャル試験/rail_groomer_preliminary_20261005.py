"""Rail groomer concept screening. No measured material or supplier prices.
Run: python rail_groomer_preliminary_20261005.py [input.json]
Outputs deterministic JSON and Markdown tables next to this script.
"""
import json, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
G = 9.81

def annuity(r, n):
    return n if r == 0 else (1 - (1+r)**(-n))/r

def case(s, c, rates):
    L, B = s["length_m"], s["width_m"]
    angle = math.radians(c["slope_deg"])
    ns = 2*(math.ceil(L/c["footing_pitch_m"])+1)
    area = L*B
    material_mass = c["material_density_kg_m3"]*s["hold_m3"]
    f_frame = s["machine_kg"]*G*(math.sin(angle)+c["rolling"]*math.cos(angle))/1000
    f_mat = material_mass*G*(math.sin(angle)+c["material_mu"]*math.cos(angle))/1000
    f_body = f_frame + f_mat + s["tool_kN"]
    # Long rope rests on side guide rollers. Include upper-end gravity component.
    f_rope = s["rope_kg_m"]*L*G*math.sin(angle)/1000
    f_line = f_body/2 + f_rope + s["rope_loss_kN_each"]
    work_h = L/(c["work_speed_m_s"]*3600*c["duty"])
    return_h = L/(c["return_speed_m_s"]*3600)
    runtime_h = work_h+return_h+c["setup_h"]
    # Quasi-static uphill mechanical energy: machine/material at mean pull,
    # rope deployment decreases linearly L->0 as machine climbs.
    move_h = L/(c["work_speed_m_s"]*3600)
    traction_kwh = (f_body + f_rope + 2*s["rope_loss_kN_each"])*c["work_speed_m_s"]/c["efficiency"]*move_h
    tool_kwh = s["tool_kw_avg"]*work_h
    battery_need = tool_kwh/0.8
    # No regenerative credit on descent; auxiliaries remain active for controls.
    energy_kwh = traction_kwh + tool_kwh + 1.0*(return_h+c["setup_h"])
    operating_yen = c["days"]*(energy_kwh*c["electric_yen_kwh"]+s["supervision_h"]*c["labor_yen_h"])+s["maintenance_yen_year"]
    rows = []
    def row(group, name, qty, unit, prices, basis="予算仮置き"):
        rows.append(dict(group=group,item=name,qty=qty,unit=unit,unit_yen=prices,amount_yen=[qty*x for x in prices],basis=basis))
    def allowance(key,name,group="専用設備"):
        row(group,name,1,"式",s["allowances"][key])
    allowance("survey","測量 地盤調査","共通土木")
    allowance("design","機構 電装 構造設計")
    row("専用設備","レール材 予備5%含む",2*L*1.05*s["rail_kg_m"],"kg",rates["rail_yen_kg"])
    row("専用設備","レール支持鋼梁 加工防食込",2*L*s["beam_kg_m"],"kg",rates["beam_fabricated_yen_kg"])
    row("専用設備","基礎コンクリート 鉄筋型枠込",ns*s["footing_m3"],"m3",rates["concrete_rebar_form_yen_m3"])
    row("専用設備","基礎掘削 据付 位置調整",ns,"箇所",rates["footing_excavate_set_each"])
    row("専用設備","レール締結 支承",ns,"組",rates["rail_fastening_each"])
    row("専用設備","側方ガード 索受け カバー",2*L,"m",rates["side_guard_yen_m"])
    allowance("winches_pair","同期牽引2基 ブレーキ 索収納")
    allowance("anchor_pair","山側アンカー2系統")
    row("専用設備","牽引索2本 長さ余裕含む",2*(L+s["rope_extra_m"]),"m",rates["rope_yen_m_p" if s["id"]=="P100" else "rope_yen_m_f"])
    row("専用設備","本体鋼製トラス 加工塗装込",s["structural_frame_kg"],"kg",rates["frame_fab_yen_kg"])
    row("専用設備","捕捉台車",4 if s["id"]=="P100" else 8,"組",rates["bogie_each"])
    row("専用設備","1m作業モジュール 刃 ゲート ローラー スカート",s["tool_modules"],"組",rates["tool_module_each"])
    for key,name in [("control","計測 PLC 独立停止制御"),("battery","作業部バッテリー 駆動 電池管理"),("parking","全幅退避場 接続設備"),("power","受電 配電 充電"),("commission","運送 揚重 組立 試運転")]:
        allowance(key,name)
    row("共通土木","既存斜面整形",area,"m2",rates["rough_grade_yen_m2"])
    row("共通土木","排水砕石 購入施工",area*c["drain_depth_m"],"m3",rates["drain_gravel_yen_m3"])
    row("共通土木","フィルター施工",area,"m2",rates["filter_yen_m2"])
    row("共通土木","両側排水路",2*L,"m",rates["side_drain_yen_m"])
    row("共通土木","横断集排水",math.ceil(L/c["drain_pitch_m"])*B,"m",rates["cross_drain_yen_m"])
    allowance("catch","材料回収槽 土砂分離","共通土木")
    # Surface installation shown separately to avoid ignoring new material cost.
    row("材料敷設","表層材料の敷均し 購入費別",area*c["bed_depth_m"],"m3",rates["surface_place_yen_m3"])
    totals = {group:[sum(r["amount_yen"][i] for r in rows if r["group"]==group) for i in range(3)] for group in ["専用設備","共通土木","材料敷設"]}
    multiplier=(1+c["cost_overhead"])*(1+c["cost_reserve"])
    equipment=[x*multiplier for x in totals["専用設備"]]
    civil=[x*multiplier for x in totals["共通土木"]]
    placement=[x*multiplier for x in totals["材料敷設"]]
    folded=[x*multiplier for x in s["allowances"]["fold_option"]]
    nonmaterial=[equipment[i]+civil[i]+placement[i] for i in range(3)]
    af=annuity(c["discount"],c["years"])
    replace_pv=s["replacement_yen"]/(1+c["discount"])**s["replacement_year"]
    eac=equipment[1]/af+operating_yen+replace_pv/af
    rope_vol=math.pi*(s["rope_mm"]/1000)**2/4*(L+s["rope_extra_m"])
    drum_outer=math.sqrt(s["drum_core_m"]**2+4*rope_vol/(math.pi*s["drum_width_m"]*c["drum_fill"]))
    normal=s["machine_kg"]*G*math.cos(angle)/1000
    return_brake_peak=(s["machine_kg"]*G*math.sin(angle)/1000+2*f_rope)*c["return_speed_m_s"]
    return_brake_energy=(s["machine_kg"]*G*L*math.sin(angle)+s["rope_kg_m"]*G*L**2*math.sin(angle))/3.6e6
    return dict(id=s["id"],label=s["label"],area_m2=area,foundation_count=ns,rail_purchase_m=2*L*1.05,drain_cross_count=math.ceil(L/c["drain_pitch_m"]),
      return_brake_peak_kw=return_brake_peak,return_brake_energy_kwh=return_brake_energy,force_body_kN=f_body,force_material_kN=f_mat,force_frame_kN=f_frame,rope_gravity_each_kN=f_rope,winch_service_each_kN=f_line,
      winch_body_1_5_each_kN=1.5*f_body/2+f_rope+s["rope_loss_kN_each"],
      rope_mass_total_kg=2*(L+s["rope_extra_m"])*s["rope_kg_m"],
      rope_screen_allowable_kN=s["rope_break_kN"]*c["endpoint_efficiency"]/c["rope_screen_factor"],
      service_traction_kw=2*f_line*c["work_speed_m_s"]/c["efficiency"],
      work_h=work_h,return_h=return_h,total_h=runtime_h,energy_kwh=energy_kwh,battery_nominal_need_kwh=battery_need,
      loose_feed_m3_h=B*c["work_speed_m_s"]*.01*3600*c["finished_to_loose_ratio"],
      normal_weight_kN=normal,roller_load_50kPa_kN=50*B*.1,hold_down_100kPa_kN=max(0,100*B*.1-normal),
      drum_rope_volume_m3=rope_vol,drum_outer_m=drum_outer,drum_outer_pull_ratio=s["drum_core_m"]/drum_outer,
      rainfall_100mm_h_L_s=area*.1/3600*1000,catch_full_water_minutes=s["catch_m3"]/(area*.1)*60,
      rows=rows,direct_by_group=totals,all_in_equipment_yen=equipment,all_in_civil_yen=civil,all_in_surface_place_yen=placement,
      all_in_nonmaterial_yen=nonmaterial,all_in_fold_extra_yen=folded,annual_operating_yen=operating_yen,
      replacement_pv_yen=replace_pv,equipment_annual_equivalent_yen=eac,
      full_supervision_extra_yen=max(0,runtime_h-s["supervision_h"])*c["labor_yen_h"]*c["days"],
      lcc_10y_equipment_yen=equipment[1]+operating_yen*af+replace_pv)

def main():
    inp=Path(sys.argv[1]) if len(sys.argv)>1 else HERE/"rail_groomer_preliminary_inputs_20261005.json"
    cfg=json.loads(inp.read_text(encoding="utf-8-sig"))
    c=cfg["common"]
    cases=[case(s,c,cfg["rates"]) for s in cfg["scenarios"]]
    f=cfg["scenarios"][1]; st=cfg["storm"]
    # loose volume mass ledger. All volume fractions use identical reference state.
    mobilized=st["mobilized_m3"]; collected=mobilized*st["capture_fraction"]
    reusable=collected*st["reuse_fraction"]
    trips=math.ceil(reusable/f["hold_m3"])
    trip_h=st["average_up_distance_m"]/(c["work_speed_m_s"]*3600*st["haul_duty"])+st["average_up_distance_m"]/(c["return_speed_m_s"]*3600)+st["loading_h"]
    storm=dict(mobilized_m3=mobilized,captured_m3=collected,reusable_m3=reusable,
       uncaptured_m3=mobilized-collected,rejected_m3=collected-reusable,makeup_m3=mobilized-reusable,trips=trips,trip_h=trip_h,haul_h=trips*trip_h,
       haul_plus_finish_h=trips*trip_h+cases[1]["total_h"],sixteen_hour_including_finish_haul_max_m3=max(0,math.floor((16-cases[1]["total_h"])/trip_h))*f["hold_m3"],eight_hour_haul_max_m3=math.floor(st["repair_window_h"]/trip_h)*f["hold_m3"],
       eight_hour_including_finish_haul_max_m3=max(0,math.floor((st["repair_window_h"]-cases[1]["total_h"])/trip_h))*f["hold_m3"])
    # haul sensitivity separates blade-load limit from assumed destination distance.
    haul_sensitivity=[]
    for d in [50,250,500,1000]:
        th=d/(c["work_speed_m_s"]*3600*st["haul_duty"])+d/(c["return_speed_m_s"]*3600)+st["loading_h"]
        haul_sensitivity.append(dict(distance_m=d,trips=trips,total_haul_h=trips*th))
    surfaces=[]
    for s in cfg["scenarios"]:
        for depth in [.3,.45,1.5]:
            for density in cfg["surface_dry_bulk_kg_m3"]:
                volume=s["length_m"]*s["width_m"]*depth
                surfaces.append(dict(id=s["id"],depth_m=depth,dry_bulk_kg_m3=density,volume_m3=volume,mass_t=volume*density/1000,
                  material_yen=[volume*density*p for p in cfg["surface_price_yen_kg"]]))
    force_sensitivity=[]
    for slope in [20,30]:
        for density in [500,1800]:
            for mu in [.2,.4,.6]:
                cc={**c,"slope_deg":slope,"material_density_kg_m3":density,"material_mu":mu}
                r=case(f,cc,cfg["rates"])
                force_sensitivity.append(dict(slope=slope,density=density,mu=mu,body_kN=r["force_body_kN"],top_each_kN=r["winch_service_each_kN"]))
    daytime=[]
    for speed in cfg["daytime"]["work_speeds_m_s"]:
        for window in cfg["daytime"]["closure_windows_h"]:
            available=window-cfg["daytime"]["in_window_setup_h"]-cfg["daytime"]["curing_h"]
            transit_h=f["length_m"]*(1/(speed*c["duty"])+1/c["return_speed_m_s"])/3600
            number=math.ceil(transit_h/available) if available>0 else None
            daytime.append(dict(speed_m_s=speed,closure_h=window,machines=number,segment_m=f["length_m"]/number if number else None,
              actual_closure_h=transit_h/number+cfg["daytime"]["in_window_setup_h"]+cfg["daytime"]["curing_h"] if number else None))
    daytime_systems=[]
    for d in cfg["daytime"]["systems"]:
        n=d["count"]
        seg=json.loads(json.dumps(f))
        seg.update({k:d[k] for k in ["machine_kg","structural_frame_kg","tool_modules","rope_mm","rope_kg_m","rope_break_kN","winch_kN_each","winch_motor_kw_each","battery_kwh","tool_kw_avg"]})
        seg.update(id=d["id"],label=d["label"],length_m=f["length_m"]/n,rope_extra_m=f["length_m"]/n*.1,
          maintenance_yen_year=d["maintenance_total_yen"]/n,replacement_yen=d["replacement_total_yen"]/n,supervision_h=1)
        seg["allowances"]["design"]=[x/n for x in f["allowances"]["design"]]
        seg["allowances"]["survey"]=[x/n for x in f["allowances"]["survey"]]
        seg["allowances"]["battery"]=[400000,800000,1600000] if d["id"]=="D5" else [700000,1500000,3000000]
        seg["allowances"]["power"]=[800000,2000000,6000000]
        seg["allowances"]["catch"]=[x/n for x in f["allowances"]["catch"]]
        # Explicit alternate-end parking for bidirectional mode (additional to fold mechanism).
        seg["allowances"]["parking"]=[x+d["extra_endpoint_parking_each"] for x in f["allowances"]["parking"]]
        cc={**c,"work_speed_m_s":.2,"days":c["days"]*cfg["daytime"]["cycles_per_day"]}
        rr=case(seg,cc,cfg["rates"])
        closure=rr["work_h"]+(rr["return_h"] if d["return_required"] else 0)+cfg["daytime"]["in_window_setup_h"]+cfg["daytime"]["curing_h"]
        equipment=[n*(rr["all_in_equipment_yen"][i]+rr["all_in_fold_extra_yen"][i]) for i in range(3)]
        civil=[n*x for x in rr["all_in_civil_yen"]]
        placement=[n*x for x in rr["all_in_surface_place_yen"]]
        # D3 op-energy conservatively retains empty-return energy/aux in case(); no credit for alternating travel.
        yearly=n*rr["annual_operating_yen"]
        pv_replace=n*rr["replacement_pv_yen"]
        daytime_systems.append(dict(id=d["id"],label=d["label"],count=n,unit_input=seg,per_unit=rr,
          closure_h=closure,margin_min=(cfg["daytime"]["user_selected_closure_h"]-closure)*60,
          all_in_equipment_with_fold_yen=equipment,all_in_civil_yen=civil,all_in_placement_yen=placement,
          all_in_nonmaterial_yen=[equipment[i]+civil[i]+placement[i] for i in range(3)],
          annual_operating_yen=yearly,annual_equivalent_yen=equipment[1]/annuity(c["discount"],c["years"])+yearly+pv_replace/annuity(c["discount"],c["years"])))
    zoned=[]
    for zw in cfg["zoned_bed"]["focus_widths_m"]:
        vol=f["length_m"]*(zw*cfg["zoned_bed"]["focus_depth_m"]+(f["width_m"]-zw)*cfg["zoned_bed"]["other_depth_m"])
        zoned.append(dict(focus_width_m=zw,volume_m3=vol,extra_volume_m3=vol-f["length_m"]*f["width_m"]*c["bed_depth_m"],
          material_at_500kg_20yen=vol*500*20,placement_extra_base_yen=(vol-f["length_m"]*f["width_m"]*c["bed_depth_m"])*cfg["rates"]["surface_place_yen_m3"][1]*(1+c["cost_overhead"])*(1+c["cost_reserve"])))
    resources = {sid:[dict(item=v["item"],**v[sid],amount_yen=v[sid]["count"]*v[sid]["days"]*v[sid]["yen_per_machine_day"]) for v in cfg["construction_resources"]] for sid in ["P100","F1000"]}
    outputs=dict(daytime_systems=daytime_systems,daytime=daytime,zoned_bed=zoned,construction_resources=resources,construction_resource_note=cfg["construction_resource_note"],metadata=cfg["metadata"],inputs_file=inp.name,cases=cases,storm=storm,haul_sensitivity=haul_sensitivity,
                 surface_sensitivity=surfaces,force_sensitivity=force_sensitivity,annuity=annuity(c["discount"],c["years"]))
    # Conservation and unit checks; independent elementary bounds.
    assert abs(storm["reusable_m3"]+storm["rejected_m3"]+storm["uncaptured_m3"]-mobilized)<1e-9
    assert trips*f["hold_m3"]>=reusable
    if f["length_m"]==1000 and f["width_m"]==20 and c["footing_pitch_m"]==5:
        assert cases[1]["foundation_count"]==402
        assert abs(cases[1]["rainfall_100mm_h_L_s"]-555.5555555556)<1e-6
    for d in daytime_systems:
        d["meets_time_window_without_curing"] = d["closure_h"] < cfg["daytime"]["user_selected_closure_h"]
        assert d["per_unit"]["rope_screen_allowable_kN"] > d["unit_input"]["winch_kN_each"]
    for s,r in zip(cfg["scenarios"],cases):
        assert r["force_body_kN"]>s["machine_kg"]*G*math.sin(math.radians(c["slope_deg"]))/1000
        assert r["all_in_nonmaterial_yen"][0]<r["all_in_nonmaterial_yen"][1]<r["all_in_nonmaterial_yen"][2]
        assert r["rope_screen_allowable_kN"]>s["winch_kN_each"]
    (HERE/"rail_groomer_preliminary_results_20261005.json").write_text(json.dumps(outputs,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# 数量と予算仮定の自動集計","","全単価は未見積りの予算仮置き。税別。単位 万円。入力JSONを変更してPythonを再実行する。","","現場管理・一般管理等15%と不確定分25%を順に加算。低 中央 高は確率区間ではない。"]
    for r in cases:
        lines+=["",f"## {r['label']}","","|区分|項目|数量|単位|単価低 中央 高 円|金額低 中央 高 万円|","|---|---|---:|---|---|---|"]
        for row in r["rows"]:
            lines.append("|{group}|{item}|{qty:,.2f}|{unit}|{rates}|{amounts}|".format(**row,rates=" / ".join(f"{x:,.0f}" for x in row["unit_yen"]),amounts=" / ".join(f"{x/10000:,.1f}" for x in row["amount_yen"])))
        lines+=["","|加算後の合計|低 万円|中央 万円|高 万円|","|---|---:|---:|---:|"]
        for label,key in [("専用設備","all_in_equipment_yen"),("共通土木","all_in_civil_yen"),("表層敷均し 購入別","all_in_surface_place_yen"),("合計 材料購入別","all_in_nonmaterial_yen"),("折畳み追加オプション","all_in_fold_extra_yen")]:
            lines.append("|"+label+"|"+"|".join(f"{x/10000:,.1f}" for x in r[key])+"|")
    for d in daytime_systems:
        n=d["count"]; r=d["per_unit"]
        lines+=["",f"## {d['label']} 全機合計","","機械・駆動・工具は台数分、設計と測量は共有分。全機折畳みを含む。","",
                "|区分|項目|合計数量|単位|単価低 中央 高 円|直接金額低 中央 高 万円|","|---|---|---:|---|---|---|"]
        for row in r["rows"]:
            lines.append("|{group}|{item}|{qty:,.2f}|{unit}|{rates}|{amounts}|".format(group=row["group"],item=row["item"],qty=n*row["qty"],unit=row["unit"],
              rates=" / ".join(f"{x:,.0f}" for x in row["unit_yen"]),amounts=" / ".join(f"{n*x/10000:,.1f}" for x in row["amount_yen"])))
        lines.append("|専用設備|折畳み追加機構|"+str(n)+"|式|"+" / ".join(f"{x:,.0f}" for x in d["unit_input"]["allowances"]["fold_option"])+"|"+" / ".join(f"{n*x/10000:,.1f}" for x in d["unit_input"]["allowances"]["fold_option"])+"|")
        lines+=["","|加算後の合計|低 万円|中央 万円|高 万円|","|---|---:|---:|---:|"]
        for label,key in [("専用設備 折畳み込","all_in_equipment_with_fold_yen"),("共通土木","all_in_civil_yen"),("表層敷均し","all_in_placement_yen"),("材料購入別合計","all_in_nonmaterial_yen")]:
            lines.append("|"+label+"|"+"|".join(f"{x/10000:,.1f}" for x in d[key])+"|")
    (HERE/"rail_groomer_preliminary_costs_20261005.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"cases":[{k:r[k] for k in ["id","force_body_kN","winch_service_each_kN","winch_body_1_5_each_kN","total_h","energy_kwh","battery_nominal_need_kwh","all_in_equipment_yen","all_in_civil_yen","all_in_nonmaterial_yen","annual_operating_yen","equipment_annual_equivalent_yen","drum_outer_m"]} for r in cases],"storm":storm},ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
