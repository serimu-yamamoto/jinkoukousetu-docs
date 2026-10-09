from pathlib import Path
from urllib.parse import unquote
import json,csv,re,math
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REPORT=ROOT/'GPT往復/GPT回答_多方向探索第67巡_低摩擦相を微小接点へ行き渡らせる材料設計_20261009.md'
r=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
p=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
checks=[]
def require(name,condition):
 if not condition:raise AssertionError(name)
 checks.append(name)
require('physical tests and probability remain unmeasured',r['physical_tests']==0 and r['success_probability'] is None and p['physical_tests']==0 and p['success_probability'] is None)
require('independent numerical checks passed',r['checks_passed']==23 and len(r['checks'])==23)
rows={f.name:list(csv.DictReader(f.open(encoding='utf-8',newline=''))) for f in HERE.glob('*.csv')}
require('geometry count exact',len(rows['contact_presence.csv'])==140)
require('planned experiments distinct from outputs',len(rows['planned_coupon_tests.csv'])==168 and all(x['status']=='NOT_EXECUTED' and x['observed_friction']=='' and x['observed_wear']=='' for x in rows['planned_coupon_tests.csv']))
require('plan includes four moisture states',len({x['water_state'] for x in rows['planned_coupon_tests.csv']})==4)
require('stage A and B correct',sum(x['stage']=='A' for x in rows['planned_coupon_tests.csv'])==96)
require('stage A nominal time correct',r['planned']['stage_A_nominal_rig_hours']==72)
sources=json.loads((HERE/'sources.json').read_text(encoding='utf-8'))
require('source IDs unique',len({s['id'] for s in sources})==len(sources)==6)
require('missing full text not hidden',all('unavailable' in next(s for s in sources if s['id']==i)['access'] for i in ['S2','S3']))
require('phase presence distinguished from mean area',r['reference_rows'][1]['contact_presence']>.99 and r['reference_rows'][1]['expected_area_fraction']<.03)
require('same composition clustering counterexample retained',r['cluster_counterexamples'][2]['contact_presence']<.251)
text=REPORT.read_text(encoding='utf-8')
require('report states limitations and winter/rain conditions',all(t in text for t in ['物理試験0件','成功確率','温暖噴霧','450mm','300mm','60分','台風','追加融雪','人体']))
files=[REPORT,*HERE.glob('*.md'),ROOT/'README.md',ROOT/'回覧板.md',ROOT/'GPT往復/README.md',ROOT/'調査台帳/一般.md',ROOT/'調査台帳/計算部品索引.md']
links=0
for f in files:
 t=f.read_text(encoding='utf-8')
 for link in re.findall(r'\]\(([^)]+)\)',t):
  target=unquote(link.split('#')[0].strip('<>'))
  if not target or '://' in target or target.startswith('mailto:'):continue
  if not (f.parent/target).exists() and (f.parent/target).resolve()!=(HERE/'audit_results.json').resolve():raise AssertionError('missing local link '+str(f)+': '+target)
  links+=1
require('relative links all exist',links>0)
for f in sorted(set([REPORT,*HERE.iterdir(),*files])):
 if f.name=='audit_results.json':continue
 if f.is_file() and f.suffix in ['.md','.json','.py','.csv','.txt']:
  b=f.read_bytes()
  require('LF text: '+f.name,b'\r' not in b and b.endswith(b'\n') and not b.endswith(b'\n\n'))
out={'document_checks':len(checks),'numerical_checks':23,'local_links':links,'csv_rows':{k:len(v) for k,v in rows.items()},'physical_tests':0,'success_probability':None,'checks':checks}
(HERE/'audit_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in out.items() if k!='checks'},ensure_ascii=False))
