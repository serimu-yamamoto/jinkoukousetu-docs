"""Cycle 78: independent arithmetic, units, history and reference audit."""
from pathlib import Path
import json,csv,math,re,subprocess,hashlib,shutil,urllib.request
from urllib.parse import unquote,quote
D=Path(__file__).resolve().parent;R=D.parents[1]
BASE='ae463e8ebcf16ef02fd23369d1398b4081216139'
REPORT=R/'GPT往復/GPT回答_多方向探索第78巡_支持ばねの実寸制約と揺動する荷重分配_20261009.md'
def norm(s):return s.replace('\r\n','\n').rstrip()+'\n'
def j(n):return json.loads((D/n).read_text(encoding='utf-8'))
checks=[]
def ck(n,b):
 assert b,n
 checks.append({'name':n,'passed':True})
def near(a,b):return math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-13)
s=j('summary.json');mc=j('checks.json')
ck('physical_trials_zero_probability_null',s['physical_trials']==0 and s['success_probability'] is None)
ck('28_math_checks',mc['total']==mc['passed']==28 and all(x['passed'] for x in mc['checks']))
rows={}
for fn,n in s['row_counts'].items():
 with (D/fn).open(encoding='utf-8') as f:rows[fn]=list(csv.DictReader(f))
 ck('row_count_'+fn,len(rows[fn])==n)
ck('592_calculation_rows',sum(map(len,rows.values()))==592)
W=.8*math.pi*5e6*(50e-6)**2;delta=W/20000
for x in rows['axial_posts.csv']:
 r=float(x['r_um'])*1e-6;L=float(x['L_um'])*1e-6;E=float(x['E_Pa']);k=20000/int(x['N']);force=W/int(x['N'])
 assert near(E*math.pi*r*r/L,k)
 assert near(math.pi**2*E*(math.pi*r**4/4)/(4*L*L)/force,float(x['Euler_fixed_free_Pcr_over_F']))
ck('column_units_and_boundary_condition',True)
for x in rows['fixed_guided_beams.csv']:
 L=float(x['L_um'])*1e-6;t=float(x['t_um'])*1e-6;w=float(x['required_width_um'])*1e-6
 assert near(4*float(x['E_Pa'])*w*t**3/L**3,20000/int(x['N']))
 assert near(3*t*2.5e-6/L**2,float(x['at_2p5um_strain']))
ck('fixed_guided_factors',True)
for x in rows['rocker_pairs.csv']:
 force=2*W/int(x['N']);hi=float(x['high_load_mN'])*1e-3;lo=float(x['low_load_mN'])*1e-3
 assert near(hi+lo,force) and near((hi-lo)/force,float(x['imbalance']))
 ah=math.sqrt(4*force*250e-6/(math.pi*5e8*100e-6));th=float(x['theta_deg'])*math.pi/180
 assert near(ah*1e6,float(x['fulcrum_contact_half_width_um']))
 assert near((10e-6-ah-250e-6*abs(th))*1e6,float(x['fulcrum_contact_margin_um']))
ck('rocker_force_and_micrometre_margin',True)
for x in rows['uniaxial_energy_bound.csv']:
 v=float(x['volume_per_original_head_um3'])*1e-18
 assert near(.5*float(x['E_Pa'])*float(x['assumed_elastic_strain_limit'])**2*v,.5*W*delta)
ck('energy_capacity_units',True)
for x in rows['lateral_moment_budget.csv']:
 n=int(x['N']);force=2*W/n;l=(3*50e-6/math.sqrt(n)+10e-6)/2
 cap=5*2*math.pi*10e-6*.0679*25e-6
 val=(float(x['b_um'])*1e-6+cap/force+2e-9*(2*math.pi/180)/force+float(x['mu_assumed'])*float(x['h_um'])*1e-6)/l
 assert near(val,float(x['imbalance_bound_from_torque']))
ck('lateral_moment_bound_units',True)
ck('test_specs_not_run',j('test_plan.json')['status']=='not_executed' and len(j('test_plan.json')['specifications'])==7)
ck('decision_unproven',j('decision.json')['no_adoption_yet'] and j('decision.json')['success_probability'] is None)
text=REPORT.read_text(encoding='utf-8')
ck('report_evidence_scope',all(x in text for x in ['物理試験0件','成功確率未算定','592計算行','28数式照合','12.21','全体の平衡','未確認']))
for png in ('support_rocker_cost.png','rocker_concept.png'):ck('PNG_'+png,(D/png).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
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
out={'cycle':78,'document_checks':len(checks),'links_checked':links,'checks':checks,'baseline_index_sha256_lf_normalized':hashes,'physical_trials':0,'success_probability':None,'visual_review':'Both generated PNGs visually inspected. Primary source access is limited to the scopes in sources.json. Code/maths only.','copyrighted_source_PDFs_republished':False}
(D/'document_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'document_checks':len(checks),'links_checked':links,'all_passed':True}))
