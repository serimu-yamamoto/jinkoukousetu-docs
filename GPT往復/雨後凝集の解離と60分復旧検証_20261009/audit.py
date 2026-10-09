"""Audit cycle 76 arithmetic, artifact status, references, and exact history preservation."""
from pathlib import Path
import json,csv,math,re,subprocess,hashlib,shutil,urllib.request
from urllib.parse import unquote,quote
D=Path(__file__).resolve().parent;R=D.parents[1]
BASE='31aa85c28d705206192a40ac980fc741d6a2f3b0'
REPORT=R/'GPT往復/GPT回答_多方向探索第76巡_濡れた粒を壊さずほぐす条件と60分復旧_20261009.md'
def norm(s):return s.replace('\r\n','\n').rstrip()+'\n'
def j(n):return json.loads((D/n).read_text(encoding='utf-8'))
checks=[]
def ck(n,b):
    assert b,n
    checks.append({'name':n,'passed':True})
def near(a,b):return math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-15)
result=j('results.json');mathchecks=j('checks.json')
ck('physical_experiments_zero',result['physical_experiments']==0)
ck('probability_not_fabricated',result['success_probability'] is None)
ck('29_math_checks',mathchecks['total']==29==mathchecks['passed'] and all(x['passed'] for x in mathchecks['checks']))
rows={}
for fn,count in result['row_counts'].items():
    with (D/fn).open(encoding='utf-8') as f:rows[fn]=list(csv.DictReader(f))
    ck('rows_'+fn,len(rows[fn])==count)
ck('191_comparison_rows',sum(map(len,rows.values()))==191)
b=result['reference_bridge'];Rc=25e-6;v=.001;T=50
tau=1-(T+273.15)/647.096;gam=.2358*tau**1.256*(1-.625*tau)
ck('independent_gamma',near(b['gamma_N_m'],gam))
ck('independent_peak_force',near(b['force_contact_uN']*1e-6,2*math.pi*Rc*gam))
ck('independent_rupture_length',near(b['rupture_distance_um']*1e-6,Rc*(v**(1/3)+.1*v**(2/3))))
ck('independent_reduced_mass',near(3.5e-8*b['pair_relative_speed_energy_m_s']**2/4,b['rupture_work_nJ']*1e-9))
# A separate midpoint quadrature, without importing reproduce.py.
N=200000;smax=Rc*(v**(1/3)+.1*v**(2/3));ds=smax/N;f0=2*math.pi*Rc*gam
work=sum(f0/(1+1.05*((i+.5)*ds/(Rc*math.sqrt(v)))+2.5*((i+.5)*ds/(Rc*math.sqrt(v)))**2)*ds for i in range(N))
ck('independent_midpoint_energy',math.isclose(work,b['rupture_work_nJ']*1e-9,rel_tol=1e-8))
for r in rows['restoration_throughput.csv']:
    V=float(r['area_m2'])*float(r['process_depth_m'])*float(r['damaged_area_fraction'])
    assert near(float(r['volume_m3']),V) and near(float(r['flow_m3_h']),V/2280*3600)
ck('independent_restoration_volume',True)
ck('root_reference_two_moduli',len(result['root_reference'])==2)
for r in result['root_reference']:
    f=b['force_contact_uN']*1e-6
    assert near(r['root_strain_linear'],6*f*.0005/(r['E_Pa_assumed']*.0001*(20e-6)**2))
ck('independent_root_strain',True)
for r in rows['maintenance_loss_cost.csv']:
    M=float(r['area_m2'])*.45*120
    assert near(float(r['replacement_kg_to_maintain_bed_mass']),M*200*float(r['loss_fraction_each_pass']))
ck('independent_material_replacement',True)
ck('loss_100ppm_limit',near(result['annual_loss_fraction_per_pass_limit'],.02/200))
ck('drain_work_force_counterexample',result['draining_comparison'][0]['new_F_uN']<result['draining_comparison'][2]['new_F_uN'] and result['draining_comparison'][0]['new_W_nJ']>result['draining_comparison'][2]['new_W_nJ'])
ck('tests_not_executed',j('test_plan.json')['status']=='not_executed' and len(j('test_plan.json')['specifications'])==8)
text=REPORT.read_text(encoding='utf-8')
ck('report_status_scope',all(x in text for x in ['物理試験0件','成功確率は未算定','29数式照合','191表行','2億円とは別枠','100 ppm','1,080 t','再凝集','未確定']))
for name in ['figure1_force_work.png','figure2_process_cost.png']:
    ck('PNG_'+name,(D/name).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
p=j('index_changes.json')
indices=['README.md','回覧板.md','GPT往復/README.md','調査台帳/一般.md','調査台帳/計算部品索引.md']
G=shutil.which('git') or 'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def baseline(name):
    try:return norm(subprocess.run([G,'show',BASE+':'+name],cwd=R,capture_output=True,check=True).stdout.decode('utf-8'))
    except (OSError,subprocess.CalledProcessError):
        return norm(urllib.request.urlopen('https://raw.githubusercontent.com/serimu-yamamoto/jinkoukousetu-docs/'+BASE+'/'+quote(name,safe='/'),timeout=30).read().decode('utf-8'))
hashes={}
for name in indices:
    new=norm((R/name).read_text(encoding='utf-8'));old=baseline(name)
    hashes[name]=hashlib.sha256(old.encode()).hexdigest()
    if name=='README.md':restored=new.replace(p['readme_insert'],'',1)
    elif name=='GPT往復/README.md':restored=new.replace(p['gpt_insert'],'',1)
    elif name=='回覧板.md':
        restored=new.replace(p['newUpdate'],p['oldUpdate'],1).replace(p['newLatest'],p['oldLatest'],1)
        for key in ['boardEntry','historyRow','handoff']:restored=restored.replace(p[key],'',1)
    elif name=='調査台帳/一般.md':restored=new.removesuffix(p['generalAppend'])
    else:restored=new.removesuffix(p['calcAppend'])
    ck('preserved_history_'+name,restored==old)
ledger=norm((R/'調査台帳/物性値照合_自律ループv2v3.md').read_text(encoding='utf-8'))
ck('claude_ledger_unchanged',hashlib.sha256(ledger.encode()).hexdigest()==j('source_audit.json')['claude_ledger_sha256_lf']=='054c9388de3be3bd251c395059a9e02c9d3b336885236683ba3f528ff819d71f')
links=0
for file in [REPORT]+list(D.glob('*.md'))+[R/n for n in indices]:
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',file.read_text(encoding='utf-8')):
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target) or target.startswith('#'):continue
        target=unquote(target.split('#')[0].split('?')[0])
        assert (file.parent/target).exists(),str(file)+' -> '+target
        links+=1
ck('relative_links_exist',links>400)
out={'cycle':76,'document_checks':len(checks),'links_checked':links,'checks':checks,
     'baseline_index_sha256_lf_normalized':hashes,'physical_experiments':0,'success_probability':None,
     'visual_review':'Both PNGs visually inspected. Equations/assumptions distinguish numerical confirmation from physical validation.',
     'source1_full_text_republished':False}
(D/'document_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'document_checks':len(checks),'links_checked':links,'all_passed':True}))
