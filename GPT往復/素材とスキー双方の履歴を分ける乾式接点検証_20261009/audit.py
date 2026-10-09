from pathlib import Path
import hashlib,json,re,urllib.parse,subprocess,sys
P=Path(__file__).resolve().parent
R=P.parents[1]
checks=[]
def ck(name,ok):
 checks.append({'name':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
def sha(b):return hashlib.sha256(b).hexdigest()
def norm(s):return s.replace('\r\n','\n').rstrip()+'\n'
ix=json.loads((P/'index_changes.json').read_text(encoding='utf-8'))
state=json.loads((P/'research_state.json').read_text(encoding='utf-8'))
v=json.loads((P/'validation.json').read_text(encoding='utf-8'))
a=json.loads((P/'specimen_allocation.json').read_text(encoding='utf-8'))
res=json.loads((P/'results.json').read_text(encoding='utf-8'))
ck('28_numeric_checks',v['count']==28 and v['all_passed'])
ck('no_physical_trials',state['physical_experiments']==res['physical_experiments_performed']==0)
ck('no_success_estimate',state['success_probability'] is None and res['success_probability'] is None)
ck('no_contacts_or_purchases',state['contacts_sent']==state['purchases']==0)
ck('no_claimed_claude_receipt',all(state[k] is None for k in ['claude_receipt','claude_reply','claude_running']))
ck('all_endpoints_unperformed',all(r['status']=='not_performed' and r['measured_mu'] is None for r in a['endpoint_runs']))
ck('all_donors_unperformed',all(r['status']=='not_performed' for r in a['conditioning_runs']))
ledger=norm((R/state['claude_ledger']).read_text(encoding='utf-8'))
ck('claude_ledger_unchanged',sha(ledger.encode())==state['claude_ledger_normalized_sha256'])
for p,expected in ix['before_sha256'].items():
 t=norm((R/p).read_text(encoding='utf-8'))
 for op in reversed([x for x in ix['operations'] if x['path']==p]):
  ck('unique_reverse_operation_'+p+'_'+str(len(checks)),t.count(op['new'])==1)
  t=t.replace(op['new'],op['old'],1)
 ck('history_restored_'+p,sha(t.encode())==expected)
report=R/'GPT往復/GPT回答_多方向探索第89巡_慣らした板だけに依存しない滑走接点_20261009.md'
text=report.read_text(encoding='utf-8')
for token in ['物理試験0件','成功確率','架空','総額は未算定','60分','450mm','300mm','Claude','28件']:
 ck('report_contains_'+token,token in text)
ck('states_not_fitted_to_literature','フィットもしていない' in (P/'model.md').read_text(encoding='utf-8'))
ck('all_costs_incomplete',all(x['full_cost_yen'] is None for x in res['motion_budget_sensitivity']))
files=list(P.glob('*.md'))+[report]+[R/p for p in ix['before_sha256']]
local_links=[]
for f in files:
 for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
  link=link.strip('<>')
  if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',link) or link.startswith('#'):continue
  target=urllib.parse.unquote(link.split('#')[0].split('?')[0])
  if not target:continue
  dest=(f.parent/target).resolve()
  if dest.name in ['manifest.json','audit.json'] and dest.parent==P:continue
  if not dest.exists():raise AssertionError('Broken link '+str(f.relative_to(R))+' -> '+link)
  local_links.append({'file':str(f.relative_to(R)).replace('\\','/'),'target':link})
ck('local_links_resolve',len(local_links)>0)
outputs=['results.json','specimen_allocation.json','validation.json']
before={p:sha((P/p).read_bytes()) for p in outputs}
proc=subprocess.run([sys.executable,str(P/'reproduce.py')],capture_output=True)
ck('reproduction_exit_zero',proc.returncode==0)
ck('reproduction_byte_identical',before=={p:sha((P/p).read_bytes()) for p in outputs})
for f in P.iterdir():
 if f.is_file() and f.name not in ['audit.json','manifest.json'] and f.suffix in ['.md','.json','.py']:ck('lf_only_'+f.name,b'\r' not in f.read_bytes())
result={'all_passed':all(x['passed'] for x in checks),'document_checks':len(checks),'local_link_count':len(local_links),'numeric_checks':v['count'],'physical_experiments':0,'checks':checks}
(P/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:result[k] for k in ['all_passed','document_checks','local_link_count','numeric_checks','physical_experiments']}))
