from pathlib import Path
import json,hashlib,re,urllib.parse,struct,platform,math
P=Path(__file__).resolve().parent;R=P.parents[1];checks=[]
def read(n):return json.loads((P/n).read_text(encoding='utf8'))
def norm(s):return s.replace('\r\n','\n').rstrip()+'\n'
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def ck(name,ok):
    if not ok:raise AssertionError(name)
    checks.append({'name':name,'passed':True})
s=read('summary.json');d=read('decision.json');n=read('checks.json')
ck('no_physical_results_or_probability',s['physical_experiments']==d['physical_experiments']==0 and s['success_probability'] is None and d['success_probability'] is None)
ck('no_external_supplier_action',s['provider_contacts_sent']==s['orders_placed']==d['quotes_received']==0 and not s['equipment_secured'])
ck('23_numeric_checks',len(n)==s['numeric_checks']==23 and all(x['passed'] for x in n))
ck('177_calculation_records',sum(len(read(f)) for f in ['contact_recruitment.json','quadrature_check.json','nonidentifiability.json','inverse_windows.json'])+1==s['calculation_rows']==177)
ck('no_actual_material_or_snow_target',d['actual_50C_material_moduli'] is None and d['actual_snow_contact_fraction_target'] is None)
ck('unquoted_total',d['actual_total_manufacturing_cost_yen'] is None and s['actual_total_manufacturing_cost_yen'] is None)
ck('no_ski_adoption',not d['adopted_for_ski_use'] and not d['manufacturing_demonstrated'] and not d['finished_safety_verified'])
plans=read('test_plan.json')
ck('6_unperformed_observation_specs',len(plans)==6 and all(x['status']=='not_run' and x['measurements'] is None and x['replicate_count'] is None for x in plans))
ck('all_contact_results_diagnostics',all(x['actual_allowable_strain'] is None and x['snowlike_performance'] is None and x['actual_50C_modulus'] is None for x in read('contact_recruitment.json')))
ck('separate_dry_wet_screens',all(x['actual_joint_wet_contact_solution'] is None for x in read('inverse_windows.json')))
w=read('design_witness.json')
ck('high_load_counterexample_preserved',w['20kPa_diagnostic']['approach_over_arm_length']>.29 and w['20kPa_diagnostic']['linear_model_invalid_for_design'])
ck('witness_not_manufactured',not w['manufactured'] and not w['validated'])
ck('primary_sources',len(read('sources.json'))==2 and all(x['verified']=='2026-10-09' and x['url'].startswith('https://') for x in read('sources.json')))
rr=read('reference_scope.json')
ck('speed_range_exclusions',sum(not x['accepted_as_observation_at_15'] for x in rr)==2 and not rr[1]['accepted_as_observation_at_10'])
ck('no_third_party_PDF_in_artifacts',not any(x.suffix.lower()=='.pdf' for x in P.iterdir()))
pm=read('plot_metadata.json')
ck('figures_own_unmanufactured_concept',len(pm['figures'])==2 and pm['physical_experiments']==0 and not pm['manufacturing_demonstrated'])
for f in pm['figures']:
    b=(P/f).read_bytes()
    ck('png_signature_'+f,b[:8]==b'\x89PNG\r\n\x1a\n')
    width,height=struct.unpack('>II',b[16:24])
    ck('png_dimensions_'+f,width>=1000 and height>=800)
idx=read('index_changes.json')
for f,h in idx['before_hashes'].items():
    t=norm((R/f).read_text(encoding='utf8'))
    for op in reversed(idx['operations']):
        if op['path']==f:
            ck('unique_reverse_'+str(len(checks)),t.count(op['new'])==1)
            t=t.replace(op['new'],op['old'])
    ck('history_preserved_'+f,sha(t)==h)
ck('claude_ledger_unchanged',sha(norm((R/'調査台帳/物性値照合_自律ループv2v3.md').read_text(encoding='utf8')))=='054c9388de3be3bd251c395059a9e02c9d3b336885236683ba3f528ff819d71f')
rep=R/'GPT往復/GPT回答_多方向探索第87巡_実雪の接触根拠と高さ分布から見直す荷重設計_20261009.md'
body=rep.read_text(encoding='utf8')
for phrase in ['物理試験0件','成功確率は未算定','50℃の実測値ではありません','原料費は減らない','最適解や採用確定とはしません','450mm','300mm','R39','約60分','人体・環境への無害性は未証明','受領・返答・稼働は未確認','総製造費は未取得','20kPa','0.291','172.2','241.7','23照合','177計算']:
    ck('report_guard_'+phrase,phrase in body)
local_links=0
for f in [rep,*P.glob('*.md'),*(R/x for x in idx['before_hashes'])]:
    for u in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',f.read_text(encoding='utf8')):
        if re.match(r'^[a-zA-Z]+:',u) or u.startswith('#'):continue
        target=f.parent/urllib.parse.unquote(u.split('#')[0]).strip('<>')
        if not target.exists() and target.name not in ['manifest.json','document_audit.json']:raise AssertionError('missing link '+str(target))
        local_links+=1
ck('local_links',local_links>500)
for f in [rep,*P.iterdir(),*(R/x for x in idx['before_hashes'])]:
    if f.is_file() and f.suffix in ['.md','.py','.json'] and f.name not in ['manifest.json','document_audit.json']:
        ck('LF_'+f.name,b'\r' not in f.read_bytes())
out={'checks':checks,'local_links_checked':local_links,'python':platform.python_version(),'physical_experiments':0,'success_probability':None}
(P/'document_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'document_checks':len(checks),'local_links':local_links,'numeric_checks':23,'calculation_rows':177,'physical_experiments':0}))
