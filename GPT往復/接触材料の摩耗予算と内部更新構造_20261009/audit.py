from pathlib import Path
import hashlib,json,re,urllib.parse,math,csv
P=Path(__file__).resolve().parent;R=P.parents[1]
checks=[]
def ck(n,v):
 if not v: raise AssertionError(n)
 checks.append({'check':n,'passed':True})
def norm(s):return s.replace('\r\n','\n').rstrip()+'\n'
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
s=json.loads((P/'summary.json').read_text(encoding='utf8'));ver=json.loads((P/'verification.json').read_text(encoding='utf8'))
ck('physical_tests_zero',s['physical_tests_performed']==0 and ver['physical_experiments']==0)
ck('probability_null',s['success_probability'] is None)
ck('numeric_checks',len(ver['checks'])==s['math_accounting_checks']==53 and all(x['passed'] for x in ver['checks']))
ck('rows',sum(len(list(csv.DictReader(f.open(encoding='utf8')))) for f in P.glob('*.csv'))==s['comparison_rows']==86)
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
rep=R/'GPT往復/GPT回答_多方向探索第80巡_摩耗後も滑る接触部と混雑帯の耐久条件_20261009.md'
body=rep.read_text(encoding='utf8')
for phrase in ['物理試験0件','成功確率は未算定','保証寿命','仮のk','76.4％','450mm','60分','原料分のみ','300mm','R39','受領・返答・稼働は未確認']:
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
out={'document_checks':checks,'local_links_checked':local_links,'physical_experiments':0,'reported_success_probability':None}
(P/'document_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'document_checks':len(checks),'local_links':local_links,'numeric_checks':s['math_accounting_checks'],'comparison_rows':s['comparison_rows'],'physical_experiments':0}))
