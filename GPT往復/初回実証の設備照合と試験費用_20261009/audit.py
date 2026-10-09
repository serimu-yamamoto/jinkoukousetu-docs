from pathlib import Path
import hashlib,json,re,urllib.parse,platform
P=Path(__file__).resolve().parent;R=P.parents[1]
checks=[]
def ck(name,ok):
 if not ok:raise AssertionError(name)
 checks.append({'name':name,'passed':True})
def norm(s):return s.replace('\r\n','\n').rstrip()+'\n'
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def read(n):return json.loads((P/n).read_text(encoding='utf8'))
s=read('summary.json');n=read('checks.json');d=read('decision.json')
ck('physical_zero_and_probability_unknown',s['physical_experiments']==d['physical_experiments']==0 and s['success_probability'] is None and d['success_probability'] is None)
ck('no_actual_supplier_action',s['provider_contacts_sent']==s['purchase_orders']==d['quotes_received']==0 and d['equipment_secured'] is False)
ck('numeric_checks',s['numeric_checks']==len(n)==25 and all(x['passed'] for x in n))
ck('calculation_rows',sum(len(read(f)) for f in ['geometry.json','wear_detection.json','cost_scenarios.json','time_scenarios.json'])==s['calculation_rows']==23)
plan=read('main_run_plan.json')
ck('not_run_plan',len(plan)==18 and all(x['status']=='not_run' and x['data'] is None for x in plan))
ck('balanced_material_state_counts',all(sum(x['material']==m and x['state']==v for x in plan)==3 for m in read('inputs.json')['test']['materials'] for v in ['dry','once_wet_then_drained']))
ck('total_cost_unknown',s['main_total_cost_yen'] is None)
ck('source_inventory',len(read('sources.json'))==9 and all(x['verified']=='2026-10-09' and x['url'].startswith('https://') for x in read('sources.json')))
idx=read('index_changes.json')
for f,h in idx['before_hashes'].items():
 t=norm((R/f).read_text(encoding='utf8'))
 for op in reversed(idx['operations']):
  if op['path']==f:
   ck('unique_reverse_'+str(len(checks)),t.count(op['new'])==1)
   t=t.replace(op['new'],op['old'])
 ck('history_preserved_'+f,sha(t)==h)
ck('claude_ledger_unchanged',sha(norm((R/'調査台帳/物性値照合_自律ループv2v3.md').read_text(encoding='utf8')))=='054c9388de3be3bd251c395059a9e02c9d3b336885236683ba3f528ff819d71f')
rep=R/'GPT往復/GPT回答_多方向探索第82巡_設備未確保から始める実証と試験費用_20261009.md'
body=rep.read_text(encoding='utf8')
for phrase in ['物理試験0件','成功確率は未算定','実見積りでも総額でもなく','約477.5rpm','約0.9〜1.1m/s','クリープ','450mm','300mm','R39','約60分','人体・環境への無害性は未証明','受領・返答・稼働は未確認']:
 ck('report_guard_'+phrase,phrase in body)
local_links=0
for f in [rep,*P.glob('*.md'),*(R/x for x in idx['before_hashes'])]:
 for u in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',f.read_text(encoding='utf8')):
  if re.match(r'^[a-zA-Z]+:',u) or u.startswith('#'):continue
  target=f.parent/urllib.parse.unquote(u.split('#')[0]).strip('<>')
  if not target.exists() and target.name not in ['manifest.json','document_audit.json']:
   raise AssertionError('missing link '+str(target))
  local_links+=1
ck('local_links_verified',local_links>500)
for f in [rep,*P.iterdir(),*(R/x for x in idx['before_hashes'])]:
 if f.is_file():ck('LF_'+f.name,b'\r' not in f.read_bytes())
out={'document_checks':checks,'local_links_checked':local_links,'python':platform.python_version(),'physical_experiments':0,'success_probability':None}
(P/'document_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'document_checks':len(checks),'local_links':local_links,'numeric_checks':25,'calculation_rows':23,'physical_experiments':0}))
