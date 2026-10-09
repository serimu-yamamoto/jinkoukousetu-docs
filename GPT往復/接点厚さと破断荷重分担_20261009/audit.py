"""Reproducible document/data integrity checks; not physical validation."""
import csv,json,math,re
from pathlib import Path
from urllib.parse import unquote
P=Path(__file__).resolve().parent
root=P.parents[1]
report=P.parent/'GPT回答_多方向探索第65巡_短い解放を阻む接点剛性と修復機能の再配置_20261009.md'
checks=[]
def ck(name,ok):
    checks.append({'name':name,'passed':bool(ok)})
    if not ok:raise AssertionError(name)
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
R=json.loads((P/'results.json').read_text(encoding='utf-8'))
N=json.loads((P/'numerical_checks.json').read_text(encoding='utf-8'))
S=json.loads((P/'sources.json').read_text(encoding='utf-8'))
ck('no_physical_trials',I['evidence']['physical_tests']==R['evidence']['physical_tests']==N['physical_tests']==0)
ck('no_success_probability',I['evidence']['success_probability'] is None and R['evidence']['success_probability'] is None)
ck('24_numerical_checks',len(N['checks'])==24 and N['passed'] and all(x['passed'] for x in N['checks']))
ck('96_assumption_rows_55_consistent_not_probability',R['grid_rows']==96 and R['valid_form_and_strain_rows']==55 and R['valid_rows_are_not_success_probability'])
ck('load_fraction_not_area_fraction',math.isclose(R['load_split']['actual_beta_if_Km100'],0.8263885533930705))
ck('thin_layer_same_final_opening',all(x['final_opening_um']==20 for x in R['thickness']))
ck('mechanical_release_work_includes_chemical',math.isclose(R['load_split']['ideal_release_total_work_J'],R['load_split']['ideal_release_chemical_work_J']+R['load_split']['ideal_release_mechanical_work_J']))
ck('fixture_instability_detected',not R['fixture'][0]['quasistatic_displacement_branch_stable'])
counts={}
for name,n in [('bridge_screen.csv',96),('thickness_screen.csv',3),('force_paths.csv',801),('fixture_screen.csv',3)]:
    with (P/name).open(encoding='utf-8',newline='') as f: counts[name]=len(list(csv.DictReader(f)))
    ck('rows_'+name,counts[name]==n)
ck('903_csv_data_rows',sum(counts.values())==903)
ck('supplement_not_obtained', 'not obtained' in S[0]['supplement_status'])
ck('snow_pdf_identified', S[1]['sha256']=='5aadf68a0612256fcad835adee8a8649bf0f3fdd8d7253d503c879b91be00297')
ck('raw_dynamic_snow_data_not_reanalysed','no raw data reanalysis' in S[2]['read'])
text=report.read_text(encoding='utf-8')
for phrase in ['物理試験0件','90％超は未実証','H65-M','H65-P','要求曲線','未測定の仮定','装置変位','未取得','60分','450mm','冬','費用','Claudeの閲覧・受領・同意・稼働は確認していない']:
    ck('report_'+phrase,phrase in text)
paths=[report,P/'README.md',root/'README.md',root/'回覧板.md',P.parent/'README.md',root/'調査台帳/一般.md',root/'調査台帳/計算部品索引.md']
link_count=0
for path in paths:
    txt=path.read_text(encoding='utf-8')
    for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',txt):
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',link) or link.startswith('#'):continue
        target=unquote(link.split('#',1)[0].split('?',1)[0]).strip('<>')
        if not target:continue
        if not (path.parent/target).exists():raise AssertionError('missing link '+str(path)+' '+target)
        link_count+=1
ck('local_markdown_links_resolve',link_count>300)
board=(root/'回覧板.md').read_text(encoding='utf-8')
section=board.split('## 8. 更新履歴（新しい順、1行ずつ）',1)[1]
ck('newest_history_row_is_65','第65巡' in next(x for x in section.splitlines() if x.startswith('| 2026-')))
for n in [26,61,63,64]:
    ck('history_preserved_'+str(n),'第'+str(n)+'巡' in board)
for name in ['force_and_release','fixture_and_thickness']:
    ck('figure_pair_'+name,all((P/(name+ext)).stat().st_size>1000 for ext in ['.png','.svg']))
out={'passed':True,'checks':checks,'check_count':len(checks),'local_links_checked':link_count,'csv_data_rows':sum(counts.values()),'physical_trials':0,'success_probability':None,'visual_review':'Two original figure PNGs inspected by Codex before publication; no clipping found. External snow PDF pages 8 and 15 inspected; not redistributed.'}
(P/'document-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'passed':True,'checks':len(checks),'links':link_count,'csv_rows':sum(counts.values())}))
