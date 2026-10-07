"""Cycle 7: inverse response constraints and an ideal mechanism.
No fitted synthetic-snow material law, DEM, FEM or physical trial is performed.
"""
import sys,json,math,itertools
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parents[1]/'.deps'))
import numpy as np
P=json.loads((H/'inputs.json').read_text(encoding='utf-8'))

def arch(a,h,r,E):
    A=math.pi*r*r;L0=math.hypot(a,h)
    Lcrit=(a*a*L0)**(1/3);qcrit=math.sqrt(Lcrit*Lcrit-a*a)
    def force(w):
        q=h-w;L=np.sqrt(a*a+q*q)
        return 2*E*A*q*(1/L-1/L0)
    def energy(w):
        q=h-w;L=np.sqrt(a*a+q*q)
        return E*A/L0*(L-L0)**2
    peak=float(force(h-qcrit));epsmax=1-a/L0
    # Conservative *ideal Euler* screen uses the largest reference length.
    # Short struts and real hinges invalidate treating this as a safety factor.
    euler_ratio=math.pi**2*r*r/(4*L0*L0*epsmax)
    return dict(a_mm=a,h_mm=h,r_mm=r,E_MPa=E,bar_length_mm=L0,
        peak_N=peak,peak_displacement_mm=h-qcrit,stroke_mm=2*h,
        maximum_axial_strain=epsmax,max_linear_axial_stress_MPa=E*epsmax,
        ideal_euler_conservative_ratio=euler_ratio,bar_slenderness=2*L0/r,
        two_bars_volume_mm3=2*A*L0,energy_barrier_N_mm=float(energy(h)),
        scope='Ideal hinged axial bars, fixed supports. No actual hinge, 50 C law, finite-body buckling or cyclic-life validation.'),force,energy

def main():
    S=P['ski_reference'];HV=S['H_V_N_mm3'];Sf=S['S_f_N_mm2'];N=S['normal_force_N'];L=S['tool_length_mm'];W=S['tool_width_mm']
    ski=[]
    for angle in S['edge_angles_deg']:
        t=math.radians(angle)
        e=N/(HV*L*W) if angle==0 else math.sqrt(2*N*math.tan(t)/(HV*L))
        valid=angle==0 or e<W*math.sin(t)
        assert valid
        ski.append(dict(angle_deg=angle,depth_mm=e,initial_failure_force_N=None if angle==0 else Sf*L*e,
                        partial_contact_formula_valid=valid))
    ref=next(x for x in ski if x['angle_deg']==45)
    peak=ref['initial_failure_force_N'];epeak=ref['depth_mm']
    post=[];u=np.linspace(0,P['post_peak']['evaluation_displacement_mm'],10001)
    for c in P['post_peak']['models']:
        q=c['residual_ratio'];dc=c['decay_length_mm'];U=u[-1]
        f=peak*(q+(1-q)*np.exp(-u/dc))
        work=peak*(q*U+(1-q)*dc*(1-math.exp(-U/dc)))/1000
        numeric=float(np.trapezoid(f,u))/1000
        assert abs(numeric-work)/work<1e-5
        post.append(dict(**c,identical_peak_N=peak,force_after_5mm_N=float(f[-1]),
                         post_peak_work_J=work,numerical_work_J=numeric))
    unload=[]
    for ratio in [0,.3,.7]:
        # Same quadratic initial loading. Unloading is a translated/rescaled
        # quadratic; its positive loop area is an explicit passive counterexample.
        dres=ratio*epeak
        work_in=N*epeak/3/1000
        work_out=N*(epeak-dres)/3/1000
        unload.append(dict(residual_depth_ratio=ratio,residual_depth_mm=dres,
            identical_peak_normal_N=N,work_in_J=work_in,work_returned_J=work_out,
            dissipated_J=work_in-work_out))
    A=P['arch'];selected,F,U=arch(A['a_mm'],A['h_mm'],A['r_mm'],A['E_MPa'])
    sweep=[]
    for ratio,r in itertools.product(A['ratios_h_a'],A['radii_mm']):
        row,_,_=arch(A['a_mm'],A['a_mm']*ratio,r,A['E_MPa']);sweep.append(row)
    w=np.linspace(0,2*A['h_mm'],20001)
    # Exact energy-gradient check and mesh-independent peak, not a fitted curve.
    dh=1e-7;sample=np.linspace(.001,2*A['h_mm']-.001,501)
    fd=(U(sample+dh)-U(sample-dh))/(2*dh)
    force_error=float(np.max(np.abs(fd-F(sample))))
    numeric_peak=float(np.max(F(w)))
    contact=[]
    C=P['contact'];pitch=C['pitch_m']*1000
    for pressure,fraction in itertools.product(C['pressure_Pa'],C['active_fraction']):
        f=pressure/1e6*pitch*pitch/fraction
        contact.append(dict(pressure_Pa=pressure,active_fraction=fraction,force_per_active_contact_N=f,
            max_normal_coupling_for_one_arch=selected['peak_N']/f))
    maxforce=max(x['force_per_active_contact_N'] for x in contact)
    lateral=P['illustrative_lateral_stress_N_mm2']*pitch*pitch
    channels=dict(upper_illustrative_normal_N=maxforce,arch_peak_N=selected['peak_N'],
        alpha_must_be_below=selected['peak_N']/maxforce,
        hypothetical_shear_force_per_full_active_contact_N=lateral,
        beta_must_be_at_least=selected['peak_N']/lateral,
        scope='Necessary load-path inequalities for the chosen reference forces, not actual orientation-dependent transfer coefficients.')
    energy=[];G=P['energy']
    for diss in G['synthetic_dissipation_J_m2']:
        drag=diss*G['width_m'];mu=drag/G['normal_force_N']
        energy.append(dict(dissipation_per_fresh_area_J_m2=diss,additional_drag_N=drag,
            mechanical_mu=mu,total_mu_with_assumed_other=mu+G['reserved_other_mu']))
    ceiling=(G['illustrative_mu_budget']-G['reserved_other_mu'])*G['normal_force_N']/G['width_m']
    R=P['recovery'];recovery=[]
    for v in R['velocities_m_s']:
        travel=R['ski_length_m']/v
        recovery.append(dict(velocity_m_s=v,passage_time_s=travel,
            minimum_exponential_memory_tau_s=travel/(-math.log(R['illustrative_groove_retention_fraction']))))
    tau_max=R['available_reset_s']/(-math.log(1-R['desired_recovery_fraction']))
    hard_tau=(550/1000)/26.2 # 550 kg/s = 0.55 N s/mm
    cost=P['cost'];rr=cost['r'];T=cost['T_year'];crf=rr*(1+rr)**T/((1+rr)**T-1)
    rhocap=(cost['B_yen_year']-crf*cost['I_yen']-cost['O_yen_year'])/((crf+cost['lambda_year'])*cost['A_m2']*cost['h_m']*cost['P_yen_kg'])
    extraV=cost['W2_volume_upper_mm3']*(rhocap/cost['W2_bulk_upper_kg_m3']-1)
    costs=[]
    for count in [0,1,3,6]:
        vol=cost['W2_volume_upper_mm3']+count*selected['two_bars_volume_mm3']
        rho=cost['W2_bulk_upper_kg_m3']*vol/cost['W2_volume_upper_mm3'];mass=rho*cost['A_m2']*cost['h_m']
        cap=(cost['B_yen_year']-crf*cost['I_yen']-cost['O_yen_year'])/((crf+cost['lambda_year'])*mass)
        eac=crf*cost['I_yen']+cost['O_yen_year']+(crf+cost['lambda_year'])*mass*cost['P_yen_kg']
        costs.append(dict(number_bar_pairs=count,bulk_for_bars_only_kg_m3=rho,EAC_yen_year=eac,
            finished_price_ceiling_yen_kg_if_no_other_changes=cap,
            excludes='Hinges, frame, normal stops, reverse-reset mechanism and all changed manufacturing costs. Not finished S1 cost.'))
    checks=dict(energy_gradient_matches_force=force_error<1e-10,
        analytic_peak_matches_dense_curve=abs(numeric_peak-selected['peak_N'])/selected['peak_N']<1e-7,
        arch_both_zero_load_states=abs(float(F(0)))<1e-12 and abs(float(F(2*A['h_mm'])))<1e-12,
        arch_flat_state_is_energy_barrier=U(A['h_mm'])>U(0) and U(A['h_mm'])>U(2*A['h_mm']),
        further_compression_does_not_reverse_reset=float(F(2.2*A['h_mm']))>0,
        uncalibrated_post_peak_curves_have_same_peak=all(math.isclose(x['identical_peak_N'],peak) for x in post),
        normal_loop_energies_are_nonnegative=all(x['dissipated_J']>=-1e-12 for x in unload),
        energy_ceiling_positive=ceiling>0,
        cost_ceiling_decreases_with_added_bars=all(costs[i+1]['finished_price_ceiling_yen_kg_if_no_other_changes']<costs[i]['finished_price_ceiling_yen_kg_if_no_other_changes'] for i in range(len(costs)-1)))
    checks={k:bool(v) for k,v in checks.items()}
    assert all(checks.values()),checks
    out=dict(scope=P['scope'],physical_test_count=0,physical_success_probability=None,
        ski_reference=ski,post_peak_counterexamples=post,normal_unloading_counterexamples=unload,
        ideal_arch=selected,arch_geometry_sweep=sweep,contact_force_budget=contact,load_channel_constraints=channels,
        dissipation_cases=energy,dissipation_ceiling_J_m2=ceiling,
        recovery_memory_cases=recovery,maximum_exponential_tau_for_660s_reset=tau_max,
        hard_snow_local_kelvin_tau_reference_s=hard_tau,
        material_volume_budget=dict(bulk_cap_kg_m3=rhocap,extra_volume_above_W2_mm3=extraV,
            ideal_bar_pairs_that_fill_all_remaining_budget=extraV/selected['two_bars_volume_mm3']),
        cost_bars_only=costs,
        calibration_warning='Any listed curve or fraction agreement is conditional on chosen model inputs; no physical candidate receives a passing score.')
    (H/'results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (H/'validation.json').write_text(json.dumps(dict(checks=checks,max_energy_derivative_force_error_N=force_error,
        analytic_numeric_peak_relative_error=abs(numeric_peak-selected['peak_N'])/selected['peak_N'],physical_validation=False),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(arch=selected,channels=channels,post=post,energy_ceiling=ceiling,extra_volume=extraV,checks=checks)))

if __name__=='__main__':main()
