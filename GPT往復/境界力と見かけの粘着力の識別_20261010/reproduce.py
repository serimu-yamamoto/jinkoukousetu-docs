from pathlib import Path
import json,sys,math,hashlib
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from boundary_pressure import *
dep1='GPT往復/温暖形成と開放環粒の製造監査_20261010/results.json'
dep2='GPT往復/押上げを減らす開離形状と圧力依存の検証_20261010/inputs.json'
p105=json.loads((R/dep1).read_text());p98=json.loads((R/dep2).read_text())
i=json.loads((D/'inputs.json').read_text());a=i['assumed'];p=i['reported'];checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def close(x,y):return math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-10)
rows=[]
for c in a['wall_offsets_cases']:
 for P in a['nominal_pressures_pa']:
  r=nominal_response(P,c['mu'],c['c_pa'],c['a'],c['b_pa']);r['case']=c['name'];rows.append(r)
  ck('same apparent curve '+str((c['name'],P)),close(r['shear_stress_pa'],1.78*P+290))
  ck('local and nominal pressure relation '+str((c['name'],P)),close(r['local_pressure_pa_assumed']-P,c['a']*P+c['b_pa']))
walls=[]
for mult in a['diameter_multipliers']:
 r=cylindrical_wall_pressure(p['cell_diameter_m']*mult,a['engaged_height_m'],a['wall_shear_pa']);walls.append(r)
 ck('force area closure '+str(mult),close(r['pressure_offset_pa']*r['cross_section_area_m2'],r['wall_force_N']))
 ck('diameter inverse at fixed height and traction '+str(mult),close(r['pressure_offset_pa']*mult,walls[0]['pressure_offset_pa']))
 # Direct lateral area versus disk area, independent simplified formula.
 ck('perimeter area formula '+str(mult),close(r['pressure_offset_pa'],4*a['engaged_height_m']*a['wall_shear_pa']/r['diameter_m']))
grows=[]
rho=p105['inputs']['dry_bulk_density_kg_m3']
for h in a['normal_depths_m']:
 P=gravity_pressure(rho,h,a['slope_deg'])
 grows.append(dict(normal_depth_m_assumed=h,bulk_density_kg_m3_assumed=rho,self_weight_normal_pressure_pa=P,
  published_apparent_intercept_over_pressure=290/P,
  prior98_contact_pressure_ratio=[x*1000/P for x in p98['pressure_kPa']],
  warning='Ratios compare scales only; prior98 pressure is single-contact nominal force/area, not the local bed stress here'))
 ck('slope weight projection '+str(h),close(P/math.cos(math.radians(a['slope_deg'])),rho*9.8*h))
zero=[nominal_response(0,c['mu'],c['c_pa'],0,0)['shear_stress_pa'] for c in a['wall_offsets_cases']]
ck('identical fixture fits have different zero-confinement limits',zero==[290,0,0])
ck('zero-depth gravity stress',gravity_pressure(rho,0,30)==0)
for f,args in [(nominal_response,(-1,1,0,0,0)),(cylindrical_wall_pressure,(0,.05,100)),(gravity_pressure,(rho,.02,90))]:
 try:f(*args)
 except ValueError:ck('invalid boundary '+str(args),True)
 else:raise AssertionError('invalid accepted')
data=dict(cycle=118,physical_trials=0,success_probability=None,dependency_hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in [dep1,dep2]},
 constructed_identical_nominal_curves=rows,no_wall_zero_pressure_limits_pa=zero,wall_scaling=walls,
 self_weight_scale_comparisons=grows,missing=['wall traction measured by location','shear-plane stress','actual50C wet properties','continuous load-release path','raw source curves and uncertainty covariance'],
 caveat='Diagnostic counterexamples, not corrected source coefficients or artificial-firn strength. Internal material friction, bed friction, contact friction and ski-base friction remain distinct.')
v=dict(count=len(checks),checks=checks,passed=True,physical_validation=False,scope="Identifiability, force/area and dimensional pressure comparisons only")
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for name,obj in [('results.json',data),('validation.json',v)]:
 if '--check' in sys.argv:assert (D/name).read_bytes()==enc(obj)
 else:(D/name).write_bytes(enc(obj))
print(json.dumps(dict(checks=len(checks),no_wall_zero_pressure_limits_pa=zero,wall_scaling=walls,pressure_scales=grows)))
