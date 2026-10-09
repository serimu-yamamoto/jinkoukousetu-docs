from pathlib import Path
import sys,json,hashlib,math
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1]
sys.path.insert(0,str(R/'計算部品'))
from viscoelastic_glide import *
checks=[]
def check(name,b):
 if not b:raise AssertionError(name)
 checks.append(name)
def close(a,b):return math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-10)
deps=['GPT往復/滑走方向の変形仕事と横解放の分離_20261010/model.md',
      'GPT往復/動的接触と圧力分布の滑走面検証_20261009/model.md',
      'GPT往復/結晶接触材の粒度基準と保持量監査_20261010/results.json']
hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in deps}
old=json.loads((R/deps[2]).read_text());inventory=old['reference_localized_coating']
check('prior material inventory',inventory['core_kg']==133650 and inventory['target_area_fraction']==.2)
# These k and tau describe hypothetical response functions at one unspecified fixed material state.
# No real 50C material values or temperature shift factor are assigned.
load=700;k0=1e6;dk=9e6
cases=[]
models=[('elastic',0,1e-4),('fast_relaxation',dk,1e-6),('mid_relaxation',dk,1e-4),('slow_relaxation',dk,1e-2)]
for name,delta,tau in models:
 for speed in (2,5,10,20):
  for lam in (.0005,.001,.003):
   for ar in (.01,.03):
    x=sinusoidal_glide(speed,lam,lam*ar,load,k0,delta,tau)
    x.update(model=name,tau_s=tau,amplitude_over_wavelength=ar);cases.append(x)
    check('nonnegative energy '+str(len(cases)),x['loss_J_per_cycle']>=0 and x['drag_N']>=0)
reference=[]
for name,delta,tau in models:
 r=sinusoidal_glide(5,.001,.00003,load,k0,delta,tau);r.update(model=name,tau_s=tau)
 reference.append(r)
check('elastic zero cycle loss',reference[0]['loss_J_per_cycle']==0)
check('reference all massless contact screens',all(c['continuous_contact_massless_diagnostic'] for c in reference))
check('f range lower',close(min(c['frequency_Hz'] for c in cases),2/.003))
check('f range upper',close(max(c['frequency_Hz'] for c in cases),40000))
check('zero frequency relaxed',complex_stiffness(0,k0,dk,.001)==complex(k0,0))
check('large frequency instantaneous plateau',abs(complex_stiffness(1e14,k0,dk,.001).real/(k0+dk)-1)<1e-10)
check('loss peak x1',close(complex_stiffness(1/(2*math.pi*.001),k0,dk,.001).imag,dk/2))
r=reference[2]
double=sinusoidal_glide(5,.001,.00006,load,k0,dk,1e-4)
check('amplitude squared energy',close(double['drag_N'],4*r['drag_N']))
check('amplitude force variation',close(double['force_variation_amplitude_N_massless'],2*r['force_variation_amplitude_N_massless']))
check('power from cycle rate',close(r['work_rate_W'],r['loss_J_per_cycle']*r['frequency_Hz']))
check('some rows invalidate contact',any(not c['continuous_contact_massless_diagnostic'] for c in cases))
matched=[]
for name,delta,tau in models:
 c=matched_dynamic_stiffness(5000,1e6,k0,delta,tau)
 out=sinusoidal_glide(5,.001,.00003,load,c['k0'],c['dk'],tau)
 check('matched dynamic storage '+name,close(out['k_storage_N_m'],1e6))
 out.update(model=name,tau_s=tau,scale=c['scale'],k_relaxed_N_m=c['k0'])
 matched.append(out)
td=[]
for x in (.1,1,10):
 coarse=time_domain_work(x,2048);fine=time_domain_work(x,4096)
 check('ODE fine vs closed form '+str(x),fine['relative_error']<1e-5)
 check('ODE refinement improves '+str(x),fine['relative_error']<coarse['relative_error'])
 td.extend([coarse,fine])
for func,args in [(complex_stiffness,(-1,1,1,.1)),(sinusoidal_glide,(0,.1,.001,1,1,1,.1)),(complex_stiffness,(1,1,1,0))]:
 try:func(*args)
 except ValueError:check('invalid input '+str(args),True)
 else:raise AssertionError('invalid accepted')
# Functional microscopic surface area inherited from110, not slope plan area or factory web area.
area=inventory['core_kg']*inventory['coatable_area_m2_per_kg_core']*inventory['target_area_fraction']
cost=[dict(functional_area_m2=area,assumed_treatment_jpy_per_m2=p,processing_only_jpy=area*p) for p in (.1,1,10)]
check('functional area from prior inventory',close(area,267300))
data=dict(cycle=112,physical_trials=0,success_probability=None,dependency_hashes=hashes,
 assumptions=dict(load_N=load,k_relaxed_N_m=k0,k_increment_N_m=dk,reference_speed_m_s=5,reference_wavelength_m=.001,reference_amplitude_m=.00003,
 tau_values_s=[1e-6,1e-4,1e-2],temperature_C=None,note='Hypothetical responses. No real material constants, temperature shift factors or total friction assigned.'),
 rows=cases,reference=reference,matched_dynamic_support=matched,time_domain=td,
 frequency_range_Hz=[min(c['frequency_Hz'] for c in cases),max(c['frequency_Hz'] for c in cases)],
 contact_invalid_rows=sum(not c['continuous_contact_massless_diagnostic'] for c in cases),
 inherited_coating=inventory,functional_surface_cost=cost)
validation=dict(count=len(checks),checks=checks,passed=True,physical_validation=False,
 scope='96 response scenarios and mathematical consistency; all contact screens are uncalibrated diagnostics, not success rates.')
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for name,obj in [('results.json',data),('validation.json',validation)]:
 if '--check' in sys.argv:assert (D/name).read_bytes()==enc(obj),'stored result mismatch'
 else:(D/name).write_bytes(enc(obj))
print(json.dumps(dict(checks=len(checks),rows=len(cases),frequency=data['frequency_range_Hz'],invalid_contact=data['contact_invalid_rows'],
 reference=[{k:c[k] for k in ['model','k_storage_N_m','k_loss_N_m','drag_N','mu_deformation_only','force_variation_amplitude_N_massless']} for c in reference],
 matched=[{k:c[k] for k in ['model','drag_N','mu_deformation_only','equilibrium_displacement_under_held_load_m']} for c in matched],
 time_domain=td,cost=cost,reproduced='--check' in sys.argv),ensure_ascii=False))
