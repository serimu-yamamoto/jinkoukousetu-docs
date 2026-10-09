"""Audit arithmetic summaries, references and preservation of the five shared indices."""
from pathlib import Path
import csv,json,math,re,subprocess,hashlib,shutil,urllib.request
from urllib.parse import unquote
D=Path(__file__).resolve().parent;R=D.parents[1]
def norm(s):return s.replace('\r\n','\n').rstrip()+'\n'
I=json.loads((D/'inputs.json').read_text(encoding='utf-8'))
P=json.loads((D/'index_changes.json').read_text(encoding='utf-8'))
result=json.loads((D/'results.json').read_text(encoding='utf-8'))
checks=[]
def ck(n,v):
    assert v,n
    checks.append({'name':n,'passed':True})
def near(a,b):return math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-10)
ck('physical_trial_status',result['physical_trials']==0)
ck('success_probability_not_fabricated',result['success_probability'] is None)
cs=json.loads((D/'checks.json').read_text(encoding='utf-8'))
ck('math_check_record',len(cs)==25 and all(x['passed'] for x in cs))
expected={'composition':5,'closed_coats':24,'coupled_binder':28,'separated_binder':27,'drying_scenarios':6,'pad_costs':18,'manufacturing':3}
tables={}
for n,c in expected.items():
    with (D/(n+'.csv')).open(encoding='utf-8') as f:tables[n]=list(csv.DictReader(f))
    ck('rows_'+n,len(tables[n])==c)
ck('row_total',sum(map(len,tables.values()))==111==result['computed_rows'])
ck('surface_budget_independent',(near(result['binder_surface_load_budget'],(.04-.01-.025)/(.2-.025))))
ck('hold_requirement_independent',near(result['separated_reference']['required_wet_shear_MPa'],2*4*(.025+.175*.01)/.05))
ck('drying_mass_independent',near(result['drying_reference'][0]['water_kg_per_kg_dry_composite'],20/.13))
ck('cost_limits_ordered',0<result['pad_5um_cost_min']<result['pad_5um_cost_max'])
tp=json.loads((D/'test_plan.json').read_text(encoding='utf-8'))
ck('tests_not_executed',tp['status']=='not_executed' and len(tp['specifications'])==8)
report=R/'GPT往復/GPT回答_多方向探索第73巡_結晶複合材の耐水性と滑走面を隠さない結合_20261009.md'
text=report.read_text(encoding='utf-8')
ck('report_status_and_scope',all(s in text for s in ['物理試験0件','成功確率は未算定','2億円とは別枠','税別','約590〜5,679万円','25数式照合・111計算行']))
for name in ['figure1_binder.png','figure2_design_cost.png']:
    ck('image_'+name,(D/name).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
indices=['README.md','回覧板.md','GPT往復/README.md','調査台帳/一般.md','調査台帳/計算部品索引.md']
G=shutil.which('git') or 'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def baseline(name):
    try:
        return norm(subprocess.run([G,'show',I['basis_commit']+':'+name],cwd=R,capture_output=True,check=True).stdout.decode('utf-8'))
    except (OSError,subprocess.CalledProcessError):
        from urllib.parse import quote
        url='https://raw.githubusercontent.com/serimu-yamamoto/jinkoukousetu-docs/'+I['basis_commit']+'/'+quote(name,safe='/')
        return norm(urllib.request.urlopen(url,timeout=30).read().decode('utf-8'))
old_hashes={}
for name in indices:
    new=norm((R/name).read_text(encoding='utf-8'));old=baseline(name)
    old_hashes[name]=hashlib.sha256(old.encode()).hexdigest()
    if name=='README.md':restored=new.replace(P['readme_insert'],'',1)
    elif name=='GPT往復/README.md':restored=new.replace(P['gpt_insert'],'',1)
    elif name=='回覧板.md':
        restored=new.replace(P['newUpdate73'],P['oldUpdate73'],1).replace(P['newLatest73'],P['oldLatest73'],1)
        for key in ['boardEntry73','historyRow73','handoff73']:restored=restored.replace(P[key],'',1)
    elif name=='調査台帳/一般.md':restored=new.removesuffix(P['generalAppend73'])
    else:restored=new.removesuffix(P['calcAppend73'])
    ck('history_preserved_'+name,restored==old)
all_md=[report]+list(D.glob('*.md'))+[R/n for n in indices]
links=0
for file in all_md:
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',file.read_text(encoding='utf-8')):
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target) or target.startswith('#'):continue
        target=unquote(target.split('#')[0].split('?')[0])
        ckname=str(file.relative_to(R))+' -> '+target
        assert (file.parent/target).exists(),ckname
        links+=1
ck('all_local_links_exist',links>400)
out={'cycle':73,'physical_trials':0,'success_probability':None,'document_checks':len(checks),'links_checked':links,'checks':checks,'baseline_index_sha256_lf_normalized':old_hashes,'visual_review':'Two rendered figures inspected; concept drawing not to scale; numerical figures use hypothetical inputs.'}
(D/'document_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'document_checks':len(checks),'links_checked':links,'all_passed':True}))
