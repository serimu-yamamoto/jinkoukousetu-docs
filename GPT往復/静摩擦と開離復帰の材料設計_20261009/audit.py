from pathlib import Path
import json,csv,re,hashlib,base64,math
P=Path(__file__).resolve().parent;root=P.parents[1]
R=json.loads((P/'results.json').read_text(encoding='utf-8'));I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
report=root/'GPT往復/GPT回答_多方向探索第59巡_濡れた静摩擦を越える開離復帰と材料分担_20261009.md'
txt=report.read_text(encoding='utf-8');checks=[]
def ck(n,ok):
 if not ok:raise SystemExit('FAILED: '+n)
 checks.append(n)
ck('physical trials not claimed',R['physical_tests']==0 and R['success_probability'] is None and '物理試験は0件' in txt)
ck('25 algebra checks',json.loads((P/'validation.json').read_text(encoding='utf-8'))['count']==25 and '25件' in txt)
ck('source table rows',sum(1 for _ in csv.DictReader((P/'published_static_water.csv').open(encoding='utf-8')))==13)
ck('steel counterexample not assigned to grain',all(r['transfer_to_our_material_valid']=='False' for r in csv.DictReader((P/'published_counterexamples.csv').open(encoding='utf-8'))))
ck('apparent wet coefficient not double counted as calibrated law','二重計上' in txt)
ck('static and kinetic coefficients separated','μ_s' in txt and 'μ_k' in txt)
ck('reported material thresholds match',['78.6','149.8','176.9']==[f"{R['cam'][s]['E_required_MPa']:.1f}" for s in ['at_mu_06','at_published_max','at_mu_08']])
ck('reported new threshold',f"{R['opening']['E_required_for_baseline_MPa']:.2f}" in txt)
ck('opening conditional not CAD approval','立体設計は未完成' in txt and '必要条件' in txt)
ck('3kPa energy counterexample retained',R['opening']['energy_only_counterexample']['energy_only_condition'] and not R['opening']['energy_only_counterexample']['necessary_force_condition'])
ck('45cm entire depth checked','表層だけの成功で450mm床を承認しない' in txt and '400.8' in txt)
ck('incremental cost not total course','支持芯、外面片、枠、接合' in txt and '2億円' in txt)
ck('raw cost scale',round(R['cost']['additional_mass_1120_kg']*3000/10000)==1912)
ck('material dimension not asserted measurement','実際の膨張の測定ではない' in txt)
ck('physical snow/safety/winter gates exist',all(s in txt for s in ['人体','摩耗粉','冬','自然地盤','60分']))
ck('Claude acknowledgment not claimed','受領・返答・同意は未確認' in txt)
ck('figures all present',all((P/(stem+'.'+ext)).stat().st_size>5000 for stem in ['figure1_material_bounds','figure2_opening_force_energy','figure3_concept_cost'] for ext in ['png','svg']))
for f in [report,P/'README.md',P/'sources.md',P/'model.md']:
 for target in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
  if target.startswith(('https://','http://','#')):continue
  ck('local link '+f.name+' -> '+target,(f.parent/target.split('#')[0]).exists())
for path in ['README.md','回覧板.md','GPT往復/README.md']:
 t=(root/path).read_text(encoding='utf-8')
 ck('index leads to 59 '+path,t.find('多方向探索第59巡')<t.find('多方向探索第58巡'))
 ck('index preserves 58 '+path,'多方向探索第58巡' in t)
# If publication snapshot exists, ensure all older index paragraphs survived except declared board pointers.
before=root/'.git/before59.json'
if before.exists():
 old=json.loads(before.read_text(encoding='utf-8'))
 for path,v in old.items():
  prev=base64.b64decode(v).decode('utf-8').replace('\r\n','\n');new=(root/path).read_text(encoding='utf-8')
  paragraphs=prev.split('\n\n')
  preserved=[p for p in paragraphs if p and not p.startswith(('## 最新','**最終更新：','**今回の最新報告：'))]
  ck('older paragraphs preserved '+path,all(p in new for p in preserved))
ck('no source PDF republished',not list(P.glob('*.pdf')))
ck('no invented measured lab execution',json.loads((P/'test_plan.json').read_text(encoding='utf-8'))['status']=='planned_not_executed')
(P/'document-audit.json').write_text(json.dumps({'kind':'document consistency checks, not physical validation','checks':checks,'count':len(checks),'passed':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(f'{len(checks)} document consistency checks passed; physical experiments = 0')
