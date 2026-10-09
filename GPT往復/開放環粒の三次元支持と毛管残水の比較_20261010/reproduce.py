from pathlib import Path
import json,sys,math,os,hashlib
import numpy as np
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
sys.path.insert(0,os.environ.get('FIRN_COMMON_LIB',str(R/'計算部品')))
import rim_grain_hex as h
import formation_routes as g
checks=[]
def ck(name,value):assert value,name;checks.append(name)
coords=(h.SIGNS+1)/2;K,vol=h.elements(coords[None,:,:],.3);K=K[0]
ck('unit cube volume',abs(vol[0]-1)<1e-12);ck('symmetry',np.max(abs(K-K.T))<1e-12)
for axis in range(3):
 u=np.zeros((8,3));u[:,axis]=1
 ck('rigid translation '+str(axis),np.linalg.norm(K@u.ravel())<1e-12)
 u=np.cross(np.eye(3)[axis],coords)
 ck('rigid rotation '+str(axis),np.linalg.norm(K@u.ravel())<1e-12)
mu=1/(2*1.3);lam=.3/(1.3*.4)
u=np.zeros((8,3));u[:,2]=coords[:,2]
ck('constant axial strain energy',abs(.5*u.ravel()@K@u.ravel()-.5*(lam+2*mu))<1e-12)
u=np.zeros((8,3));u[:,0]=coords[:,1]
ck('constant shear strain energy',abs(.5*u.ravel()@K@u.ravel()-.5*mu)<1e-12)
bench=h.solve(2,36,6,1.,0.)
ck('assembled annulus exact axial stiffness at nu0',abs(bench['normal']['stiffness_E1']-bench['mesh_volume_mm3']/.6**2)<1e-9)
rows=[]
for mesh in [(2,36,6),(2,72,12),(3,108,18)]:
 base=None
 for fraction in [1.,2/3,1/3]:
  r=h.solve(*mesh,fraction)
  if base is None:base=r
  r['normal_ratio']=r['normal']['stiffness_E1']/base['normal']['stiffness_E1']
  r['lateral_ratio']=r['lateral']['stiffness_E1']/base['lateral']['stiffness_E1']
  truevol=g.grain(web_fraction=fraction)['volume_mm3']
  polygonfactor=math.sin(2*math.pi/mesh[1])/(2*math.pi/mesh[1])
  ck('independent geometry volume '+str((mesh,fraction)),abs(r['mesh_volume_mm3']/truevol-polygonfactor)<1e-11)
  for axis in ['normal','lateral']:
   ck('residual '+str((mesh,fraction,axis)),r[axis]['relative_residual']<1e-8)
   ck('force balance '+str((mesh,fraction,axis)),r[axis]['force_balance']<1e-8)
   ck('energy '+str((mesh,fraction,axis)),abs(r[axis]['energy_reaction_ratio']-1)<1e-8)
  rows.append(r)
  (D/'partial.json').write_text(json.dumps({'completed_states':len(rows),'rows':rows},indent=2)+'\n')
convergence=[]
for fraction in [1.,2/3,1/3]:
 pair=[r for r in rows if r['web_fraction']==fraction][-2:]
 delta={k:abs(pair[1][k]-pair[0][k])/pair[1][k] for k in ['normal_ratio','lateral_ratio']}
 convergence.append(dict(web_fraction=fraction,relative_ratio_changes=delta,
                         within_3_percent=max(delta.values())<.03))
 # Preserve failed mesh acceptance separately from algebraic consistency checks.
caps=[]
for angle in [0.,30.,60.,80.,89.,90.,100.]:
 caps.append(dict(path='axial_bore',**h.capillary(1.4,angle_deg=angle)))
 for fraction in [2/3,1/3]:
  width=.85*(2*math.pi/6)*(1-fraction)
  caps.append(dict(path='side_window',web_fraction=fraction,window_width_at_mean_radius_mm=width,
                   **h.capillary(width,.4,angle_deg=angle)))
ck('circular pressure special case',abs(h.capillary(1.4,angle_deg=0)['pressure_magnitude_Pa']-4*.06794/.0014)<1e-10)
ck('rectangular square pressure special case',abs(h.capillary(1.,1.,angle_deg=0)['pressure_magnitude_Pa']-4*.06794/.001)<1e-10)
out=dict(cycle=106,physical_trials=0,success_probability=None,rows=rows,convergence=convergence,
 benchmark=bench,capillary_scales=caps,grain_gravity_pressure_Pa=1000*9.81*.0006,
 assumptions=dict(E=1,nu=.3,sigma_N_m=.06794,water_density_kg_m3=1000,
 strain_scale=1e-6,structural_boundary='clamped bottom annulus, uniform top displacement in one axis; other top axes free',
 capillary_model='P/A force scale for a prismatic circle or locally approximated rectangular opening; no flow simulation or drainage threshold'),
 dependencies={name:hashlib.sha256((R/'計算部品'/name).read_bytes()).hexdigest() for name in ['rim_grain_hex.py','formation_routes.py']})
validation=dict(count=len(checks),status='algebraic_checks_passed',checks=checks,physical_trials=0,success_probability=None,
 mesh_acceptance_limit=.03,mesh_acceptance_passed=all(x['within_3_percent'] for x in convergence),
 mesh_unresolved=[x['web_fraction'] for x in convergence if not x['within_3_percent']],
 limitations=['fixed bottom and orientation; not a bed','no contact buckling fatigue large strain or 50 C properties',
 'pressure scale not water recovery fraction or capillary breakthrough prediction','mesh differences not continuum error bound'])
if '--check' in sys.argv:
 old=json.loads((D/'results.json').read_text())
 def compare(a,b):
  if isinstance(a,dict):assert a.keys()==b.keys();[compare(a[k],b[k]) for k in a]
  elif isinstance(a,list):assert len(a)==len(b);[compare(x,y) for x,y in zip(a,b)]
  elif isinstance(a,(int,float)) and not isinstance(a,bool):assert math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-12),(a,b)
  else:assert a==b
 compare(out,old);assert validation==json.loads((D/'validation.json').read_text())
else:
 for name,data in [('results.json',out),('validation.json',validation)]:
  (D/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
if (D/'partial.json').exists():(D/'partial.json').unlink()
print(json.dumps(dict(checks=len(checks),fine=[{k:r[k] for k in ['web_fraction','normal_ratio','lateral_ratio','nodes','elements']} for r in rows[-3:]],convergence=convergence,capillary_at_60=[r for r in caps if r['assumed_angle_deg']==60.])))
