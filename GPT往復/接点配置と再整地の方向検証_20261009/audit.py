"""Integrity checks for H66 deliverables, not evidence of material performance."""
import csv,json,re,math
from pathlib import Path
from urllib.parse import unquote
P=Path(__file__).resolve().parent;root=P.parents[1]
checks=[]
def ck(name,ok):
 checks.append({'name':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'));R=json.loads((P/'results.json').read_text(encoding='utf-8'));N=json.loads((P/'numerical_checks.json').read_text(encoding='utf-8'));S=json.loads((P/'sources.json').read_text(encoding='utf-8'))
ck('no_physical_trials',I['evidence']['physical_tests']==R['evidence']['physical_tests']==N['physical_tests']==0)
ck('probability_unestimated',I['evidence']['success_probability'] is None and R['evidence']['success_probability'] is None)
ck('32_checks_passed',N['passed'] and len(N['checks'])==32 and all(c['passed'] for c in N['checks']))
ck('11_network_cases',len(R['summary'])==11)
c=R['cases']['one_direction_restore'];ck('connected_420_but_zero_x',c['active_edges']==420 and c['graph_spans_z'] and c['K_over_k'][0][0]<1e-20)
a={r['case']:r for r in R['summary']}
ck('adverse_centre_first_result_preserved',a['balanced_cluster_restore']['minimum_xy_shear_ratio']>a['four_direction_spread_restore']['minimum_xy_shear_ratio'])
ck('z_relaxation_changes_two_family_spread',a['balanced_spread_restore']['minimum_xy_shear_ratio_relaxed_z']<.3)
ck('cost_is_assumed',I['cost']['all_assumptions'])
ck('cost_example',math.isclose(R['cost'][1]['max_extra_capex_JPY'],1017724.6636665589,rel_tol=1e-10))
ck('source_final_not_preprint',S[1]['year']==2024 and 'Final peer-reviewed' in S[1]['read'])
ck('source_data_not_reexecuted','not downloaded or executed' in S[1]['scope'])
counts={}
for name,n in [('network_cases.csv',11),('repair_curve.csv',20),('jitter_screen.csv',9),('size_screen.csv',12),('cost_screen.csv',6),('local_damage.csv',9),('nodes.csv',108),('edges_and_masks.csv',450)]:
 with (P/name).open(encoding='utf-8',newline='') as f:counts[name]=len(list(csv.DictReader(f)))
 ck('rows_'+name,counts[name]==n)
ck('625_rows_including_geometry',sum(counts.values())==625)
report=P.parent/'GPT回答_多方向探索第66巡_つながる粒と支える粒を分ける再接続設計_20261009.md';text=report.read_text(encoding='utf-8')
for phrase in ['物理試験0件','90％超は未実証','FCCは節点配置','予測した解析ではない','H66-M','H66-C','H66-G','60分','450mm','R39','冬','32照合','625回の独立条件試験ではない','最適解ではない','中央寄り案が優れた結果','受領・同意は確認していない']:
 ck('report_'+phrase,phrase in text)
paths=[report,P/'README.md',root/'README.md',root/'回覧板.md',P.parent/'README.md',root/'調査台帳/一般.md',root/'調査台帳/計算部品索引.md']
links=0
for path in paths:
 for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
  if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',link) or link.startswith('#'):continue
  target=unquote(link.split('#',1)[0].split('?',1)[0]).strip('<>')
  if not target:continue
  if not (path.parent/target).exists():raise AssertionError('Missing link: '+str(path)+' -> '+target)
  links+=1
ck('relative_links_resolve',links>340)
board=(root/'回覧板.md').read_text(encoding='utf-8');history=board.split('## 8. 更新履歴（新しい順、1行ずつ）',1)[1]
ck('newest_history_row66','第66巡' in next(l for l in history.splitlines() if l.startswith('| 2026-')))
for n in [39,49,63,64,65]:ck('earlier_history_'+str(n),'第'+str(n)+'巡' in board)
for name in ['01_contact_layouts','02_support_and_repair','03_damage_jitter_cost']:
 ck('figure_pair_'+name,all((P/(name+ext)).stat().st_size>1000 for ext in ['.png','.svg']))
out={'passed':True,'checks':checks,'check_count':len(checks),'relative_links':links,'csv_rows_including_geometry':sum(counts.values()),'physical_trials':0,'success_probability':None,'visual_review':'Three original PNG figures inspected before publication; first figure layout repaired and re-inspected. No third-party figures republished.'}
(P/'document-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'checks':len(checks),'links':links,'csv_rows':sum(counts.values()),'passed':True}))
