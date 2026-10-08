"""Document / reproducibility checks, not material performance tests."""
import base64, csv, json, math, re
from pathlib import Path
P=Path(__file__).resolve().parent; root=P.parents[1]
R=json.loads((P/'results.json').read_text(encoding='utf-8'))
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
V=json.loads((P/'validation.json').read_text(encoding='utf-8'))
T=json.loads((P/'test_plan.json').read_text(encoding='utf-8'))
report=root/'GPT往復/GPT回答_多方向探索第57巡_荷重を支える芯と解放する接点の統合_20261009.md'
text=report.read_text(encoding='utf-8'); checks=[]
def chk(name, ok):
    checks.append(dict(name=name,passed=bool(ok)))
    if not ok:raise SystemExit('FAILED DOCUMENT CHECK: '+name)
chk('all_33_algebraic_checks_pass',len(V['checks'])==33 and all(x['passed'] for x in V['checks']))
chk('physical_tests_zero_everywhere',all(x['physical_tests']==0 for x in [I,R,T,V]))
chk('success_probability_not_assigned',all(x['success_probability'] is None for x in [I,R,T]))
chk('test_plan_not_executed',T['status']=='NOT_EXECUTED')
chk('report_discloses_inverse_specification',all(x in text for x in ['逆算','実物','物理試験0件','90％超を示す証拠はない']))
chk('report_preserves_spray_objective', '現地噴霧結晶化を実現した案ではない' in text)
chk('report_preserves_budget_boundary', '税込2億円' in text and '芯だけの材料費' in text)
chk('report_discloses_beam_limit', '厚さ／長さが0.5' in text)
chk('report_discloses_no_physical_quote','実見積りは未取得' in text)
chk('reported_progressive_stiffness_rounded',abs(R['progressive_core']['high_to_low_tangent_ratio']-24)<.01)
chk('reported_core_mass_rounded',abs(R['candidate_core_mass_kg']/1000-20.22)<.005)
chk('reported_core_gap_rounded',abs(R['candidate_core_side_gap_um_at_15pct']-19.51)<.005)
# Check every internal link in the new documents, not unrelated historical broken links.
newdocs=[report]+list(P.glob('*.md')); missing=[]
for f in newdocs:
    for target in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
        if target.startswith(('http:','https:','#')):continue
        dest=(f.parent/target.split('#')[0]).resolve()
        if not dest.exists():missing.append(str(dest))
chk('new_document_relative_links_resolve',not missing)
# The base snapshots are temporary and excluded from publication.
snapshot=root/'.git/docs-before57.json'
history_status='SKIPPED_BASE_SNAPSHOT_NOT_AVAILABLE'
if snapshot.exists():
    before=json.loads(snapshot.read_text(encoding='utf-8'))
    for path,data in before.items():
        old=base64.b64decode(data).decode('utf-8').splitlines();new=(root/path).read_text(encoding='utf-8').splitlines()
        it=iter(new)
        chk('history_retained_'+path,all(any(a.rstrip()==b.rstrip() for b in it) for a in old))
    history_status='BASE_SNAPSHOT_VERIFIED'
for name in ['figure1_force_window','figure2_clearance_gas','figure3_component_cost','figure4_progressive_support']:
    chk('figure_exists_'+name,(P/(name+'.png')).read_bytes().startswith(b'\x89PNG\r\n\x1a\n') and '<svg' in (P/(name+'.svg')).read_text(encoding='utf-8'))
counts={f.name:sum(1 for _ in csv.DictReader(f.open(encoding='utf-8'))) for f in P.glob('*.csv')}
chk('all_nine_model_tables_present',len(counts)==9)
chk('source_access_limits_explicit',all(x in (P/'sources.md').read_text(encoding='utf-8') for x in ['403','cache miss','有料本文は未取得']))
result=dict(cycle=57,scope='document consistency only',physical_tests=0,success_probability=None,checks=checks,
            history_check=history_status,csv_rows=counts,total_csv_rows=sum(counts.values()),visual_review='four PNGs inspected; readable labels and no clipped text',
            original_computation_disclaimer='No physical trial, 3D FEA, DEM, or calibrated constitutive fit was performed.')
(P/'document-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(checks=len(checks),all_passed=True,csv_rows=sum(counts.values()),physical_tests=0),ensure_ascii=False))
