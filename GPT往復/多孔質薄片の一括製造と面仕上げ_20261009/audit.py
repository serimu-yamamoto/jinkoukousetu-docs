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
ck("21_numeric_checks",len(n)==s["numeric_checks"]==21 and all(x["passed"] for x in n))
ck("117_calculation_rows",2+sum(len(read(f)) for f in ["skin_sweep.json","powder_scale.json","inventory.json","line_requirements.json","material_heat_costs.json","nested_geometry.json","route_comparison.json","cutting_requirements.json"])==s["calculation_rows"]==117)
ck("geometry_yield_is_not_success",math.isclose(d["nested_geometric_retention"],.9271872587712815) and d["success_probability"] is None and not d["manufacturing_demonstrated"])
ck("oil_friction_not_transferred",not read("literature_conversion.json")["is_ski_or_50C_measurement"])
ck("total_manufacturing_quote_unknown",s["total_manufacturing_cost_yen"] is None and d["total_manufacturing_cost_yen"] is None and not s["factory_quote_received"])
plans=read("manufacturing_test_plan.json")
ck("all_24_trials_unperformed",len(plans)==24 and all(x["status"]=="not_run" and x["data"] is None and not x["manufacturing_recipe_qualified"] for x in plans))
ck("cutting_capacity_unknown",all(x["actual_machine_speed_m_s"] is None and x["parallel_tool_capacity"] is None for x in read("cutting_requirements.json")))
ck("50C_finished_properties_unknown",all(d[k] is None for k in ["finished_50C_mu","finished_50C_H","finished_50C_S"]) and not d["finished_safety_verified"])
ck("no_ski_adoption",not d["adopted_for_ski_use"] and not d["patent_novelty_established"])
ck("primary_sources",len(read("sources.json"))==3 and all(x["verified"]=="2026-10-09" and x["url"].startswith("https://") for x in read("sources.json")))
ck("no_third_party_PDF_in_artifacts",not any(x.suffix.lower()==".pdf" for x in P.iterdir()))
pm=read("plot_metadata.json")
ck("figures_are_own_unmanufactured_concept",len(pm["figures"])==2 and pm["physical_experiments"]==0 and not pm["manufacturing_demonstrated"])
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
rep=R/"GPT往復/GPT回答_多方向探索第85巡_油を使わない多孔質薄片の製造と量産条件_20261009.md"
body=rep.read_text(encoding="utf8")
for phrase in ["物理試験0件","成功確率は未算定","室温の樹脂弾性率を床のHへ比例換算しない","92.7％はシート面積の利用率","未製造","450mm","300mm","R39","約60分","人体・環境への無害性は未証明","受領・返答・稼働は未確認","総製造費は未取得","特許性を主張するものではありません"]:
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
print(json.dumps({"document_checks":len(checks),"local_links":local_links,"numeric_checks":21,"calculation_rows":117,"physical_experiments":0}))
