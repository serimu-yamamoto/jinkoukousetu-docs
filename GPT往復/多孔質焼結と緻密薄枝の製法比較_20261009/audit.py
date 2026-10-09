"""Integrity checks for cycle 91; no physical-performance assertion."""
from pathlib import Path
import hashlib,json,re,urllib.parse,subprocess,sys,struct
P=Path(__file__).resolve().parent;R=P.parents[1]
checks=[]
def ck(n,v):
 checks.append({"name":n,"passed":bool(v)})
 if not v:raise AssertionError(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def norm(s):return s.replace("\r\n","\n").rstrip()+"\n"
def read(n):return json.loads((P/n).read_text(encoding="utf-8"))
s=read("research_state.json");v=read("validation.json");res=read("results.json");ix=read("index_changes.json");plan=read("test_plan.json");sources=read("sources.json")
ck("35_arithmetic_checks",v["count"]==35 and v["all_passed"])
ck("physical_trials_zero",s["physical_experiments"]==res["physical_experiments"]==0)
ck("probability_not_fabricated",s["success_probability"] is None and res["success_probability"] is None)
ck("50C_moduli_unmeasured",res["all_50C_moduli_assumed"] and all(x.get("actual_50C_modulus") is None for x in res["comparison_rows"]))
ck("31_comparisons",len(res["comparison_rows"])==31)
ck("93_wet_conditions",sum(len(x["wet"]["rows"]) for x in res["comparison_rows"])==93)
ck("270_cost_scenarios",len(res["cost_rows"])==270)
ck("no_actual_quote",s["actual_quote"] is None and all(x["actual_quote"] is None for x in res["cost_rows"]))
ck("no_actual_rain_result",all(x["wet"]["actual_rain_result"] is None for x in res["comparison_rows"]))
ck("no_material_adoption",s["selected_material"] is None and res["chosen_material"] is None)
ck("no_contacts_orders_equipment",s["contacts_sent"]==s["purchases"]==0 and not s["equipment_secured"] and not s["collaborator_secured"])
ck("claude_status_unknown",all(s[k] is None for k in ["claude_receipt","claude_reply","claude_running"]))
ck("claude_source_preserved",sha(norm((R/s["claude_ledger"]).read_text(encoding="utf-8")).encode())==s["claude_ledger_normalized_sha256"])
ck("source_files_not_republished",not s["source_figures_republished"] and not any(x.suffix==".pdf" for x in P.iterdir()))
ck("own_figures_reviewed",s["own_figures_visually_checked"])
ck("alternate_directions_retained",len(s["original_directions_retained"])>=5)
ck("24_unique_unperformed_preparations",len(plan)==24 and len({x["id"] for x in plan})==24 and all(x["status"]=="not_run" and x["measurements"] is None for x in plan))
ck("12_independent_batch_groups",len({x["batch_group"] for x in plan})==12 and all(sum(y["batch_group"]==x["batch_group"] for y in plan)==2 for x in plan))
ck("no_dry_wet_replication_inflation",all(not x["independent_of_other_condition_same_batch"] and x["requires_separate_specimen"] for x in plan))
ck("sources_have_primary_urls",all(x["url"].startswith("https://") for x in sources))
ck("density_unit_ambiguity_disclosed",any("density unit" in t for x in sources for t in x.get("cautions",[])))
for p,expected in ix["before_sha256"].items():
 t=norm((R/p).read_text(encoding="utf-8"))
 for op in reversed([x for x in ix["operations"] if x["path"]==p]):
  ck("unique_reverse_"+str(len(checks)),t.count(op["new"])==1)
  t=t.replace(op["new"],op["old"],1)
 ck("history_restored_"+p,sha(t.encode())==expected)
report=R/"GPT往復/GPT回答_多方向探索第91巡_内部孔に頼らない薄枝と製造費の両立_20261009.md"
t=report.read_text(encoding="utf-8")
for token in ["物理試験0件","未算定","35算術照合","0.471","154.28","44.69","−116.50","50℃","60分","300mm","450mm","噴霧結晶化","同質量","未確認"]:
 ck("report_contains_"+token,token in t)
for name in ["mass_stiffness_wet.png","manufacture_cost_boundary.png"]:
 b=(P/name).read_bytes()
 ck("PNG_signature_"+name,b[:8]==b"\x89PNG\r\n\x1a\n")
 w,h=struct.unpack(">II",b[16:24]);ck("PNG_dimensions_"+name,w>=1000 and h>=600)
links=[]
for f in list(P.glob("*.md"))+[report]+[R/x for x in ix["before_sha256"]]:
 for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',f.read_text(encoding="utf-8")):
  link=link.strip("<>")
  if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:",link) or link.startswith("#"):continue
  target=urllib.parse.unquote(link.split("#")[0].split("?")[0])
  if not target:continue
  dest=(f.parent/target).resolve()
  if dest.parent==P and dest.name in ["manifest.json","document_audit.json"]:continue
  if not dest.exists():raise AssertionError("Broken link "+str(f.relative_to(R))+" -> "+link)
  links.append(link)
ck("local_links_resolve",len(links)>0)
before={n:sha((P/n).read_bytes()) for n in ["results.json","validation.json"]}
run=subprocess.run([sys.executable,str(P/"reproduce.py"),"--check"],capture_output=True)
ck("independent_rerun_exit_zero",run.returncode==0)
ck("rerun_did_not_mutate_results",before=={n:sha((P/n).read_bytes()) for n in before})
for f in P.iterdir():
 if f.is_file() and f.name not in ["document_audit.json","manifest.json"] and f.suffix in [".md",".json",".py"]:
  ck("LF_only_"+f.name,b"\r" not in f.read_bytes())
out={"all_passed":all(x["passed"] for x in checks),"document_checks":len(checks),"local_link_count":len(links),"numeric_checks":v["count"],"physical_experiments":0,"checks":checks}
(P/"document_audit.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({k:out[k] for k in ["all_passed","document_checks","local_link_count","numeric_checks","physical_experiments"]}))
