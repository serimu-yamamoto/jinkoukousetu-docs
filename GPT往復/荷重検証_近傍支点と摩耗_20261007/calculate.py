"""Geometry and ideal load budgets. No measured 50 C material law is supplied."""
import json,math,itertools
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent
P=json.loads((H/'inputs.json').read_text(encoding='utf-8'))
G=P['G3'];R,r,re,gap=G['R'],G['r'],G['end_radius'],G['gap']
theta=math.asin((2*re+gap)/(2*R)); Rc=R*math.cos(theta)
rho=P['seat']['rho']; a,ay,b=P['seat']['axes']
rb=P['local_support']['sphere_radius_mm'];s=P['local_support']['center_offset_z_mm']
tau=P['outward_seat_envelope_mm'];beta=Rc-rho

def base_support(n):
    p=np.hypot(n[:,0],n[:,1])
    arc=np.where(n[:,0]>p*math.cos(theta),R*(n[:,0]*math.cos(theta)+np.abs(n[:,1])*math.sin(theta)),R*p)
    guard=R*(n[:,0]*math.cos(theta)+np.abs(n[:,1])*math.sin(theta))+re
    return np.maximum(arc+r,guard)

def inner_support(n):
    return -rho*n[:,0]+np.sqrt((a*n[:,0])**2+(ay*n[:,1])**2+(b*n[:,2])**2)

def bump_support(n):
    return -rho*n[:,0]+s*np.abs(n[:,2])+rb

def lower_function(p):
    root=np.sqrt(b*b+(a*a-b*b)*p*p)
    return np.maximum(beta*p+r-root,s*np.sqrt(1-p*p)+rb-root)

def main():
    # rb=r in this candidate. Each branch is concave, so minima occur at ends
    # or their crossing. The crossing is beta*p = s*sqrt(1-p²).
    assert rb==r and a>=b and beta>0
    pc=s/math.sqrt(beta*beta+s*s)
    candidates=[0,pc,1]
    lb=min(float(lower_function(v)) for v in candidates)
    oldlb=min(r-b,Rc-rho+r-a)
    count=P['direction_count']; i=np.arange(count)
    z=1-2*(i+.5)/count;xy=np.sqrt(1-z*z);angle=i*math.pi*(3-math.sqrt(5))
    n=np.stack([xy*np.cos(angle),xy*np.sin(angle),z],axis=1)
    n=np.concatenate([n,np.eye(3),-np.eye(3)])
    hk=base_support(n);hs=inner_support(n);hb=bump_support(n)
    newgap=np.maximum(hk,hb)-hs
    index=int(np.argmin(newgap))
    wear=[]
    for w in P['wear_radial_mm']:
        wear.append(dict(uniform_radial_loss_mm=w,old_margin_lower_mm=oldlb-tau-w,
                         new_margin_lower_mm=lb-tau-w,
                         backbone_bending_I_ratio=((r-w)/r)**4,
                         equal_bending_moment_stress_ratio=(r/(r-w))**3,
                         same_force_hertz_peak_pressure_ratio=(rb/(rb-w))**(2/3),
                         scope='Centers fixed; all protective round radii shrink uniformly; seat unchanged. Not wear rate or service life.'))
    # Central segment between sphere centers only, ignoring added seat.
    Cbody=2*math.atanh(s/rb)/(math.pi*rb)
    zz=np.linspace(-s,s,10001)
    areas=math.pi*(rb*rb-(s-np.abs(zz))**2)
    Cnum=float(np.trapezoid(1/areas,zz))
    loads=[]
    for F,E in itertools.product(P['loads_N'],P['illustrative_E_MPa']):
        Estar=E/(1-P['poisson_assumption']**2)
        ac=(3*F*rb/(4*Estar))**(1/3)
        indentation=ac*ac/rb
        peak=3*F/(2*math.pi*ac*ac)
        body=F/E*Cbody
        loads.append(dict(force_N=F,assumed_E_MPa=E,rigid_counterface_effective_E_MPa=Estar,
                          body_only_1D_shortening_mm=body,one_contact_Hertz_indent_mm=indentation,
                          two_contacts_plus_body_model_mm=body+2*indentation,
                          contact_radius_mm=ac,contact_radius_over_sphere_radius=ac/rb,
                          Hertz_peak_pressure_MPa=peak,
                          small_contact_screen_pass=ac/rb<=P['hertz_small_contact_a_over_R_limit'],
                          yield_creep_or_finite_body_validated=False,
                          predicts_actual_shield_margin_loss=False))
    volume_pair=2*(4*math.pi*rb**3/3)-math.pi*(4*rb+2*s)*(2*rb-2*s)**2/12
    Vseat=4*math.pi*a*ay*b/3*(1+tau/min(a,ay,b))**3
    Vupper=P['G3_volume_upper_mm3']+Vseat+volume_pair
    bulk=P['cost']['rho_g3_pe_kg_m3']*Vupper/P['G3_volume_upper_mm3']
    C=P['cost'];crf=C['r']*(1+C['r'])**C['T_year']/((1+C['r'])**C['T_year']-1)
    mass=bulk*C['A_m2']*C['h_m']
    eac=crf*C['I_yen']+C['O_yen_year']+(crf+C['lambda_year'])*mass*C['P_yen_kg']
    cap=(C['B_yen_year']-crf*C['I_yen']-C['O_yen_year'])/((crf+C['lambda_year'])*mass)
    comparisons=[]
    for offset in P['support_offsets_for_comparison_mm']:
        cross=offset/math.sqrt(beta*beta+offset*offset)
        branch=lambda p:max(beta*p+r-math.sqrt(b*b+(a*a-b*b)*p*p),offset*math.sqrt(1-p*p)+rb-math.sqrt(b*b+(a*a-b*b)*p*p))
        lower=min(branch(p) for p in [0,cross,1])
        pair=2*(4*math.pi*rb**3/3)-math.pi*(4*rb+2*offset)*(2*rb-2*offset)**2/12
        upper=P['G3_volume_upper_mm3']+Vseat+pair
        rowmass=C['rho_g3_pe_kg_m3']*upper/P['G3_volume_upper_mm3']*C['A_m2']*C['h_m']
        comparisons.append(dict(center_offset_z_mm=offset,certified_lower_with_texture_mm=lower-tau,
            sampled_minimum_with_texture_mm=float(np.min(np.maximum(hk,-rho*n[:,0]+offset*np.abs(n[:,2])+rb)-hs))-tau,
            pair_union_volume_mm3=pair,
            finished_price_cap_yen_kg=(C['B_yen_year']-crf*C['I_yen']-C['O_yen_year'])/((crf+C['lambda_year'])*rowmass),
            scope='Analytic ideal lower bound and finite directional screen; no strength, safety or manufacturing validation.'))
    pcrit=(b*b-(a-beta)**2)/(a*a-b*b-beta*beta)
    scrit=beta*pcrit/math.sqrt(1-pcrit*pcrit)
    # On the entire projected support disk, the ellipsoid's z half-height is
    # >= b*sqrt(1-(rb/min(a,ay))²). If s is no larger, the seat contains both
    # support sphere centers on every such vertical line. The union interval
    # is connected. This is nominal z-monotonicity, not molding validation.
    assert rb<min(a,ay)
    seat_min_halfheight=b*math.sqrt(1-(rb/min(a,ay))**2)
    dx,dy=0,.0299
    rootball=math.sqrt(rb*rb-dx*dx-dy*dy)
    seat_z=b*math.sqrt(1-(dx/a)**2-(dy/ay)**2)
    xglobal=-rho+dx
    # This point projects onto the retained side of the C arc, not its gap.
    radial=math.hypot(xglobal,dy)
    core_z=math.sqrt(max(0,r*r-(radial-R)**2))
    tall_s=max(P['support_offsets_for_comparison_mm'])
    gap_on_line=tall_s-rootball-max(core_z,seat_z)
    axial_mold=dict(sufficient_max_offset_for_no_z_undercut_mm=seat_min_halfheight,
        selected_geometry_no_z_undercut=s<=seat_min_halfheight,
        counterexample=dict(offset_mm=tall_s,line_xy_mm=[xglobal,dy],
          middle_union_interval_z_mm=[-max(core_z,seat_z),max(core_z,seat_z)],
          upper_ball_interval_z_mm=[tall_s-rootball,tall_s+rootball],
          lower_ball_interval_z_mm=[-tall_s-rootball,-tall_s+rootball],
          gap_each_side_mm=gap_on_line),
        scope='Ideal untextured solids; line intersections. No draft, shrinkage, parting, gate, tool life or release-force validation.')
    residual=[]
    for w,sigma in itertools.product(P['wear_radial_mm'],[1,.9,.8]):
        residual.append(dict(uniform_reference_wear_mm=w,common_affine_sigma_min=sigma,
            old_residual_sum_budget_mm=sigma*(oldlb-tau-w),
            new_residual_sum_budget_mm=sigma*(lb-tau-w),
            scope='Sufficient residual displacement budget after common affine alignment; not measured local deformation.'))
    affine=[]
    for name,A in [('common_z_compression_10pct',np.diag([1,1,.9])),('common_z_compression_20pct',np.diag([1,1,.8])),('rotation_90deg',np.array([[0,-1,0],[1,0,0],[0,0,1]]))]:
        amin=float(np.min(np.linalg.svd(A,compute_uv=False)))
        affine.append(dict(name=name,A=A.tolist(),min_singular_value=amin,
                           old_gap_lower_with_texture_mm=amin*(oldlb-tau),new_gap_lower_with_texture_mm=amin*(lb-tau),
                           scope='Common invertible affine map of all geometry including texture; no pressure or material law attached.'))
    checks={
        'continuous_branch_bound_checked':float(np.min(lower_function(np.linspace(0,1,100001))))>=lb-1e-12,
        'sampled_normals_above_analytic_bound':float(np.min(newgap))>=lb-1e-12,
        'adding_support_cannot_reduce_ideal_margin':bool(np.all(newgap>=hk-hs-1e-12)),
        'rod_integral_matches_analytic':abs(Cbody-Cnum)/Cbody<1e-6,
        'wear_stiffness_monotone':all(wear[j+1]['backbone_bending_I_ratio']<wear[j]['backbone_bending_I_ratio'] for j in range(len(wear)-1)),
        'rotation_preserves_margin_bound':math.isclose(affine[-1]['new_gap_lower_with_texture_mm'],lb-tau),
        'overlapping_spheres_volume_bounds':4*math.pi*rb**3/3<volume_pair<2*4*math.pi*rb**3/3,
        'positive_budget_price':cap>0,
        'lower_bound_plateau_identity':math.isclose(beta*pcrit+r-math.sqrt(b*b+(a*a-b*b)*pcrit*pcrit),beta+r-a),
        'selected_offset_reaches_conservative_plateau':s>=scrit and math.isclose(lb,beta+r-a),
        'selected_support_has_sufficient_no_undercut_condition':s<=seat_min_halfheight,
        'tall_support_has_explicit_vertical_gap':gap_on_line>0,
    }
    assert all(checks.values()),checks
    out=dict(scope=P['scope'],physical_test_count=0,physical_success_probability=None,
             geometry=dict(old_bound_mm=oldlb,new_bound_mm=lb,new_bound_with_texture_mm=lb-tau,
                           branch_crossing_p=pc,finite_direction_count=len(n),sampled_minimum_mm=float(newgap[index]),
                           sampled_worst_normal=n[index].tolist(),centered_axial_aperture_radius_lower_mm=min(R-r,R-re,rho-a-tau,rho-rb)),
             uniform_wear=wear,common_affine=affine,
             support_height_comparison=comparisons,
             conservative_bound_plateau_offset_mm=scrit,
             axial_mold_geometry=axial_mold,residual_deformation_budgets=residual,
             central_body_reference=dict(compliance_geometry_factor_per_mm=Cbody,numerical_integral_per_mm=Cnum,
                 min_bare_pair_area_mm2=math.pi*(rb*rb-s*s),
                 E_required_MPa_for_body_only_2um_at_6_48mN=.00648*Cbody/P['body_shortening_budget_mm'],
                 scope='Uniaxial variable-area rod between sphere centers; added seat ignored; end contacts separate; not 3D solid elasticity.'),
             opposed_load_cases=loads,cost_upper=dict(pair_union_volume_mm3=volume_pair,seat_envelope_volume_mm3=Vseat,
                 total_volume_upper_mm3=Vupper,bulk_upper_kg_m3=bulk,mass_kg=mass,EAC_yen_year=eac,finished_price_cap_yen_kg=cap))
    (H/'results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (H/'validation.json').write_text(json.dumps(dict(checks=checks,physical_validation=False),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(geometry=out['geometry'],body=out['central_body_reference'],cost=out['cost_upper'],checks=checks)))

if __name__=='__main__':main()
