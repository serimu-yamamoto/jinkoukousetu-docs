"""Reproduce numeric transcription/doc checks from the repository root.
Original XML and base-document text are read from public sources if local caches are absent.
The visual checks recorded below were performed by Codex at publication; they are not automated here.
"""
from pathlib import Path
import csv,json,re,hashlib,xml.etree.ElementTree as ET
from urllib.request import urlopen
from urllib.parse import quote
root=Path(__file__).resolve().parents[2]
folder=root/'GPT往復/結晶配置と寿命検証_20261009'
report=root/'GPT往復/GPT回答_多方向探索第51巡_結晶の配置と寿命から滑走素材を再設計_20261009.md'
text=report.read_text(encoding='utf-8')
checks=[]
def check(name,ok):
    if not ok:raise AssertionError(name)
    checks.append(name)
results=json.loads((folder/'results.json').read_text(encoding='utf-8'))
check('28 numerical checks completed',results['checks_passed']==28)
check('No physical probability assigned',results['physical_tests']==0 and results['physical_success_probability'] is None)
for name in ['model.py','draw.py']:
    code=(folder/name).read_text(encoding='utf-8').rstrip()
    check('Exact self-contained appendix '+name,'```python\n'+code+'\n```' in text)
# Independently read source XML table rather than test the manually typed table against itself.
cache=root/'.research51/erucamide2024.xml'
xml=ET.fromstring(cache.read_bytes() if cache.exists() else urlopen('https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10883039/fullTextXML',timeout=30).read())
table=next(x for x in xml.iter('table-wrap') if x.attrib.get('id')=='tbl2')
data=[]
for tr in table.iter('tr'):
    cells=[''.join(td.itertext()).strip() for td in tr.findall('td')]
    if cells:data.append(cells)
check('Original Table 2 has two groups',len(data)==2)
with (folder/'source_table.csv').open(encoding='utf-8') as f: source=list(csv.DictReader(f))
mapping=[9,5,6,1,2,8]
for row,col in zip(source,mapping):
    nums=[]
    for group in data:
        nums.append([float(s) for s in re.findall(r'\d+(?:\.\d+)?',group[col])])
    check('Original XML values '+row['property'],nums[0]==[float(row['PP_mean']),float(row['PP_SD'])] and nums[1]==[float(row['PP_ER_1p5wtpct_mean']),float(row['PP_ER_SD'])])
base='e214635f5766f214a148964b60ee7ac30bcca5b0'
cache_before=root/'.git/docs-before51.json'
before=json.loads(cache_before.read_text(encoding='utf-8')) if cache_before.exists() else {p:urlopen('https://raw.githubusercontent.com/serimu-yamamoto/jinkoukousetu-docs/'+base+'/'+quote(p),timeout=30).read().decode('utf-8') for p in ['README.md','GPT往復/README.md','回覧板.md']}
for p,old in before.items():
    new=(root/p).read_text(encoding='utf-8')
    old=old.replace('\r\n','\n')
    # Only board's date line and current report pointer may be replaced.
    preserved=[l for l in old.splitlines() if l and not(p=='回覧板.md' and (l.startswith('**最終更新：') or l.startswith('**今回の最新報告：')))]
    check('Previous history retained '+p,all(l in new for l in preserved))
    check('Latest pointer '+p,'多方向探索第51巡' in new)
for target in re.findall(r'\]\(([^)]+)\)',re.sub(r'```.*?```','',text,flags=re.S)):
    if not target.startswith(('http:','https:','#')):
        check('Relative report link '+target,(report.parent/target).is_file())
check('Six source scopes recorded',len(json.loads((folder/'source_audit.json').read_text(encoding='utf-8'))['sources'])==6)
check('Mixture assumptions explicit',all(s in text for s in ['φと、このaは別物','µ=0.05、部分被覆はµ=0.10','単一Fick','追加被覆','軟化置換']))
proof={'cycle':51,'numerical_checks':28,'document_checks':len(checks),'checks':checks,
 'manual_visual_checks_at_original_publication':['Original S1 PDF page 6 table and figure','Original S4 PDF pages 7 and 8','All three generated PNG figures'],
 'physical_tests':0,'physical_success_probability':None}
(folder/'verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'document_checks':len(checks),'numerical_checks':28},ensure_ascii=False))
