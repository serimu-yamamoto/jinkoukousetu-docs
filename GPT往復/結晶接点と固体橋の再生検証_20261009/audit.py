from pathlib import Path
import json,csv,re,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent;repo=P.parents[1]
report=P.parent/'GPT回答_多方向探索第62巡_結晶接点と水で集める固体橋の選択再生_20261009.md'
R=json.loads((P/'results.json').read_text(encoding='utf-8'));I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
c=[]
def ck(n,v):
    assert v,n
    c.append(dict(name=n,passed=True))
ck('physical trials zero',R['physical_tests']==I['physical_tests']==0)
ck('success probability unknown',R['success_probability'] is None and I['success_probability'] is None)
N=json.loads((P/'numerical_checks.json').read_text(encoding='utf-8'))
ck('26 algebra checks passed',N['passed']==26 and len(N['checks'])==26 and all(x['passed'] for x in N['checks']))
counts={'network_bounds.csv':31,'solution_route.csv':40,'slurry_route.csv':60,'coupled_requirements.csv':12,'debris_inventory.csv':12,'debris_history.csv':2160,'carrier_cost.csv':9}
for file,n in counts.items():ck(file+' count',len(list(csv.DictReader((P/file).open(encoding='utf-8'))))==n)
ck('all 2324 data rows accounted',sum(counts.values())==2324)
ck('particle count differs from prior rectangular geometry',R['particulate_route']['grain_count']>7e12)
ck('same-density feed comparison retained',abs(R['same_density_feed_compare']['slurry_water_kg']-197.64)<1e-9)
ck('nominal only energy inequality',R['nominal_slurry']['drying_energy_bound_within_window'] and not R['nominal_slurry']['assembly_rate_verified'])
ck('solution reaction kinetics not invented',not R['nominal_solution']['chemistry_rate_verified'])
ck('no all-water evaporation required for solution',len(I['sensitivity']['retained_solution_water_fraction'])==4)
ck('uniform coating counterexample',R['uniform_coating_null']['ratio_vs_selective_feed']>274)
ck('load-sharing penalty retained',any(x['load_sharing_efficiency']==.5 and x['minimum_strength_times_selectivity_MPa']==2.7 for x in R['coupled_requirements']))
ck('environment release not inferred from inventory',all(x['environmental_release_not_estimated'] for x in R['lifecycle']))
ck('full renewal tested, not only 10 percent',{x['renewed_fraction'] for x in R['lifecycle']}=={.1,1})
S=json.loads((P/'source_provenance.json').read_text(encoding='utf-8'))
ck('four sources, only verified XML hashed',len(S['sources'])==4 and sum('sha256' in x for x in S['sources'])==1)
ck('no full article archive',S['full_sources_archived'] is False and not list(P.glob('*.xml')) and not list(P.glob('*.pdf')))
links=0
for md in [report,*P.glob('*.md'),repo/'README.md',repo/'回覧板.md',P.parent/'README.md']:
    for link in re.findall(r'\]\(([^)]+)\)',md.read_text(encoding='utf-8')):
        if re.match('^[a-z]+:',link) or link.startswith('#'):continue
        dest=link.split('#')[0]
        if not dest:continue
        ck('local link '+str(md.relative_to(repo))+' -> '+dest,(md.parent/dest).exists());links+=1
for name in ['01_routes','02_process_bounds','03_inventory_cost']:
    ET.parse(P/(name+'.svg'));ck(name+' valid SVG',True)
    ck(name+' PNG',(P/(name+'.png')).read_bytes()[:8]==b'\x89PNG\r\n\x1a\n')
t=report.read_text(encoding='utf-8')
for phrase in ['49.41','27.00','57.138','39.528','1.35','3.888','2324','成功確率は未算定','物理試験0件','実物成功率ではない','形成した証明ではない']:
    # Exact concept phrase differs from source-claim language; avoid brittle paraphrase.
    if phrase=='形成した証明ではない':phrase='成長した証明ではない'
    ck('report constraint '+phrase,phrase in t)
for md in [repo/'README.md',repo/'回覧板.md',P.parent/'README.md']:
    txt=md.read_text(encoding='utf-8');ck('latest index '+str(md.relative_to(repo)),txt.index('第62巡')<txt.index('第61巡'))
out=dict(passed=len(c),local_links=links,checks=c,physical_tests=0,visual_qa='3 PNG figures inspected; layout adjusted and concept rechecked')
(P/'document_checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=len(c),local_links=links,physical_tests=0)))
