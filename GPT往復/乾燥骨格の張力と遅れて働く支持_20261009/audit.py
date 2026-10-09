"""Audit cycle 69 artifacts; numerical checks are not physical trials."""
from pathlib import Path
import csv,json,re,urllib.parse
D=Path(__file__).resolve().parent
R=D.parents[1]
name='GPT回答_多方向探索第69巡_結晶化と成形張力を分ける乾燥粒の支持設計_20261009.md'
report=R/'GPT往復'/name
j=lambda p:json.loads(p.read_text(encoding='utf-8'))
r=j(D/'results.json');c=j(D/'checks.json');p=j(D/'test_plan.json')
a=[]
def ck(n,v):
    a.append({'name':n,'passed':bool(v)})
    assert v,n
ck('all 21 mathematical checks',c['count']==21 and all(x['passed'] for x in c['checks']))
ck('no physical trials',r['physical_tests']==p['physical_tests']==0)
ck('success probability remains undefined',r['success_probability'] is None and p['success_probability'] is None)
ck('eight packages unexecuted',len(p['packages'])==8 and all(x['status']=='NOT_EXECUTED' and x['result'] is None and x['sample_count'] is None for x in p['packages']))
ck('source moduli not represented as 50C data',r['source_moduli_not_50C_data'] is True)
ck('inverse curve not represented as measured',r['inverse_spec']['is_measured_response'] is False)
ck('source thermal normalization unresolved',r['source_thermal_ratio_audit']['same_normalization_confirmed'] is False)
row_counts={}
for stem,n in r['rows'].items():
    with (D/(stem+'.csv')).open(encoding='utf-8',newline='') as f: row_counts[stem]=len(list(csv.DictReader(f)))
    ck('rows '+stem,row_counts[stem]==n)
ck('353 calculated rows',sum(row_counts.values())==353)
text=report.read_text(encoding='utf-8')
ck('report states zero physical trials and undefined probability','物理試験は0件' in text and '成功確率は未算定' in text)
ck('retained operation and depth constraints',all(s in text for s in ['450mm','300mm','60分','R39']))
ck('four branches and warm spray route retained',all(s in text for s in ['H69-C','H69-F','H69-P','H69-M','H68-A']))
ck('one structural diagram',(D/'design.md').read_text(encoding='utf-8').count(chr(96)*3+'mermaid')==1)
ck('two plotted figures',all((D/n).read_bytes().startswith(bytes.fromhex('89504e470d0a1a0a')) for n in ['figure1_support.png','figure2_material_and_area.png']))
ck('no NaN or Infinity output',all(s not in (D/'results.json').read_text(encoding='utf-8') for s in ['NaN','Infinity']))
paths=[report]+list(D.glob('*.md'))+[R/x for x in ['README.md','回覧板.md','GPT往復/README.md','調査台帳/一般.md','調査台帳/計算部品索引.md']]
links=[];missing=[]
for path in paths:
    txt=path.read_text(encoding='utf-8')
    ck('LF encoding '+str(path.relative_to(R)),b'\r' not in path.read_bytes())
    for match in re.finditer(r'!?\[[^\]\n]*\]\(([^)\n]+)\)',txt):
        u=match.group(1).strip().strip('<>')
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',u) or u.startswith('#'):continue
        target=(path.parent/urllib.parse.unquote(u.split('#')[0])).resolve()
        if not target.is_relative_to(R.resolve()):continue
        exists=target.exists() or target==D/'document_audit.json'
        links.append({'from':str(path.relative_to(R)).replace('\\','/'),'to':str(target.relative_to(R)).replace('\\','/'),'exists':exists})
        if not exists:missing.append(links[-1])
ck('all referenced local documents exist',not missing)
out={'cycle':69,'physical_tests':0,'success_probability':None,'checks':a,'check_count':len(a),'data_rows':row_counts,'local_links_checked':len(links),'missing_links':missing,'all_passed':all(x['passed'] for x in a)}
(D/'document_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'document_checks':len(a),'links':len(links),'rows':sum(row_counts.values()),'passed':out['all_passed']},ensure_ascii=False))
