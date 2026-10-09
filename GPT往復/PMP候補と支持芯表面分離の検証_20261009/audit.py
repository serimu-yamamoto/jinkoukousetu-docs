"""Publication integrity audit; it does not validate physical performance."""
from pathlib import Path
import hashlib,json,re,urllib.parse,subprocess,sys,struct
P=Path(__file__).resolve().parent;R=P.parents[1];checks=[]
def ck(n,v):
 checks.append({"name":n,"passed":bool(v)})
 if not v:raise AssertionError(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def norm(s):return s.replace("\r\n","\n").rstrip()+"\n"
def read(n):return json.loads((P/n).read_text(encoding="utf-8"))
s=read("research_state.json");res=read("results.json");v=read("validation.json");i=read("inputs.json");ix=read("index_changes.json");plan=read("test_plan.json");sources=read("sources.json")
ck("34_arithmetic_checks",v["count"]==34 and v["all_passed"])
ck("physical_trials_zero",s["physical_experiments"]==res["physical_experiments"]==i["physical_experiments"]==0)
ck("success_unknown",s["success_probability"] is None and res["success_probability"] is None)
ck("material_not_selected",s["selected_material"] is None and res["actual_material_selected"] is None)
ck("50C_bond_unmeasured",not s["actual_hybrid_bond_confirmed"] and res["actual_50C_interface_bond"] is None)
ck("50C_moduli_are_scenarios",res["all_50C_moduli_are_scenarios"])
ck("not_particle_bed_simulation",not res["physical_grain_bed_simulation"])
ck("15_sections_60_interfaces",len(res["hybrid_rows"])==15 and len(res["interface_rows"])==60)
ck("12_friction_27_cost_cases",len(res["friction_budget_rows"])==12 and len(res["cost_rows"])==27)
ck("all_costs_unquoted",s["actual_quote"] is None and all(x["actual_quote"] is None for x in res["cost_rows"]))
ck("patent_not_ski_input",s["patent_steel_mu_not_used_as_ski_mu"] and not i["friction"]["source_patent_friction_used_as_design_input"])
ck("patent_not_commercial_grade_measurement",i["source_checks"]["patent_values_not_Rt18_or_Opulent"])
ck("film_large_deflection_disclosed",res["thin_film_diagnostic"]["large_deflection_invalidates_linear_prediction"] and res["thin_film_diagnostic"]["actual_deflection"] is None)
ck("18_unperformed_pairs",len(plan)==18 and len({x["id"] for x in plan})==18 and all(x["status"]=="not_run" and x["measurements"] is None for x in plan))
ck("no_fabricated_lot_replication",all(not x["manufacturing_lot_independence_confirmed"] for x in plan))
ck("no_contacts_orders_equipment",s["contacts_sent"]==s["purchases"]==0 and not s["equipment_secured"] and not s["collaborator_secured"])
ck("claude_status_unknown",all(s[k] is None for k in ["claude_receipt","claude_reply","claude_running"]))
ck("claude_source_unchanged",sha(norm((R/s["claude_ledger"]).read_text(encoding="utf-8")).encode())==s["claude_ledger_normalized_sha256"])
ck("original_figures_reviewed",s["own_figures_visually_checked"])
ck("sources_not_republished",not s["source_figures_republished"] and not any(p.suffix==".pdf" for p in P.iterdir()))
ck("alternate_routes_retained",len(s["alternate_directions_retained"])>=5)
ck("abstract_access_limit_recorded","abstract" in next(x for x in sources if x["id"]=="S5")["inspection"])
for p,expected in ix["before_sha256"].items():
 t=norm((R/p).read_text(encoding="utf-8"))
 for op in reversed([x for x in ix["operations"] if x["path"]==p]):
  ck("unique_reverse_"+str(len(checks)),t.count(op["new"])==1)
  t=t.replace(op["new"],op["old"],1)
 ck("history_restored_"+p,sha(t.encode())==expected)
report=R/"GPT往復/GPT回答_多方向探索第92巡_離型性と滑走性を分けたPMP複合枝の検証_20261009.md"
text=report.read_text(encoding="utf-8")
for tok in ["物理試験0件","未算定","34算術照合","100.48","1,215","62.9","約47％","14.3％","6,781","50℃","60分","450mm","300mm","常温噴霧結晶化","嵩密度","A1"]:
 ck("report_contains_"+tok,tok in text)
for name in ["core_skin_sections.png","stiffness_cost_frontiers.png"]:
 b=(P/name).read_bytes();ck("PNG_signature_"+name,b[:8]==b"\x89PNG\r\n\x1a\n")
 w,h=struct.unpack(">II",b[16:24]);ck("PNG_size_"+name,w>=1000 and h>=600)
links=[]
for f in list(P.glob("*.md"))+[report]+[R/p for p in ix["before_sha256"]]:
 for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',f.read_text(encoding="utf-8")):
  link=link.strip("<>")
  if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:",link) or link.startswith("#"):continue
  target=urllib.parse.unquote(link.split("#")[0].split("?")[0])
  if not target:continue
  dest=(f.parent/target).resolve()
  if dest.parent==P and dest.name in ["manifest.json","document_audit.json"]:continue
  if not dest.exists():raise AssertionError("Broken local link: "+str(f.relative_to(R))+" -> "+link)
  links.append(link)
ck("local_links_resolve",len(links)>0)
before={n:sha((P/n).read_bytes()) for n in ["results.json","validation.json"]}
run=subprocess.run([sys.executable,str(P/"reproduce.py"),"--check"],capture_output=True)
ck("reproduction_succeeds",run.returncode==0)
ck("reproduction_preserves_results",before=={n:sha((P/n).read_bytes()) for n in before})
for f in P.iterdir():
 if f.is_file() and f.name not in ["document_audit.json","manifest.json"] and f.suffix in [".md",".json",".py"]:
  ck("LF_only_"+f.name,b"\r" not in f.read_bytes())
out={"all_passed":all(x["passed"] for x in checks),"document_checks":len(checks),"local_link_count":len(links),"numeric_checks":v["count"],"physical_experiments":0,"checks":checks}
(P/"document_audit.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({k:out[k] for k in ["all_passed","document_checks","local_link_count","numeric_checks","physical_experiments"]}))
