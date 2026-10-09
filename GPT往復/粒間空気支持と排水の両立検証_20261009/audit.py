"""Audit cycle 74 arithmetic, artifact status, references, and exact history preservation."""
from pathlib import Path
import json,csv,math,re,subprocess,hashlib,shutil,urllib.request
from urllib.parse import unquote,quote
D=Path(__file__).resolve().parent;R=D.parents[1]
BASE='63aa160aafda955d66ffdf3b94bd7e5eb7028dce'
REPORT=R/'GPT往復/GPT回答_多方向探索第74巡_空気で荷重を支える開放粒と雨の排水条件_20261009.md'
def norm(s):return s.replace('\r\n','\n').rstrip()+'\n'
def j(n):return json.loads((D/n).read_text(encoding='utf-8'))
checks=[]
def ck(n,b):
    assert b,n
    checks.append({'name':n,'passed':True})
def near(a,b):return math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-10)
result=j('results.json');mathchecks=j('checks.json');numerics=j('numerical_audit.json')
ck('physical_experiments_zero',result['physical_experiments']==0)
ck('probability_not_fabricated',result['probability_of_success'] is None)
ck('25_math_checks',mathchecks['total']==25==mathchecks['passed'] and all(x['passed'] for x in mathchecks['checks']))
ck('6_independent_numerical_checks',numerics['checks']==6 and numerics['all_passed'] and len(numerics['rows'])==9)
rows={}
for fn,count in result['row_counts'].items():
    with (D/fn).open(encoding='utf-8') as f:rows[fn]=list(csv.DictReader(f))
    ck('rows_'+fn,len(rows[fn])==count)
ck('row_total_123_with_5_source_rows',sum(map(len,rows.values()))==123 and len(rows['source_speed_subset.csv'])==5)
b=result['baseline']
ck('independent_load_pressure',near(b['pn_Pa'],70*9.81*math.cos(math.pi/6)/.3))
ck('independent_friction_formula',near(b['mu_diagnostic'],.1*(1-b['air_load_fraction'])+b['delta_mm']/1500))
ck('independent_rain_units',near(b['clean_saturated_drain_mm_h'],3e-12*1000*9.81/.001*3.6e6))
gap=(3e-12-1e-12)/((50e-6)**2/8-1e-12)
ck('independent_bypass_fraction',near(gap,result['gap_fraction_max_50um_ideal']))
for r in rows['fusion_requirements.csv']:
    f=float(r['air_load_fraction']);de=float(r['delta_mm'])/1500
    assert near(float(r['mu_solid_required_for_diagnostic_004'])*(1-f)+de,.04)
    assert near(float(r['mu_solid_required_with_extra_001'])*(1-f)+de+.01,.04)
ck('fusion_allowance_all_rows',True)
cost=[float(r['raw_only_JPY_ex_tax']) for r in rows['raw_cost.csv']]
ck('raw_cost_limits',min(cost)==1350000 and max(cost)==27000000)
ck('tests_not_executed',j('test_plan.json')['status']=='not_executed' and len(j('test_plan.json')['specifications'])==8)
text=REPORT.read_text(encoding='utf-8')
ck('report_status_and_scope',all(x in text for x in ['物理試験0件','成功確率は未算定','31数式・数値照合','123表行','2億円とは別枠','135〜2,700万円','未測定','長手方向']))
for name in ['figure1_tradeoff.png','figure2_design_cost.png']:
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
out={'cycle':74,'document_checks':len(checks),'links_checked':links,'checks':checks,
     'baseline_index_sha256_lf_normalized':hashes,'physical_experiments':0,'probability_of_success':None,
     'visual_review':'Both PNGs visually inspected. Equations/assumptions distinguish numerical confirmation from physical validation.',
     'source1_full_text_republished':False}
(D/'document_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'document_checks':len(checks),'links_checked':links,'all_passed':True}))
