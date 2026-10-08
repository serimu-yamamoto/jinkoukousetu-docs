"""Cycle 57: energy-consistent screening, NOT a physical/material validation."""
import csv, json, math
from pathlib import Path
P = Path(__file__).resolve().parent
I = json.loads((P/'inputs.json').read_text(encoding='utf-8'))
C = I['cell']; U = 1e-6
W0 = C['W0_um']*U; theta0 = math.radians(C['theta0_deg'])
L = W0/(2*math.cos(theta0)); H0 = 2*L*(C['a']+math.sin(theta0)); A0 = W0**2

def kin(e):
    if e == 0: return theta0, W0, 0.0
    theta = math.asin((1-e)*(C['a']+math.sin(theta0))-C['a'])
    return theta, 2*L*math.cos(theta), e*H0

def mech(e, par=None):
    p = C if par is None else par
    theta, w, d = kin(e); rotation = theta0-theta
    k = p['E_MPa']*1e6*(p['b_um']*U)*(p['t_um']*U)**3/(12*p['l_um']*U)
    energy = .5*p['hinges']*k*rotation**2
    force = p['hinges']*k*rotation/w
    return dict(strain=e,delta_um=d/U,rotation_rad=rotation,width_um=w/U,retreat_one_side_um=(W0-w)/2/U,
                hinge_k_Nm_rad=k,energy_J=energy,force_N=force,projected_pressure_kPa=force/A0/1000,
                hinge_bending_surface_strain=p['t_um']*rotation/(2*p['l_um']),
                thickness_length_ratio=p['t_um']/p['l_um'])

def write_csv(name, rows):
    with (P/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    return rows

curve=write_csv('hinge_force.csv',[dict(modulus_MPa=E,**mech(e,{**C,'E_MPa':E})) for E in I['hinge_moduli_MPa'] for e in I['strain_grid']])
e0=I['core']['design_strain']; baseline=mech(e0); d0=e0*H0; Fc=I['core']['design_pressure_kPa']*1000*A0-baseline['force_N']
hc=I['core']['height_um']*U; Kc=Fc/d0
required=write_csv('required_modulus.csv',[dict(target_pressure_kPa=p,required_hinge_modulus_MPa=C['E_MPa']*p/baseline['projected_pressure_kPa']) for p in I['pressure_targets_kPa']])
core_rows=[]
for b in I['core']['widths_um']:
    area=(b*U)**2; Ereq=Kc*hc/area
    for nu in I['core']['poisson_values']:
        for e in I['strain_grid']:
            theta,w,d=kin(e); cavity=I['core']['nominal_cavity_width_um']*w/W0
            core_width=b*(1+nu*d/hc); gap=(cavity-core_width)/2
            core_rows.append(dict(core_width_um=b,core_modulus_required_kPa=Ereq/1000,poisson=nu,strain=e,
              core_strain=d/hc,cavity_width_um=cavity,expanded_core_width_um=core_width,side_gap_um=gap,
              screen_gap_at_least_10_um=gap>=I['core']['minimum_side_gap_um'],
              pressure_kPa=(Kc*d+mech(e)['force_N'])/A0/1000))
write_csv('core_clearance.csv',core_rows)

def total_pressure(e, retention=1):
    return (retention*Kc*e*H0+mech(e)['force_N'])/A0/1000

def equilibrium(p, retention):
    limit=I['core']['max_screening_strain']
    if total_pressure(limit,retention)<p:
        return dict(target_pressure_kPa=p,core_stiffness_retention=retention,status='BEYOND_TRAVEL_NO_VALID_EQUILIBRIUM',strain=None,retreat_one_side_um=None,capacity_at_travel_kPa=total_pressure(limit,retention))
    lo,hi=0.,limit
    for _ in range(80):
        mid=(lo+hi)/2
        if total_pressure(mid,retention)<p:lo=mid
        else:hi=mid
    e=(lo+hi)/2
    return dict(target_pressure_kPa=p,core_stiffness_retention=retention,status='EQUILIBRIUM_IN_IDEAL_MODEL',strain=e,retreat_one_side_um=mech(e)['retreat_one_side_um'],capacity_at_travel_kPa=total_pressure(limit,retention))
load_rows=write_csv('load_control.csv',[equilibrium(p,r) for p in I['pressure_targets_kPa'] for r in I['core']['stiffness_retention_factors']])
# Gas piston thought experiment: no flexible wall stiffness, no leakage or side expansion.
b=I['core']['candidate_width_um']*U; ac=b*b; p_atm=I['gas']['ambient_Pa']
gas_rows=[]
for assembly in ['operating_temperature_equilibrated','sealed_at_23C_fixed_volume_heated_to_50C']:
    Tfactor=1. if assembly.startswith('operating') else (I['gas']['operating_C']+273.15)/(I['gas']['assembly_C']+273.15)
    for e in I['strain_grid']:
        strain=e*H0/hc; pg=p_atm*Tfactor/(1-strain)-p_atm
        gas_rows.append(dict(assembly_case=assembly,strain=e,core_volume_strain=strain,gauge_pressure_kPa=pg/1000,projected_support_kPa=pg*ac/A0/1000))
write_csv('gas_core.csv',gas_rows)
# Number and volume are re-derived from H57 envelope, never taken from H53 particle count.
volume=I['cost']['course_area_m2']*I['cost']['bed_depth_m']; envelope=W0*W0*H0
N=volume*I['cost']['envelope_packing_fraction']/envelope
cost=[]
for width in I['core']['widths_um']:
    cv=(width*U)**2*hc; mass=N*cv*I['core']['envelope_density_kg_m3']
    for price in I['cost']['core_prices_yen_kg']:
        cost.append(dict(core_width_um=width,core_volume_m3_each=cv,core_fraction_of_cell_envelope=cv/envelope,
                         core_mass_kg_each=cv*I['core']['envelope_density_kg_m3'],cell_count=N,total_core_mass_kg=mass,
                         core_price_yen_kg=price,core_only_cost_yen=mass*price,core_only_cost_yen_m2=mass*price/I['cost']['course_area_m2']))
write_csv('core_cost.csv',cost)
comparisons=write_csv('architecture_comparison.csv',[
    dict(architecture='H56_localized_hinge_proxy',**baseline),
    dict(architecture='distributed_bending_proxy_not_CAD',**mech(e0,I['distributed_hinge']))])
q=I['caging_density_ratio']; critical_theta=-math.acos(math.cos(theta0)/math.sqrt(q))
e_release=1-(C['a']+math.sin(critical_theta))/(C['a']+math.sin(theta0))
checks=[]
def check(name, condition, observed=None):
    checks.append(dict(name=name,passed=bool(condition),observed=observed))
    if not condition:raise SystemExit("FAILED CHECK: "+name)
def close(a,b,rtol=1e-8,atol=1e-14): return abs(a-b)<=atol+rtol*abs(b)
check('origin_has_zero_energy_and_force',mech(0)['energy_J']==0 and mech(0)['force_N']==0)
check('ten_percent_geometry_retained_from_H56',close(baseline['width_um'],461.8802153517006))
check('kinematic_height_consistency',close(2*L*(C['a']+math.sin(kin(e0)[0])),.9*H0))
# Independent numerical differentiation of energy with respect to shortening.
step=1e-6
fd=(mech(e0+step)['energy_J']-mech(e0-step)['energy_J'])/(2*step*H0)
check('force_is_energy_derivative',close(fd,baseline['force_N'],rtol=1e-7),fd)
points=2000; de=e0/points
integral=sum((mech(i*de)['force_N']+mech((i+1)*de)['force_N'])*.5*de*H0 for i in range(points))
check('integrated_force_returns_energy',close(integral,baseline['energy_J'],rtol=1e-6),integral)
check('average_work_force_not_endpoint_force',abs(baseline['energy_J']/d0/baseline['force_N']-1)>.4,baseline['energy_J']/d0/baseline['force_N'])
check('modulus_linear_scaling',close(mech(e0,{**C,'E_MPa':40})['force_N'],2*baseline['force_N']))
check('thickness_cubic_scaling',close(mech(e0,{**C,'t_um':40})['force_N'],8*baseline['force_N']))
check('hinge_strain_independent_of_modulus',close(mech(e0,{**C,'E_MPa':1000})['hinge_bending_surface_strain'],baseline['hinge_bending_surface_strain']))
check('core_plus_hinge_meets_defined_design_point',close(total_pressure(e0),I['core']['design_pressure_kPa']))
check('core_stiffness_positive',Kc>0,Kc)
check('core_modulus_recovers_required_stiffness',all(close(r['core_modulus_required_kPa']*1000*(r['core_width_um']*U)**2/hc,Kc) for r in core_rows))
check('loaded_equilibrium_inverse',all(r['strain'] is None or close(total_pressure(r['strain'],r['core_stiffness_retention']),r['target_pressure_kPa']) for r in load_rows))
check('high_load_exceeds_assumed_travel',all(r['status'].startswith('BEYOND') for r in load_rows if r['target_pressure_kPa']==100))
check('stiffness_loss_can_exceed_travel',equilibrium(20,.5)['strain'] is None)
small=next(r for r in core_rows if r['core_width_um']==260 and r['poisson']==.3 and r['strain']==.15)
large=next(r for r in core_rows if r['core_width_um']==300 and r['poisson']==.3 and r['strain']==.1)
check('narrow_core_keeps_assumed_clearance_at_limit',small['side_gap_um']>=10,small['side_gap_um'])
check('wide_core_fails_clearance_at_design_point',large['side_gap_um']<10,large['side_gap_um'])
check('gas_equilibrated_unloaded_has_zero_gauge_pressure',gas_rows[0]['gauge_pressure_kPa']==0)
check('gas_temperature_preload_is_positive',gas_rows[len(I['strain_grid'])]['gauge_pressure_kPa']>0)
check('envelope_volume_conservation',close(N*envelope,volume*I['cost']['envelope_packing_fraction']))
check('core_mass_conservation',all(close(r['cell_count']*r['core_mass_kg_each'],r['total_core_mass_kg']) for r in cost))
check('core_width_cost_square_scaling',close(cost[0]['total_core_mass_kg']/cost[6]['total_core_mass_kg'],(260/300)**2))
check('fixed_center_release_threshold',close(kin(e_release)[1],W0/math.sqrt(q)))
check('lower_pressure_may_not_open_contacts',equilibrium(5,1)['strain']<e_release)
check('no_physical_or_probability_claim',I['physical_tests']==0 and I['success_probability'] is None)
result=dict(cycle=57,physical_tests=0,success_probability=None,base_commit=I['base_commit'],
    geometry=dict(W0_um=W0/U,H0_um=H0/U,L_um=L/U,footprint_m2=A0),hinge_design_point=baseline,
    core_stiffness_N_m=Kc,core_required_modulus_kPa=Kc*hc/ac/1000,
    distributed_bending_design_point=mech(e0,I['distributed_hinge']),
    fixed_center_release_threshold_strain=e_release,pressure_at_release_threshold_kPa=total_pressure(e_release),
    candidate_core_side_gap_um_at_15pct=small['side_gap_um'],wide_core_side_gap_um_at_10pct=large['side_gap_um'],
    candidate_core_mass_kg=cost[0]['total_core_mass_kg'],gas_design_point=gas_rows[I['strain_grid'].index(.1)],
    maximum_pressure_at_travel_kPa=total_pressure(.15),number_of_algebraic_checks=len(checks),
    interpretation='Uncalibrated screening model, not FEA, DEM, material fitting, snow equivalence, or reliability evidence.')
# Two-stage inverse specification, not a measured nonlinear foam law.
# Stage 2 engages after a prescribed clearance; preserves continuous force but has a tangent jump.
target_width=W0/math.sqrt(q)-I['progressive']['required_pair_gap_um']*U
transition_theta=-math.acos(target_width/(2*L))
e_on=1-(C['a']+math.sin(transition_theta))/(C['a']+math.sin(theta0))
d_on=e_on*H0
Ksoft=(I['progressive']['low_pressure_kPa']*1000*A0-mech(e_on)['force_N'])/d_on
dmax=I['core']['max_screening_strain']*H0
Ksecond=(I['progressive']['high_pressure_kPa']*1000*A0-mech(.15)['force_N']-Ksoft*dmax)/(dmax-d_on)
def progressive_pressure(e, retention=1):
    delta=e*H0
    return (mech(e)['force_N']+retention*(Ksoft*delta+Ksecond*max(0.,delta-d_on)))/A0/1000
progress=[]
for p in [5,20,50,100]:
    for retention in [.5,.75,1]:
        if progressive_pressure(.15,retention)+1e-10<p:
            progress.append(dict(target_pressure_kPa=p,retention=retention,strain=None,retreat_one_side_um=None,status='BEYOND_TRAVEL',capacity_at_limit_kPa=progressive_pressure(.15,retention)))
            continue
        lo,hi=0.,.15
        for _ in range(80):
            mid=(lo+hi)/2
            if progressive_pressure(mid,retention)<p:lo=mid
            else:hi=mid
        e=(lo+hi)/2
        progress.append(dict(target_pressure_kPa=p,retention=retention,strain=e,retreat_one_side_um=mech(e)['retreat_one_side_um'],status='CONSTRUCTED_MODEL_EQUILIBRIUM',capacity_at_limit_kPa=progressive_pressure(.15,retention)))
write_csv('progressive_core.csv',progress)
q_cases=[]
for qq in [1.04,1.09,1.25,1.5]:
    theta_q=-math.acos(math.cos(theta0)/math.sqrt(qq))
    eq=1-(C['a']+math.sin(theta_q))/(C['a']+math.sin(theta0))
    q_cases.append(dict(density_ratio=qq,required_opening_strain=eq,within_travel=eq<=.15,projected_pressure_if_within_kPa=progressive_pressure(eq) if eq<=.15 else None))
write_csv('packing_counterexamples.csv',q_cases)
check('progressive_core_soft_stiffness_positive',Ksoft>0)
check('progressive_core_added_stiffness_positive',Ksecond>0)
check('progressive_core_force_continuity',close(progressive_pressure(e_on-1e-10),progressive_pressure(e_on+1e-10),rtol=1e-7))
check('progressive_core_low_design_point_by_construction',close(progressive_pressure(e_on),5))
check('progressive_core_high_design_point_by_construction',close(progressive_pressure(.15),100))
check('dense_packing_still_cannot_open',q_cases[-1]['within_travel'] is False)
check('softening_still_breaks_high_design_load',progress[-3]['status']=='BEYOND_TRAVEL')
check('progressive_target_has_positive_pair_gap',close((W0/math.sqrt(q)-kin(e_on)[1])/U,I['progressive']['required_pair_gap_um']))
result['progressive_core']=dict(transition_cell_strain=e_on,required_pair_gap_um=I['progressive']['required_pair_gap_um'],soft_stiffness_N_m=Ksoft,added_stiffness_N_m=Ksecond,transition_shortening_um=d_on/U,
    transition_core_strain=d_on/hc,high_to_low_tangent_ratio=(Ksoft+Ksecond)/Ksoft,
    soft_equivalent_modulus_kPa=Ksoft*hc/ac/1000,high_equivalent_tangent_modulus_kPa=(Ksoft+Ksecond)*hc/ac/1000,
    warning='Both design points are inverse specifications, NOT successful physical predictions; kink, hysteresis, buckling, joints and 3D fit are unmodeled.')
result['number_of_algebraic_checks']=len(checks)

(P/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(P/'validation.json').write_text(json.dumps(dict(scope='algebra and bookkeeping only',physical_tests=0,checks=checks),indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
