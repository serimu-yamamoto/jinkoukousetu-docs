from pathlib import Path
import json,re,base64,math
from urllib.parse import unquote
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
REPORT=ROOT/'GPT往復/GPT回答_多方向探索第56巡_接点が縮んで抜ける粒と雪の支えの両立_20261009.md'
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'));R=json.loads((P/'results.json').read_text(encoding='utf-8'));V=json.loads((P/'validation.json').read_text(encoding='utf-8'));T=json.loads((P/'test_plan.json').read_text(encoding='utf-8'));text=REPORT.read_text(encoding='utf-8');checks=[]
def ck(n,b):checks.append(dict(name=n,passed=bool(b)))
ck('22 algebra checks pass',V['count']==22 and V['passed'])
ck('zero physical tests and null probability',all(x['physical_tests']==0 and x['success_probability'] is None for x in [I,R,T]))
ck('test plan not executed',T['status']=='NOT_EXECUTED')
ck('54 condition cells arithmetic',3*2*3*T['stage_B']['independent_lots']==T['stage_B']['condition_cells']==54)
ck('record counts match report',len(R['fold'])==5 and len(R['hinges'])==45 and len(R['ring'])==24 and len(R['clearance'])==20 and len(R['tolerance'])==3 and len(R['cost'])==12)
ck('retreat rounding matches',round(R['selected_fold']['one_side_retreat_um'],2)==19.06)
ck('hinge rounding matches',round(100*R['selected_hinge']['approx_bending_surface_strain'],2)==3.00)
ck('fixed pressure caveat present','一定圧力では平均応答が重なる' in text)
ck('source speed discrepancy retained','速度10mm/sとFig.10説明の1mm/s' in text)
ck('raw data retrieval limitation stated','403' in text and '疲労データ再解析は未実施' in text)
ck('no claimed force law','力の法則を得ていない' in text)
ck('human environment winter and gouge requirements retained',all(x in text for x in ['安全','冬の接続','300mm','450mm','表面50℃']))
ck('3 PNG and SVG figures exist',all((P/f'figure{i}_{n}.{e}').exists() for i,n in [(1,'retreat'),(2,'release'),(3,'tolerance_cost')] for e in ['png','svg']))
missing=[]
for f in [REPORT,*P.glob('*.md')]:
 for link in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
  if '://' in link or link.startswith('#'):continue
  if not (f.parent/unquote(link.split('#')[0])).is_file():missing.append([str(f.relative_to(ROOT)),link])
ck('all report asset links exist',not missing)
before=ROOT/'.git/docs-before56.json'
if before.exists():
 B=json.loads(before.read_text(encoding='utf-8'));ok=[]
 for name in ['README.md','GPT往復/README.md']:
  old=base64.b64decode(B[name]).decode('utf-8').replace('\r\n','\n');now=(ROOT/name).read_text(encoding='utf-8');h='## 最新の独立検証とClaudeへの受け渡し' if name=='README.md' else '## 最新の受け渡し';p=old.index(h);n=old.index('\n## ',p+len(h));ok.append(old[:p] in now and old[p+len(h):n].strip() in now and old[n:] in now)
 old=base64.b64decode(B['回覧板.md']).decode('utf-8').replace('\r\n','\n');now=(ROOT/'回覧板.md').read_text(encoding='utf-8');ok.append(old[old.index('**第55巡の表面再生・処理能力検証：**'):] in now)
 ck('previous shared history retained',all(ok))
else:checks.append(dict(name='publication-time historical preservation',passed=None,note='Local-only prior index snapshot removed after publishing; inspect Git commit diff.'))
failed=[x for x in checks if x['passed'] is False];output=dict(kind='document audit only',count=len(checks),passed=not failed,checks=checks,missing_links=missing)
(P/'document-audit.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(dict(count=len(checks),passed=not failed,failed=failed),ensure_ascii=False))
if failed:raise SystemExit(1)
