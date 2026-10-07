"""Contact compatibility and mechanical holding budgets, not a physical trial."""
from allocation import *
from scipy.optimize import lsq_linear,nnls

def kinematic_check(m,forces,mu=.6,tol=1e-6):
 f=np.array(forces).reshape(4,3);d=(m['compliance']@f.reshape(12)).reshape(4,3);B=np.vstack([np.column_stack([I3,-skew(p)]) for p in m['points'][1:]]);active=[];columns=[]
 for j,n in enumerate(m['normals'][1:]):
  ff=f[j+1];fn=float(ff@n);ft=ff-fn*n;t=np.linalg.norm(ft)
  if fn>1e-14 and t/max(fn,1e-30)>=mu-tol:
   col=np.zeros(9);col[3*j:3*j+3]=ft/max(t,1e-30);columns.append(col);active.append(j+1)
 A=np.column_stack([B,*columns]);lower=np.r_[np.full(6,-np.inf),np.zeros(len(columns))];displacement_scale=max(float(np.linalg.norm(d[1:])),1e-20);sol=lsq_linear(A,-d[1:].reshape(9)/displacement_scale,bounds=(lower,np.full(A.shape[1],np.inf)),tol=1e-13,max_iter=1000,lsmr_tol=1e-13);solution=sol.x*displacement_scale;res=A@solution+d[1:].reshape(9)
 # Independent elimination of rigid motion, followed by nonnegative least squares.
 target=d[1:].reshape(9);proj=np.eye(9)-B@np.linalg.pinv(B);D=np.column_stack(columns) if columns else np.zeros((9,0));ss=nnls(proj@D,-proj@target)[0] if columns else np.zeros(0);rr=np.linalg.lstsq(B,-target-D@ss,rcond=None)[0];res2=target+B@rr+D@ss;agreement=abs(np.linalg.norm(res2)-np.linalg.norm(res));
 assert sol.success and agreement<1e-12
 return dict(solver_success=bool(sol.success),normalized_solver_optimality=float(sol.optimality),displacement_scale_mm=displacement_scale,independent_elimination_residual_agreement_mm=float(agreement),allowed_slip_contacts=active,rigid_motion=solution[:6].tolist(),slip_distances_mm=solution[6:].tolist(),relative_displacement_residual_mm=res.reshape(3,3).tolist(),L2_mismatch_mm=float(np.linalg.norm(res)),max_mismatch_mm=float(np.linalg.norm(res.reshape(3,3),axis=1).max()),force_friction_tolerance=tol,scope='Bottom contacts only; top frictionless. Strictly interior friction contacts must stick; near-boundary contacts may slide opposite friction, with nonnegative distance. Local fixed normals and first-order geometry. Giving near-boundary contacts permission to slide is favorable, not exact boundary certification.')

def cone_projection(f,n,mu):
 normal=float(f@n);v=f-normal*n;t=float(np.linalg.norm(v))
 if normal>=0 and t<=mu*normal:return f.copy()
 if normal+mu*t<=0:return np.zeros(3)
 z=(normal+mu*t)/(1+mu*mu);return z*n+mu*z*v/max(t,1e-30)

def main():
 data=json.loads((H/'allocation_results.json').read_text(encoding='utf-8'));mini=json.loads((H/'minimax_results.json').read_text(encoding='utf-8'));original=load_fixtures();kin=[];holding=[]
 for x in data['fixtures']:
  o=next(q for q in original if q['model']==x['model'] and q['pose_id']==x['pose_id']);m=build(x['model'],o['central_rotation'],o['points'],o['normals'],brace=x['brace'],brace_a=.014)
  mm=next((z for z in mini['fixtures'] if z['name']==x['name'] and z['pose_id']==x['pose_id']),None)
  for method,rows in [('energy',x['energy_relaxations']),('minimax',mm['cases'] if mm else [])]:
   for q in rows:
    if q['mu_top']!=0 or 'forces_normalized' not in q:continue
    f=np.array(q['forces_normalized'])*F0*.01;audit=kinematic_check(m,f,q['mu_internal']);kin.append(dict(name=x['name'],pose_id=x['pose_id'],method=method,load_uN=F0*.01*1e6,kinematics=audit,small_load_response=evaluate(m,f)))
  if x['pose_id']!=3:continue
  trial=x['sticking_trials'][0]
  for loadscale in [1.,.01]:
   for mu in [0,.1,.3]:
    ff=np.array(trial['forces_normalized'])*F0*loadscale;items=[]
    for j,n in enumerate(m['normals'][1:]):
     f=ff[j+1];contact=cone_projection(f,n,mu);h=f-contact;dist=float(np.linalg.norm(h));items.append(dict(contact=j+1,ideal_stick_force_N=f.tolist(),compressive_friction_part_N=contact.tolist(),minimum_extra_vector_N=h.tolist(),minimum_extra_force_mN=dist*1000,optimistic_clips=math.ceil(dist/(.01730e-3)) if dist>1e-14 else 0))
    holding.append(dict(name=x['name'],load_mN=F0*loadscale*1000,mu=mu,nominal_diagnostic_ratio=trial['response']['linear_diagnostic_ratio']*loadscale,contacts=items,minimum_ideal_clip_count=sum(v['optimistic_clips'] for v in items),thin_clip_volume_mm3=sum(v['optimistic_clips'] for v in items)*.000105,scope='Distance to compressive friction cone for ideal all-stick trial tractions. Only a favorable force-vector yardstick. The old clip has another geometry and a one-axis limit; this is neither a design nor guaranteed holding. Grain response at 0.9 mN may be outside linear range.'))
 (H/'contact_audit_results.json').write_text(json.dumps(dict(physical_tests=0,success_probability=None,kinematic_checks=kin,holding_budgets=holding),indent=2)+'\n',encoding='utf-8');print(json.dumps({'kinematic_checks':len(kin),'holding_budgets':len(holding)}))
if __name__=='__main__':main()
