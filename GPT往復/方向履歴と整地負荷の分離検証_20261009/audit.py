"""Publication integrity audit. No physical performance validation."""
from pathlib import Path
import hashlib,json,re,urllib.parse,subprocess,sys,struct
P=Path(__file__).resolve().parent;R=P.parents[1];checks=[]
def ck(n,v):
    checks.append({"name":n,"passed":bool(v)})
    if not v:raise AssertionError(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def norm(t):return t.replace("\r\n","\n")
def read(n):return json.loads((P/n).read_text(encoding="utf-8"))
s=read("research_state.json");res=read("results.json");v=read("validation.json")
i=read("inputs.json");ix=read("index_changes.json");plan=read("test_plan.json")
ck("25_arithmetic_checks",v["count"]==25 and v["all_passed"])
ck("physical_trials_zero",s["physical_experiments"]==res["physical_experiments"]==i["physical_experiments"]==plan["physical_experiments"]==0)
ck("success_unknown",s["success_probability"] is None and res["success_probability"] is None)
ck("wear_not_predicted",res["wear_volume_prediction"] is None and res["wear_savings_fraction"] is None)
ck("decay_not_measured",res["actual_decay_length_mm"] is None and not s["decay_length_measured"])
ck("not_selected",s["selected_material"] is None)
ck("facilities_unavailable",not s["facilities_available"] and not s["collaborators_available"])
ck("no_external_contact",s["contacts_sent"]==0 and s["quotes_obtained"]==0)
ck("claude_receipt_unknown",not s["claude_receipt_confirmed"] and not s["claude_reply_confirmed"])
ck("15_diagnostic_rows",len(res["diagnostic_rows"])==15)
ck("18_unperformed_pairs",len(plan["pairs"])==18 and all(x["status"]=="not_run" and x["measured_friction"] is None and x["measured_wear"] is None for x in plan["pairs"]))
ck("pair_ids_unique",len({x["id"] for x in plan["pairs"]})==18)
ck("calibration_excluded",plan["calibration_runs_not_performed"]==3 and plan["calibration_excluded_from_partial_hours"])
ck("time_16_125h",res["test_timing"]["hours_18_pairs_partial"]==16.125)
ck("cost_not_quote","tax" in res["test_timing"]["excludes"])
ledger=norm((R/"調査台帳/物性値照合_自律ループv2v3.md").read_text(encoding="utf-8"))
ck("claude_ledger_preserved",sha(ledger.encode())==s["claude_ledger_sha256_LF"])
for p,expected in ix["before_sha256"].items():
    text=norm((R/p).read_text(encoding="utf-8"))
    for op in reversed(ix["operations"]):
        if op["path"]==p:
            ck("unique_reverse_"+p+"_"+str(ix["operations"].index(op)),text.count(op["new"])==1)
            text=text.replace(op["new"],op["old"],1)
    ck("history_preserved_"+p,sha(text.encode())==expected)
report=R/"GPT往復/GPT回答_多方向探索第93巡_方向変更間隔を含む滑走面と整地の再設計_20261009.md"
txt=report.read_text(encoding="utf-8")
for term in ["50℃","450mm","300mm","60分","2億円","成功確率は未算定","摩耗が9.52倍になるという結果ではない","受領・返答・稼働は未確認"]:
    ck("report_caveat_"+term,term in txt)
sources=(P/"sources.md").read_text(encoding="utf-8")
ck("new_primary_sources_present","2011.06.006" in sources and "s11249-022-01660-w" in sources)
ck("prior_work_attributed","第42巡" in sources and "第54巡" in sources)
png=(P/"history_activity.png").read_bytes()
ck("PNG_signature",png[:8]==b"\x89PNG\r\n\x1a\n")
w,h=struct.unpack(">II",png[16:24]);ck("PNG_dimensions",w>=1000 and h>=600)
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
ck("reproduction_bytes_unchanged",before=={n:sha((P/n).read_bytes()) for n in before})
for f in P.iterdir():
    if f.is_file() and f.suffix in [".md",".py",".json"] and f.name not in ["manifest.json","document_audit.json"]:
        ck("LF_only_"+f.name,b"\r" not in f.read_bytes())
out={"all_passed":all(x["passed"] for x in checks),"document_checks":len(checks),"local_link_count":len(links),"numeric_checks":v["count"],"physical_experiments":0,"checks":checks}
(P/"document_audit.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({k:out[k] for k in ["all_passed","document_checks","local_link_count","numeric_checks","physical_experiments"]}))
