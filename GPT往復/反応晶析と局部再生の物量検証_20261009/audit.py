"""Audit cycle 68: conservation evidence, unexecuted status and links."""
from pathlib import Path
import csv,json,re,urllib.parse
D=Path(__file__).resolve().parent
R=D.parents[1]
name='GPT回答_多方向探索第68巡_温暖反応晶析と内部結晶の再生経路_20261009.md'
report=R/'GPT往復'/name
j=lambda p:json.loads(p.read_text(encoding='utf-8'))
r=j(D/'results.json');c=j(D/'checks.json');p=j(D/'test_plan.json')
a=[]
def ck(n,v):
    a.append({'name':n,'passed':bool(v)})
    assert v,n
ck('all 22 conservation checks',c['count']==22 and all(x['passed'] for x in c['checks']))
ck('no physical trials',r['physical_tests']==p['physical_tests']==0)
ck('success not invented',r['success_probability'] is None and p['success_probability'] is None)
ck('12 packages unexecuted',len(p['packages'])==12 and all(x['status']=='NOT_EXECUTED' and x['result'] is None for x in p['packages']))
ck('reported electrochemical maxima not merged',r['electrochemical_audit']['combined_published_maxima_validated'] is False)
ck('chemical cycle not demonstrated',r['energy_separate_conditions']['is_demonstrated_closed_loop'] is False)
row_counts={}
for stem,n in r['output_rows'].items():
    with (D/(stem+'.csv')).open(encoding='utf-8',newline='') as f: row_counts[stem]=len(list(csv.DictReader(f)))
    ck('rows '+stem,row_counts[stem]==n)
ck('78 sensitivity rows',sum(row_counts.values())==78)
text=report.read_text(encoding='utf-8')
ck('report keeps zero trial status','物理試験0件' in text and '未算定' in text)
ck('report keeps 60 minute closure','昼60分' in text)
ck('report keeps 450mm and 300mm','450 mm' in text and '300 mm' in text)
ck('three branches and mechanical comparator',all(s in text for s in ['H68-A','H68-B','H68-C','B-M']))
ck('two conceptual diagrams',(D/'design.md').read_text(encoding='utf-8').count(chr(96)*3+'mermaid')==2)
ck('no printed NaN','NaN' not in (D/'results.json').read_text(encoding='utf-8'))
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
out={'cycle':68,'physical_tests':0,'success_probability':None,'checks':a,'check_count':len(a),'data_rows':row_counts,'local_links_checked':len(links),'missing_links':missing,'all_passed':all(x['passed'] for x in a)}
(D/'document_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'document_checks':len(a),'links':len(links),'rows':sum(row_counts.values()),'passed':out['all_passed']},ensure_ascii=False))
