from pathlib import Path
import hashlib,json,re,urllib.parse,platform
P=Path(__file__).resolve().parent;R=P.parents[1]
checks=[]
def ck(name,ok):
    if not ok:raise AssertionError(name)
    checks.append({"name":name,"passed":True})
def norm(s):return s.replace("\r\n","\n").rstrip()+"\n"
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def read(n):return json.loads((P/n).read_text(encoding="utf8"))
s=read("summary.json");n=read("checks.json");d=read("decision.json");m=read("materials.json");i=read("inputs.json")
ck("physical_zero_and_probability_unknown",s["physical_experiments"]==d["physical_experiments"]==0 and s["success_probability"] is None and d["success_probability"] is None)
ck("no_actual_supplier_action",s["provider_contacts_sent"]==s["orders_placed"]==d["quotes_received"]==0 and not d["equipment_secured"])
ck("numeric_checks",s["numeric_checks"]==len(n)==12 and all(x["passed"] for x in n))
ck("calculation_rows",sum(len(read(f)) for f in ["bom.json","material_scale.json","cost_scenarios.json"])==s["calculation_rows"]==14)
plan=read("trial_bindings.json")
ck("not_run_plan",len(plan)==24 and all(x["status"]=="not_run" and x["data"] is None for x in plan))
ck("no_adoption_or_total_price",s["complete_trial_total_yen"] is None and not s["materials_adopted_as_final"] and not d["public_price_is_project_quote"])
ck("missing_50C_properties_preserved",all(x["mu_50C_against_ski"] is None and x["E_50C_MPa"] is None and x["k_50C_mm3_Nm"] is None for x in m["candidates"]))
ck("M3_unfilled_not_invented",d["material_status"]["M3"]=="held_pending_unfilled_and_additive_confirmation" and m["candidates"][2]["room_reference_tensile_E_MPa"] is None)
src=read("sources.json")
ck("eight_primary_or_price_sources",len(src)==8 and all(x["verified"]=="2026-10-09" and x["url"].startswith("https://") for x in src))
ck("three_pdf_hashes_recorded",sum(bool(x.get("sha256")) for x in src)==3 and all(len(x["sha256"])==64 for x in src if x.get("sha256")))
ck("source_ids_resolve",all(q in {x["id"] for x in src} for a in m["candidates"]+[m["counterface"]] for q in a["source_ids"]))
ck("no_PDF_republication",not any(x.suffix.lower() in [".pdf",".png",".jpg"] for x in P.iterdir()))
idx=read("index_changes.json")
for f,h in idx["before_hashes"].items():
    t=norm((R/f).read_text(encoding="utf8"))
    for op in reversed(idx["operations"]):
        if op["path"]==f:
            ck("unique_reverse_"+str(len(checks)),t.count(op["new"])==1)
            t=t.replace(op["new"],op["old"])
    ck("history_preserved_"+f,sha(t)==h)
ck("claude_ledger_unchanged",sha(norm((R/"調査台帳/物性値照合_自律ループv2v3.md").read_text(encoding="utf8")))=="054c9388de3be3bd251c395059a9e02c9d3b336885236683ba3f528ff819d71f")
rep=R/"GPT往復/GPT回答_多方向探索第83巡_具体グレードと試片費用から絞る材料構成_20261009.md"
body=rep.read_text(encoding="utf8")
for phrase in ["物理試験0件","成功確率は未算定","実見積りでも総額でもなく","50℃の完成材予測ではない","採用を保留","450mm","300mm","R39","約60分","人体・環境への無害性は未証明","受領・返答・稼働は未確認","逆配置"]:
    ck("report_guard_"+phrase,phrase in body)
local_links=0
for f in [rep,*P.glob("*.md"),*(R/x for x in idx["before_hashes"])]:
    for u in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)",f.read_text(encoding="utf8")):
        if re.match(r"^[a-zA-Z]+:",u) or u.startswith("#"):continue
        target=f.parent/urllib.parse.unquote(u.split("#")[0]).strip("<>")
        if not target.exists() and target.name not in ["manifest.json","document_audit.json"]:
            raise AssertionError("missing link "+str(target))
        local_links+=1
ck("local_links_verified",local_links>500)
for f in [rep,*P.iterdir(),*(R/x for x in idx["before_hashes"])]:
    if f.is_file() and f.name not in ["manifest.json","document_audit.json"]:ck("LF_"+f.name,b"\r" not in f.read_bytes())
out={"document_checks":checks,"local_links_checked":local_links,"python":platform.python_version(),"physical_experiments":0,"success_probability":None}
(P/"document_audit.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8",newline="\n")
print(json.dumps({"document_checks":len(checks),"local_links":local_links,"numeric_checks":12,"calculation_rows":14,"physical_experiments":0}))
