"""H58 internal cam screening; no physical validation or fitted snow curve."""
import csv,json,math
from pathlib import Path
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8')); C=I['cam']; U=1e-6
E=C['beam_E_MPa']*1e6;b=C['beam_width_um']*U;t=C['beam_thickness_um']*U;l=C['beam_length_um']*U
kz=C['beams_per_cam']*E*b*t**3/(4*l**3);X=C['stroke_um']*U
Tau=1-(I['temperature_C']+273.15)/647.096
gamma=.2358*Tau**1.256*(1-.625*Tau)
Acell=I['prior_normal_model']['geometry']['footprint_m2']

def cam(angle,mu,preload=0):
    ang=math.radians(angle);s=math.tan(ang);d=1-mu*s
    if d<=0:return dict(angle_deg=angle,mu=mu,preload_uN=preload/U,status='FORWARD_JAM',ratio_load=None,ratio_return=None,load_work_J=None,return_work_J=None,dissipated_fraction=None,peak_force_N=None,peak_contact_pressure_MPa=None)
    rp=(s+mu)/d; rm=(s-mu)/(1+mu*s)
    factor=preload*X+.5*kz*s*X**2
    load=rp*factor;ret=rm*factor
    Wpeak=preload+kz*X*s
    Npeak=Wpeak/(math.cos(ang)-mu*math.sin(ang))
    return dict(angle_deg=angle,mu=mu,preload_uN=preload/U,status='SELF_RETURN_IDEAL' if rm>0 else 'NO_AUTONOMOUS_RETURN',
      ratio_load=rp,ratio_return=rm,load_work_J=load,return_work_J=ret,
      dissipated_fraction=(load-ret)/load if rm>0 else None,peak_force_N=rp*Wpeak,
      peak_contact_pressure_MPa=Npeak/(C['contact_area_um2']*U**2)/1e6)

def csvout(name,rows):
    with (P/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
    return rows

grid=csvout('cam_regimes.csv',[cam(a,mu) for a in C['angles_deg'] for mu in C['friction_coefficients']])
curves=[]
for mu in [.1,.3,.6,.8]:
    row=cam(45,mu)
    for j in range(101):
        x=X*j/100;W=kz*x
        curves.append(dict(mu=mu,stroke_um=x/U,load_force_uN=W*row['ratio_load']/U,return_force_uN=W*row['ratio_return']/U))
csvout('force_branches.csv',curves)
wet=[]
for a in [35,45]:
    s=math.tan(math.radians(a))
    for mu in [.3,.6,.8]:
        for preload_uN in C['preloads_uN']:
            row=cam(a,mu,preload_uN*U)
            for r_um in I['wet']['bridge_radius_um']:
                Fa=2*math.pi*(r_um*U)*gamma*I['wet']['bridge_cos_contact_angle']
                if row['status']!='SELF_RETURN_IDEAL':
                    xstop=None;gate=False;status=row['status'];rmax=None
                else:
                    raw=(Fa/row['ratio_return']-preload_uN*U)/(kz*s)
                    xstop=min(X,max(0,raw));gate=xstop<=I['wet']['return_tolerance_um']*U
                    status='STUCK_FROM_MAXIMUM_STROKE' if raw>=X else ('RETURNS_WITHIN_ASSUMED_TOLERANCE' if gate else 'RESIDUAL_OFFSET')
                    Ftol=(preload_uN*U+kz*s*I['wet']['return_tolerance_um']*U)*row['ratio_return']
                    rmax=Ftol/(2*math.pi*gamma*I['wet']['bridge_cos_contact_angle'])/U
                wet.append(dict(angle_deg=a,mu=mu,preload_uN=preload_uN,bridge_radius_um=r_um,adhesion_force_uN=Fa/U,
                  residual_offset_um=None if xstop is None else xstop/U,within_assumed_1um=gate,status=status,max_bridge_radius_for_tolerance_um=rmax,
                  peak_projected_shear_kPa=None if row['peak_force_N'] is None else C['cams_per_grain']*row['peak_force_N']/Acell/1000))
csvout('wet_return.csv',wet)
# Same wetted area split into n circular bridges: independent ideal forces add.
bridges=[];r0=10*U
for n in I['wet']['equal_area_bridge_counts']:
    r=r0/math.sqrt(n);Fa=n*2*math.pi*r*gamma
    bridges.append(dict(count=n,radius_each_um=r/U,total_wetted_area_um2=n*math.pi*r*r/U**2,total_adhesion_uN=Fa/U,force_ratio_to_single=math.sqrt(n)))
csvout('bridge_splitting.csv',bridges)
# Sizing tradeoff: making the load-bearing patch as small as the liquid bridge can raise stress.
pressure=[]
for mu in [.3,.6,.8]:
    row=cam(45,mu);rmax=kz*I['wet']['return_tolerance_um']*U*row['ratio_return']/(2*math.pi*gamma)
    Npeak=kz*X/(math.cos(math.pi/4)-mu*math.sin(math.pi/4))
    pressure.append(dict(mu=mu,maximum_single_bridge_radius_um=rmax/U,
       nominal_contact_pressure_MPa=row['peak_contact_pressure_MPa'],
       pressure_if_contact_radius_equals_bridge_radius_MPa=Npeak/(math.pi*rmax*rmax)/1e6))
csvout('contact_pressure_tradeoff.csv',pressure)
# Additional flexures only. Bodies, pads and process losses remain unknown.
G=I['prior_normal_model']['geometry']; bedvol=I['cost']['course_area_m2']*I['cost']['bed_depth_m']
N=bedvol*I['cost']['packing_fraction']/((G['W0_um']*U)**2*G['H0_um']*U)
mgrain=C['cams_per_grain']*C['beams_per_cam']*l*b*t*C['solid_density_kg_m3'];mass=N*mgrain
cost=csvout('additional_flexure_cost.csv',[dict(price_yen_kg=price,additional_flexures_mass_kg=mass,additional_raw_material_cost_yen=mass*price,grain_count=N) for price in I['cost']['material_prices_yen_kg']])
beam=[]
for a in [35,45]:
    for p in C['preloads_uN']:
        z=p*U/kz+X*math.tan(math.radians(a))
        beam.append(dict(angle_deg=a,preload_uN=p,kz_N_m=kz,maximum_vertical_deflection_um=z/U,
          linear_beam_surface_strain_estimate=3*t*z/(2*l*l),thickness_length_ratio=t/l))
csvout('flexure_strain.csv',beam)
# H57-B normal energy, independently integrated without assigning a loss percentage.
B=I['prior_normal_model'];D=B['cell'];R=B['progressive_core'];H=G['H0_um']*U;LL=G['L_um']*U
th0=math.radians(D['theta0_deg']);k=D['E_MPa']*1e6*D['b_um']*U*(D['t_um']*U)**3/(12*D['l_um']*U)
normal=[]
for e in [0,.05,.1,.15]:
    delta=e*H;theta=th0 if e==0 else math.asin((1-e)*(D['a']+math.sin(th0))-D['a'])
    uh=.5*D['hinges']*k*(th0-theta)**2
    uc=.5*R['soft_stiffness_N_m']*delta**2+.5*R['added_stiffness_N_m']*max(0,delta-R['transition_shortening_um']*U)**2
    normal.append(dict(cell_shortening=e,stored_energy_J=uh+uc,model_dissipated_energy_J=0,model_quasistatic_return_energy_J=uh+uc))
csvout('prior_elastic_energy.csv',normal)
checks=[]
def chk(name,ok,observed=None):
    checks.append(dict(name=name,passed=bool(ok),observed=observed))
    if not ok:raise SystemExit('FAILED CHECK: '+name)
def close(a,b,rtol=1e-8,atol=1e-15):return abs(a-b)<=atol+rtol*abs(b)
chk('zero_friction_conserves_energy',close(cam(45,0)['load_work_J'],cam(45,0)['return_work_J']))
chk('water_surface_tension_50C_near_table_value',abs(gamma*1000-67.94)<.02,gamma)
chk('beam_pair_stiffness',close(kz,13.88888888888889))
chk('preload_adds_work_not_free_energy',cam(45,.3,50*U)['load_work_J']>cam(45,.3)['load_work_J'])
chk('45deg_analytic_return_ratio',close(cam(45,.6)['return_work_J']/cam(45,.6)['load_work_J'],((1-.6)/(1+.6))**2))
chk('high_friction_locks_some_angles',cam(35,.8)['status']=='NO_AUTONOMOUS_RETURN')
chk('high_angle_forward_jamming',cam(55,.8)['status']=='FORWARD_JAM')
chk('mu_above_one_no_angle_satisfies_both',not any(cam(a,1.1)['status']=='SELF_RETURN_IDEAL' for a in range(1,90)))
# Independent integration of normal force * path length gives friction work on each branch.
for a,mu in [(35,.3),(45,.6),(45,.8)]:
    theta=math.radians(a);s=math.tan(theta);row=cam(a,mu);dx=X/10000
    fp=sum(mu*(kz*((i+.5)*dx)*s)/(math.cos(theta)-mu*math.sin(theta))*dx/math.cos(theta) for i in range(10000))
    fm=sum(mu*(kz*((i+.5)*dx)*s)/(math.cos(theta)+mu*math.sin(theta))*dx/math.cos(theta) for i in range(10000))
    stored=.5*kz*(X*s)**2
    chk('loading_energy_balance_'+str(a)+'_'+str(mu),close(row['load_work_J'],stored+fp))
    chk('unloading_energy_balance_'+str(a)+'_'+str(mu),close(stored,row['return_work_J']+fm))
    chk('loop_area_is_friction_loss_'+str(a)+'_'+str(mu),close(row['load_work_J']-row['return_work_J'],fp+fm))
for rr in wet:
    if rr['residual_offset_um'] is not None and 0<rr['residual_offset_um']<C['stroke_um']:
        row=cam(rr['angle_deg'],rr['mu'],rr['preload_uN']*U);s=math.tan(math.radians(rr['angle_deg']))
        F=(rr['preload_uN']*U+kz*rr['residual_offset_um']*U*s)*row['ratio_return']
        if not close(F,rr['adhesion_force_uN']*U):raise SystemExit('Wet force balance failed')
chk('residual_offsets_satisfy_force_balance',True)
nom=next(r for r in wet if r['angle_deg']==45 and r['mu']==.8 and r['preload_uN']==0 and r['bridge_radius_um']==10)
pre=next(r for r in wet if r['angle_deg']==45 and r['mu']==.8 and r['preload_uN']==50 and r['bridge_radius_um']==10)
chk('high_loss_can_fail_wet_return',not nom['within_assumed_1um'],nom['residual_offset_um'])
chk('preload_improves_ideal_return_with_force_penalty',pre['within_assumed_1um'] and pre['peak_projected_shear_kPa']>nom['peak_projected_shear_kPa'])
chk('equal_area_subdivision_preserves_area',all(close(r['total_wetted_area_um2'],bridges[0]['total_wetted_area_um2']) for r in bridges))
chk('equal_area_subdivision_increases_force',close(bridges[-1]['force_ratio_to_single'],4))
chk('shrinking_loaded_patch_raises_pressure',all(r['pressure_if_contact_radius_equals_bridge_radius_MPa']>r['nominal_contact_pressure_MPa'] for r in pressure if math.pi*r['maximum_single_bridge_radius_um']**2<C['contact_area_um2']))
chk('additional_mass_conservation',close(mass,N*mgrain))
chk('H57_energy_positive_but_zero_modeled_dissipation',normal[-1]['stored_energy_J']>0 and all(r['model_dissipated_energy_J']==0 for r in normal))
chk('no_physical_probability_assertion',I['physical_tests']==0 and I['success_probability'] is None)
result=dict(cycle=58,physical_tests=0,success_probability=None,kz_N_m=kz,water_surface_tension_N_m=gamma,
    nominal_cam_mu03=cam(45,.3),nominal_cam_mu06=cam(45,.6),nominal_cam_mu08=cam(45,.8),wet_high_friction_no_preload=nom,
    wet_high_friction_with_preload=pre,pressure_tradeoff=pressure,additional_flexures_mass_kg=mass,grain_count=N,
    maximum_H57_stored_normal_energy_J=normal[-1]['stored_energy_J'],algebra_checks=len(checks),
    note='No experimentally measured damping, shear release, return speed, friction law, temperature durability, or safety. Friction loss fraction is NOT probability.')
# Component damping must not be reported as whole-grain damping.
energy_rows=[];required_scale=[];Uc=normal[-1]['stored_energy_J'];ncam=C['cams_per_grain']
for mu in [.3,.6,.8]:
    row=cam(45,mu);Wc=ncam*row['load_work_J'];loss=ncam*(row['load_work_J']-row['return_work_J'])
    energy_rows.append(dict(mu=mu,normal_elastic_energy_J=Uc,cam_input_work_J=Wc,cam_loss_J=loss,
       cam_only_loss_fraction=row['dissipated_fraction'],combined_input_work_J=Uc+Wc,combined_loss_fraction=loss/(Uc+Wc),
       series_peak_projected_pressure_kPa=ncam*I['energy_audit']['cam_lever_ratio']*row['peak_force_N']/Acell/1000))
    for target in I['energy_audit']['total_loss_examples']:
        scale=target*Uc/(Wc*(row['dissipated_fraction']-target)) if row['dissipated_fraction']>target else None
        required_scale.append(dict(mu=mu,example_total_loss_target=target,cam_work_scale_required=scale,
            extra_flexure_mass_if_parallel_replication_kg=None if scale is None else mass*scale,
            status='UNATTAINABLE_WITH_THIS_COMPONENT_LOSS' if scale is None else 'IDEAL_ENERGY_SCALING_NOT_A_BUILDABLE_DESIGN'))
csvout('whole_grain_energy.csv',energy_rows);csvout('damping_scale_cost.csv',required_scale)
chk('component_loss_not_whole_grain_loss',all(r['combined_loss_fraction']<r['cam_only_loss_fraction'] for r in energy_rows))
chk('whole_grain_energy_conservation',all(close(r['combined_input_work_J']-r['cam_loss_J'],Uc+ncam*cam(45,r['mu'])['return_work_J']) for r in energy_rows))
chk('series_force_capacity_not_assumed_100kPa',all(r['series_peak_projected_pressure_kPa']<100 for r in energy_rows))
chk('energy_loss_cannot_exceed_component_limit',required_scale[1]['status'].startswith('UNATTAINABLE'))
for rr in required_scale:
    if rr['cam_work_scale_required'] is not None:
        crow=next(x for x in energy_rows if x['mu']==rr['mu']);s=rr['cam_work_scale_required']
        if not close(s*crow['cam_loss_J']/(Uc+s*crow['cam_input_work_J']),rr['example_total_loss_target']):raise SystemExit('Scaling energy balance failed')
chk('energy_scaling_inverse_is_consistent',True)
result['whole_grain_energy']=energy_rows
result['energy_scale_examples']=required_scale
result['algebra_checks']=len(checks)

# A separate candidate removes sub-micron preload setting by widening the return flexures.
from itertools import product
Q=I['candidate'];candidate=[];Fa=2*math.pi*Q['assumed_bridge_radius_um']*U*gamma
for EE,bb,tt,ll,mu in product(Q['E_MPa_cases'],Q['width_um_cases'],Q['thickness_um_cases'],Q['length_um_cases'],Q['mu_cases']):
    kval=C['beams_per_cam']*EE*1e6*(bb*U)*(tt*U)**3/(4*(ll*U)**3)
    rm=(1-mu)/(1+mu);rp=(1+mu)/(1-mu);stroke=Q['stroke_um']*U
    residual=min(stroke,Fa/(kval*rm))
    candidate.append(dict(E_MPa=EE,width_um=bb,thickness_um=tt,length_um=ll,mu=mu,kz_N_m=kval,
        residual_offset_um=residual/U,peak_projected_shear_kPa=C['cams_per_grain']*kval*stroke*rp/Acell/1000,
        linear_beam_strain=3*(tt*U)*stroke/(2*(ll*U)**2),within_assumed_1um=residual<=U))
csvout('candidate_tolerance.csv',candidate)
worst=max((r for r in candidate if r['mu']<=.6),key=lambda r:r['residual_offset_um'])
failed=max((r for r in candidate if r['mu']==.8),key=lambda r:r['residual_offset_um'])
m_c=mass*Q['beam_width_um']/C['beam_width_um']
chk('candidate_bound_meets_only_assumed_mu_range',worst['residual_offset_um']<=1,worst['residual_offset_um'])
chk('candidate_still_fails_higher_mu',failed['residual_offset_um']>1,failed['residual_offset_um'])
chk('width_increase_doubles_material_only',close(m_c,2*mass))
chk('shorter_stroke_reduces_bending_strain',max(r['linear_beam_strain'] for r in candidate)<.03)
result['candidate']=dict(specification=Q,worst_in_required_mu_range=worst,higher_mu_counterexample=failed,
    additional_flexure_mass_kg=m_c,maximum_computed_beam_strain=max(r['linear_beam_strain'] for r in candidate),
    nominal_material_cost_yen_at_1000_per_kg=m_c*1000,number_of_sensitivity_cases=len(candidate),
    warning='Bounds are not independent trials or an observed manufacturing yield. No 3D fit, wet friction, measured E, fatigue or ski feel validation.')
result['algebra_checks']=len(checks)

(P/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
(P/'validation.json').write_text(json.dumps(dict(scope='energy, force and bookkeeping only',physical_tests=0,checks=checks),indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
