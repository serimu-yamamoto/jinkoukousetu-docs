"""Minimize the sampled cycle14 linear diagnostic over statically admissible forces.
This is a favorable relaxation, not a realizable contact dynamics model.
"""
from allocation import *

def operators(m):
 p=[];NN=[];MM=[];TT=[];VV=[]
 for e in m['elements']:
  sec=e['sec'];t=e['tangents'];w=np.linalg.solve(e['C'],e['B']@m['U'][e['ids']])*F0;ff=w[:3];mm=w[3:][None,:,:]+np.einsum('ijk,kl->ijl',np.array([skew(q) for q in e['points'][-1]-e['points']]),ff);N=t@ff;T=np.einsum('ij,ijk->ik',t,mm);mb=mm-t[:,:,None]*T[:,None,:];v=ff[None,:,:]-t[:,:,None]*N[:,None,:]
  NN.append(N/(sec['A']*sec['E']*.01));MM.append(mb*sec['a']/(sec['I']*sec['E']*.01));TT.append(T*sec['a']/(sec['J']*sec['G']*.02));VV.append(v*4/(3*sec['A']*sec['G']*.02));p.append(e['points'])
 p=np.vstack(p);D=[];R=[]
 for j in range(12):
  f=np.eye(12)[j]*F0;r=evaluate(m,f,profiles=True);rigid=np.array(r['fitted_rigid_motion']);disp=np.vstack([x['displacements'] for x in r['profiles']]);rot=np.vstack([x['rotations'] for x in r['profiles']]);d=disp-rigid[:3]-np.cross(rigid[3:],p);rot-=rigid[3:];D.append(d/(m['R']*.05));R.append(rot/.05)
 return dict(N=np.vstack(NN),M=np.vstack(MM),T=np.vstack(TT),V=np.vstack(VV),D=np.stack(D,axis=2),R=np.stack(R,axis=2),points=p)

def solve(m,ops,mut,mui):
 A,b=matrices(m,mut);x=cp.Variable(12);bound=cp.Variable();eq=A@x==b;cons=[eq];families=[];conecons=[]
 def vec_norm(M):return cp.norm(cp.reshape(M.reshape(-1,12)@x,(len(M),3),order='C'),axis=1)
 for name,expr in [('normal',cp.abs(ops['N']@x)+vec_norm(ops['M'])),('shear',cp.abs(ops['T']@x)+vec_norm(ops['V'])),('displacement',vec_norm(ops['D'])),('rotation',vec_norm(ops['R']))]:
  cn=expr<=bound;cons.append(cn);families.append((name,cn))
 for j,n in enumerate(m['normals']):
  if j==0 and mut==0:continue
  mu=mut if j==0 else mui;G=np.vstack([mu*n,I3-np.outer(n,n)]);cn=cp.SOC(G[0]@x[j*3:j*3+3],G[1:]@x[j*3:j*3+3]);cons.append(cn);conecons.append((j,G,cn))
 prob=cp.Problem(cp.Minimize(bound),cons);prob.solve(solver='CLARABEL',tol_gap_abs=1e-8,tol_gap_rel=1e-8,tol_feas=1e-9,max_iter=300);xx=np.array(x.value);grad=np.zeros(12);total_lambda=0.;dual_nonneg=0.
 # Numerical KKT check using one valid subgradient at zero. A residual is diagnostic.
 for name,cn in families:
  lam=np.array(cn.dual_value);total_lambda+=float(lam.sum());dual_nonneg=max(dual_nonneg,float(-lam.min()))
  if name in ['normal','shear']:
   S=ops['N'] if name=='normal' else ops['T'];M=ops['M'] if name=='normal' else ops['V'];z=np.einsum('ijk,k->ij',M,xx);nz=np.linalg.norm(z,axis=1);g=np.sign(S@xx)[:,None]*S+np.einsum('ij,ijk->ik',z/np.maximum(nz[:,None],1e-30),M)
  else:
   M=ops['D'] if name=='displacement' else ops['R'];z=np.einsum('ijk,k->ij',M,xx);nz=np.linalg.norm(z,axis=1);g=np.einsum('ij,ijk->ik',z/np.maximum(nz[:,None],1e-30),M)
  grad+=lam@g
 grad+=A.T@eq.dual_value;cone_duals=[]
 for j,G,cn in conecons:
  s=np.r_[np.array(cn.dual_value[0]).reshape(-1),np.array(cn.dual_value[1]).reshape(-1)];grad[j*3:j*3+3]-=G.T@s;cone_duals.append(dict(contact=j,dual=s.tolist()))
 return dict(mu_top=mut,mu_internal=mui,status=prob.status,sampled_optimum=float(prob.value),dual_objective=float(-b@eq.dual_value),duality_gap=float(prob.value+b@eq.dual_value),stationarity_force_residual=float(np.linalg.norm(grad)),stationarity_bound_residual=abs(1-total_lambda),maximum_constraint_violation=max(float(np.max(c.violation())) for c in cons),dual_multiplier_negativity=dual_nonneg,forces_normalized=xx.reshape(4,3).tolist(),force_audit=audit_forces(m,xx),sampled_response=evaluate(m,xx*F0),compatibility=rigid_fit(m,xx*F0),equality_dual=eq.dual_value.tolist(),cone_duals=cone_duals,active_family_weight={name:float(np.sum(cn.dual_value)) for name,cn in families})

def main():
 energy=json.loads((H/'allocation_results.json').read_text(encoding='utf-8'));fixtures=load_fixtures();out=[]
 for z in energy['fixtures']:
  allowed=[q for q in z['energy_relaxations'] if 'response' in q]
  if not allowed:continue
  orig=next(q for q in fixtures if q['model']==z['model'] and q['pose_id']==z['pose_id']);args=(z['model'],orig['central_rotation'],orig['points'],orig['normals']);m=build(*args,brace=z['brace'],brace_a=.014,interior=33);fine=build(*args,brace=z['brace'],brace_a=.014,interior=257);ops=operators(m);res=[]
  for q in allowed:
   r=solve(m,ops,q['mu_top'],q['mu_internal']);r['dense_response']=evaluate(fine,np.array(r['forces_normalized'])*F0);res.append(r)
  out.append(dict(name=z['name'],model=z['model'],pose_id=z['pose_id'],brace=z['brace'],sampled_points=len(ops['points']),cases=res));print(json.dumps({'name':z['name'],'pose':z['pose_id'],'conditions':len(res)}),flush=True)
 (H/'minimax_results.json').write_text(json.dumps(dict(physical_tests=0,success_probability=None,scope='Best sampled linear diagnostic over static force cones. Point refinement is checked separately. Numerical dual objectives are not interval-certified proofs or physical success probabilities.',fixtures=out),indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
