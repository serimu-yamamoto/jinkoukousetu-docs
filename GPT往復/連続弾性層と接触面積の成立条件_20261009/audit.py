"""Cycle 79: arithmetic, scope, history, and reference audit; no experiments."""
from pathlib import Path
import json,csv,math,re,subprocess,hashlib,shutil
from urllib.parse import unquote
D=Path(__file__).resolve().parent;R=D.parents[1]
BASE='9547993e3fe089afde054334b1161ed050c8faac'
REPORT=R/'GPT往復/GPT回答_多方向探索第79巡_可動部を省く弾性層と滑り抵抗の交換条件_20261009.md'
def norm(s):return s.replace('\r\n','\n').rstrip()+'\n'
def j(n):return json.loads((D/n).read_text(encoding='utf-8'))
checks=[]
def ck(n,b):
 assert b,n
 checks.append(dict(name=n,passed=True))
def near(a,b):return math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-12)
s=j('summary.json');mc=j('checks.json');inp=j('inputs.json')
ck('physical_evidence_scope',s['physical_trials']==0 and s['success_probability'] is None)
ck('30_numerical_checks',len(mc)==30 and all(x['passed'] for x in mc))
rows={}
for fn,n in s['row_counts'].items():
 with (D/fn).open(encoding='utf-8') as f:rows[fn]=list(csv.DictReader(f))
 ck('rows_'+fn,len(rows[fn])==n)
ck('479_comparison_rows',sum(len(v) for k,v in rows.items() if k!='pressure_profiles.csv')==479)
ck('1280_profile_samples_not_experiments',len(rows['pressure_profiles.csv'])==1280)
pbar=.8*math.pi*5e6*(50e-6)**2/(190e-6)**2
ck('pressure_unit_mapping',near(pbar,inp['mean_pressure_Pa']))
for r in rows['contact_results.csv']:
 phi=float(r['contact_fraction_1D']); tau=float(r['tau_max_kPa_for_mu0p1_other0p02'])*1000
 assert near(tau*phi/pbar,.08)
 assert float(r['relative_load_error'])<1e-10 and float(r['kkt_error_um'])<1e-7
ck('load_gap_and_shear_budget',True)
for r in rows['material_cost.csv']:
 A=inp['grains_at_2000m2']*float(r['area_m2'])/2000*6*(190e-6)**2
 mass=A*(float(r['substrate_d_um'])+float(r['skin_t_um']))*1e-6*950
 assert near(A,float(r['coated_pad_area_m2'])) and near(mass,float(r['finished_added_mass_kg']))
 assert near(mass*500/.8,float(r['raw_only_JPY_excl_tax']))
ck('area_mass_cost_units',True)
for r in rows['coating_throughput.csv']:
 A=inp['grains_at_2000m2']*float(r['area_m2'])/2000*6*(190e-6)**2
 hrs=A/(float(r['width_m'])*float(r['speed_m_min'])*60*.7*.8)
 assert near(hrs,float(r['operating_clock_hours']))
ck('throughput_units',True)
for r in rows['frequency_requirements.csv']:assert near(float(r['speed_m_s'])/(float(r['wavelength_um'])*1e-6),float(r['passage_frequency_Hz']))
ck('frequency_units',True)
ck('eight_specs_not_run',len(j('test_plan.json')['tests'])==8 and all(t['status']=='not_run' for t in j('test_plan.json')['tests']))
ck('decision_unproven',j('decision.json')['success_probability'] is None and j('decision.json')['adoption']=='comparison_only_not_validated')
ck('correct_snow_paper_author','Theile' in j('sources.json')['sources'][2]['title'])
t=REPORT.read_text(encoding='utf-8')
ck('report_scope_and_values',all(x in t for x in ['物理試験0件','30数式・数値照合','479比較行','1,280','約93.8','未確認','2.36','有限粒子','1,042万円']))
for png in ['layer_tradeoffs.png','concept.png']:ck('PNG_'+png,(D/png).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
indices=['README.md','回覧板.md','GPT往復/README.md','調査台帳/一般.md','調査台帳/計算部品索引.md']
G=shutil.which('git') or str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe')
hashes={}; changes=j('index_changes.json')['changes']
for name in indices:
 old=norm(subprocess.run([G,'show',BASE+':'+name],cwd=R,capture_output=True,check=True).stdout.decode('utf-8'))
 new=norm((R/name).read_text(encoding='utf-8'))
 for p in reversed(changes):
  if p['path']==name:
   assert new.count(p['new'])==1
   new=new.replace(p['new'],p['old'],1)
 ck('history_'+name,new==old);hashes[name]=hashlib.sha256(old.encode()).hexdigest()
ledger=norm((R/'調査台帳/物性値照合_自律ループv2v3.md').read_text(encoding='utf-8'))
ck('claude_unchanged',hashlib.sha256(ledger.encode()).hexdigest()==j('sources.json')['claude']['sha256_lf']=='054c9388de3be3bd251c395059a9e02c9d3b336885236683ba3f528ff819d71f')
links=0
for file in [REPORT]+list(D.glob('*.md'))+[R/n for n in indices]:
 for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',file.read_text(encoding='utf-8')):
  if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target) or target.startswith('#'):continue
  target=unquote(target.split('#')[0].split('?')[0]);assert (file.parent/target).exists(),str(file)+' -> '+target
  links+=1
ck('relative_links',links>400)
out=dict(cycle=79,document_checks=len(checks),links_checked=links,checks=checks,baseline_index_sha256_lf_normalized=hashes,physical_trials=0,success_probability=None,visual_review='Both original generated PNGs inspected. No third-party source figures/PDFs republished.')
(D/'document_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(document_checks=len(checks),links=links,all_passed=True)))
