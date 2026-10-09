from pathlib import Path
import sys,json,math,hashlib,os
import numpy as np
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
sys.path.insert(0,os.environ.get('FIRN_COMMON_LIB',str(R/'計算部品')))
import flared_ligament as f
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def ck(name,value):
    assert value,name
    checks.append(name)
coords=np.array([[0.,0.],[.5,0.],[.5,2.],[0.,2.]])
ke,_=f.element(coords,0.)
ck('Q4 symmetry',np.max(abs(ke-ke.T))<1e-13)
for axis in [0,1]:
    u=np.zeros(8);u[axis::2]=1
    ck('rigid translation '+str(axis),np.linalg.norm(ke@u)<1e-13)
rot=np.array([[-y,x] for x,y in coords]).ravel()
ck('rigid rotation',np.linalg.norm(ke@rot)<1e-13)
ux=np.array([[x,0.] for x,y in coords]).ravel()
uy=np.array([[0.,y] for x,y in coords]).ravel()
ck('constant axial energy',abs(.5*uy@ke@uy-.5)<1e-12)
ck('constant transverse energy',abs(.5*ux@ke@ux-.5)<1e-12)
exact=f.solve(2.,.1,.1,0.,8,40,True)
ck('independent uniform axial stiffness E*A/h',abs(exact['normal']['stiffness']-.25)<1e-10)
step=f.integrals(rho=0)
ck('step axial independent formula',abs(step['axial_ratio']-1/(.1+.9*4/3))<1e-12)
ck('step bending independent formula',abs(step['bending_ratio']-1/(.1**3+(1-.1**3)*(4/3)**3))<1e-12)
ck('step flow independent formula',abs(step['local_flow_resistance_ratio']-.85)<1e-12)
A=(.125+.25)/2;B=(.25-.125)/2
C=.25**3/2*(2*A*A+B*B)/(2*(A*A-B*B)**2.5)
analytical=[]
for tau,rho in [(.1,0),(.1,.1),(.05,.2)]:
    r=f.integrals(tau,rho)
    ck('cosine flow '+str((tau,rho)),abs(r['local_flow_resistance_ratio']-(4*tau+C*rho+.5*(1-tau-rho)))<1e-11)
    ck('volume '+str((tau,rho)),abs(r['volume_ratio']-(.75+.25*tau+.125*rho))<1e-12)
    r.update(tau=tau,rho=rho)
    analytical.append(r)
rows=[];baseline={}
for height in [.5,2.]:
    for nu in [.3,.45]:
        for mesh in [(8,40),(16,80),(32,160)]:
            b=f.solve(height,.1,.1,nu,*mesh,uniform=True)
            baseline[(height,nu,mesh)]=b
            for tau,rho in [(.1,.1),(.05,.2)]:
                r=f.solve(height,tau,rho,nu,*mesh)
                for name in ['normal','lateral']:
                    ck('residual '+str((height,nu,mesh,tau,rho,name)),r[name]['relative_free_residual']<1e-8)
                    ck('balance '+str((height,nu,mesh,tau,rho,name)),r[name]['relative_force_balance']<1e-8)
                    ck('energy '+str((height,nu,mesh,tau,rho,name)),
                       abs(2*r[name]['energy']/(r[name]['stiffness']*(1e-6*height)**2)-1)<1e-8)
                rows.append(dict(height=height,nu=nu,nx=mesh[0],ny=mesh[1],tau=tau,rho=rho,
                    normal_ratio=r['normal']['stiffness']/b['normal']['stiffness'],
                    lateral_ratio=r['lateral']['stiffness']/b['lateral']['stiffness'],
                    baseline=b,flared=r))
convergence=[]
for height in [.5,2.]:
 for nu in [.3,.45]:
  for tau,rho in [(.1,.1),(.05,.2)]:
   pair=[r for r in rows if (r['height'],r['nu'],r['tau'],r['rho'])==(height,nu,tau,rho) and r['nx'] in [16,32]]
   pair.sort(key=lambda r:r['nx']);a,b=pair
   dif={k:abs(b[k]-a[k])/b[k] for k in ['normal_ratio','lateral_ratio']}
   convergence.append(dict(height=height,nu=nu,tau=tau,rho=rho,relative_changes=dif))
   ck('ratio convergence '+str((height,nu,tau,rho)),max(dif.values())<.025)
# Cycle103's normal-contact pattern scaled uniformly; not FE contact recomputation.
old_delta=1.1875;new_delta=1.032967032967033;new_span=.032967032967033
for r in rows:
    if r['nx']!=32:continue
    k=r['normal_ratio'];i=f.integrals(r['tau'],r['rho'])
    r['scaled_103_proxy']=dict(delta_max=new_delta/k,delta_span=new_span/k,
        E_factor_to_match_old_max_delta=new_delta/(k*old_delta),
        E_factor_to_restore_normal_stiffness=1/k,
        E_factor_to_restore_lateral_stiffness=1/r['lateral_ratio'])
    r['maximum_channel_wall_slope']=.125*math.pi/(4*r['rho']*r['height'])
    r['local_flow_resistance_ratio']=i['local_flow_resistance_ratio']
    r['volume_ratio']=i['volume_ratio']
out=dict(cycle=104,physical_trials=0,success_probability=None,analytical=analytical,
         rows=rows,convergence=convergence,source_module_sha256=sha(R/'計算部品/flared_ligament.py'),
         cosine_transition_resistance_coefficient=C,
         reference94_sha256=sha(R/'GPT往復/弾性根元と高温復元骨格の検証_20261009/reproduce.py'))
validation=dict(status='passed',count=len(checks),checks=checks,
    physical_trials=0,success_probability=None,
    mesh_study='ratios between final two meshes; not a continuum error bound',
    limitations=['plane stress, small strain, fixed root; not granular contact',
                 'local Poiseuille resistance omits access and transition dissipation',
                 'E and nu at 50 C unmeasured','no friction fatigue wear clogging or safety tests'])
if '--check' in sys.argv:
    old=json.loads((D/'results.json').read_text())
    def compare(a,b):
        if isinstance(a,dict):assert a.keys()==b.keys();[compare(a[k],b[k]) for k in a]
        elif isinstance(a,list):assert len(a)==len(b);[compare(x,y) for x,y in zip(a,b)]
        elif isinstance(a,(int,float)) and not isinstance(a,bool):assert math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-12),(a,b)
        else:assert a==b,(a,b)
    compare(out,old)
    assert validation==json.loads((D/'validation.json').read_text())
else:
    for name,obj in [('results.json',out),('validation.json',validation)]:
        (D/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps(dict(checks=len(checks),states=len(rows),physical_trials=0,
 best_mesh=[{k:v for k,v in r.items() if k not in ['baseline','flared']} for r in rows if r['nx']==32]),ensure_ascii=False))
