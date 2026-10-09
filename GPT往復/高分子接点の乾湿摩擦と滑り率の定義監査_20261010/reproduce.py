from pathlib import Path
import json,sys,math,hashlib
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from rolling_slip_audit import kinematics,rpm_ratios,implied_diameter_ratio,friction_power
a=json.loads((D/'inputs.json').read_text());checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def eq(x,y):return math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-12)
rows=[];h=a['assumed']
for q in a['source']['table6']:
 k=rpm_ratios(q['rpm1'],q['rpm2'],h['equal_diameter_ratio']);name=str(q['label_fraction'])
 ck('symmetric conversion '+name,eq(k['symmetric_fraction'],2*k['one_surface_fraction']/(2-k['one_surface_fraction'])))
 ck('factor two convention '+name,eq(k['symmetric_fraction'],2*k['half_symmetric_fraction']))
 ck('rate reconstruction '+name,eq(k['relative_speed'],1-q['rpm2']/q['rpm1']))
 ck('diagnostic rounded half convention '+name,round(100*k['half_symmetric_fraction'])==round(100*q['label_fraction']))
 ds={}
 for definition in ('one_surface','symmetric','half_symmetric'):
  d=implied_diameter_ratio(q['rpm1'],q['rpm2'],q['label_fraction'],definition)
  check=rpm_ratios(q['rpm1'],q['rpm2'],d)
  ck('diameter inverse '+definition+name,eq(check[definition+'_fraction'],q['label_fraction']))
  ds[definition]=d
 v1=h['illustrative_v1_m_s'];v2=v1*q['rpm2']/q['rpm1']
 p=friction_power(h['illustrative_mu'],h['illustrative_normal_force_N'],v1,v2)
 p_full=friction_power(h['illustrative_mu'],h['illustrative_normal_force_N'],v1,0)
 ck('work balance '+name,eq(p,abs(h['illustrative_mu']*h['illustrative_normal_force_N']*v1-h['illustrative_mu']*h['illustrative_normal_force_N']*v2)))
 ck('full sliding power factor '+name,eq(p_full/p,1/k['relative_speed']))
 rows.append(dict(source_label=q['label_fraction'],**k,implied_diameter_ratios=ds,illustrative_power_W=p,illustrative_full_sliding_power_W=p_full,full_over_rolling_sliding_power=p_full/p))
for n in (1.,5.,20.):
 z=kinematics(n,0)
 ck('stationary counterface one fraction '+str(n),eq(z['one_surface_fraction'],1))
 ck('stationary counterface symmetric fraction '+str(n),eq(z['symmetric_fraction'],2))
 ck('co-moving relative zero '+str(n),kinematics(n,n)['relative_speed']==0)
ck('zero friction power',friction_power(0,100,5,0)==0)
for fun,args in [(kinematics,(0,0)),(kinematics,(1,-1)),(rpm_ratios,(750,0,1)),(implied_diameter_ratio,(750,400,.3,'bad')),(friction_power,(-1,100,5,0))]:
 try:fun(*args)
 except ValueError:ck('invalid '+str(args),True)
 else:raise AssertionError('invalid input accepted')
deps=['GPT往復/局部圧力と乾式接点検証_20261008/sources.md','GPT往復/滑走面と回転摩耗検証_20261009/sources.md']
data=dict(cycle=126,physical_trials=0,success_probability=None,dependency_hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in deps},conditional_equal_diameter_cases=rows,limits=a['limits'])
v=dict(count=len(checks),passed=True,checks=checks,physical_validation=False)
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for name,x in [('results.json',data),('validation.json',v)]:
 if '--check' in sys.argv:assert (D/name).read_bytes()==enc(x)
 else:(D/name).write_bytes(enc(x))
print(json.dumps(dict(checks=len(checks),cases=rows),ensure_ascii=False))
