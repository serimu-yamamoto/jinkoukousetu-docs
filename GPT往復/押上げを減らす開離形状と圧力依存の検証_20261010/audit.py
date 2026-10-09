from pathlib import Path
import json,re,hashlib,subprocess,urllib.parse
D=Path(__file__).resolve().parent
R=D.parents[1]
G='C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
I=load(D/'inputs.json');V=load(D/'validation.json');O=load(D/'results.json');S=load(D/'research_state.json');P=load(D/'test_plan.json');C=load(D/'index_changes.json')
checks=[]
def check(n,c):
 if not c:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
check('unmeasured-not-probability',V['physical_tests']==S['physical_tests']==0 and S['success_probability'] is None)
check('numeric-validation',V['passed'] and V['checks']==142 and len(O['rows'])==72)
check('base-agreement',I['base_commit']==S['base_commit']==C['base_commit'])
check('planned-126',len(P['conditions'])==126)
check('unique-allocations',len({r['id'] for r in P['conditions']})==126)
check('all-unperformed',all(r['status']=='not_run' and r['measured_curve'] is None and r['actual_temperature_C'] is None for r in P['conditions']))
check('artificial-108',sum(r['shape']!='fresh_groomed_snow_reference' for r in P['conditions'])==108)
check('reference-18',sum(r['shape']=='fresh_groomed_snow_reference' for r in P['conditions'])==18)
check('target-not-complete',not S['goal_complete'] and S['core_requirements']['physical_snow_feel']=='unproven')
for p,original_hash in C['original_sha256'].items():
 text=(R/p).read_text(encoding='utf-8')
 for op in reversed([op for op in C['operations'] if op['path']==p]):
  check('unique-added-anchor-'+p+str(len(checks)),text.count(op['after'])==1)
  text=text.replace(op['after'],op['before'],1)
 check('old-content-preserved-'+p,sha(text.encode())==original_hash)
 proc=subprocess.run([G,'show',C['base_commit']+':'+p],cwd=R,capture_output=True)
 check('base-content-verified-'+p,proc.returncode==0 and sha(proc.stdout)==original_hash)
ledger='調査台帳/物性値照合_自律ループv2v3.md'
check('claude-unchanged',sha((R/ledger).read_text(encoding='utf-8').encode())==S['claude_ledger_sha256'])
report=next(R.glob('GPT往復/GPT回答_多方向探索第98巡_*.md'))
files=list(D.glob('*.md'))+[report]+[R/p for p in C['original_sha256']]
links=0
for p in files:
 body=p.read_text(encoding='utf-8')
 for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',body):
  target=target.split('#')[0]
  if not target or re.match(r'[A-Za-z][A-Za-z0-9+.-]*:',target):continue
  resolved=(p.parent/urllib.parse.unquote(target)).resolve()
  check('local-link-'+str(links),resolved.exists())
  links+=1
for p in D.iterdir():
 if p.is_file() and p.name!='document_audit.json' and p.suffix in {'.json','.py','.md','.txt'}:
  check('utf8-LF-'+p.name,b'\r' not in p.read_bytes())
check('code-no-syntax-errors',all(compile(p.read_text(encoding='utf-8'),str(p),'exec') for p in D.glob('*.py')))
for name in ['concept.png','pressure_and_release.png']:
 check('png-'+name,(D/name).read_bytes()[:8]==b'\x89PNG\r\n\x1a\n')
out={'passed':True,'checks':len(checks),'local_links_verified':links,'purpose':'Publication data consistency; not physical validation','physical_tests':0,'success_probability':None,'index_reversible_operations':len(C['operations']),'names':checks}
(D/'document_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in out.items() if k!='names'},ensure_ascii=False))
