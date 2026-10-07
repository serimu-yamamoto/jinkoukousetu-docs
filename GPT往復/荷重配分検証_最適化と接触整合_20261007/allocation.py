"""Cycle15: force allocation vs contact compatibility. N, mm.
Exact circular Coulomb cones for static relaxation only. Constrained energy
minimization is not itself a sticking/sliding contact law.
"""
from pathlib import Path
import sys,json,math
H=Path(__file__).resolve().parent;ROOT=H.parent.parent
sys.path.insert(0,str(ROOT/'.deps'));sys.path.insert(0,str(H.parent/'骨格変形検証_表面摩擦と自由粒_20261007'))
from elastic_free import build,evaluate,skew,I3,np
import cvxpy as cp
F0=.0009

def matrices(m,mu_top):
 p=m['points'];n=m['normals'];A=np.zeros((7,12));A[:3]=np.tile(I3,(1,4));A[3:6]=np.hstack([skew(v/m['R']) for v in p]);A[6,:3]=n[0];b=np.r_[np.zeros(6),1.]
 if mu_top==0:
  A=np.vstack([A[:6],np.column_stack([I3,np.zeros((3,9))])]);b=np.r_[np.zeros(6),n[0]]
 return A,b

def rigid_fit(m,forces,spring=None):
 d=(m['compliance']@np.array(forces).reshape(12)).reshape(4,3);B=np.vstack([np.column_stack([I3,-skew(p)]) for p in m['points'][1:]]);target=d[1:].reshape(9)
 if spring is not None:target+=spring@np.array(forces).reshape(12)[3:]
 r=np.linalg.lstsq(B,-target,rcond=None)[0];err=(target+B@r).reshape(3,3);nn=np.array(m['normals'][1:]);normal=np.sum(err*nn,axis=1);tangent=err-normal[:,None]*nn
 return dict(rigid_motion=r.tolist(),maximum_stick_mismatch_mm=float(np.linalg.norm(err,axis=1).max()),normal_mismatch_mm=normal.tolist(),tangential_mismatch_mm=tangent.tolist(),contact_displacements_with_rigid_mm=(d+np.array([r[:3]+np.cross(r[3:],p) for p in m['points']])).tolist(),scope='Least-squares mismatch at three fixed support contact points. For springs add the specified elastic contact displacement. Nonzero mismatch is not a valid all-stick solution.')

def audit_forces(m,x):
 ff=np.array(x).reshape(4,3);n=m['normals'];nn=np.sum(ff*n,axis=1);tt=ff-nn[:,None]*n;rat=[]
 for v,z in zip(tt,nn):rat.append(float(np.linalg.norm(v)/z) if z>1e-12 else None)
 return dict(normal_components_normalized=nn.tolist(),friction_ratios=rat,all_compressive=bool(np.min(nn)>=-1e-9))

def optimize_energy(m,mu_top,mu_internal):
 C=(m['compliance']+m['compliance'].T)/2;scale=float(np.trace(C));Q=C/scale;A,b=matrices(m,mu_top);x=cp.Variable(12);eq=A@x==b;cons=[eq];cones=[]
 for j,n in enumerate(m['normals']):
  if j==0 and mu_top==0:continue
  mu=mu_top if j==0 else mu_internal;T=I3-np.outer(n,n);G=np.vstack([mu*n,T]);c=cp.SOC(G[0]@x[j*3:j*3+3],G[1:]@x[j*3:j*3+3]);cons.append(c);cones.append((j,G,c))
 prob=cp.Problem(cp.Minimize(.5*cp.quad_form(x,cp.psd_wrap(Q))),cons);prob.solve(solver='CLARABEL',tol_gap_abs=1e-10,tol_gap_rel=1e-10,tol_feas=1e-10,max_iter=300)
 out=dict(status=prob.status,mu_top=mu_top,mu_internal=mu_internal,scope='Minimum complementary energy within static friction cones; no Coulomb displacement law or automatic physical realizability.')
 if x.value is None:return out
 xx=np.array(x.value);station=Q@xx+A.T@eq.dual_value;cone_duals=[];comp=0.;dual_violation=0.;primal_violation=0.
 for j,G,c in cones:
  s=np.r_[np.array(c.dual_value[0]).reshape(-1),np.array(c.dual_value[1]).reshape(-1)];z=G@xx[j*3:j*3+3];station[j*3:j*3+3]-=G.T@s;comp+=float(s@z);dual_violation=max(dual_violation,np.linalg.norm(s[1:])-s[0]);primal_violation=max(primal_violation,np.linalg.norm(z[1:])-z[0]);cone_duals.append(dict(contact=j,dual=s.tolist()))
 out.update(forces_normalized=xx.reshape(4,3).tolist(),energy_scaled=float(prob.value),energy_scale_compliance=scale,force_audit=audit_forces(m,xx),response=evaluate(m,xx*F0),compatibility=rigid_fit(m,xx*F0),numerical_kkt=dict(equality_residual=float(np.linalg.norm(A@xx-b)),stationarity_residual=float(np.linalg.norm(station)),cone_primal_violation=float(primal_violation),cone_dual_violation=float(dual_violation),complementarity=float(comp)),equality_dual=eq.dual_value.tolist(),cone_duals=cone_duals)
 return out

def sticking(m,kn=None,kt_ratio=.5):
 C=(m['compliance']+m['compliance'].T)/2;Cc=np.zeros((12,12));spring=np.zeros((9,9))
 if kn is not None:
  for j,n in enumerate(m['normals'][1:]):
   cc=np.outer(n,n)/kn+(I3-np.outer(n,n))/(kn*kt_ratio);spring[j*3:j*3+3,j*3:j*3+3]=cc
  Cc[3:,3:]=spring
 A,b=matrices(m,0);Q=C+Cc;scale=float(np.trace(Q));M=np.block([[Q/scale,A.T],[A,np.zeros((len(b),len(b)))] ]);sol=np.linalg.solve(M,np.r_[np.zeros(12),b]);x=sol[:12];forceaudit=audit_forces(m,x)
 mu=max([v for v in forceaudit['friction_ratios'][1:] if v is not None],default=math.inf) if forceaudit['all_compressive'] else None
 return dict(kn_N_mm=kn,kt_over_kn=kt_ratio if kn is not None else None,forces_normalized=x.reshape(4,3).tolist(),force_audit=forceaudit,required_internal_mu=mu,response=evaluate(m,x*F0),compatibility=rigid_fit(m,x*F0,spring),KKT_residual=float(np.linalg.norm(M@sol-np.r_[np.zeros(12),b])),scope='Trial all-stick initial linear response at three support points, top frictionless. Valid only with compression and sufficient friction, and only inside small-deformation range. Contact spring coefficients are independent assumptions.')

def load_fixtures():
 return json.loads((H.parent/'粒間接触検証_自由回転と濡れ_20261007/cluster_results.json').read_text(encoding='utf-8'))['fixtures']

def main():
 rows=[]
 for z in load_fixtures():
  if not z['neighbor_geometry_valid']:continue
  configs=[(z['model'],None)]
  if z['model']=='C3' and z['pose_id']==3:configs.append(('C3-T6-28','T6'))
  for name,brace in configs:
   m=build(z['model'],z['central_rotation'],z['points'],z['normals'],brace=brace,brace_a=.014);energy=[]
   for mut in [0,.1,.3]:
    for mui in [.1,.3,.6]:energy.append(optimize_energy(m,mut,mui))
   sticks=[sticking(m)]+[sticking(m,kn,ratio) for kn in [.01,.1,1.,10.] for ratio in [.2,.5,1.]]
   rows.append(dict(name=name,model=z['model'],pose_id=z['pose_id'],brace=brace,energy_relaxations=energy,sticking_trials=sticks));print(json.dumps({'name':name,'pose':z['pose_id'],'energy_feasible':sum('response' in q for q in energy),'stick_mu':sticks[0]['required_internal_mu']}),flush=True)
 out=dict(physical_tests=0,success_probability=None,force_N=F0,E_MPa=300,nu=.45,fixtures=rows);(H/'allocation_results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
