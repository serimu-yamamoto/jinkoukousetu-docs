"""Document and evidence-state audit for cycle 71."""
from pathlib import Path
import csv,json,re,urllib.parse
D=Path(__file__).resolve().parent;R=D.parents[1]
report=R/'GPT往復'/'GPT回答_多方向探索第71巡_跳ねる接点の限界と圧力を均す滑走面_20261009.md'
j=lambda p:json.loads(p.read_text(encoding='utf-8'))
r=j(D/'results.json');c=j(D/'checks.json');p=j(D/'test_plan.json');a=[]
def ck(n,v):
 a.append({'name':n,'passed':bool(v)});assert v,n
ck('33 math checks',c['count']==33 and all(x['passed'] for x in c['checks']))
ck('physical tests remain zero',r['physical_tests']==p['physical_tests']==0)
ck('success probability not inferred',r['success_probability'] is None and p['success_probability'] is None)
ck('eight specifications not executed',len(p['packages'])==8 and all(x['status']=='NOT_EXECUTED' and x['result'] is None and x['sample_count'] is None for x in p['packages']))
ck('no material selected',r['material_selected'] is False)
ck('not source simulation reproduction',r['coordinate_identity']['source_dynamics_reproduced'] is False and r['coordinate_identity']['author_code_checked'] is False)
counts={}
for stem,n in r['rows'].items():
 with (D/(stem+'.csv')).open(encoding='utf-8',newline='') as f:counts[stem]=len(list(csv.DictReader(f)))
 ck('rows '+stem,counts[stem]==n)
ck('179 rows',sum(counts.values())==179)
t=report.read_text(encoding='utf-8')
ck('physical and probabilistic limitations explicit','物理試験0件' in t and '成功確率未算定' in t)
ck('constraints retained',all(s in t for s in ['450mm','300mm','60分','R39','50℃']))
ck('multiple routes retained',all(s in t for s in ['H71-P','H71-D','H71-M','H68-A']))
ck('one structure diagram',(D/'design.md').read_text(encoding='utf-8').count('~~~mermaid')==1)
ck('two PNG figures',all((D/x).read_bytes().startswith(bytes.fromhex('89504e470d0a1a0a')) for x in ['figure1_pressure.png','figure2_vibration.png']))
ck('finite JSON',all(x not in (D/'results.json').read_text(encoding='utf-8') for x in ['NaN','Infinity']))
paths=[report]+list(D.glob('*.md'))+[R/x for x in ['README.md','回覧板.md','GPT往復/README.md','調査台帳/一般.md','調査台帳/計算部品索引.md']]
links=[];missing=[]
for path in paths:
 text=path.read_text(encoding='utf-8');ck('LF '+str(path.relative_to(R)),b'\r' not in path.read_bytes())
 for mat in re.finditer(r'!?\[[^\]\n]*\]\(([^)\n]+)\)',text):
  u=mat.group(1).strip().strip('<>')
  if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',u) or u.startswith('#'):continue
  target=(path.parent/urllib.parse.unquote(u.split('#')[0])).resolve()
  if not target.is_relative_to(R.resolve()):continue
  exists=target.exists() or target==D/'document_audit.json'
  links.append({'from':str(path.relative_to(R)).replace('\\','/'),'to':str(target.relative_to(R)).replace('\\','/'),'exists':exists})
  if not exists:missing.append(links[-1])
ck('all local links resolve',not missing)
out={'cycle':71,'physical_tests':0,'success_probability':None,'check_count':len(a),'checks':a,'local_links_checked':len(links),'missing_links':missing,'calculated_rows':counts,'all_passed':all(x['passed'] for x in a)}
(D/'document_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'document_checks':len(a),'links':len(links),'rows':sum(counts.values()),'passed':out['all_passed']},ensure_ascii=False))
