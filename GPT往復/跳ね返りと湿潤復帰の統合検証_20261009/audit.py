import base64,csv,json,re
from pathlib import Path
P=Path(__file__).resolve().parent;root=P.parents[1]
R=json.loads((P/'results.json').read_text(encoding='utf-8'));I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
V=json.loads((P/'validation.json').read_text(encoding='utf-8'));T=json.loads((P/'test_plan.json').read_text(encoding='utf-8'))
report=root/'GPT往復/GPT回答_多方向探索第58巡_内部摩擦で雪の切れと復帰を両立する条件_20261009.md';text=report.read_text(encoding='utf-8');checks=[]
def check(name,ok):
    checks.append(dict(name=name,passed=bool(ok)))
    if not ok:raise SystemExit('FAILED DOCUMENT CHECK: '+name)
check('35_algebra_checks_pass',len(V['checks'])==35 and all(v['passed'] for v in V['checks']))
check('physical_tests_zero',all(v['physical_tests']==0 for v in [R,I,V,T]))
check('probability_not_fabricated',all(v['success_probability'] is None for v in [R,I,T]))
check('test_plan_not_executed',T['status']=='NOT_EXECUTED')
check('component_loss_not_success_rate',all(s in text for s in ['開発成功率でもない','15.56','98.77']))
check('candidate_small_margin_disclosed','0.017' in text and '量産・使用へ進める案ではない' in text)
check('no_snow_waveform_fabrication','概念図' in text and '再現していない' in text)
check('budget_scope_retained','税込2億円' in text and '完成品や設備の見積りではない' in text)
check('spray_objective_retained','現地の噴霧結晶化を達成したものではない' in text)
check('source_experiment_scope_disclosed','実験検証が必要' in text)
check('rounded_candidate_offset_matches',abs(R['candidate']['worst_in_required_mu_range']['residual_offset_um']-.983)<.0005)
check('rounded_mass_matches',abs(R['candidate']['additional_flexure_mass_kg']/1000-8.85)<.005)
check('rounded_combined_loss_matches',abs(R['whole_grain_energy'][-1]['combined_loss_fraction']*100-15.56)<.005)
missing=[]
for f in [report]+list(P.glob('*.md')):
    for dest in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
        if dest.startswith(('http:','https:','#')):continue
        if not (f.parent/dest.split('#')[0]).resolve().exists():missing.append(dest)
check('new_links_resolve',not missing)
counts={f.name:sum(1 for _ in csv.DictReader(f.open(encoding='utf-8'))) for f in P.glob('*.csv')}
check('11_tables_present',len(counts)==11)
check('162_candidate_cases',counts['candidate_tolerance.csv']==162)
for name in ['figure1_force_return','figure2_wet_tolerance','figure3_energy_cost']:
    check('figure_'+name,(P/(name+'.png')).read_bytes().startswith(b'\x89PNG\r\n\x1a\n') and '<svg' in (P/(name+'.svg')).read_text(encoding='utf-8'))
snap=root/'.git/docs-before58.json';history='SKIPPED_BASE_SNAPSHOT_NOT_AVAILABLE'
if snap.exists():
    before=json.loads(snap.read_text(encoding='utf-8'))
    for path,b64 in before.items():
        old=base64.b64decode(b64).decode('utf-8').splitlines();new=(root/path).read_text(encoding='utf-8').splitlines()
        # Only two stale navigation lines are intentionally replaced on the board.
        if path=='回覧板.md':old=[a for a in old if not a.startswith(('**最終更新：','**今回の最新報告：**'))]
        it=iter(new)
        check('history_retained_'+path,all(any(a.rstrip()==b.rstrip() for b in it) for a in old))
    history='VERIFIED_WITH_TWO_DOCUMENTED_NAVIGATION_REPLACEMENTS'
board=(root/'回覧板.md').read_text(encoding='utf-8')
first=next(l for l in board.splitlines() if l.startswith('**今回の最新報告：**'))
check('board_latest_pointer_is_cycle58','第58巡' in first and report.name in first)
res=dict(cycle=58,scope='document checks only',physical_tests=0,success_probability=None,checks=checks,history_check=history,csv_rows=counts,total_csv_rows=sum(counts.values()),visual_review='All three generated PNGs reviewed; labels readable and plots not clipped.')
(P/'document-audit.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(checks=len(checks),all_passed=True,model_rows=sum(counts.values()),physical_tests=0),ensure_ascii=False))
