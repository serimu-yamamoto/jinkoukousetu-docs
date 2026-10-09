from pathlib import Path
import json,sys,hashlib,itertools,math
import numpy as np
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'計算部品'))
from contact_fabric import cone_points,operators,condensed_state,metrics,axisymmetric_closed,regular_star,random_star_average
def calculate():
 checks=[]
 def check(name,condition):
  if not condition:raise AssertionError(name)
  checks.append(dict(name=name,passed=True))
 rows=[]
 for k,a,t in itertools.product([.01,.02,.1,.5,1.],[0.,15.,30.,45.,60.,90.],[0.,15.,30.,45.]):
  n,w=cone_points(a,t);op=operators(n,w,k)
  rows.append(dict(kappa=k,cap_deg=a,tilt_deg=t,affine=metrics(op['C']),central_relaxed=metrics(op['relaxed'])))
 check('120 full tensor comparisons',len(rows)==120)
 # Closed-form sphere and cone moments are an independent analytical benchmark.
 for k,a in itertools.product([.02,.1,1.],[0.,15.,30.,45.,90.]):
  n,w=cone_points(a);op=operators(n,w,k);x=axisymmetric_closed(a,k)
  check('closed Czz '+str((k,a)),abs(op['C'][2,2]-x['Czz'])<1e-12)
  check('closed Gxz '+str((k,a)),abs(op['C'][4,4]-x['Gxz'])<1e-12)
 for k in [.01,.02,.1,.5,1.]:
  n,w=cone_points(90.);op=operators(n,w,k)
  check('isotropic ratio '+str(k),abs(metrics(op['C'])['ratio_Czz_Gxz']-(6+4*k)/(2+3*k))<1e-12)
  check('isotropic central relaxation zero '+str(k),np.max(np.abs(op['C']-op['relaxed']))<1e-12)
 # Direct link-level minimization energies and residuals, not just stored tensors.
 for a,t in [(0.,0.),(15.,0.),(30.,30.),(90.,45.)]:
  n,w=cone_points(a,t);op=operators(n,w,.02)
  e=np.array([.13,-.07,.19,.11,-.17,.05]);s=condensed_state(op,e)
  check('direct energy '+str((a,t)),abs(s['energy']-.5*e@op['relaxed']@e)<1e-12)
  check('particle force torque equilibrium '+str((a,t)),s['force_torque_residual']<1e-12)
  check('relaxation cannot raise quadratic energy '+str((a,t)),np.linalg.eigvalsh(op['C']-op['relaxed']).min()>-1e-12)
  check('relaxed nonnegative energy '+str((a,t)),np.linalg.eigvalsh(op['relaxed']).min()>-1e-12)
 # Rotating every link preserves the Mandel eigenvalues, but changes slope-frame coupling.
 for a in [0.,15.,30.,90.]:
  n,w=cone_points(a,0.);p=operators(n,w,.02);n,w=cone_points(a,30.);q=operators(n,w,.02)
  for mode in ['C','relaxed']:
   check('Mandel rotation spectrum '+str((a,mode)),np.max(np.abs(np.array(metrics(p[mode])['mandel_eigenvalues'])-metrics(q[mode])['mandel_eigenvalues']))<1e-12)
 n,w=cone_points(0.);op=operators(n,w,.02)
 check('aligned fixed rotational shear finite',math.isclose(op['C'][4,4],.005,rel_tol=1e-12))
 check('aligned free rotation removes xz shear',abs(op['relaxed'][4,4])<1e-12)
 check('aligned free rotation leaves one supported strain mode',metrics(op['relaxed'])['mandel_rank']==1)
 quad=[]
 for nm,np_ in [(4,16),(8,32),(16,64)]:
  n,w=cone_points(37.,29.,nm,np_);op=operators(n,w,.037);quad.append(dict(n_mu=nm,n_phi=np_,C=op['C'].tolist(),relaxed=op['relaxed'].tolist()))
 for i in [0,1]:
  check('quadrature C '+str(i),np.max(np.abs(np.array(quad[i]['C'])-quad[2]['C']))<1e-12)
  check('quadrature relaxed '+str(i),np.max(np.abs(np.array(quad[i]['relaxed'])-quad[2]['relaxed']))<1e-12)
 # This ratio is an arbitrary diagnostic threshold, not a snow acceptance value.
 lo,hi=0.,90.
 for _ in range(60):
  mid=(lo+hi)/2
  if axisymmetric_closed(mid,.02)['ratio']>=10:lo=mid
  else:hi=mid
 angle=(lo+hi)/2
 check('illustrative ratio boundary',abs(axisymmetric_closed(angle,.02)['ratio']-10)<1e-10)
 travel=[]
 for passes in [1,2]:
  for speed in [.5,1.]:
   minutes=1000*passes/speed/60+24
   travel.append(dict(full_width_passes_assumed=passes,path_length_each_m=1000,travel_speed_m_s=speed,
       other_minutes_assumed=24,closure_minutes=minutes,within_60_by_travel_only=minutes<=60))
 check('one pass timing',math.isclose(travel[0]['closure_minutes'],57+1/3))
 check('two pass timing',math.isclose(travel[2]['closure_minutes'],90+2/3))
 check('two pass minimum speed',math.isclose(2000/(36*60),25/27))
 stars=[]
 for name in ['six_axes','eight_diagonals','twelve_icosahedral']:
  for tilt in [0.,15.,30.,45.]:
   n,w=regular_star(name,tilt);op=operators(n,w,.02)
   stars.append(dict(name=name,tilt_deg=tilt,contacts=len(n),affine=metrics(op['C']),central_relaxed=metrics(op['relaxed'])))
  n,w=regular_star(name);op=operators(n,w,.02)
  check('regular star second fabric isotropic '+name,np.max(np.abs(np.einsum('n,ni,nj->ij',w,n,n)-np.eye(3)/3))<1e-12)
  check('regular star central relaxation zero '+name,np.max(np.abs(op['C']-op['relaxed']))<1e-12)
  check('regular star six strain modes positive '+name,metrics(op['relaxed'])['mandel_rank']==6)
 by={x['name']:x for x in stars if x['tilt_deg']==0}
 check('six axes closed ratio',abs(by['six_axes']['central_relaxed']['ratio_Czz_Gxz']-100)<1e-10)
 check('eight diagonal closed ratio',abs(by['eight_diagonals']['central_relaxed']['ratio_Czz_Gxz']-2*(1+.04)/(2+.02))<1e-12)
 n,w=cone_points(90.);iso=operators(n,w,.02)['C']
 n,w=regular_star('twelve_icosahedral');ico=operators(n,w,.02)['relaxed']
 check('icosahedral full fourth moment isotropic',np.max(np.abs(ico-iso))<1e-12)
 check('icosahedral closed ratio',abs(metrics(ico)['ratio_Czz_Gxz']-(6+.08)/(2+.06))<1e-12)
 avg,total=random_star_average('six_axes',.02)
 check('SO3 weights normalized',abs(total-1)<1e-12)
 check('randomized six axes loses cubic anisotropy',np.max(np.abs(avg-iso))<1e-12)
 deps=['計算部品/contact_fabric.py','GPT往復/滑走方向の変形仕事と横解放の分離_20261010/model.md','GPT往復/開放環粒の三次元支持と毛管残水の比較_20261010/results.json']
 results=dict(cycle=109,physical_trials=0,success_probability=None,numpy_version=np.__version__,rows=rows,quadrature=quad,
    illustrative_fixed_rotation_ratio10_cap_deg=angle,regular_stars=stars,random_six_axes=metrics(avg),travel=travel,two_pass_min_speed_m_s=2000/(36*60),
    assumptions=dict(normalization='contact density times squared branch length times axial stiffness = 1; not Pa',branch_length=1.,central_contact_radius=.5,contact_law='preloaded bilateral linear links; incremental strain only; no opening sliding fracture prestress geometric term',
    boundary='outer link endpoints follow homogeneous strain; central grain translation and rotation either clamped or minimized',
    distribution='uniform solid angle in antipodal caps, cap axis tilted from slope normal toward x',basis='engineering strains xx yy zz gamma_yz gamma_xz gamma_xy; Mandel eigenvalues for invariant spectra'),
    dependency_hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in deps})
 validation=dict(status='numerical_and_analytic_consistency_only',physical_validation=False,count=len(checks),checks=checks)
 return results,validation
if __name__=='__main__':
 r,v=calculate()
 if '--check' in sys.argv:
  old=json.loads((D/'results.json').read_text());old.pop('numpy_version',None);new=dict(r);new.pop('numpy_version',None)
  assert old==new and json.loads((D/'validation.json').read_text())==v
  print('Stored result reproduction passed')
 else:
  for name,obj in [('results.json',r),('validation.json',v)]:(D/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
  key=[x for x in r['rows'] if x['kappa']==.02 and ((x['tilt_deg']==0 and x['cap_deg'] in [0,15,30,45,90]) or (x['tilt_deg']==30 and x['cap_deg']==30))]
  print(json.dumps(dict(checks=v['count'],cap_boundary=r['illustrative_fixed_rotation_ratio10_cap_deg'],examples=key),ensure_ascii=False))
