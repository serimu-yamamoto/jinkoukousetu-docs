"""Audit cycle 75 arithmetic, artifact status, references, and exact history preservation."""
from pathlib import Path
import json,csv,math,re,subprocess,hashlib,shutil,urllib.request
from urllib.parse import unquote,quote
D=Path(__file__).resolve().parent;R=D.parents[1]
BASE='f2f920434683c60d55a035d3c0f12b92d070cc09'
REPORT=R/'GPT往復/GPT回答_多方向探索第75巡_雪の通気構造との比較と濡れ固着を減らす薄片粒_20261009.md'
def norm(s):return s.replace('\r\n','\n').rstrip()+'\n'
def j(n):return json.loads((D/n).read_text(encoding='utf-8'))
checks=[]
def ck(n,b):
    assert b,n
    checks.append({'name':n,'passed':True})
def near(a,b):return math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-15)
result=j('results.json');mathchecks=j('checks.json');numerics=j('distributed_audit.json')
ck('physical_experiments_zero',result['physical_experiments']==0)
ck('probability_not_fabricated',result['success_probability'] is None)
ck('30_math_checks',mathchecks['total']==30==mathchecks['passed'] and all(x['passed'] for x in mathchecks['checks']))
ck('7_distributed_checks',numerics['total_checks']==7 and all(x['passed'] for x in numerics['checks']) and len(numerics['rows'])==6)
rows={}
for fn,count in result['row_counts'].items():
    with (D/fn).open(encoding='utf-8') as f:rows[fn]=list(csv.DictReader(f))
    ck('rows_'+fn,len(rows[fn])==count)
ck('231_rows_including_6_source_rows',sum(map(len,rows.values()))==231 and len(rows['snow_source_subset.csv'])==6)
a=result['reference_plate'];gamma=.072;E=1e9;t=10e-6;L=100e-6;s=40e-6
lam=6*gamma*L**4/(E*t**3*s**2)
ck('independent_plate_lambda',near(a['Lambda'],lam))
ck('quadratic_equilibrium',near(a['gap_closure_fraction']*(1-a['gap_closure_fraction']),lam))
ck('independent_critical_span',near(a['critical_span_um'],(E*t**3*s**2/(24*gamma))**.25*1e6))
ck('independent_root_stiffness',near(result['root_reference_k_N_m'],E*100e-6*(20e-6)**3/(4*(500e-6)**3)))
ck('independent_overlap_threshold',near(result['interparticle_full_overlap']['overlap_area_limit_m2'],1.6*s**2/(16*gamma)))
ck('tolerance_counterexample',near(result['tolerance_short_worst_Lambda'],.05859375) and near(result['tolerance_long_worst_Lambda'],.9375))
c=[r for r in rows['channel_geometries.csv'] if r['geometry']=='parallel_slit' and float(r['dimension_um'])==40 and float(r['resistance_factor'])==1][0]
ck('independent_path_resistance',near(float(c['resistance_factor_needed_for_target']),.8*s*s/12/3e-12))
ck('independent_capillary_height',near(float(c['complete_wetting_capillary_head_m']),2*gamma/(1000*9.81*s)))
for r in rows['snow_source_subset.csv']:
    assert near(float(r['mean_k_m2']),sum(float(r[k]) for k in ['kx_m2','ky_m2','kz_m2'])/3)
    assert near(float(r['k_over_cycle74_assumption']),float(r['mean_k_m2'])/3e-12)
ck('source_tensor_arithmetic',True)
for r in rows['particle_mobility.csv']:
    area=float(r['area_m2']);gap=float(r['gap_um'])*1e-6
    assert near(float(r['pressure_component_N']),2*gamma*area/gap)
    assert near(float(r['contact_line_scale_N']),2*gamma*math.sqrt(math.pi*area))
    assert near(float(r['particle_weight_N']),3.5e-8*9.81)
ck('free_particle_force_scales',True)
cost=[r for r in rows['rib_cost.csv'] if float(r['pitch_um'])==50 and float(r['rib_height_um'])==40]
mass=330565*40e-6*(2*.2-.2**2)*1200
ck('independent_rib_mass',len(cost)==2 and all(near(float(r['added_mass_kg']),mass) for r in cost))
ck('raw_cost_limits_for_50um_pitch',near(min(float(r['raw_only_JPY_ex_tax']) for r in cost),3570102) and near(max(float(r['raw_only_JPY_ex_tax']) for r in cost),14280408))
ck('tests_not_executed',j('test_plan.json')['status']=='not_executed' and len(j('test_plan.json')['specifications'])==8)
prior=j('inputs.json')['source']
ck('prior_operator_unchanged',hashlib.sha256(norm((R/prior['prior_air_operator']).read_text(encoding='utf-8')).encode()).hexdigest()==prior['prior_code_sha256_lf'])
text=REPORT.read_text(encoding='utf-8')
ck('report_status_and_scope',all(x in text for x in ['物理試験0件','成功確率は未算定','37数式・数値照合','231表行','2億円とは別枠','357〜1,428万円','自由粒','未確認']))
for name in ['figure1_evidence_and_limits.png','figure2_structure_cost.png']:
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
out={'cycle':75,'document_checks':len(checks),'links_checked':links,'checks':checks,
     'baseline_index_sha256_lf_normalized':hashes,'physical_experiments':0,'success_probability':None,
     'visual_review':'Both PNGs visually inspected. Equations/assumptions distinguish numerical confirmation from physical validation.',
     'source1_full_text_republished':False}
(D/'document_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'document_checks':len(checks),'links_checked':links,'all_passed':True}))
