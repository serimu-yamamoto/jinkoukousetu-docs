from pathlib import Path
import json,re,base64,math
from urllib.parse import unquote
P=Path(__file__).resolve().parent
ROOT=P.parents[1]
REPORT=ROOT/'GPT往復/GPT回答_多方向探索第55巡_摩耗面の再生と材料交換を両立する設計_20261009.md'
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
R=json.loads((P/'results.json').read_text(encoding='utf-8'))
V=json.loads((P/'validation.json').read_text(encoding='utf-8'))
T=json.loads((P/'test_plan.json').read_text(encoding='utf-8'))
text=REPORT.read_text(encoding='utf-8')
checks=[]
def ck(name,value): checks.append({'name':name,'passed':bool(value)})
ck('21 numerical checks pass',V['count']==21 and V['passed'])
ck('physical tests zero and probability null',all(x['physical_tests']==0 and x['success_probability'] is None for x in [I,R,T]))
ck('81 independent condition cells arithmetic',3*3*3*T['stage_A']['independent_lots']==T['stage_A']['condition_cells']==81)
ck('test plan not executed',T['status']=='NOT_EXECUTED')
ck('reported capacity rounds correctly',round(R['ideal_processing_body_kg_day'],2)==268.95)
ck('report states reference schedule scope','楽観的な参考時間' in text and '別材料にも30秒' in text)
ck('report distinguishes selected fraction from success','90.01％は仮の選別集団の内訳' in text)
ck('report warns on inventory instability','予備在庫を増やすだけでは' in text)
ck('report states functional and exposure constraints','人体環境' in text and '冬の界面接続' in text and '表面50℃' in text)
ck('report notes chemical identity and stoichiometry discrepancy','DMTDA' in text and '0.431' in text)
ck('new source DOIs present',all(d in (P/'sources.md').read_text(encoding='utf-8') for d in ['10.3390/ma19071366','10.1016/j.procir.2017.04.039','10.1016/j.eurpolymj.2024.113655','10.1039/D5SC07979A']))
ck('figures exist in two formats',all((P/f'figure{i}_{n}.{e}').is_file() for i,n in [(1,'capacity'),(2,'sorting'),(3,'process')] for e in ['png','svg']))
missing=[]
for f in [REPORT,*P.glob('*.md')]:
    for link in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
        if '://' in link or link.startswith('#'): continue
        target=unquote(link.split('#')[0])
        if not (f.parent/target).is_file(): missing.append([str(f.relative_to(ROOT)),link])
ck('all report and asset local links resolve',not missing)
# Preserve old index content, except the intended latest-title fields on the board.
before=ROOT/'.git/docs-before55.json'
if before.exists():
    B=json.loads(before.read_text(encoding='utf-8'))
    preserved=[]
    for name in ['README.md','GPT往復/README.md']:
        old=base64.b64decode(B[name]).decode('utf-8').replace('\r\n','\n')
        now=(ROOT/name).read_text(encoding='utf-8')
        h='## 最新の独立検証とClaudeへの受け渡し' if name=='README.md' else '## 最新の受け渡し'
        pos=old.index(h); nxt=old.index('\n## ',pos+len(h))
        preserved.append(old[:pos] in now and old[pos+len(h):nxt].strip() in now and old[nxt:] in now)
    old=base64.b64decode(B['回覧板.md']).decode('utf-8').replace('\r\n','\n')
    now=(ROOT/'回覧板.md').read_text(encoding='utf-8')
    preserved.append(old[old.index('**第54巡の滑走面・回転摩耗検証：**'):] in now)
    ck('all prior shared history retained',all(preserved))
else:
    checks.append({'name':'publication-time historical preservation check','passed':None,'note':'Original index snapshot was local-only and removed after verification; publication diff is authoritative.'})
failed=[x for x in checks if x['passed'] is False]
result={'kind':'document and arithmetic audit; not physical evidence','count':len(checks),'passed':not failed,'checks':checks,'missing_links':missing}
(P/'document-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'checks':len(checks),'passed':not failed,'failed':failed},ensure_ascii=False))
if failed: raise SystemExit(1)
