"""Document/data integrity audit, not a product or safety certification."""
from pathlib import Path
import hashlib,json,re,urllib.parse,subprocess,sys,struct
P=Path(__file__).resolve().parent; R=P.parents[1]; checks=[]
def ck(n,v):
    checks.append({'name':n,'passed':bool(v)})
    if not v:raise AssertionError(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(n):return json.loads((P/n).read_text(encoding='utf-8'))
def norm(t):return t.replace('\r\n','\n')
s=read('research_state.json'); res=read('results.json'); plan=read('test_plan.json')
ix=read('index_changes.json'); v=read('validation.json'); inp=read('inputs.json')
ck('physical_experiments_zero',all(d['physical_experiments']==0 for d in [s,res,plan,inp]))
ck('success_probability_unknown',all(d['success_probability'] is None for d in [s,res,plan,inp]))
ck('source_data_not_mislabeled_product_data',res['actual_50C_creep_of_proposed_product'] is None and res['actual_recovery'] is None)
ck('no_ski_or_wear_measurements',res['actual_wear'] is None and res['actual_ski_friction'] is None)
ck('no_material_selected',s['selected_material'] is None)
ck('no_equipment_or_partners',not s['facilities_available'] and not s['collaborators_available'])
ck('no_contacts_or_quotes',s['contacts_sent']==s['quotes_obtained']==0)
ck('claude_response_unknown',not s['claude_receipt_confirmed'] and not s['claude_reply_confirmed'])
ck('dataset_content_unavailable',not s['dataset_content_obtained'] and s['public_dataset_metadata_obtained'])
ck('not_crystal_growth',not s['snow_crystal_growth_confirmed'])
ck('48_unperformed_specimens',len(plan['specimens'])==48 and all(x['status']=='not_run' and x['lot_id'] is None and x['measured_creep'] is None and x['measured_recovery'] is None for x in plan['specimens']))
ck('unique_specimens',len({x['id'] for x in plan['specimens']})==48)
ck('all_factors_present',len({(x['dose_kGy'],x['shape'],x['environment'],x['replicate']) for x in plan['specimens']})==48)
ck('72_arithmetic_checks',v['count']==72 and v['all_passed'])
ck('case_counts',len(res['manufacturing_cases'])==27 and len(res['energy_cases'])==9 and len(res['transport_cases'])==6 and len(res['lifetime_cases'])==3)
ck('assumed_prices','not quotations' in inp['manufacturing']['price_status'])
ck('duration_ambiguity_preserved','1 h' in inp['source_table']['holding_time_note'] and '2 h' in inp['source_table']['holding_time_note'])
ledger=norm((R/'調査台帳/物性値照合_自律ループv2v3.md').read_text(encoding='utf-8'))
ck('claude_ledger_preserved',sha(ledger.encode())==s['claude_ledger_sha256_LF'])
for p,expected in ix['before_sha256'].items():
    text=norm((R/p).read_text(encoding='utf-8'))
    for k,o in reversed(list(enumerate(ix['operations']))):
        if o['path']==p:
            ck('unique_reverse_'+str(k),text.count(o['new'])==1)
            text=text.replace(o['new'],o['old'],1)
    ck('history_preserved_'+p,sha(text.encode())==expected)
report=R/'GPT往復/GPT回答_多方向探索第95巡_一体架橋枝の50℃根拠と端材回収の経済性_20261009.md'
text=report.read_text(encoding='utf-8')
for term in ['50℃','450mm','300mm','60分','2億円','成功確率未算定','36.51％は復元率ではない','受領・返答・稼働は未確認']:
    ck('report_condition_'+term,term in text)
sources=(P/'sources.md').read_text(encoding='utf-8')
ck('dataset_failure_disclosed','再解析は未実施' in sources and 'HTTP403' in sources)
png=(P/'evidence_and_process.png').read_bytes()
ck('PNG_signature',png[:8]==b'\x89PNG\r\n\x1a\n')
w,h=struct.unpack('>II',png[16:24]);ck('PNG_dimensions',w>=1000 and h>=600)
links=[]
for f in list(P.glob('*.md'))+[report]+[R/p for p in ix['before_sha256']]:
    for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
        link=link.strip('<>')
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',link) or link.startswith('#'):continue
        target=urllib.parse.unquote(link.split('#')[0].split('?')[0])
        if not target:continue
        dest=(f.parent/target).resolve()
        if dest.parent==P and dest.name in ['manifest.json','document_audit.json']:continue
        if not dest.exists():raise AssertionError('Broken local link '+str(f.relative_to(R))+' -> '+link)
        links.append(link)
ck('local_links_resolve',len(links)>0)
before={n:sha((P/n).read_bytes()) for n in ['results.json','validation.json']}
run=subprocess.run([sys.executable,str(P/'reproduce.py'),'--check'],capture_output=True)
ck('reproduction_succeeds',run.returncode==0)
ck('reproduction_keeps_bytes',before=={n:sha((P/n).read_bytes()) for n in before})
for f in P.iterdir():
    if f.is_file() and f.suffix in ['.md','.py','.json','.txt'] and f.name not in ['manifest.json','document_audit.json']:
        ck('LF_only_'+f.name,b'\r' not in f.read_bytes())
out={'all_passed':all(x['passed'] for x in checks),'document_checks':len(checks),'numeric_checks':v['count'],'local_link_count':len(links),'physical_experiments':0,'checks':checks}
(P/'document_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:out[k] for k in ['all_passed','document_checks','numeric_checks','local_link_count','physical_experiments']}))
