from pathlib import Path
import json,csv,re,base64
P=Path(__file__).resolve().parent;root=P.parents[1];R=json.loads((P/'results.json').read_text(encoding='utf-8'))
report=root/'GPT往復/GPT回答_多方向探索第60巡_戻る順序の反証と留め具を増やさない連成復帰_20261009.md'
prev=root/'GPT往復/GPT回答_多方向探索第59巡_濡れた静摩擦を越える開離復帰と材料分担_20261009.md'
t=report.read_text(encoding='utf-8');checks=[]
def ck(n,ok):
 if not ok:raise SystemExit('FAILED: '+n)
 checks.append(n)
ck('physical evidence not invented','物理試験0件' in t and R['physical_tests']==0 and R['success_probability'] is None)
ck('30 model checks',json.loads((P/'validation.json').read_text(encoding='utf-8'))['count']==30 and '30件' in t)
ck('contact reaction corrected','N = W + Fa − Fo' in t)
ck('ordering counterexample shown',R['baseline_events']['first_slip_before_opening'] and '先に面を滑らせる' in t)
for k in ['first_slip_pressure_kPa','opening_pressure_kPa','rupture_pressure_kPa']:ck('event value '+k,f"{R['baseline_events'][k]:.3f}" in t)
ck('first jump not counted as all friction','未解決のエネルギー' in t and R['first_jump_energy']['unresolved_transient_energy_nJ']>0)
ck('quasi-static not time trace','時間波形ではなく' in t)
ck('whole cycle not claimed','全サイクル' in t and '未計算' in t)
ck('cross axis bound reported',f"{R['cross_axis']['kappa_limit_for_1um_at_1kPa_after_break']:.5f}" in t)
ck('cross axis scope is final state only','破断後の最終平衡だけ' in t)
ck('no assembled CAD claim','完成CADや製造図面を作成したとはしていない' in t)
ck('latch is not free','抜去摩擦' in t and '留め具仮体積' in t)
ck('3kPa counterexample persists',R['end_3kPa']['bridge_intact'] and R['end_3kPa']['tangential_offset_um']<1)
ck('all user operating gates retained',all(s in t for s in ['450mm','30°','60分','冬','人体','2億円','噴霧結晶化']))
ck('safety and full scope not replaced with local return','全厚450mm、30°保持、雨後60分復旧、冬接続、安全、採算を省略' in t)
ck('Claude receipt not invented','受領・返答・同意' in t and '確認したとはしていない' in t)
ck('test plan still unexecuted',json.loads((P/'test_plan.json').read_text(encoding='utf-8'))['status']=='planned_not_executed')
for f in [report,P/'README.md',P/'sources.md',P/'model.md']:
 for target in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
  if target.startswith(('http://','https://','#')):continue
  ck('local link '+f.name+' '+target,(f.parent/target.split('#')[0]).exists())
ck('all six figure assets exist',all((P/(stem+'.'+ext)).stat().st_size>5000 for stem in ['figure1_contact_order','figure2_coupled_path','figure3_partial_cost'] for ext in ['png','svg']))
ck('prior report correction link exists','第60巡追記' in prev.read_text(encoding='utf-8') and report.name in prev.read_text(encoding='utf-8'))
for p in ['README.md','回覧板.md','GPT往復/README.md']:
 s=(root/p).read_text(encoding='utf-8');ck('latest pointer '+p,s.find('多方向探索第60巡')<s.find('多方向探索第59巡'))
before=root/'.git/before60.json'
if before.exists():
 b=json.loads(before.read_text(encoding='utf-8'))
 for p,v in b['indexes'].items():
  old=base64.b64decode(v).decode('utf-8').replace('\r\n','\n');now=(root/p).read_text(encoding='utf-8')
  paras=[x for x in old.split('\n\n') if x and not x.startswith(('## 最新','**最終更新：','**今回の最新報告：'))]
  ck('old index paragraphs preserved '+p,all(x in now for x in paras))
 old=b['previous_report'].replace('\r\n','\n');now=prev.read_text(encoding='utf-8');now=re.sub(r'> 2026-10-09 第60巡追記：[^\n]+\n\n','',now)
 ck('prior59 text unchanged except explicit addendum',old==now)
rows=sum(sum(1 for _ in csv.DictReader(f.open(encoding='utf-8'))) for f in P.glob('*.csv'))
ck('626 CSV rows accounted',rows==626)
(P/'document-audit.json').write_text(json.dumps({'kind':'document consistency, not physical tests','checks':checks,'count':len(checks),'csv_rows':rows,'passed':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(f'{len(checks)} document checks passed; {rows} CSV rows; physical tests 0')
