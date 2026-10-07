"""Independent displacement solve, cone projection, KKT and refinement checks."""
from allocation import *
from contact_audit import cone_projection,kinematic_check
from minimax import operators,solve

def main():
 checks=[];details=[]
 def check(name,value,tol):checks.append(dict(name=name,value=float(value),tolerance=float(tol),passed=bool(value<=tol)))
 dat=json.loads((H/'allocation_results.json').read_text(encoding='utf-8'));mini=json.loads((H/'minimax_results.json').read_text(encoding='utf-8'));orig=load_fixtures()
 for x in dat['fixtures']:
  o=next(q for q in orig if q['model']==x['model'] and q['pose_id']==x['pose_id']);m=build(x['model'],o['central_rotation'],o['points'],o['normals'],brace=x['brace'],brace_a=.014)
  C=(m['compliance']+m['compliance'].T)/2;check(x['name']+str(x['pose_id'])+'_compliance_PSD_relative',max(0.,-np.linalg.eigvalsh(C)[0]/np.linalg.norm(C,2)),1e-9)
  if x['pose_id']==3:
   s=np.tile([1,1,1,1/.24,1/.24,1/.24],len(m['nodes']));K=s[:,None]*m['K']*s[None,:];B=s[:,None]*m['load'][:,3:];force=(s[:,None]*m['load'][:,:3])@np.array([0.,0,-F0]);M=np.block([[K,B],[B.T,np.zeros((9,9))]]);u=np.linalg.solve(M,np.r_[force,np.zeros(9)]);fb=-u[-9:]/F0;expected=np.array(x['sticking_trials'][0]['forces_normalized'])[1:].reshape(9);check(x['name']+'_independent_displacement_reactions',float(np.linalg.norm(fb-expected)/max(np.linalg.norm(expected),1)),2e-6);check(x['name']+'_surface_constraints_mm',float(np.linalg.norm(B.T@u[:-9])),1e-8)
  for j,q in enumerate(x['energy_relaxations']):
   if 'response' not in q:continue
   name=x['name']+str(x['pose_id'])+'_energy_'+str(j);r=q['numerical_kkt'];check(name+'_equilibrium',r['equality_residual'],1e-7);check(name+'_stationarity',r['stationarity_residual'],1e-7);check(name+'_cone',max(r['cone_primal_violation'],r['cone_dual_violation']),1e-7);check(name+'_complementarity',abs(r['complementarity']),1e-7)
  for q in x['sticking_trials']:check(x['name']+str(x['pose_id'])+'_stick_compatibility_'+str(q['kn_N_mm'])+'_'+str(q['kt_over_kn']),q['compatibility']['maximum_stick_mismatch_mm'],1e-8)
 for x in mini['fixtures']:
  for j,q in enumerate(x['cases']):
   name=x['name']+str(x['pose_id'])+'_minimax_'+str(j);check(name+'_primal_violation',q['maximum_constraint_violation'],2e-6);check(name+'_relative_gap',abs(q['duality_gap'])/(1+abs(q['sampled_optimum'])),1e-7);check(name+'_stationarity_force',q['stationarity_force_residual'],2e-4);check(name+'_bound_gradient',q['stationarity_bound_residual'],1e-6);check(name+'_dense_evaluation_relative',abs(q['dense_response']['linear_diagnostic_ratio']/q['sampled_optimum']-1),.002)
 # Reoptimize refined sampling for C3 and T6; do not just resample a fixed force.
 for name,brace in [('C3',None),('C3-T6-28','T6')]:
  o=next(q for q in orig if q['model']=='C3' and q['pose_id']==3);m=build('C3',o['central_rotation'],o['points'],o['normals'],brace=brace,brace_a=.014,interior=65);r=solve(m,operators(m),0,.6);old=next(q for q in mini['fixtures'] if q['name']==name and q['pose_id']==3)['cases'][0];check(name+'_reoptimized_33_65',abs(r['sampled_optimum']/old['sampled_optimum']-1),.002);details.append(dict(name=name,refinement_65=r))
 # Contact geometry refinement from the cycle13 saved first-touch audit.
 ref=json.loads((H.parent/'粒間接触検証_自由回転と濡れ_20261007/numerical_audit.json').read_text(encoding='utf-8'))['refined_C3_pose3'];o=next(q for q in orig if q['model']=='C3' and q['pose_id']==3);m=build('C3',o['central_rotation'],ref['points'],ref['normals']);r=optimize_energy(m,0,.6);k=kinematic_check(m,np.array(r['forces_normalized'])*F0*.01,.6);details.append(dict(name='C3_pose3_refined_contact_geometry',energy=r,kinematic_check_at_9uN=k))
 # Independent SOC projection for positive, lateral, tensile and zero vectors.
 for j,f in enumerate([np.array([.4,.2,1.]),np.array([1.,0,.1]),np.array([.1,.2,-1.]),np.zeros(3)]):
  n=np.array([0.,0,1.]);mu=.3;g=cp.Variable(3);p=cp.Problem(cp.Minimize(cp.sum_squares(g-f)),[cp.norm(g[:2])<=mu*g[2]]);p.solve(solver='CLARABEL',tol_gap_abs=1e-11,tol_gap_rel=1e-11,tol_feas=1e-11,max_iter=300);analytic=cone_projection(f,n,mu);check('cone_projection_'+str(j),float(np.linalg.norm(analytic-g.value)),2e-5)
 result=dict(physical_tests=0,success_probability=None,checks=checks,all_pass=all(q['passed'] for q in checks),details=details);(H/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'checks':len(checks),'all_pass':result['all_pass']}));assert result['all_pass']
if __name__=='__main__':main()
