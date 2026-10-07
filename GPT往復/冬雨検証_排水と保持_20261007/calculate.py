"""Analytical limits only. Run with Python 3.12; standard library only."""
import itertools
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
I = json.loads((HERE / 'inputs.json').read_text(encoding='utf-8'))
g, rw, phi = I['g_m_s2'], I['water_density_kg_m3'], I['solid_fraction']
eps = 1 - phi
C = I['cost']
crf = C['r'] * (1+C['r'])**C['T_year'] / ((1+C['r'])**C['T_year']-1)
mass_cap = (C['B_yen_year']-crf*C['I_yen']-C['O_yen_year']) / (C['P_yen_kg']*(crf+C['lambda_year']))
bulk_cap = mass_cap / (C['A_m2']*C['h_m'])
solid_cap = bulk_cap/phi

def eac(rho):
    mass = rho*phi*C['A_m2']*C['h_m']
    return crf*(C['I_yen']+C['P_yen_kg']*mass)+C['O_yen_year']+C['lambda_year']*C['P_yen_kg']*mass

materials = []
buoyancy = []
for m in I['materials']:
    rho = m['rho_kg_m3']
    # alpha is trapped air / initial pore volume. Flooded hydrostatic idealization.
    alpha_limit = phi*(rho/rw-1)/eps
    materials.append(dict(m, bulk_kg_m3=rho*phi, EAC_yen_year=eac(rho),
                          neutral_air_pore_fraction=alpha_limit,
                          no_air_submerged_force_vertical_N_m2=(rho-rw)*phi*g*C['h_m']))
    for alpha in I['air_pore_fraction']:
        force = g*C['h_m']*((rho-rw)*phi-rw*eps*alpha)
        buoyancy.append(dict(id=m['id'], alpha=alpha, net_downward_vertical_N_m2=force))

air_budget = []
for alpha in I['air_pore_fraction']:
    rho_min = rw*(1+eps*alpha/phi)
    air_budget.append(dict(alpha=alpha, neutral_solid_density_kg_m3=rho_min,
                          neutral_bulk_density_kg_m3=phi*rho_min,
                          EAC_yen_year=eac(rho_min),
                          density_window_exists_at_assumed_cost=rho_min <= solid_cap))

capillary = []
P = I['capillary']
for theta, radius in itertools.product(P['contact_angle_deg'], P['radius_um']):
    signed_suction = 2*P['gamma_N_m']*math.cos(math.radians(theta))/(radius*1e-6)
    capillary.append(dict(theta_deg=theta, radius_um=radius,
                          signed_suction_Pa=signed_suction,
                          positive_entry_head_mm=max(0,-signed_suction)/(rw*g)*1000))

rain = []
R = I['rain']
for rate, capacity in itertools.product(R['intensity_horizontal_mm_h'], R['assumed_normal_outlet_capacity_mm_h']):
    qin = rate*math.cos(math.radians(R['slope_deg']))/1000
    qcap = capacity/1000
    s0 = R['normal_depth_m']*R['initial_water_fraction']
    sres = R['normal_depth_m']*R['residual_water_fraction']
    smax = R['normal_depth_m']*eps
    raw = s0+(qin-qcap)*R['duration_h']
    send = max(sres,min(smax,raw))
    overflow = max(0,raw-smax)
    actual_out = s0+qin*R['duration_h']-send-overflow
    drain_time = (send-sres)/qcap*60
    rain.append(dict(horizontal_rain_mm_h=rate, normal_capacity_mm_h=capacity,
                     inflow_m3_h=qin*R['area_slope_m2'], inflow_L_s=qin*R['area_slope_m2']/3.6,
                     end_stored_water_mm=send*1000, overflow_mm=overflow*1000,
                     end_water_volume_fraction=send/R['normal_depth_m'],
                     ideal_postrain_drain_to_residual_min=drain_time,
                     balance_error_m=s0+qin*R['duration_h']-send-overflow-actual_out))

snow = []
S=I['snow']
sin_a=math.sin(math.radians(S['slope_deg']))
cos_a=math.cos(math.radians(S['slope_deg']))
for h,rho,mu,u in itertools.product(S['normal_depth_m'], S['density_kg_m3'], S['friction_assumption'], S['pore_pressure_Pa']):
    drive=rho*g*h*sin_a
    normal=rho*g*h*cos_a
    # Loss of compression changes failure mode; do not silently clamp to zero.
    effective=normal-u
    snow.append(dict(normal_snow_depth_m=h, snow_density_kg_m3=rho, assumed_mu=mu,
                     pore_pressure_Pa=u, driving_Pa=drive, total_normal_Pa=normal,
                     effective_normal_Pa=effective,
                     extra_interface_shear_needed_Pa=max(0,S['illustrative_force_factor']*drive-mu*effective) if effective>0 else None,
                     compressive_contact_assumption_valid=effective>0))

apertures=[dict(aggregate_D_mm=d, local_inscribed_opening_D_mm=(2/math.sqrt(3)-1)*d,
                bounding_sphere_fits=(2/math.sqrt(3)-1)*d>I['filter']['bounding_grain_D_mm'])
           for d in I['filter']['equal_sphere_D_mm']]

out=dict(scope=I['scope'], physical_test_count=0, physical_success_probability=None,
         constants=dict(solid_fraction=phi, porosity=eps, CRF=crf), materials=materials,
         buoyancy=buoyancy, air_budget=air_budget,
         cost_bound=dict(max_bulk_density_kg_m3=bulk_cap,max_solid_density_kg_m3=solid_cap,
                         max_neutral_air_pore_fraction=phi*(solid_cap/rw-1)/eps),
         capillary=capillary, rain=rain, winter_shear_demand=snow, local_filter_apertures=apertures)
out['additional_budgets'] = {
    'postrain_11min_capacity_required_mm_h_at_200mm_h_rain':
        (R['normal_depth_m']*(R['initial_water_fraction']-R['residual_water_fraction'])
         +.2*math.cos(math.radians(R['slope_deg']))*R['duration_h'])
        /(R['duration_h']+11/60)*1000,
    'G3_hole_ideal_radius_um_not_packed_pore': 220,
    'illustrative_106deg_220um_entry_head_mm':
        -2*P['gamma_N_m']*math.cos(math.radians(106))/(220e-6)/(rw*g)*1000,
    'max_angle_for_5mm_head_at_220um_deg':
        math.degrees(math.acos(-rw*g*.005*220e-6/(2*P['gamma_N_m']))),
    'end_guard_2um_uniform_radial_removal_worst_path_remaining_overlap_um':
        90-(90+30)/math.sqrt(2)-2*2,
    'strand_2um_uniform_radial_removal_EI_ratio': (56/60)**4,
}

checks={
    'solid_and_void_conserve_volume': math.isclose(phi+eps,1),
    'PE_net_buoyancy_without_air': materials[0]['no_air_submerged_force_vertical_N_m2']<0,
    'neutral_density_balance': all(abs((x['neutral_solid_density_kg_m3']-rw)*phi-rw*eps*x['alpha'])<1e-9 for x in air_budget),
    'cost_limit_reproduces_budget': math.isclose(eac(solid_cap),C['B_yen_year'],rel_tol=1e-12),
    'rain_mass_conservation': all(abs(x['balance_error_m'])<1e-12 for x in rain),
    'entry_head_inverse_radius': math.isclose(capillary[-1]['positive_entry_head_mm']/capillary[-5]['positive_entry_head_mm'],20/250),
    'invalid_snow_contact_not_reported_as_stable': all(x['extra_interface_shear_needed_Pa'] is None for x in snow if not x['compressive_contact_assumption_valid']),
    'cost_increases_with_air_density_compensation': all(air_budget[i+1]['EAC_yen_year']>air_budget[i]['EAC_yen_year'] for i in range(len(air_budget)-1)),
}
assert all(checks.values()),checks
for name,obj in [('results.json',out),('validation.json',dict(algebra_checks=checks,physical_validation=False))]:
    (HERE/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(checks=checks,cost_bound=out['cost_bound'],materials=materials,air_budget=air_budget),ensure_ascii=False))
