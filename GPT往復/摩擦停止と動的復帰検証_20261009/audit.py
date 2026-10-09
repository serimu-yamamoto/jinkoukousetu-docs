from pathlib import Path
import csv,json,re,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent; repo=P.parents[1]
report=P.parent/'GPT回答_多方向探索第61巡_接触中の摩擦停止と離れた後の復帰を分ける設計_20261009.md'
R=json.loads((P/'results.json').read_text(encoding='utf-8')); I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
checks=[]
def ck(name,ok):
    assert ok,name
    checks.append(dict(name=name,passed=True))
ck('physical tests remain zero',I['physical_tests']==R['physical_tests']==0)
ck('probability remains null',I['success_probability'] is None and R['success_probability'] is None)
N=json.loads((P/'numerical_checks.json').read_text(encoding='utf-8'))
ck('29 numeric checks present and passed',N['passed']==29 and len(N['checks'])==29 and all(c['passed'] for c in N['checks']))
expected={'source_table_TPU.csv':2,'friction_events.csv':6,'free_return.csv':7,'mass_sensitivity.csv':3,'friction_ratio_sensitivity.csv':8,'time_history.csv':14007,'frequency_response.csv':486,'damping_volume_cost.csv':6}
for filename,count in expected.items():
    rows=list(csv.DictReader((P/filename).open(encoding='utf-8')))
    ck(filename+' row count',len(rows)==count)
ck('all CSV rows accounted',sum(expected.values())==14525)
ck('nominal Coulomb event holds both before/after relaxation',all(x['static_hold_at_stop'] and x['static_hold_after_relax'] for x in R['first_friction_event']))
ck('friction ratio 0.8 counterexample > 6um',R['friction_ratio_sensitivity'][2]['x_first_stop_um']>6)
ck('elastic free case does not falsely settle',R['free_return'][0]['settle_energy_and_position_us'] is None)
ck('mass sensitivity keeps actual tau fixed',max(x['tau_us'] for x in R['mass_sensitivity'])-min(x['tau_us'] for x in R['mass_sensitivity'])<1e-10)
ck('larger branch is not declared faster',R['free_return'][3]['settle_energy_and_position_us']>R['free_return'][2]['settle_energy_and_position_us'])
ck('small pad requires large strain',R['small_pad']['required_shear_strain_at_deltaG_1MPa']>1)
ck('smallest-cost row is labelled lower bound',all(x['lower_bound'] for x in R['cost_lower_bounds']))
ck('source data only 40/60 C observations',set(x['temperature_C'] for x in R['source_table_means'])=={40,60})
S=json.loads((P/'source_provenance.json').read_text(encoding='utf-8'))
ck('three source hashes recorded',len(S['sources'])==3 and all(re.fullmatch('[0-9a-f]{64}',s['sha256']) for s in S['sources']))
ck('source full copies excluded',S['full_copyrighted_sources_in_archive'] is False)
# Check local Markdown links exactly, including new report and old-report addendum.
files=[report,*P.glob('*.md'),repo/'README.md',repo/'回覧板.md',P.parent/'README.md',P.parent/'GPT回答_多方向探索第60巡_戻る順序の反証と留め具を増やさない連成復帰_20261009.md']
link_total=0
for p in files:
    for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if re.match(r'^[a-z]+:',link) or link.startswith('#'):continue
        target=link.split('#')[0]
        if not target:continue
        ck('local link '+str(p.relative_to(repo))+' -> '+target,(p.parent/target).exists());link_total+=1
for name in ['01_concept','02_dynamics','03_volume_cost']:
    ET.parse(P/(name+'.svg')); ck(name+' valid SVG',True)
    b=(P/(name+'.png')).read_bytes(); ck(name+' PNG signature',b[:8]==b'\x89PNG\r\n\x1a\n')
text=report.read_text(encoding='utf-8')
for phrase in ['29.8038','0.441964','92.449','106.694','物理試験は0件','成功確率は未算定','独立した試験条件','業者見積りではない']:
    ck('report constraint/value '+phrase,phrase in text)
for p in [repo/'README.md',repo/'回覧板.md',P.parent/'README.md']:
    t=p.read_text(encoding='utf-8'); ck('latest pointer '+str(p.relative_to(repo)),t.index('第61巡')<t.index('第60巡'))
# This file checks content integrity; individual link checks are not research experiments.
out=dict(passed=len(checks),local_links=link_total,checks=checks,physical_tests=0,visual_qa='3 PNGs inspected in conversation; concept wording revised and regenerated')
(P/'document_checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:out[k] for k in ['passed','local_links','physical_tests']}))
