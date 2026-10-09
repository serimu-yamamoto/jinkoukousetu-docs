from pathlib import Path
import json,hashlib,re,urllib.parse,struct,platform,math
P=Path(__file__).resolve().parent;R=P.parents[1];checks=[]
def read(n):return json.loads((P/n).read_text(encoding="utf8"))
def norm(s):return s.replace("\r\n","\n").rstrip()+"\n"
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def ck(name,ok):
    if not ok:raise AssertionError(name)
    checks.append({"name":name,"passed":True})
s=read("summary.json");d=read("decision.json");n=read("checks.json")
ck("no_physical_results_or_probability",s["physical_experiments"]==d["physical_experiments"]==0 and s["success_probability"] is None and d["success_probability"] is None)
ck("no_external_supplier_action",s["provider_contacts_sent"]==s["orders_placed"]==d["quotes_received"]==0 and not s["equipment_secured"])
ck("20_numeric_checks",len(n)==s["numeric_checks"]==20 and all(x["passed"] for x in n))
ck("291_comparison_rows",sum(len(read(f)) for f in ["parameter_sweep.json","paired_states.json","dynamic_domain.json","measurement_bounds.json","material_quantities.json"])==s["calculation_rows"]==291)
ck("onset_mask_counterexample",math.isclose(s["key_masked_recovery"]["constant_load_onset_ratio"],.7/math.sqrt(.5)) and s["key_masked_recovery"]["H_ratio"]==.5)
ck("full_width_and_flat_lateral_data_null",all(x["lateral_onset_N"] is None for x in read("parameter_sweep.json") if x["geometry_domain"]!="partial_width"))
ck("dynamic_diagnostic_not_material_prediction",all(x["material_prediction"] is False for x in read("dynamic_domain.json")) and not d["static_and_dynamic_laws_spliced"])
ck("unknown_cost_and_target",s["actual_total_test_cost_yen"] is None and not s["new_snow_target_calibrated"] and not s["full_450mm_bed_verified"])
plans=read("bed_plan.json")
ck("independent_preparations_not_tracks",len(plans)==12 and sum(len(x["fresh_tracks"]) for x in plans)==24)
ck("all_bed_data_unmeasured",all(x["status"]=="not_run" and x["mass_loss_g"] is None and x["post_yield_curve"] is None and all(y["data"] is None for y in x["fresh_tracks"]) for x in plans))
ck("measurement_bounds_not_confidence",all(x["statistical_confidence_level"] is None and not x["instrument_secured"] for x in read("measurement_bounds.json")))
ck("primary_sources",len(read("sources.json"))==3 and all(x["verified"]=="2026-10-09" and x["url"].startswith("https://") for x in read("sources.json")))
ck("no_third_party_PDF_in_artifacts",not any(x.suffix.lower()==".pdf" for x in P.iterdir()))
pm=read("plot_metadata.json")
ck("plot_nodes_separate_from_tests",pm["heatmap_model_nodes"]==22801 and pm["physical_experiments"]==0)
for f in pm["figures"]:
    b=(P/f).read_bytes()
    ck("png_signature_"+f,b[:8]==b"\x89PNG\r\n\x1a\n")
    w,h=struct.unpack(">II",b[16:24])
    ck("png_dimensions_"+f,w>=1000 and h>=800)
idx=read("index_changes.json")
for f,h in idx["before_hashes"].items():
    t=norm((R/f).read_text(encoding="utf8"))
    for op in reversed(idx["operations"]):
        if op["path"]==f:
            ck("unique_reverse_"+str(len(checks)),t.count(op["new"])==1)
            t=t.replace(op["new"],op["old"])
    ck("history_preserved_"+f,sha(t)==h)
ck("claude_ledger_unchanged",sha(norm((R/"調査台帳/物性値照合_自律ループv2v3.md").read_text(encoding="utf8")))=="054c9388de3be3bd251c395059a9e02c9d3b336885236683ba3f528ff819d71f")
rep=R/"GPT往復/GPT回答_多方向探索第84巡_沈み込みと横抵抗から雪らしさを見分ける_20261009.md"
body=rep.read_text(encoding="utf8")
for phrase in ["物理試験0件","成功確率は未算定","新雪圧雪の確定目標にはしない","室温の樹脂弾性率を床のHへ比例換算しない","仮の診断模型","信頼区間でもない","450mm","300mm","R39","約60分","人体・環境への無害性は未証明","受領・返答・稼働は未確認","総額は未取得"]:
    ck("report_guard_"+phrase,phrase in body)
local_links=0
for f in [rep,*P.glob("*.md"),*(R/x for x in idx["before_hashes"])]:
    for u in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)",f.read_text(encoding="utf8")):
        if re.match(r"^[a-zA-Z]+:",u) or u.startswith("#"):continue
        target=f.parent/urllib.parse.unquote(u.split("#")[0]).strip("<>")
        if not target.exists() and target.name not in ["manifest.json","document_audit.json"]:raise AssertionError("missing link "+str(target))
        local_links+=1
ck("local_links",local_links>500)
for f in [rep,*P.iterdir(),*(R/x for x in idx["before_hashes"])]:
    if f.is_file() and f.suffix in [".md",".py",".json"] and f.name not in ["manifest.json","document_audit.json"]:
        ck("LF_"+f.name,b"\r" not in f.read_bytes())
out={"checks":checks,"local_links_checked":local_links,"python":platform.python_version(),"physical_experiments":0,"success_probability":None}
(P/"document_audit.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8",newline="\n")
print(json.dumps({"document_checks":len(checks),"local_links":local_links,"numeric_checks":20,"calculation_rows":291,"physical_experiments":0}))
