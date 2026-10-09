"""Independent arithmetic and artifact audit; git base or public raw base required."""
from pathlib import Path
import json,csv,math,re,subprocess,hashlib,shutil,urllib.request
from urllib.parse import unquote,quote
D=Path(__file__).resolve().parent;R=D.parents[1]
BASE='2b70115cfb1ca2e06dc78fdae650c315c6e635db'
REPORT=R/'GPT往復/GPT回答_多方向探索第77巡_滑走接点の発熱を抑える分割と荷重集中の反証_20261009.md'
def norm(s):return s.replace('\r\n','\n').rstrip()+'\n'
def j(n):return json.loads((D/n).read_text(encoding='utf-8'))
checks=[]
def ck(n,b):
 assert b,n
 checks.append({'name':n,'passed':True})
def near(a,b):return math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-14)
s=j('summary.json');mc=j('checks.json')
ck('physical_trials_zero_probability_null',s['physical_trials']==0 and s['success_probability'] is None)
ck('32_math_checks',mc['total']==mc['passed']==32 and all(x['passed'] for x in mc['checks']))
counts={'thermal_sensitivity.csv':144,'height_load_cases.csv':44,'array_memory.csv':12,'coupled_array.csv':48,'cost_sensitivity.csv':16,'normal_load_budget.csv':4,'convergence.csv':9}
rows={}
for fn,n in counts.items():
 with (D/fn).open(encoding='utf-8') as f:rows[fn]=list(csv.DictReader(f))
 ck('rows_'+fn,len(rows[fn])==n)
ck('277_comparison_rows',sum(counts.values())==277)
ck('load_independent',near(s['W0_N'],.8*math.pi*5e6*(50e-6)**2))
ck('effusivity_independent',near(s['effusivity'],math.sqrt(.4*950*2000)))
for x in rows['normal_load_budget.csv']:
 ck('root_budget_N'+x['N'],near(float(x['load_to_root_budget']),s['W0_N']/int(x['N'])/(1.6*5e-6)))
for x in rows['thermal_sensitivity.csv']:
 predicted=s['baseline_single_rise_C']*(float(x['mu_assumed'])/.1)*math.sqrt(float(x['v_m_s'])/10)*(float(x['eta_assumed'])/.5)*int(x['N'])**(-.25)
 assert near(predicted,float(x['deltaT_single_C']))
ck('all_thermal_scaling',True)
for x in rows['cost_sensitivity.csv']:
 area=float(x['area_m2']);n=int(x['N']);heads=3.117691453623979e12*6*area/2000;b=75e-6/math.sqrt(n)
 mass=heads*n*math.pi*b*b*10e-6*950+heads*n*math.pi*(2*b*2e-6-(2e-6)**2)*10e-6*950
 assert near(mass,float(x['total_addon_mass_kg'])) and near(mass/.8*float(x['assumed_JPY_kg']),float(x['raw_material_only_JPY']))
ck('material_mass_cost_independent',True)
ck('tests_not_run',len(j('test_matrix.json')['protocols'])==9 and all(x['state']=='not_run' for x in j('test_matrix.json')['protocols']))
text=REPORT.read_text(encoding='utf-8')
ck('report_status_and_scope',all(x in text for x in ['物理試験は0件','成功確率は未算定','277表行','32項目','1,080 t','14.074','8.573','受領は未確認']))
for png in ('thermal_and_tolerance.png','memory_and_material.png'):ck('PNG_'+png,(D/png).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
p=j('index_changes.json');indices=['README.md','回覧板.md','GPT往復/README.md','調査台帳/一般.md','調査台帳/計算部品索引.md']
G=shutil.which('git') or 'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def baseline(name):
 try:return norm(subprocess.run([G,'show',BASE+':'+name],cwd=R,capture_output=True,check=True).stdout.decode('utf-8'))
 except (OSError,subprocess.CalledProcessError):return norm(urllib.request.urlopen('https://raw.githubusercontent.com/serimu-yamamoto/jinkoukousetu-docs/'+BASE+'/'+quote(name,safe='/'),timeout=30).read().decode('utf-8'))
hashes={}
for name in indices:
 new=norm((R/name).read_text(encoding='utf-8'));old=baseline(name);hashes[name]=hashlib.sha256(old.encode()).hexdigest()
 if name=='README.md':restored=new.replace(p['readme_insert'],'',1)
 elif name=='GPT往復/README.md':restored=new.replace(p['gpt_insert'],'',1)
 elif name=='回覧板.md':
  restored=new.replace(p['newUpdate'],p['oldUpdate'],1).replace(p['newLatest'],p['oldLatest'],1)
  for key in ('boardEntry','handoff'):restored=restored.replace(p[key],'',1)
 elif name=='調査台帳/一般.md':restored=new.removesuffix(p['generalAppend'])
 else:restored=new.removesuffix(p['calcAppend'])
 ck('preserved_history_'+name,restored==old)
ledger=norm((R/'調査台帳/物性値照合_自律ループv2v3.md').read_text(encoding='utf-8'))
ck('claude_ledger_unchanged',hashlib.sha256(ledger.encode()).hexdigest()==j('sources.json')['claude_ledger']['sha256_lf']=='054c9388de3be3bd251c395059a9e02c9d3b336885236683ba3f528ff819d71f')
links=0
for file in [REPORT]+list(D.glob('*.md'))+[R/n for n in indices]:
 for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',file.read_text(encoding='utf-8')):
  if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target) or target.startswith('#'):continue
  target=unquote(target.split('#')[0].split('?')[0]);dest=file.parent/target
  assert dest.exists(),str(file)+' -> '+target
  links+=1
ck('relative_links_exist',links>400)
out={'cycle':77,'document_checks':len(checks),'links_checked':links,'checks':checks,'baseline_index_sha256_lf_normalized':hashes,'physical_trials':0,'success_probability':None,'visual_review':'Both generated PNGs visually inspected; source method pages inspected. Code/maths validated only.','copyrighted_source_PDFs_republished':False}
(D/'document_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'document_checks':len(checks),'links_checked':links,'all_passed':True}))
