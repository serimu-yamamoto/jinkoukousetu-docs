"""Deterministic screening, not DEM/FEM, physical tests, or success probabilities.
Run: python calculate.py [--output-dir DIRECTORY]
All unmeasured inputs are in inputs.json. Python standard library only.
"""
from pathlib import Path
import argparse, itertools, json, math

HERE = Path(__file__).resolve().parent
P = json.loads((HERE / 'inputs.json').read_text(encoding='utf-8'))
p = P['particle']
MASS = p['rho_s_kg_m3'] * p['area_mm2'] * p['length_mm'] * 1e-9

def stress_scale(rho_bulk, z, ell_mm, active, force_mN, mass_multiplier=1):
    # n contacts/particle z counts each contact twice; isotropic central forces -> /3.
    # NOT Mohr-Coulomb c, edge resistance Sf, or a validated capacity.
    n = rho_bulk / (MASS * mass_multiplier)
    return active * n * z * (ell_mm * 1e-3) * (force_mN * 1e-3) / 6

def stop_force(stress_MPa, width_mm, t_mm, e_mm):
    # MPa = N/mm2. Ideal axial stress and rectangular bending checks, separately.
    axial = stress_MPa * width_mm * t_mm
    bending = stress_MPa * width_mm * t_mm**2 / (6 * e_mm)
    return min(axial, bending) * 1000

def ramp_factor(angle, mu):
    tangent = math.tan(math.radians(angle))
    denominator = 1 - mu * tangent
    return None if denominator <= 0 else (mu + tangent) / denominator

def lower_success_bound(n, failures, alpha):
    # Exact one-sided Clopper-Pearson bound. Invert P_p(K_fail <= failures)=alpha.
    if n <= failures:
        return 0.0
    lo, hi = 0.0, 1.0
    for _ in range(100):
        q = (lo + hi) / 2
        tail = sum(math.comb(n, k) * (1-q)**k * q**(n-k) for k in range(failures + 1))
        if tail < alpha:
            lo = q
        else:
            hi = q
    return (lo + hi) / 2

def run():
    g=P['contact_grid']
    contact=[]
    for rb,z,l,a in itertools.product(g['rho_bulk'],g['z'],g['ell_mm'],g['active_fraction']):
        contact.append(dict(rho_bulk=rb,z=z,ell_mm=l,active_fraction=a,
            stress_scale_Pa=stress_scale(rb,z,l,a,p['gate_force_mN'])))
    b=P['backstop_grid']; stops=[]
    for s,t,e,m,a in itertools.product(b['design_stress_MPa'], b['thickness_mm'],
            b['eccentricity_mm'], b['mass_multiplier'], b['active_fraction']):
        f=stop_force(s,b['width_mm'],t,e)
        stops.append(dict(design_stress_MPa=s,thickness_mm=t,eccentricity_mm=e,
            mass_multiplier=m,active_fraction=a,force_mN=f,
            stress_scale_Pa=stress_scale(p['rho_bulk_kg_m3'],p['z'],p['ell_mm'],a,f,m)))
    ramps=[]
    for angle,mu in itertools.product(P['ramp_grid']['return_angle_deg'],P['ramp_grid']['mu']):
        f=ramp_factor(angle,mu)
        ramps.append(dict(return_angle_deg=angle,mu=mu,factor=f,
            extraction_force_mN=None if f is None else f*p['gate_force_mN'],
            status='ideal_wedge_lock_or_formula_invalid' if f is None else 'ideal_ramp_finite'))
    c=P['cost']; r=c['discount_rate']; T=c['life_years']
    af=(1-(1+r)**(-T))/r
    available_capital=(c['annual_available_yen']-c['annual_O_yen'])*af-c['initial_nonmaterial_yen']
    costs=[]
    for rho in c['bulk_densities']:
        mass=c['area_m2']*c['depth_m']*rho
        material=mass*c['target_finished_yen_kg']
        pmax=available_capital/(mass*(1+c['replacement_fraction']*af))
        eac=(c['initial_nonmaterial_yen']+material)/af+c['annual_O_yen']+c['replacement_fraction']*material
        costs.append(dict(rho_bulk_kg_m3=rho,mass_kg=mass,material_yen=material,
            initial_including_nonmaterial_yen=c['initial_nonmaterial_yen']+material,
            annual_equivalent_yen=eac,price_cap_yen_kg=pmax))
    max_rho=available_capital/(c['area_m2']*c['depth_m']*c['target_finished_yen_kg']*(1+c['replacement_fraction']*af))
    surface_m2_particle=(p['perimeter_mm']*p['length_mm']+2*p['area_mm2'])*1e-6
    specific_area=surface_m2_particle/MASS
    core_mass=c['area_m2']*c['depth_m']*p['rho_bulk_kg_m3']
    surface=[]
    for fraction,thickness,cost_m2 in itertools.product(P['surface']['treated_fractions'],
            P['surface']['thickness_um'], P['surface']['treatment_yen_m2']):
        s=specific_area*fraction
        ratio=s*thickness*1e-6*P['surface']['coating_rho_kg_m3']
        surface.append(dict(treated_fraction=fraction,thickness_um=thickness,treatment_yen_m2=cost_m2,
            coating_mass_per_core_mass=ratio,coating_added_mass_kg=core_mass*ratio,
            coating_operation_yen_per_core_kg=s*cost_m2,
            note='First-order thin layer; operation price excludes coating purchase unless quote specifies otherwise.'))
    mt=P['maintenance']; travel=mt['course_length_m']/mt['speed_m_s']/mt['utilization']/60
    maintenance=[]
    for recovery in [0,5,10,30,60]:
        budget=mt['closure_minutes']-mt['fixed_minutes']-recovery
        maintenance.append(dict(recovery_min=recovery,total_at_nominal_min=travel+mt['fixed_minutes']+recovery,
            required_speed_m_s=None if budget<=0 else mt['course_length_m']/(mt['utilization']*budget*60)))
    rel=P['reliability']; samples=[]
    for fail in rel['failure_counts']:
        n=fail+1
        while lower_success_bound(n,fail,rel['one_sided_alpha'])<=rel['target_p']:
            n+=1
        samples.append(dict(failures=fail,min_n=n,lower_bound=lower_success_bound(n,fail,rel['one_sided_alpha']),
            previous_n_lower=lower_success_bound(n-1,fail,rel['one_sided_alpha'])))
    buoyancy=[]
    solid_fraction=p['rho_bulk_kg_m3']/p['rho_s_kg_m3']
    for skeletal in [960,1050,1410]:
        bulk=solid_fraction*skeletal
        effective=bulk-solid_fraction*1000
        buoyancy.append(dict(skeletal_density=skeletal,solid_fraction=solid_fraction,dry_bulk_density=bulk,
            fully_saturated_density=bulk+(1-solid_fraction)*1000,
            effective_submerged_bulk_density=effective,
            submerged_normal_weight_Pa=effective*9.81*c['depth_m']*math.cos(math.radians(30))))
    uniform_geom_scale=[]
    for ratio in [0.5,1,2]:
        # Pure similarity: delta,L,b,t all scale with size, n ~ size^-3 and ell~size.
        force=p['gate_force_mN']*ratio**2
        number_density=p['rho_bulk_kg_m3']/(MASS*ratio**3)
        scale=number_density*p['z']*p['ell_mm']*ratio*1e-3*force*1e-3/6
        uniform_geom_scale.append(dict(size_ratio=ratio,force_mN=force,stress_scale_Pa=scale,
            area_per_mass_multiplier=1/ratio,grain_count_multiplier=1/ratio**3))
    return dict(evidence='DETERMINISTIC_CONDITIONAL_CALCULATION_NOT_PHYSICAL_VALIDATION',
        summary=dict(particle_mass_kg=MASS,particle_count=core_mass/MASS,
            baseline_contact_stress_scale_Pa=stress_scale(120,4,.45,1,1.8),
            baseline_quarter_active_stress_scale_Pa=stress_scale(120,4,.45,.25,1.8),
            inverse_force_for_10kPa_at_quarter_active_mN=10_000/stress_scale(120,4,.45,.25,1),
            single_ramp_wet_hold_upper_mN_under_dry_no_lock=p['gate_force_mN']*(0.1+1/0.4)/(1-0.1/0.4),
            dry_no_lock_return_angle_supremum_deg=math.degrees(math.atan(1/0.4)),
            same_packing_mass_increase_max_fraction=max_rho/p['rho_bulk_kg_m3']-1,
            backstop_5um_force_mN=stop_force(3,.3,.06,.005),
            backstop_50um_force_mN=stop_force(3,.3,.06,.05),
            favorable_stop_stress_scale_Pa=stress_scale(120,4,.45,.25,stop_force(3,.3,.06,.005),1.5),
            eccentric_stop_stress_scale_Pa=stress_scale(120,4,.45,.25,stop_force(3,.3,.06,.05),1.5),
            specific_surface_m2_kg=specific_area,bed_particle_surface_m2=specific_area*core_mass,
            annuity_factor=af,max_bulk_density_at_price_500_kg_m3=max_rho,
            travel_minutes=travel,recovery_minutes_available=mt['closure_minutes']-mt['fixed_minutes']-travel,
            independent_ten_gates_each_90_percent=.9**10,
            baseline_28_all_success_bound=.05**(1/28),baseline_29_all_success_bound=.05**(1/29)),
        contact_grid=contact,backstop_grid=stops,ramp_grid=ramps,cost_grid=costs,
        surface_grid=surface,maintenance_grid=maintenance,qualification_examples=samples,
        submerged_grid=buoyancy,geometric_similarity=uniform_geom_scale)

def verify(result):
    checks={}
    def add(name,condition):
        checks[name]=bool(condition)
    add('mass_dimensional_0_02016mg',math.isclose(MASS*1e6,.02016,rel_tol=1e-12))
    add('stress_double_count_and_isotropic_factor',math.isclose(stress_scale(120,4,.45,1,1.8),3214.285714285714,rel_tol=1e-12))
    add('stress_zero_links_is_zero',stress_scale(120,4,.45,0,1.8)==0)
    add('contact_grid_108',len(result['contact_grid'])==108)
    add('backstop_grid_432',len(result['backstop_grid'])==432)
    add('ramp_grid_35',len(result['ramp_grid'])==35)
    add('dry_wedge_75deg_mu04_invalid',ramp_factor(75,.4) is None)
    add('wet_wedge_75deg_mu01_finite',ramp_factor(75,.1) is not None)
    add('single_ramp_counterexample_bound', math.isclose(result['summary']['single_ramp_wet_hold_upper_mN_under_dry_no_lock'],6.24) and result['summary']['single_ramp_wet_hold_upper_mN_under_dry_no_lock']<result['summary']['inverse_force_for_10kPa_at_quarter_active_mN'])
    add('near_support_54mN',math.isclose(stop_force(3,.3,.06,.005),54))
    add('eccentric_10_8mN',math.isclose(stop_force(3,.3,.06,.05),10.8))
    add('similarity_stress_invariant',all(math.isclose(x['stress_scale_Pa'],3214.285714285714,rel_tol=1e-12) for x in result['geometric_similarity']))
    add('29_all_pass_bound_exact',math.isclose(lower_success_bound(29,0,.05),.05**(1/29),rel_tol=1e-12))
    add('28_insufficient_29_sufficient',lower_success_bound(28,0,.05)<.9<lower_success_bound(29,0,.05))
    add('qualification_minimal_n',all(x['previous_n_lower']<=.9<x['lower_bound'] for x in result['qualification_examples']))
    add('price_cap_reconstructs_annual_budget',all(math.isclose((P['cost']['initial_nonmaterial_yen']+x['mass_kg']*x['price_cap_yen_kg'])/result['summary']['annuity_factor']+P['cost']['annual_O_yen']+P['cost']['replacement_fraction']*x['mass_kg']*x['price_cap_yen_kg'],P['cost']['annual_available_yen'],rel_tol=1e-12) for x in result['cost_grid']))
    add('fully_saturated_PE_buoyant_POM_heavier',result['submerged_grid'][0]['effective_submerged_bulk_density']<0<result['submerged_grid'][2]['effective_submerged_bulk_density'])
    add('all_numbers_finite', 'NaN' not in json.dumps(result,allow_nan=False))
    if not all(checks.values()):
        raise AssertionError(checks)
    return dict(status='ALL_ARITHMETIC_CHECKS_PASSED',checks=checks,
        limitation='Checks verify equations, limiting cases, and bookkeeping only; no physical model validation.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--output-dir',type=Path,default=HERE)
    args=parser.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=True)
    result=run(); verified=verify(result)
    for name,data in [('results.json',result),('validation.json',verified)]:
        (args.output_dir/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(summary=result['summary'],qualification=result['qualification_examples'],validation=verified['status']),ensure_ascii=False,indent=2))
