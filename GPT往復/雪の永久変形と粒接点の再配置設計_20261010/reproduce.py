from pathlib import Path
import json,sys,math,hashlib
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from contact_rearrangement import design,cycles,recovery,fit_observation
a=json.loads((D/'inputs.json').read_text());h=a['hypothetical'];checks=[]
def ck(n,b):
 if not b:raise AssertionError(n)
 checks.append(n)
def eq(x,y):return math.isclose(x,y,rel_tol=1e-9,abs_tol=1e-12)
rows=[]
for q in h['residual_fractions']:
 for hf in h['hardening_fractions']:
  label=str((q,hf));x=design(h['peak_force_N'],h['depth_m'],q,hf)
  ck('peak force '+label,eq(x['yield_force_N']+hf*x['k_N_m']*(h['depth_m']-x['yield_depth_m']),h['peak_force_N']))
  ck('recoil '+label,eq(h['depth_m']-h['peak_force_N']/x['k_N_m'],x['permanent_set_m']))
  ck('energy partition '+label,eq(x['net_work_J'],x['frictional_dissipation_J']+x['hardening_energy_J']))
  seq=[];errors=[]
  for n in h['grids']:
   c=cycles(h['peak_force_N'],h['depth_m'],q,hf,n,h['cycles'])
   er=abs(c[0]['work_J']/x['net_work_J']-1);errors.append(er)
   ck('final set '+label+str(n),eq(c[0]['permanent_set_m'],q*h['depth_m']))
   ck('all cycle peak '+label+str(n),all(eq(z['peak_force_N'],h['peak_force_N']) for z in c))
   ck('trained zero new work '+label+str(n),all(abs(z['work_J'])<1e-10 for z in c[1:]))
   ck('trained same set '+label+str(n),all(eq(z['permanent_set_m'],c[0]['permanent_set_m']) for z in c[1:]))
   seq.append(dict(steps_per_ramp=n,relative_energy_error=er,cycles=c))
  ck('fine grid accuracy '+label,errors[-1]<1e-5)
  ck('fine no worse '+label,errors[-1]<=errors[0]+1e-12)
  scale=design(2*h['peak_force_N'],h['depth_m'],q,hf)
  ck('force energy scaling '+label,eq(scale['net_work_J'],2*x['net_work_J']))
  rows.append(dict(residual_fraction=q,hardening_fraction=hf,analytic=x,refinements=seq))
rh=h['recovery'];aa=fit_observation(rh['unload_m'],rh['at60_m'],rh['time_s'],rh['short_tau_s'])
bb=dict(permanent=0.,retarded=rh['unload_m'],tau=-rh['time_s']/math.log(rh['at60_m']/rh['unload_m']))
for label,model in [('A',aa),('B',bb)]:
 ck('unload fit '+label,eq(recovery(0,**model),rh['unload_m']))
 ck('60s fit '+label,eq(recovery(rh['time_s'],**model),rh['at60_m']))
 ck('nonnegative '+label,all(v>=0 for v in model.values()))
series=[dict(time_s=t,A_m=recovery(t,**aa),B_m=recovery(t,**bb)) for t in rh['times_s']]
ck('late recovery identifies',abs(series[-1]['A_m']-series[-1]['B_m'])>.0007)
ck('different asymptotes',aa['permanent']>.00079 and bb['permanent']==0)
ck('permanent fraction is not energy fraction',not eq(rows[0]['analytic']['net_work_J']/rows[0]['analytic']['load_work_J'],rows[0]['residual_fraction']))
for args in [(500,.001,0,0),(500,.001,.9,.2),(-1,.001,.5,0)]:
 try:design(*args)
 except ValueError:ck('rejected '+str(args),True)
 else:raise AssertionError('invalid design accepted')
deps=['GPT往復/滑走方向の変形仕事と横解放の分離_20261010/model.md','GPT往復/滑走方向の変形仕事と横解放の分離_20261010/sources.json','GPT往復/高分子接点の乾湿摩擦と滑り率の定義監査_20261010/model.md']
data=dict(cycle=127,physical_trials=0,success_probability=None,dependency_hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in deps},hypothetical_contact_cases=rows,finite_window_recovery=dict(A=aa,B=bb,series=series),limits=a['limits'])
v=dict(count=len(checks),passed=True,checks=checks,physical_validation=False)
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for name,x in [('results.json',data),('validation.json',v)]:
 if '--check' in sys.argv:assert (D/name).read_bytes()==enc(x)
 else:(D/name).write_bytes(enc(x))
print(json.dumps(dict(checks=len(checks),max_final_energy_error=max(x['refinements'][-1]['relative_energy_error'] for x in rows),recovery=data['finite_window_recovery'],cases=[dict(q=x['residual_fraction'],h=x['hardening_fraction'],net_J=x['analytic']['net_work_J'],diss_J=x['analytic']['frictional_dissipation_J'],stored_J=x['analytic']['hardening_energy_J']) for x in rows])))
