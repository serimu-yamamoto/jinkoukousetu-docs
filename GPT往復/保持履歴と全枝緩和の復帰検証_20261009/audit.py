"""Integrity and model-result audit, not a material certification."""
from pathlib import Path
import json,hashlib,math,re,urllib.parse,struct,subprocess,sys
P=Path(__file__).resolve().parent;R=P.parents[1];checks=[]
def read(n):return json.loads((P/n).read_text(encoding='utf-8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def norm(t):return t.replace('\r\n','\n')
def ck(n,b):
 checks.append({'name':n,'passed':bool(b)})
 if not b:raise AssertionError(n)
s=read('research_state.json');r=read('results.json');v=read('validation.json');f=read('finite_recovery.json');e=read('event_audit.json');i=read('inputs.json');p=read('test_plan.json');ix=read('index_changes.json')
ck('experiments_zero',all(d['physical_experiments']==0 for d in [s,r,f,i,p]))
ck('probability_unknown',all(d['success_probability'] is None for d in [s,r,f,i,p]))
ck('no_equipment_contacts_or_quotes',not s['facilities_available'] and not s['collaborators_available'] and s['contacts_sent']==s['quotes_obtained']==0)
ck('no_claim_of_claude_reply',not s['claude_receipt_confirmed'] and not s['claude_reply_confirmed'])
ck('no_calibrated_material',s['selected_material'] is None and r['actual_material_parameters'] is None and not i['material_fit'])
ck('no_actual_50C_time_or_ski_response',r['actual_50C_recovery_seconds'] is None and r['actual_ski_response'] is None)
ck('not_crystal_growth',not s['snow_crystal_growth_confirmed'])
ck('173_model_checks',v['count']==173 and v['all_passed'] and all(x['passed'] for x in v['checks']))
ck('simulation_counts',len(r['cases'])==72 and len(r['candidate_cases'])==6 and len(r['tolerance_cases'])==12)
ck('independent_solver_pairs',len(r['independent_solver_comparisons'])==4 and len(f['independent_comparisons'])==6)
ck('reduced_step_event_checks',len(e['checks'])==4 and e['all_passed'])
for j,x in enumerate(r['cases']+r['candidate_cases']):
 ck('energy_and_solver_'+str(j),x['solver_success'] and x['relative_energy_balance_error']<2e-6)
 ck('no_settled_recovery_claim_'+str(j),x['settled_recovery_time'] is None and not x['zero_event_is_physical_recovery'])
for j,x in enumerate(r['candidate_cases']):
 if x['beta']==.75:ck('near_zero_event_unusable_'+str(j),not x['zero_event_timing_usable'])
ck('finite_cases_count',len(f['cases'])==12)
for j,x in enumerate(f['cases']):
 lim=x['position_band'][1];lam=x['lambda'];U=lambda z:(.5*z*(z-2))**2+.5*lam*z*z
 ck('energy_threshold_'+str(j),lam>.25 and math.isclose(x['energy_threshold'],min(U(lim),U(-lim))*(1-1e-6),rel_tol=1e-12))
 ck('enclosure_result_'+str(j),x['energy_enclosure_T'] is not None and x['relative_energy_balance_error']<2e-6 and abs(x['end_X'])<=lim and math.isclose(x['end_energy'],x['energy_threshold'],rel_tol=1e-9) and x['physical_recovery_seconds'] is None)
ck('finite_solver_agreement',all(x['passed'] and x['relative_time_difference']<2e-5 for x in f['independent_comparisons']))
for j in [0,1]:
 part=R/'.git'/('finite96_'+str(j)+'.json')
 if part.exists():
  q=json.loads(part.read_text())
  ck('partial_rerun_matches_'+str(j),q['cases']==f['cases'][2*j:2*j+2] and q['independent_comparisons']==f['independent_comparisons'][j:j+1])
ck('cost_arithmetic',all(x['increment_JPY']==x['finished_kg']*x['extra_finished_kg_cost_JPY'] and not x['quoted'] for x in r['cost_cases']))
ck('24_unperformed_individuals',len(p['specimens'])==24 and all(x['status']=='not_run' and x['lot_id'] is None and x['measured_recovery'] is None and x['measured_force_curve'] is None and x['measured_wear'] is None for x in p['specimens']))
ck('specimen_factors',len({(x['shape'],x['hold_seconds'],x['environment'],x['replicate']) for x in p['specimens']})==24)
ck('specimen_ids',len({x['id'] for x in p['specimens']})==24)
ledger=norm((R/'調査台帳/物性値照合_自律ループv2v3.md').read_text(encoding='utf-8'))
ck('claude_ledger_preserved',sha(ledger.encode())==s['claude_ledger_sha256_LF'])
for path,expected in ix['before_sha256'].items():
 text=norm((R/path).read_text(encoding='utf-8'))
 for j,o in reversed(list(enumerate(ix['operations']))):
  if o['path']==path:
   ck('unique_reverse_'+str(j),text.count(o['new'])==1)
   text=text.replace(o['new'],o['old'],1)
 ck('index_history_'+path,sha(text.encode())==expected)
report=R/'GPT往復/GPT回答_多方向探索第96巡_長時間荷重でも戻る粒形状と製造ばらつきの条件_20261009.md'
text=report.read_text(encoding='utf-8')
for word in ['50℃','450mm','300mm','60分','2億円','成功確率未算定','受領・返答・稼働は未確認','約49.8％','秒ではない','雪の結晶成長ではない']:
 ck('report_condition_'+word,word in text)
links=[]
for path in list(P.glob('*.md'))+[report]+[R/k for k in ix['before_sha256']]:
 for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
  link=link.strip('<>')
  if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',link) or link.startswith('#'):continue
  target=urllib.parse.unquote(link.split('#')[0].split('?')[0])
  if not target:continue
  dest=(path.parent/target).resolve()
  if dest.parent==P and dest.name in ['document_audit.json','manifest.json']:continue
  if not dest.exists():raise AssertionError('Broken local link '+str(path.relative_to(R))+' -> '+link)
  links.append(link)
ck('local_links_resolve',bool(links))
for name in ['recovery_history.png','force_tolerance.png']:
 data=(P/name).read_bytes();ck('png_signature_'+name,data[:8]==b'\x89PNG\r\n\x1a\n')
 w,h=struct.unpack('>II',data[16:24]);ck('png_size_'+name,w>=1000 and h>=600)
prior={n:sha((P/n).read_bytes()) for n in ['results.json','validation.json']}
rp=subprocess.run([sys.executable,str(P/'reproduce.py'),'--revalidate-saved'],capture_output=True)
ck('saved_results_revalidation',rp.returncode==0)
ck('saved_bytes_preserved',prior=={n:sha((P/n).read_bytes()) for n in prior})
for path in P.iterdir():
 if path.is_file() and path.suffix in ['.py','.md','.json','.txt'] and path.name not in ['document_audit.json','manifest.json']:
  ck('LF_'+path.name,b'\r' not in path.read_bytes())
obj={'all_passed':all(x['passed'] for x in checks),'audit_checks':len(checks),'model_checks':v['count'],'independent_solver_pairs':10,'event_step_checks':4,'local_link_count':len(links),'physical_experiments':0,'checks':checks}
(P/'document_audit.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:obj[k] for k in obj if k!='checks'}))
