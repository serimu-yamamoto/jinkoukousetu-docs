"""Numerical/document audit. Does not qualify a material or ski surface."""
from pathlib import Path
import json,hashlib,math,re,urllib.parse,struct,subprocess,sys
P=Path(__file__).resolve().parent;R=P.parents[1];checks=[]
def read(n):return json.loads((P/n).read_text(encoding='utf-8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def norm(t):return t.replace('\r\n','\n')
def ck(n,b):
 checks.append({'name':n,'passed':bool(b)})
 if not b:raise AssertionError(n)
s=read('research_state.json');r=read('results.json');v=read('validation.json');i=read('inputs.json');p=read('test_plan.json');ix=read('index_changes.json')
ck('physical_experiments_zero',all(x['physical_experiments']==0 for x in [s,r,i,p]))
ck('success_probability_unknown',all(x['success_probability'] is None for x in [s,r,i,p]))
ck('no_equipment_or_partner',not s['facilities_available'] and not s['collaborators_available'])
ck('no_contacts_or_quotes',s['contacts_sent']==s['quotes_obtained']==i['economics']['quotes_obtained']==0)
ck('claude_reply_not_claimed',not s['claude_receipt_confirmed'] and not s['claude_reply_confirmed'])
ck('material_not_selected',s['selected_material'] is None)
ck('not_crystal_growth',not s['snow_crystal_growth_confirmed'])
ck('actual_values_missing',r['actual_50C_modulus'] is None and r['actual_ski_friction'] is None and s['actual_grain_lifetime'] is None)
ck('source_temperature_unconfirmed',i['source']['measurement_temperature_C'] is None)
ck('aging_not_service_prediction',all(not x['actual_50C_prediction'] for x in r['aging_cases']+r['conditioning_windows']))
ck('scratch_not_ski',not r['scratch_coefficients_used_for_ski'])
ck('85_arithmetic_checks',v['count']==85 and v['all_passed'] and all(x['passed'] for x in v['checks']))
ck('case_counts',len(r['aging_cases'])==12 and len(r['conditioning_windows'])==36 and len(r['equal_bending_cost_cases'])==24)
ck('boundary_counts',len(r['raw_cost_parity_boundaries'])==6 and len(r['raw_price_ceilings'])==8 and len(r['holding_cost_cases'])==4)
ck('calculation_window_not_extrapolated',all(x['all_ages_within_5min_10day'] for x in r['aging_cases']) and all(x['within_age_window'] for x in r['conditioning_windows']))
ck('cost_not_quoted',all(not x['quoted'] and not x['qualified_geometry'] for x in r['equal_bending_cost_cases']))
ck('life_not_known',not r['lifetime_cost_known'])
ck('36_unperformed_sets',len(p['sets'])==36 and all(x['status']=='not_run' and x['actual_age_hours'] is None and x['lot_id'] is None for x in p['sets']))
ck('72_unperformed_specimens',len(p['specimens'])==72 and all(x['status']=='not_run' and x['measured_E50'] is None and x['measured_friction'] is None and x['measured_wear'] is None for x in p['specimens']))
ck('unique_sets_and_specimens',len({x['id'] for x in p['sets']})==36 and len({x['id'] for x in p['specimens']})==72)
ck('full_factorial_sets',len({(x['material'],x['nominal_post_forming_age_hours'],x['environment'],x['replicate']) for x in p['sets']})==36)
ck('two_types_per_set',all({x['type'] for x in p['specimens'] if x['set_id']==z['id']}=={'branch_bending','flat_ski_contact'} for z in p['sets']))
ledger=norm((R/'調査台帳/物性値照合_自律ループv2v3.md').read_text(encoding='utf-8'))
ck('claude_ledger_preserved',sha(ledger.encode())==s['claude_ledger_sha256_LF'])
for path,expected in ix['before_sha256'].items():
 txt=norm((R/path).read_text(encoding='utf-8'))
 for j,o in reversed(list(enumerate(ix['operations']))):
  if o['path']==path:
   ck('unique_reverse_'+str(j),txt.count(o['new'])==1);txt=txt.replace(o['new'],o['old'],1)
 ck('history_preserved_'+path,sha(txt.encode())==expected)
report=R/'GPT往復/GPT回答_多方向探索第97巡_PHAの結晶性と成形後硬化から見直す材料設計_20261010.md'
txt=report.read_text(encoding='utf-8')
for term in ['50℃','450mm','300mm','60分','2億円','成功確率未算定','受領・返答・稼働は未確認','50℃営業時の予測ではない','雪の結晶成長と呼ばない']:
 ck('report_condition_'+term,term in txt)
source=(P/'sources.md').read_text(encoding='utf-8')
ck('source_version_and_access_disclosed','受理稿' in source and '403' in source and '生測定データ再解析' in source)
ck('grade_difference_disclosed','旧BP350' in source and 'BP350-05' in source)
links=[]
for path in list(P.glob('*.md'))+[report]+[R/k for k in ix['before_sha256']]:
 for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
  link=link.strip('<>')
  if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',link) or link.startswith('#'):continue
  target=urllib.parse.unquote(link.split('#')[0].split('?')[0])
  if not target:continue
  dest=(path.parent/target).resolve()
  if dest.parent==P and dest.name in ['document_audit.json','manifest.json']:continue
  if not dest.exists():raise AssertionError('Broken link '+str(path.relative_to(R))+' -> '+link)
  links.append(link)
ck('local_links_resolve',bool(links))
data=(P/'aging_and_price_bounds.png').read_bytes();ck('png_signature',data[:8]==b'\x89PNG\r\n\x1a\n')
w,h=struct.unpack('>II',data[16:24]);ck('figure_size',w>=1000 and h>=600)
before={n:sha((P/n).read_bytes()) for n in ['results.json','validation.json']}
run=subprocess.run([sys.executable,str(P/'reproduce.py'),'--check'],capture_output=True)
ck('full_reproduction_passes',run.returncode==0)
ck('reproduction_preserves_bytes',before=={n:sha((P/n).read_bytes()) for n in before})
for path in P.iterdir():
 if path.is_file() and path.suffix in ['.md','.py','.json','.txt'] and path.name not in ['manifest.json','document_audit.json']:
  ck('LF_'+path.name,b'\r' not in path.read_bytes())
out={'all_passed':all(x['passed'] for x in checks),'audit_checks':len(checks),'numeric_checks':v['count'],'local_link_count':len(links),'physical_experiments':0,'checks':checks}
(P/'document_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:out[k] for k in out if k!='checks'}))
