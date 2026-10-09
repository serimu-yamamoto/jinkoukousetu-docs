from pathlib import Path
import hashlib,json,re,urllib.parse,math,csv,sys,platform,importlib.metadata
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'.deps'))
P=Path(__file__).resolve().parent;R=P.parents[1]
checks=[]
def ck(n,v):
 if not v: raise AssertionError(n)
 checks.append({'check':n,'passed':True})
def norm(s):return s.replace('\r\n','\n').rstrip()+'\n'
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
s=json.loads((P/'summary.json').read_text(encoding='utf8'));ver=json.loads((P/'checks.json').read_text(encoding='utf8'))
ck('physical_tests_zero',s['physical_experiments']==0 and ver['physical_experiments']==0)
ck('probability_null',s['success_probability'] is None)
ck('numeric_checks',len(ver['checks'])==s['math_numerical_checks']==50 and all(x['passed'] for x in ver['checks']))
profile_names={'profiles.csv','recessed_support_profiles.csv'}
ck('comparison_rows',sum(len(list(csv.DictReader(f.open(encoding='utf8')))) for f in P.glob('*.csv') if f.name not in profile_names)==s['comparison_rows_excluding_profiles']==146)
ck('profile_rows',sum(len(list(csv.DictReader((P/f).open(encoding='utf8')))) for f in profile_names)==s['profile_rows']==4096)
idx=json.loads((P/'index_changes.json').read_text(encoding='utf8'))
for f,h in idx['before_hashes'].items():
 t=norm((R/f).read_text(encoding='utf8'))
 for op in reversed(idx['operations']):
  if op['path']==f:
   ck('reverse_unique_'+str(len(checks)),t.count(op['new'])==1);t=t.replace(op['new'],op['old'])
 ck('history_preserved_'+f,digest(t)==h)
claude=norm((R/'調査台帳/物性値照合_自律ループv2v3.md').read_text(encoding='utf8'))
ck('claude_ledger_unchanged',digest(claude)=='054c9388de3be3bd251c395059a9e02c9d3b336885236683ba3f528ff819d71f')
tests=json.loads((P/'test_plan.json').read_text(encoding='utf8'))['tests'];ck('protocols_not_results',len(tests)==8 and all(t['status']=='not_run' and t['data'] is None for t in tests))
rep=R/'GPT往復/GPT回答_多方向探索第81巡_摩耗で平らになる面と突き出す接点の比較_20261009.md'
body=rep.read_text(encoding='utf8')
for phrase in ['物理試験0件','成功確率は未算定','営業寿命の予測ではない','未測定τ','85.3％','450mm','60分','実見積りではなく','300mm','R39','受領・稼働・返答は未確認','設備・協力先はまだない','格子依存']:
 ck('report_guard_'+phrase,phrase in body)
local_links=0
for f in [rep,*P.glob('*.md'),*(R/x for x in idx['before_hashes'])]:
 for u in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',f.read_text(encoding='utf8')):
  if re.match(r'^[a-zA-Z]+:',u) or u.startswith('#'):continue
  q=urllib.parse.unquote(u.split('#')[0]).strip('<>')
  target=f.parent/q
  # Two audit-generated files and manifest are created after this link pass.
  ckname='link_'+str(local_links)
  if not target.exists() and target.name not in ['manifest.json','document_audit.json']:raise AssertionError(ckname+': '+str(target))
  local_links+=1
ck('links_checked',local_links>100)
ck('no_original_papers_published',not list(P.glob('*.pdf')))
for f in [rep,*P.glob('*.md'),*P.glob('*.py'),*P.glob('*.json'),*P.glob('*.csv'),*(R/x for x in idx['before_hashes'])]:
 ck('LF_'+f.name,b'\r' not in f.read_bytes())
ck('three_plots',len(list(P.glob('*.png')))==3)
request=(P/'first_test_request.md').read_text(encoding='utf8')
ck('physical_entry_prepared',all(x in request for x in ['18','未送信','未実施','50']))
ck('user_test_access_recorded',json.loads((P/'decision.json').read_text(encoding='utf8'))['physical_test_access']['user_confirmed']=='no equipment or collaborators yet')
out={'environment':{'python':platform.python_version(),**{name:importlib.metadata.version(name) for name in ['numpy','scipy','matplotlib']}},'document_checks':checks,'local_links_checked':local_links,'physical_experiments':0,'reported_success_probability':None}
(P/'document_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'document_checks':len(checks),'local_links':local_links,'numeric_checks':s['math_numerical_checks'],'comparison_rows':s['comparison_rows_excluding_profiles'],'physical_experiments':0}))
