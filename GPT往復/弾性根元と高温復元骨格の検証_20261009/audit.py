"""Integrity checks only; no physical performance certification."""
from pathlib import Path
import hashlib,json,re,urllib.parse,subprocess,sys,struct
P=Path(__file__).resolve().parent;R=P.parents[1];checks=[]
def ck(n,v):
    checks.append({"name":n,"passed":bool(v)})
    if not v:raise AssertionError(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def norm(t):return t.replace("\r\n","\n")
def read(n):return json.loads((P/n).read_text(encoding="utf-8"))
s=read("research_state.json");res=read("results.json");v=read("validation.json");i=read("inputs.json");ix=read("index_changes.json");plan=read("test_plan.json")
ck("61_numeric_checks",v["count"]==61 and v["all_passed"])
ck("physical_experiments_zero",s["physical_experiments"]==res["physical_experiments"]==i["physical_experiments"]==plan["physical_experiments"]==0)
ck("success_unknown",s["success_probability"] is None and res["success_probability"] is None)
ck("recovery_unmeasured",res["actual_recovery_fraction"] is None and not s["actual_50C_recovery_confirmed"])
ck("bond_unmeasured",res["actual_bond_strength"] is None and not s["actual_PE_TPEE_bond_confirmed"])
ck("50C_moduli_hypothetical",res["actual_50C_moduli"] is None and i["manufacturer_data_not_model_E"]["creep_50C_of_this_grade"] is None)
ck("no_material_selected",s["selected_material"] is None)
ck("facilities_unavailable",not s["facilities_available"] and not s["collaborators_available"])
ck("no_contacts_or_quotes",s["contacts_sent"]==0 and s["quotes_obtained"]==0)
ck("claude_receipt_unconfirmed",not s["claude_receipt_confirmed"] and not s["claude_reply_confirmed"])
ck("24_beam_12_fem_27_cost",len(res["beam_cases"])==24 and len(res["fem_cases"])==12 and len(res["cost_cases"])==27)
ck("24_unperformed_specimens",len(plan["specimens"])==24 and all(x["status"]=="not_run" and x["measured_recovery"] is None for x in plan["specimens"]))
ck("unique_specimens",len({x["id"] for x in plan["specimens"]})==24)
ck("root_scenario_material_volume_fraction",res["selected_cost_scenario"]["replacement_volume_fraction"]==.08)
ck("FEM_perfect_bond_caveat","perfect bond" in i["fem"]["assumptions"])
ledger=norm((R/"調査台帳/物性値照合_自律ループv2v3.md").read_text(encoding="utf-8"))
ck("claude_ledger_preserved",sha(ledger.encode())==s["claude_ledger_sha256_LF"])
for p,expected in ix["before_sha256"].items():
    text=norm((R/p).read_text(encoding="utf-8"))
    for op in reversed(ix["operations"]):
        if op["path"]==p:
            ck("unique_reverse_"+p+"_"+str(ix["operations"].index(op)),text.count(op["new"])==1)
            text=text.replace(op["new"],op["old"],1)
    ck("history_preserved_"+p,sha(text.encode())==expected)
report=R/"GPT往復/GPT回答_多方向探索第94巡_高温復元骨格の候補と根元配置の成立条件_20261009.md"
txt=report.read_text(encoding="utf-8")
for term in ["50℃","450mm","300mm","60分","2億円","成功確率未算定","46.7％は復元率ではない","受領・返答・稼働は未確認"]:
    ck("report_caveat_"+term,term in txt)
sources=(P/"sources.md").read_text(encoding="utf-8")
ck("grades_not_merged","7247の値を7277R-07へ渡さない" in sources)
ck("manufacturer_sources_present","tc-net.co.jp/hytrel" in sources)
ck("previous_material_work_attributed","第25巡" in sources and "第59巡" in sources)
png=(P/"root_layout_comparison.png").read_bytes()
ck("PNG_signature",png[:8]==b"\x89PNG\r\n\x1a\n")
w,h=struct.unpack(">II",png[16:24]);ck("PNG_size",w>=1000 and h>=600)
links=[]
for f in list(P.glob("*.md"))+[report]+[R/p for p in ix["before_sha256"]]:
    for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',f.read_text(encoding="utf-8")):
        link=link.strip("<>")
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:",link) or link.startswith("#"):continue
        target=urllib.parse.unquote(link.split("#")[0].split("?")[0])
        if not target:continue
        dest=(f.parent/target).resolve()
        if dest.parent==P and dest.name in ["manifest.json","document_audit.json"]:continue
        if not dest.exists():raise AssertionError("Broken local link "+str(f.relative_to(R))+" -> "+link)
        links.append(link)
ck("local_links_resolve",len(links)>0)
before={n:sha((P/n).read_bytes()) for n in ["results.json","validation.json"]}
run=subprocess.run([sys.executable,str(P/"reproduce.py"),"--check"],capture_output=True)
ck("reproduction_succeeds",run.returncode==0)
ck("reproduction_keeps_bytes",before=={n:sha((P/n).read_bytes()) for n in before})
for f in P.iterdir():
    if f.is_file() and f.suffix in [".md",".py",".json",".txt"] and f.name not in ["manifest.json","document_audit.json"]:
        ck("LF_only_"+f.name,b"\r" not in f.read_bytes())
out={"all_passed":all(x["passed"] for x in checks),"document_checks":len(checks),"local_link_count":len(links),"numeric_checks":v["count"],"physical_experiments":0,"checks":checks}
(P/"document_audit.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({k:out[k] for k in ["all_passed","document_checks","local_link_count","numeric_checks","physical_experiments"]}))
