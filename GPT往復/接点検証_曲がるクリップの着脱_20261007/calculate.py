"""Cycle 8: geometrically nonlinear curved-strip / rigid-cylinder contact.
Reference model: Curtis, Griffiths & Vella, arXiv:2606.06710v1.
Four-state reduced elastica with two unknown Cartesian reactions.
Only a symmetric, friction-limit, two-end-contact branch is considered.
No stick transition, dynamic jump, finite thickness contact, 3D grain, FEM
or measured 50 C material law is claimed.
"""
import sys,json,math,itertools
from pathlib import Path
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D.parents[1]/'.deps'))
import numpy as np
from scipy.integrate import solve_bvp

def state(alpha,phi,mu,y0,previous=None,tol=2e-7,nodes=81):
    s=np.linspace(0,phi,nodes)
    if previous is None:
        guess=np.vstack((s,np.ones_like(s),np.sin(s),y0+np.cos(s)-1))
        forces=np.array([0.,0.])
    else:
        guess=previous.sol(s);guess[3]+=y0-guess[3,0];forces=previous.p
    def ode(s,z,p):
        th=z[0];H,V=p
        return np.vstack((z[1],H*np.sin(th)+V*np.cos(th),np.cos(th),-np.sin(th)))
    def bc(a,b,p):
        H,V=p;x,y=b[2:4]
        return np.array([a[0],a[2],a[3]-y0,b[1]-1,
                         (x*x+y*y-alpha*alpha)/(2*alpha),
                         (H*(y+mu*x)-V*(x-mu*y))/alpha])
    sol=solve_bvp(ode,bc,s,guess,p=forces,tol=tol,max_nodes=12000)
    sample=np.linspace(0,phi,2001);z=sol.sol(sample);H,V=sol.p
    end=z[:,-1];rad=np.hypot(z[2],z[3]);psi=math.atan2(end[2],end[3])
    fn=(H*end[2]+V*end[3])/alpha
    tangent=(-H*end[3]+V*end[2])/alpha
    bc_error=float(np.max(np.abs(bc(z[:,0],end,sol.p))))
    row=dict(y0=float(y0),F=float(2*V),H=float(H),psi_rad=psi,
        normal_reaction=float(fn),friction_residual=float(tangent-mu*fn),
        max_curvature_change=float(np.max(np.abs(z[1]-1))),
        minimum_centreline_clearance=float(rad.min()-alpha),
        minimum_x=float(z[2].min()),maximum_theta=float(z[0].max()),
        energy=float(np.trapezoid((z[1]-1)**2,sample)),
        max_boundary_residual=bc_error,max_ode_residual=float(np.max(sol.rms_residuals)),
        solver_success=bool(sol.success),mesh_nodes=len(sol.x))
    row['two_contact_admissible']=bool(sol.success and fn>=-1e-7 and rad.min()>=alpha-2e-6 and z[2].min()>=-1e-7)
    return sol,row,z

def curve(alpha,phi,mu,steps=81,tol=2e-7,nodes=81):
    ystart=1-math.cos(phi)+math.sqrt(alpha**2-math.sin(phi)**2)
    # Stop just before midpoint-cylinder contact; do not silently solve a three-contact problem.
    yend=alpha+1e-5
    heights=np.linspace(ystart,yend,steps)
    prior=None;rows=[];shapes=[]
    for i,h in enumerate(heights):
        sol,row,z=state(alpha,phi,mu,h,prior,tol,nodes)
        rows.append(row)
        if i in [0,steps//3,2*steps//3,steps-1]:shapes.append(dict(index=i,x=z[2,::20].tolist(),y=z[3,::20].tolist()))
        if not row['solver_success']:break
        prior=sol
    # Sliding-limit disassembly branch. Starting from final assembly shape is a
    # numerical initial guess, not proof of the physical stick-to-slip transition.
    dis=[]
    if len(rows)==steps and rows[-1]['solver_success']:
        for h in heights[::-1]:
            sol,row,z=state(alpha,phi,-mu,h,prior,tol,nodes)
            dis.append(row)
            if not row['solver_success']:break
            prior=sol
    slip_ok=all(rows[i+1]['psi_rad']>=rows[i]['psi_rad']-1e-6 for i in range(len(rows)-1)) and all(dis[i+1]['psi_rad']<=dis[i]['psi_rad']+1e-6 for i in range(len(dis)-1))
    valid=len(rows)==steps and len(dis)==steps and slip_ok and all(r['two_contact_admissible'] for r in rows+dis)
    fA=max(r['F'] for r in rows);fD=max([-r['F'] for r in dis] or [0])
    endA=rows[-1]['F'];endD=dis[0]['F'] if dis else None
    regime='inadmissible_or_incomplete'
    if valid:
        regime='snap' if endA<0 and endD<0 else ('stick' if endD<0 else 'eject')
    return dict(alpha=alpha,phi_rad=phi,mu=mu,steps=steps,valid_two_contact_branch=valid,
       regime=regime,sliding_direction_screen=slip_ok,assembly_peak=fA,disassembly_peak=max(0.,fD),assembly_end_force=endA,
       disassembly_start_force=endD,max_curvature_change=max(r['max_curvature_change'] for r in rows+dis),
       max_boundary_residual=max(r['max_boundary_residual'] for r in rows+dis),
       max_ode_residual=max(r['max_ode_residual'] for r in rows+dis),
       minimum_clearance=min(r['minimum_centreline_clearance'] for r in rows+dis),
       assembly=rows,disassembly=dis,shapes=shapes)


def brief(c):
    return {k:v for k,v in c.items() if k not in ['assembly','disassembly','shapes']}

def main():
    P=json.loads((D/'inputs.json').read_text(encoding='utf-8'))
    grid=[]
    for alpha,phi,mu in itertools.product(P['grid']['alpha'],P['grid']['phi_rad'],P['grid']['mu']):
        c=curve(alpha,phi,mu)
        grid.append(c)
    ref=next(c for c in grid if c['alpha']==P['reference']['alpha'] and c['phi_rad']==P['reference']['phi_rad'] and c['mu']==P['reference']['mu'])
    fine=curve(1.14,2.1,.2,steps=161,tol=2e-9,nodes=161)
    zero=next(c for c in grid if c['alpha']==1.14 and c['phi_rad']==2.1 and c['mu']==0)
    refinements={k:abs(fine[k]-ref[k])/max(abs(fine[k]),1e-12) for k in ['assembly_peak','disassembly_peak','max_curvature_change']}
    F0=np.array([r['F'] for r in zero['assembly']]);Fback=np.array([r['F'] for r in zero['disassembly'][::-1]])
    h0=np.array([r['y0'] for r in zero['assembly']]);en=np.array([r['energy'] for r in zero['assembly']])
    derivative=-np.gradient(en,h0,edge_order=2)
    energy_error=float(np.max(abs(F0[2:-2]-derivative[2:-2])))
    # Frictionless virtual-work at one interior height with independent energy differencing.
    hi=float(h0[len(h0)//2]);ds=1e-4
    sc,rc,_=state(1.14,2.1,0,hi,tol=1e-10,nodes=161)
    _,rp,_=state(1.14,2.1,0,hi+ds,sc,tol=1e-10,nodes=161)
    _,rm,_=state(1.14,2.1,0,hi-ds,sc,tol=1e-10,nodes=161)
    work_derivative=-(rp['energy']-rm['energy'])/(2*ds)
    work_error=abs(work_derivative-rc['F'])
    tolrows=[]
    T=P['tolerance']
    for Rs,Rc,phi,mu in itertools.product(T['shell_radius_mm'],T['cylinder_radius_mm'],T['phi_rad'],T['mu']):
        c=curve(Rc/Rs,phi,mu,steps=61)
        tolrows.append(dict(shell_radius_mm=Rs,cylinder_radius_mm=Rc,**brief(c)))
    dim=P['dimensional'];Rs=dim['shell_radius_mm'];b=dim['strip_width_mm'];t=dim['strip_thickness_mm'];E=dim['assumed_E_MPa']
    def size(c,b,t,E):
        B=E*b*t**3/12;scale=B/Rs**2
        strain=t/(2*Rs)*c['max_curvature_change']
        return dict(b_mm=b,t_mm=t,E_MPa=E,force_scale_N=scale,assembly_peak_N=c['assembly_peak']*scale,
                    sliding_limit_pull_peak_N=c['disassembly_peak']*scale,maximum_bending_strain=strain,
                    strip_volume_mm3=2*Rs*c['phi_rad']*b*t,thinness=t/Rs,
                    passes_illustrative_screens=bool(t/Rs<=P['scaling']['thinness_screen_t_over_R']+1e-12 and strain<=P['scaling']['illustrative_strain_screen']),
                    scope='Linear elastic inextensible thin-strip scaling. No thickness or contact correction.')
    sized=[]
    for c in grid:
        if c['alpha']==1.14 and c['phi_rad']==2.1:sized.append(dict(mu=c['mu'],endpoint_screen=c['valid_two_contact_branch'],**size(c,b,t,E)))
    scaling=[size(fine,b0,t0,E0) for b0,t0,E0 in itertools.product(P['scaling']['width_mm'],P['scaling']['thickness_mm'],P['scaling']['E_MPa'])]
    C=P['cost'];Vclip=size(fine,b,t,E)['strip_volume_mm3'];crf=C['discount']*(1+C['discount'])**C['years']/((1+C['discount'])**C['years']-1)
    Vroom=C['W2_volume_upper_mm3']*(C['bulk_cap_kg_m3']/C['W2_bulk_kg_m3']-1)
    costs=[]
    for count in C['clip_counts']:
        bulk=C['W2_bulk_kg_m3']*(1+count*Vclip/C['W2_volume_upper_mm3']);mass=bulk*C['area_m2']*C['depth_m']
        annual=C['initial_other_JPY']*crf+C['annual_other_JPY']+mass*C['assumed_price_JPY_kg']*(crf+C['replacement'])
        price=(C['annual_budget_JPY']-C['initial_other_JPY']*crf-C['annual_other_JPY'])/(mass*(crf+C['replacement']))
        costs.append(dict(clip_count=count,bulk_kg_m3=bulk,annual_cost_JPY=annual,price_cap_JPY_kg=price))
    G=P['granular_comparison'];n=C['W2_bulk_kg_m3']/(G['material_density_kg_m3']*C['W2_volume_upper_mm3']*1e-9)
    Fneed=6*G['target_pressure_scale_Pa']/(G['eta']*n*G['z']*G['branch_length_m'])
    contact_budget=dict(number_density_m3=n,force_required_for_illustrative_10kPa_N=Fneed,
       pressure_scale_at_selected_clip_Pa=G['eta']*n*G['z']*size(fine,b,t,E)['sliding_limit_pull_peak_N']*G['branch_length_m']/6,
       force_ratio_required_to_selected=Fneed/size(fine,b,t,E)['sliding_limit_pull_peak_N'])
    selected=size(fine,b,t,E)
    required_thickness=t*(Fneed/selected['sliding_limit_pull_peak_N'])**(1/3)
    contact_budget['naive_thickness_for_target_mm']=required_thickness
    contact_budget['naive_t_over_R']=required_thickness/Rs
    contact_budget['warning']='Thickening extrapolation violates thin-strip assumptions. Not a feasible design.'
    contact_budget['continuous_strip_count_budget']=Vroom/Vclip
    contact_budget['optimistic_parallel_clip_force_N']=Vroom/Vclip*selected['sliding_limit_pull_peak_N']
    contact_budget['required_to_parallel_budget_ratio']=Fneed/contact_budget['optimistic_parallel_clip_force_N']
    contact_budget['parallel_bound_scope']='Only selected shape, thickness, width and E; ignores integration mass and gives all remaining volume to one connection. Not a global design bound.'
    ref_states=dict(seated_assembly_strain=t/(2*Rs)*fine['assembly'][-1]['max_curvature_change'],seated_pull_limit_strain=t/(2*Rs)*fine['disassembly'][0]['max_curvature_change'],fully_released_energy=zero['disassembly'][-1]['energy'])
    valid=[c for c in grid if c['valid_two_contact_branch']]
    checks=dict(retained_solutions_follow_assumed_slip_direction=all(c['sliding_direction_screen'] for c in valid),
       every_rejected_grid_case_has_a_screen_failure=all(not all(r['two_contact_admissible'] for r in c['assembly']+c['disassembly']) or not c['sliding_direction_screen'] for c in grid if not c['valid_two_contact_branch']),
       zero_friction_path_reversible=float(np.max(abs(F0-Fback)))<1e-6,
       zero_friction_energy_gradient_matches_force=work_error<1e-6,
       refined_peaks_and_curvature_agree=max(refinements.values())<.002,
       retained_branches_have_nonnegative_normal_and_no_sampled_penetration=all(r['two_contact_admissible'] for c in valid for r in c['assembly']+c['disassembly']),
       all_bvp_boundary_residuals_small=max(c['max_boundary_residual'] for c in valid)<1e-6,
       high_friction_reference_penetration_detected=not next(c for c in grid if c['alpha']==1.14 and c['phi_rad']==2.1 and c['mu']==.4)['valid_two_contact_branch'],
       added_strip_cost_monotone=all(costs[i]['annual_cost_JPY']<costs[i+1]['annual_cost_JPY'] for i in range(len(costs)-1)))
    validation=dict(checks={k:bool(v) for k,v in checks.items()},refinement_relative_differences=refinements,
       frictionless_force_reversal_max_difference=float(np.max(abs(F0-Fback))),energy_force_derivative_error=work_error,
       physical_test_count=0,physical_success_probability=None,stability_proven=False)
    results=dict(scope=P['model'],grid_summaries=[brief(c) for c in grid],reference_curves=[c for c in grid if c['alpha']==1.14 and c['phi_rad']==2.1],
       refined_reference=fine,tolerance_corners=tolrows,dimensional_examples=sized,dimension_sweep=scaling,
       strip_only_costs=costs,remaining_volume_mm3=Vroom,reference_strip_volume_mm3=Vclip,contact_budget=contact_budget,reference_state_strains=ref_states)
    (D/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (D/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(grid=len(grid),corner_scenarios=len(tolrows),numerical_checks=validation['checks'],contact_budget=contact_budget),ensure_ascii=False),flush=True)
    if not all(checks.values()):raise RuntimeError('Numerical validation failed; inspect validation.json')

if __name__=='__main__':main()
