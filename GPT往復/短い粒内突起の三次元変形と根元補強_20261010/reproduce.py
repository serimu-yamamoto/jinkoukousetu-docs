from pathlib import Path
import os
for key in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS"):os.environ[key]="1"
import sys,json,math,hashlib
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
import numpy,scipy
from stop_hex import solve_post
from stop_misalignment import beam_compliance
a=json.loads((D/'inputs.json').read_text());h=a['assumed'];g=a['geometry'];checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
levels=list(h['mesh_levels']);rows=[];changes=[]
for n in levels:
 for kind in g['kinds']:
  z=solve_post(n,kind,h['poisson'],g['radius_mm'],g['half_height_mm']);rows.append(z)
  if '--check' not in sys.argv:print('computed',kind,n,'elements',z['elements'],flush=True)
def compare(n0,n1):
 out=[]
 for kind in g['kinds']:
  old=next(z for z in rows if z['n']==n0 and z['kind']==kind);new=next(z for z in rows if z['n']==n1 and z['kind']==kind)
  for axis in ('x','z'):
   out.append(dict(kind=kind,axis=axis,from_n=n0,to_n=n1,relative_change=abs(new['components'][axis]['compliance_times_E_per_mm']/old['components'][axis]['compliance_times_E_per_mm']-1)))
 return out
changes=compare(levels[-2],levels[-1])
if max(x['relative_change'] for x in changes)>h['convergence_change_limit']:
 n=h['optional_final_mesh_level'];levels.append(n)
 for kind in g['kinds']:
  z=solve_post(n,kind,h['poisson'],g['radius_mm'],g['half_height_mm']);rows.append(z)
  if '--check' not in sys.argv:print('computed',kind,n,'elements',z['elements'],flush=True)
 changes=compare(levels[-2],levels[-1])
for z in rows:
 key=z['kind']+str(z['n'])
 ck('positive volume '+key,z['volume_mm3']>0)
 ck('affine strain energy '+key,abs(z['affine_patch_energy_ratio']-1)<1e-9)
 ck('load centroid '+key,max(abs(v) for v in z['top_load_centre_mm'])<1e-12)
 ck('xy symmetry '+key,abs(z['components']['x']['compliance_times_E_per_mm']/z['components']['y']['compliance_times_E_per_mm']-1)<1e-8)
 for axis,c in z['components'].items():
  ck('positive compliance '+key+axis,c['compliance_times_E_per_mm']>0)
  ck('equilibrium '+key+axis,max(c['relative_free_residual'],c['force_balance'],c['moment_balance'])<1e-8)
  ck('energy work '+key+axis,abs(c['energy_reaction_ratio']-1)<1e-8)
  ck('small load displacement '+key+axis,c['max_displacement_over_height']<.01)
final={z['kind']:z for z in rows if z['n']==levels[-1]}
ratios={}
for axis in ('x','z'):
 base=2*final['short']['components'][axis]['compliance_times_E_per_mm']
 ratios[axis]={kind:final[kind]['components'][axis]['compliance_times_E_per_mm']/base for kind in ('single','stepped')}
ck('step volume ratio2.5',abs(final['stepped']['volume_mm3']/(2*final['short']['volume_mm3'])-2.5)<1e-10)
ck('single volume equality',abs(final['single']['volume_mm3']/(2*final['short']['volume_mm3'])-1)<1e-10)
ck('final circular volume within1percent',all(abs(z['relative_volume_error'])<.01 for z in final.values()))
# Beam coefficient unit is 1/m; divide by1000 for comparison to1/mm.
r=g['radius_mm']/1000;L=g['half_height_mm']/1000;nu=h['poisson'];kap=h['beam_shear_factor']
beam={'short':beam_compliance([(L,r)],nu,kap),'single':beam_compliance([(2*L,r)],nu,kap),'stepped':beam_compliance([(L,2*r),(L,r)],nu,kap)}
comparison={kind:dict(FE_over_beam_lateral=final[kind]['components']['x']['compliance_times_E_per_mm']/(b['lateral_times_E']/1000),FE_over_beam_axial=final[kind]['components']['z']['compliance_times_E_per_mm']/(b['axial_times_E']/1000)) for kind,b in beam.items()}
deps=['計算部品/rim_grain_hex.py','計算部品/stop_misalignment.py','GPT往復/粒内突起の位置ずれと片側受け面の比較_20261010/results.json','GPT往復/開放環粒の三次元支持と毛管残水の比較_20261010/sources.json']
data=dict(cycle=125,physical_trials=0,success_probability=None,dependency_hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in deps},
 runtime=dict(numpy=numpy.__version__,scipy=scipy.__version__),mesh_levels=levels,states=rows,final_changes=changes,
 numerical_convergence_criterion_met=max(x['relative_change'] for x in changes)<=h['convergence_change_limit'],
 final_compliance_ratios_to_two_short=ratios,FE_vs_beam=comparison,limits=a['limits'])
v=dict(count=len(checks),passed=True,checks=checks,physical_validation=False)
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for name,x in [('results.json',data),('validation.json',v)]:
 if '--check' in sys.argv:assert (D/name).read_bytes()==enc(x),name+' changed'
 else:(D/name).write_bytes(enc(x))
print(json.dumps(dict(checks=len(checks),states=len(rows),levels=levels,criterion=data['numerical_convergence_criterion_met'],max_change=max(x['relative_change'] for x in changes),ratios=ratios,FE_vs_beam=comparison,runtime=data['runtime']),ensure_ascii=False))
