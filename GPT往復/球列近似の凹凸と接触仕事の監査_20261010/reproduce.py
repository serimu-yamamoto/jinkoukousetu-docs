from pathlib import Path
import sys,json,math,hashlib,ast,itertools
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from clump_surface_cycle import row_cycle,force_ratio,pitch_for_relative_peak
dep1='GPT往復/押上げを減らす開離形状と圧力依存の検証_20261010/inputs.json'
dep2='GPT往復/押上げを減らす開離形状と圧力依存の検証_20261010/reproduce.py'
dep3='GPT往復/境界力と見かけの粘着力の識別_20261010/sources.json'
old=json.loads((R/dep1).read_text());a=json.loads((D/'inputs.json').read_text())['assumed'];mus=[0,*old['particle_contact_mu']]
# Reuse only the already-read pure function definition; no top-level legacy execution.
node=next(n for n in ast.parse((R/dep2).read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='q')
ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(R/dep2),'exec'),ns);oldq=ns['q']
checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def close(x,y,t=1e-9):return math.isclose(x,y,rel_tol=t,abs_tol=t)
rows=[]
for rr,beta,mu in itertools.product(a['probe_radius_over_bead'],a['pitch_over_bead_diameter'],mus):
 r=a['bead_radius_m'];rp=r*rr;s=2*r*beta
 out=row_cycle(r,rp,s,mu,a['integration_n'][0]);fine=row_cycle(r,rp,s,mu,a['integration_n'][1])
 key=str((rr,beta,mu));out['probe_radius_ratio']=rr;out['pitch_fraction']=beta
 ck('analytic cycle integral '+key,close(out['mean_signed_force_over_load'],out['analytic_mean_force_over_load']))
 ck('signed work conservation '+key,close(out['mean_signed_force_over_load'],out['mean_friction_work_over_load_pitch']+out['mean_gravitational_work_over_load_pitch']))
 ck('zero net lift '+key,close(out['mean_gravitational_work_over_load_pitch'],0))
 ck('integration refinement '+key,close(out['mean_signed_force_over_load'],fine['mean_signed_force_over_load']))
 ck('nonnegative dissipation '+key,out['mean_friction_work_over_load_pitch']>=-1e-10)
 ck('smooth surface lower bound '+key,out['mean_signed_force_over_load']>=mu-1e-10)
 for slope in [-out['maximum_abs_slope'],0,out['maximum_abs_slope']]:
  ck('legacy law consistency '+key+str(slope),close(force_ratio(mu,slope),oldq(mu,slope)))
  phi=math.atan(slope);normal=1/(math.cos(phi)-mu*math.sin(phi))
  ck('independent normal-tangent balance '+key+str(slope),close(force_ratio(mu,slope),normal*(math.sin(phi)+mu*math.cos(phi))))
 rows.append(out)
for rr,mu in itertools.product(a['probe_radius_over_bead'],mus):
 group=[r for r in rows if r['probe_radius_ratio']==rr and r['input_contact_mu_assumed']==mu]
 ck('resolving pitch reduces ripple '+str((rr,mu)),all(group[j]['clearance_height_ripple_m']>group[j+1]['clearance_height_ripple_m'] for j in range(len(group)-1)))
 ck('resolving pitch reduces signed resistance '+str((rr,mu)),all(group[j]['mean_signed_force_over_load']>=group[j+1]['mean_signed_force_over_load']-1e-10 for j in range(len(group)-1)))
zero=next(r for r in rows if r['probe_radius_ratio']==1 and r['pitch_fraction']==1 and r['input_contact_mu_assumed']==0)
ck('force peaks do not prove dissipation',zero['maximum_force_over_load']>0 and close(zero['mean_signed_force_over_load'],0) and zero['positive_only_work_over_load_pitch']>0)
for f,args in [(row_cycle,(.0005,.0005,.002,.2)),(row_cycle,(.0005,.00001,.001,.6)),(force_ratio,(.5,2))]:
 try:f(*args)
 except ValueError:ck('invalid prescribed path '+str(args),True)
 else:raise AssertionError('invalid accepted')
resolution=pitch_for_relative_peak(.2,a['relative_peak_extra_diagnostic'],a['bead_radius_m'],a['bead_radius_m'])
pr=row_cycle(a['bead_radius_m'],a['bead_radius_m'],resolution['maximum_pitch_m'],.2)
ck('peak-target inversion',close(pr['maximum_force_over_load'],resolution['target_peak_force_over_load']))
ck('finer pitch meets diagnostic',row_cycle(a['bead_radius_m'],a['bead_radius_m'],.99*resolution['maximum_pitch_m'],.2)['maximum_force_over_load']<resolution['target_peak_force_over_load'])
ck('coarser pitch exceeds diagnostic',row_cycle(a['bead_radius_m'],a['bead_radius_m'],1.01*resolution['maximum_pitch_m'],.2)['maximum_force_over_load']>resolution['target_peak_force_over_load'])
finest=next(r for r in rows if r['probe_radius_ratio']==1 and r['pitch_fraction']==.125 and r['input_contact_mu_assumed']==.2)
resolution['finest_sweep_mean_extra_fraction']=finest['mean_signed_force_over_load']/.2-1
resolution['finest_sweep_peak_extra_fraction']=finest['maximum_force_over_load']/.2-1
resolution['bead_centers_per_meter_at_max_pitch']=1/resolution['maximum_pitch_m']
ck('mean error can hide peak error',resolution['finest_sweep_mean_extra_fraction']<.002 and resolution['finest_sweep_peak_extra_fraction']>.3)

data=dict(peak_resolution_diagnostic=resolution,cycle=119,physical_trials=0,success_probability=None,dependency_hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in [dep1,dep2,dep3]},conditions=rows,frictionless_counterexample=zero,
 scope='One constrained periodic contact path only; not a reproduction of Zhao DEM or a ski friction prediction.',
 limits=['probe does not rotate','no contact compliance','no multicontact at cusps','no out-of-plane escape','no adhesion wear temperature or water','no material parameters measured','mean ratio is apparatus-path dependent'])
v=dict(count=len(checks),checks=checks,passed=True,physical_validation=False,scope='Analytic integral, quadrature refinement, work and force balance, legacy-law consistency')
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for name,obj in [('results.json',data),('validation.json',v)]:
 if '--check' in sys.argv:assert (D/name).read_bytes()==enc(obj)
 else:(D/name).write_bytes(enc(obj))
print(json.dumps(dict(checks=len(checks),conditions=len(rows),resolution=resolution,reference=[{k:r[k] for k in ['pitch_fraction','clearance_height_ripple_m','mean_signed_force_over_load','maximum_force_over_load','minimum_force_over_load']} for r in rows if r['probe_radius_ratio']==1 and r['input_contact_mu_assumed']==.2],frictionless=zero)))
