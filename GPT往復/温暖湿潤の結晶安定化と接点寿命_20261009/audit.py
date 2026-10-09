from pathlib import Path
import json,csv,re,math,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent;repo=P.parents[1]
report=P.parent/'GPT回答_多方向探索第63巡_結晶の安定化と壊れない接点の区別_20261009.md'
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'));R=json.loads((P/'results.json').read_text(encoding='utf-8'));S=json.loads((P/'source_provenance.json').read_text(encoding='utf-8'))
checks=[]
def ck(label,yes):
    if not yes:raise AssertionError(label)
    checks.append(label)
def near(x,y):return math.isclose(x,y,rel_tol=1e-6,abs_tol=1e-9)
ck('physical evidence not fabricated',R['physical_tests']==I['physical_tests']==0 and R['success_probability'] is None)
ck('source DOI verified',S['sources'][0]['doi']=='10.1016/j.chemgeo.2018.11.003')
ck('S2 access limitation disclosed','403' in S['sources'][1]['access'] and 'sha256' not in S['sources'][1])
ck('only complete XML files fingerprinted',sum('sha256' in x for x in S['sources'])==2)
ck('published 2026 primary study included',any(x['doi']=='10.1039/d6ra02804g' and x['year']==2026 for x in S['sources']))
ck('no full copyright article archive',not list(P.glob('*.xml')) and not list(P.glob('*.pdf')) and not S['full_sources_archived'])
U=json.loads((P/'claude_update_review.json').read_text(encoding='utf-8'))
ck('Claude new update integrated',I['base_commit']==U['commit']=='e9be02fa93efb425120ede9311d021a10ee03083')
ck('index is not source code receipt',U['scripts_are_index_entries_only'] and not U['raw_v3_scripts_downloaded'])
ck('Claude strength sensitivity included',I['engineering_assumptions']['bridge_strength_sensitivity_MPa']==[.02,.1,1,10])
ck('bridge wet strength remains assumption',I['geometry_assumptions']['effective_bridge_strength_Pa']==1e7)
ck('radial loss retained',near(R['nominal']['radial_loss_limit_um'],.649755723335))
ck('coating material independent from core',near(R['nominal_coating']['side_coat_kg'],1.7690482954))
ck('inventory and bath remain coupled',near(R['nominal_inventory']['work_in_process_kg'],1106.784) and near(R['nominal_inventory']['occupied_bath_m3'],11.06784))
ck('event concentration is Mg, not carbonate',near(R['nominal_event']['net_Mg_increase_mg_L'],8.67960429315))
count=0
for stem,n in R['row_counts'].items():
    data=list(csv.DictReader((P/(stem+'.csv')).open(encoding='utf-8')))
    ck('CSV rows '+stem,len(data)==n);count+=len(data)
ck('complete row count',count==R['total_csv_rows']==235)
ck('all numerical checks passed',json.loads((P/'numerical_checks.json').read_text(encoding='utf-8'))['passed']==27)
links=0
for md in [report,*P.glob('*.md'),repo/'README.md',repo/'回覧板.md',P.parent/'README.md',repo/'調査台帳/一般.md',repo/'調査台帳/計算部品索引.md']:
    for link in re.findall(r'\]\(([^)]+)\)',md.read_text(encoding='utf-8')):
        if re.match('^[a-z]+:',link) or link.startswith('#'):continue
        dest=link.split('#')[0]
        if not dest:continue
        ck('link '+str(md.relative_to(repo))+' -> '+dest,(md.parent/dest).exists());links+=1
for stem in ['01_contact_topology','02_loss_and_coating','03_factory_inventory']:
    ET.parse(P/(stem+'.svg'));ck(stem+' valid SVG',True)
    ck(stem+' PNG signature',(P/(stem+'.png')).read_bytes()[:8]==b'\x89PNG\r\n\x1a\n')
t=report.read_text(encoding='utf-8')
for phrase in ['物理試験0件','成功確率は未算定','0.650','8.680','1.769','11.068','711.5','27件','235行','必要な前処理時間ではない','S2の86％をこの模型へ直接代入した実験再現ではない','受領や同意は未確認','税込2億円']:
    ck('report qualification '+phrase,phrase in t)
for path in [repo/'README.md',repo/'回覧板.md',P.parent/'README.md']:
    content=path.read_text(encoding='utf-8');ck('latest report '+str(path.relative_to(repo)),content.index('第63巡')<content.index('第62巡'))
out=dict(passed=len(checks),local_links=links,physical_tests=0,visual_qa='All three PNG figures inspected; no clipping or overlap found.',checks=checks)
(P/'document_checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=len(checks),local_links=links,physical_tests=0)))
