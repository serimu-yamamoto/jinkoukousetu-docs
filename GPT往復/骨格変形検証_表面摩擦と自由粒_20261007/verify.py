"""Numerical/analytical audits; these checks are not physical experiments."""
import json,math
from elastic_free import *
from brace_scan import segment_segment,segment_arc

def main():
 checks=[]
 def check(name,value,limit,relation='<='):
  ok=value<=limit if relation=='<=' else value>=limit;checks.append(dict(name=name,value=float(value),limit=float(limit),relation=relation,pass_=bool(ok)))
 C=json.loads((H.parent/'粒間接触検証_自由回転と濡れ_20261007/cluster_results.json').read_text(encoding='utf-8'));stored=json.loads((H/'elastic_results.json').read_text(encoding='utf-8'));br=json.loads((H/'brace_results.json').read_text(encoding='utf-8'))
 sec=section(.022,300,.45,.85);L=.4;x,w=np.polynomial.legendre.leggauss(64);p=np.column_stack([(x+1)*L/2,np.zeros((64,2))]);cc=compliance(p,np.tile([1.,0,0],(64,1)),w*L/2,np.array([L,0,0]),sec)
 for name,got,target in [('axial',cc[0,0],L/(sec['E']*sec['A'])),('bending_shear',cc[1,1],L**3/(3*sec['E']*sec['I'])+L/(sec['kappa']*sec['G']*sec['A'])),('coupled_rotation',cc[1,5],L**2/(2*sec['E']*sec['I'])),('torsion',cc[3,3],L/(sec['G']*sec['J']))]:check('straight_bar_'+name,abs(got/target-1),1e-11)
 for model in ['R4','C3','S3']:
  fxt=next(v for v in C['fixtures'] if v['model']==model and v['pose_id']==3);case=next(v for v in fxt['force_cases'] if v['mu_top']==(0 if model=='C3' else .1) and v['mu_internal']==.6);f=np.array(case['inner']['forces_normalized'])*.0009;args=(model,fxt['central_rotation'],fxt['points'],fxt['normals']);base=build(*args);a=evaluate(base,f);b=evaluate(build(*args,gauge=3),f);ref=evaluate(build(*args,quad=128,interior=1025),f);twice=evaluate(build(*args,E=600),f)
  for key in ['peak_nominal_normal_stress_MPa','energy_N_mm','max_rigid_removed_displacement_mm','max_rigid_removed_rotation_rad']:check(model+'_gauge_'+key,abs(b[key]/a[key]-1),2e-6)
  check(model+'_quadrature_and_interior_peak_stress',abs(ref['peak_nominal_normal_stress_MPa']/a['peak_nominal_normal_stress_MPa']-1),2e-4);check(model+'_interior_displacement',abs(ref['max_rigid_removed_displacement_mm']/a['max_rigid_removed_displacement_mm']-1),.002);check(model+'_endpoint_refined_mm',ref['endpoint_integration_error_mm'],1.5e-7)
  check(model+'_uniform_E_inverse_deformation',abs(2*twice['max_rigid_removed_displacement_mm']/a['max_rigid_removed_displacement_mm']-1),2e-8);check(model+'_uniform_E_stress_invariance',abs(twice['peak_nominal_normal_stress_MPa']/a['peak_nominal_normal_stress_MPa']-1),2e-8)
  doubled=evaluate(base,2*f);check(model+'_load_linear_stress',abs(doubled['peak_nominal_normal_stress_MPa']/a['peak_nominal_normal_stress_MPa']-2),1e-10)
  print(model,flush=True)
 x=next(v for v in C['fixtures'] if v['model']=='C3' and v['pose_id']==3);f=np.array(next(v for v in x['force_cases'] if v['mu_top']==0 and v['mu_internal']==.6)['inner']['forces_normalized'])*.0009
 args=('C3',x['central_rotation'],x['points'],x['normals']);a=evaluate(build(*args,brace='T6',brace_a=.014),f);b=evaluate(build(*args,brace='T6',brace_a=.014,gauge=3,quad=128,interior=1025),f)
 check('T6_gauge_and_refinement_stress',abs(a['peak_nominal_normal_stress_MPa']/b['peak_nominal_normal_stress_MPa']-1),2e-4);check('T6_gauge_and_refinement_displacement',abs(a['max_rigid_removed_displacement_mm']/b['max_rigid_removed_displacement_mm']-1),.002)
 allres=[x['response'] for x in stored['cases']]+[x['response'] for x in br['cases']]
 check('maximum_nodal_equilibrium_relative',max(x['nodal_equilibrium_relative'] for x in allres),2e-7)
 check('maximum_gauge_reaction_N',max(np.linalg.norm(x['gauge_reaction_force_N']) for x in allres),1e-10)
 check('maximum_gauge_reaction_Nmm',max(np.linalg.norm(x['gauge_reaction_moment_N_mm']) for x in allres),1e-10)
 check('energy_work_relative',max(abs(2*x['energy_N_mm']/x['work_N_mm']-1) for x in allres),2e-7)
 check('total_applied_force_N',max(np.linalg.norm(x['total_applied_force_N']) for x in allres),1e-12)
 check('total_applied_moment_Nmm',max(np.linalg.norm(x['total_applied_moment_N_mm']) for x in allres),1e-12)
 p=np.array;check('crossing_segments',segment_segment(p([-1.,0,0]),p([1.,0,0]),p([0,-1.,0]),p([0,1.,0])),1e-14)
 check('parallel_segments',abs(segment_segment(p([-1.,0,0]),p([1.,0,0]),p([-1,2.,0]),p([1,2.,0]))-2),1e-14)
 arc=(p([1.,0,0]),p([0,1.,0]),0,2*math.pi);lo,hi,_=segment_arc(p([0.,0,-1]),p([0.,0,1]),arc,np.eye(3),np.zeros(3),tol=1e-4);check('segment_arc_brackets_exact_radius_low',lo,.24);check('segment_arc_exact_radius_upper_with_roundoff',hi+1e-14,.24,'>=');check('segment_arc_bracket_gap',hi-lo,1.01e-4)
 out=dict(physical_tests=0,success_probability=None,checks=checks,all_pass=all(x['pass_'] for x in checks));(H/'verification.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({'checks':len(checks),'all_pass':out['all_pass']}));assert out['all_pass']
if __name__=='__main__':main()
