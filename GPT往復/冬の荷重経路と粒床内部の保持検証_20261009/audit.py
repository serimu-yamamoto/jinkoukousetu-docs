from pathlib import Path
import hashlib,json,re,urllib.parse,subprocess,sys,struct
P=Path(__file__).resolve().parent
R=P.parents[1]
checks=[]
def ck(name,ok):
 checks.append({'name':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
def sha(b):return hashlib.sha256(b).hexdigest()
def norm(s):return s.replace('\r\n','\n').rstrip()+'\n'
ix=json.loads((P/'index_changes.json').read_text(encoding='utf-8'))
s=json.loads((P/'research_state.json').read_text(encoding='utf-8'))
v=json.loads((P/'validation.json').read_text(encoding='utf-8'))
res=json.loads((P/'results.json').read_text(encoding='utf-8'))
ck('30_numeric_checks',v['count']==30 and v['all_passed'])
ck('no_physical_trials',s['physical_experiments']==res['physical_experiments']==0)
ck('probability_null',s['success_probability'] is None and res['success_probability'] is None)
ck('all_strengths_assumed',res['all_strengths_assumed'])
ck('quote_unavailable',res['equipment_budget_context']['additional_works_quote_yen'] is None)
ck('no_contacts_purchases',s['contacts_sent']==s['purchases']==0)
ck('no_claude_receipt_claim',all(s[k] is None for k in ['claude_receipt','claude_reply','claude_running']))
ck('embargo_respected',s['source_fulltext_embargo_respected'])
ck('original_figures_reviewed',s['own_figures_visually_checked'] and not s['source_figures_republished'])
ck('claude_ledger_unchanged',sha(norm((R/s['claude_ledger']).read_text(encoding='utf-8')).encode())==s['claude_ledger_normalized_sha256'])
for p,expected in ix['before_sha256'].items():
 t=norm((R/p).read_text(encoding='utf-8'))
 for op in reversed([x for x in ix['operations'] if x['path']==p]):
  ck('unique_reverse_'+str(len(checks)),t.count(op['new'])==1)
  t=t.replace(op['new'],op['old'],1)
 ck('history_restored_'+p,sha(t.encode())==expected)
report=R/'GPT往復/GPT回答_多方向探索第90巡_雪の固着を粒床と地盤までつなぐ冬季設計_20261009.md'
text=report.read_text(encoding='utf-8')
for token in ['物理試験0件','成功確率','仮入力','30件','2.2倍','0.668','3.039','50℃','300mm','60分','未見積り']:
 ck('report_contains_'+token,token in text)
ck('source_access_limit_recorded','2028-07-17' in (P/'sources.md').read_text(encoding='utf-8'))
ck('model_not_safety_prediction','安全率' in (P/'model.md').read_text(encoding='utf-8'))
for name in ['winter_load_path.png','surface_only_plateau.png']:
 b=(P/name).read_bytes()
 ck('png_signature_'+name,b[:8]==b'\x89PNG\r\n\x1a\n')
 w,h=struct.unpack('>II',b[16:24]);ck('png_dimensions_'+name,w>=1000 and h>=600)
local_links=[]
for f in list(P.glob('*.md'))+[report]+[R/p for p in ix['before_sha256']]:
 for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
  link=link.strip('<>')
  if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',link) or link.startswith('#'):continue
  target=urllib.parse.unquote(link.split('#')[0].split('?')[0])
  if not target:continue
  dest=(f.parent/target).resolve()
  if dest.name in ['manifest.json','audit.json'] and dest.parent==P:continue
  if not dest.exists():raise AssertionError('Broken link '+str(f.relative_to(R))+' -> '+link)
  local_links.append(link)
ck('local_links_resolve',len(local_links)>0)
outputs=['results.json','validation.json']
before={p:sha((P/p).read_bytes()) for p in outputs}
proc=subprocess.run([sys.executable,str(P/'reproduce.py')],capture_output=True)
ck('reproduction_exit_zero',proc.returncode==0)
ck('reproduction_byte_identical',before=={p:sha((P/p).read_bytes()) for p in outputs})
for f in P.iterdir():
 if f.is_file() and f.name not in ['audit.json','manifest.json'] and f.suffix in ['.md','.json','.py']:
  ck('LF_only_'+f.name,b'\r' not in f.read_bytes())
result={'all_passed':all(x['passed'] for x in checks),'document_checks':len(checks),'local_link_count':len(local_links),'numeric_checks':v['count'],'physical_experiments':0,'checks':checks}
(P/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:result[k] for k in ['all_passed','document_checks','local_link_count','numeric_checks','physical_experiments']}))
