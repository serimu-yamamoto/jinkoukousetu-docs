"""Reproducible concept screens, not calibrated ski or manufacturing predictions.
Run: python calculate.py (stdlib only). All dimensions use SI units.
"""
import json, math, itertools
from pathlib import Path
D=Path(__file__).resolve().parent
p=json.loads((D/'inputs.json').read_text(encoding='utf-8'))
e=p['economic']; a=e['area_m2']; h=e['thickness_m']; g=9.81
AF=(1-(1+e['discount'])**(-e['years']))/e['discount']
net=(e['annual_contribution_yen']-e['annual_other_yen'])*AF-e['nonmaterial_initial_yen']
assert AF>0 and net>0
prices=[]; cases=[]
for rho,lam in itertools.product(e['bulk_densities_kg_m3'],e['replacement_rates']):
    M=a*h*rho
    prices.append(dict(rho=rho,replacement=lam,mass_kg=M,Pmax_yen_kg=net/(M*(1+lam*AF))))
    for price in e['finished_prices_yen_kg']:
        initial=M*price+e['nonmaterial_initial_yen']
        annual=initial/AF+e['annual_other_yen']+M*price*lam
        cases.append(dict(rho=rho,replacement=lam,price=price,mass_kg=M,material_initial_yen=M*price,total_initial_yen=initial,equivalent_annual_yen=annual,annual_margin_yen=e['annual_contribution_yen']-annual))
z=p['geometry']; b=z['beam_width_m']; E=z['illustrative_modulus_at_50C_Pa']; L=z['beam_length_m']; t=z['beam_thickness_m']; delta=z['beam_deflection_m']
def beam(E,t,L,delta):
    F=E*b*t**3*delta/(4*L**3)
    stress=6*F*L/(b*t*t)
    return dict(E=E,t=t,L=L,delta=delta,F_N=F,stress_Pa=stress,delta_over_L=delta/L,small_deflection_screen=delta/L<=0.1)
base=beam(E,t,L,delta); beam_grid=[]
for values in itertools.product(z['modulus_grid_Pa'],z['thickness_grid_m'],z['length_grid_m'],z['deflection_grid_m']):
    item=beam(*values)
    item['assumed_stress_cap_screens']={str(cap):item['stress_Pa']<=cap for cap in z['assumed_reversible_stress_limits_Pa']}
    beam_grid.append(item)
particle_volume=z['polymer_cross_section_m2']*z['cut_length_m']; particle_mass=particle_volume*z['solid_density_kg_m3']
w=p['wind']; q=0.5*w['air_density']*w['speed_m_s']**2; projection=math.pi*z['outer_diameter_m']**2/4
force=q*w['Cd']*projection
wind_rows=[]
for rho,cp in itertools.product([100,180,300],w['Cnet']):
    dry_normal=rho*h*g*math.cos(math.radians(w['slope_degrees']))
    wind_rows.append(dict(rho=rho,Cnet=cp,net_suction_Pa=q*cp,dry_normal_weight_Pa=dry_normal,unbalanced_uplift_Pa=max(0,q*cp-dry_normal)))
production=[]; pr=p['production']
for holes,u in itertools.product(pr['hole_counts'],pr['line_speed_m_s']):
    gross=holes*u*z['polymer_cross_section_m2']*z['solid_density_kg_m3']*3600
    good=gross*pr['good_yield']
    production.append(dict(holes=holes,line_speed_m_s=u,gross_kg_h=gross,good_kg_h=good,cut_frequency_Hz=u/z['cut_length_m'],hours_for_162t=162000/good,processing_yen_kg=pr['line_charge_yen_h']/good,finished_price_scenarios={str(feed):feed/pr['good_yield']+pr['line_charge_yen_h']/good+pr['delivery_qc_yen_kg'] for feed in pr['feed_price_scenarios_yen_kg']}))
r=p['rain']; rain=[]
for area,frac,Q in itertools.product([a,e['large_area_m2']],r['event_displaced_fractions'],r['assumed_handling_m3_h']):
    volume=area*h*frac; M=volume*180
    rain.append(dict(area=area,displaced_fraction=frac,handling_m3_h=Q,volume_m3=volume,mass_kg=M,handling_only_h=volume/Q,unrecovered_kg_if_999_capture=M*(1-r['captured_fraction']),ideal_lift_kWh=M*g*r['vertical_lift_m']/3600000/r['pump_or_drive_efficiency']))
water=[]
for R,theta in itertools.product(p['water']['pore_radii_m'],p['water']['assumed_contact_angles_deg']):
    dp=-2*p['water']['surface_tension_N_m']*math.cos(math.radians(theta))/R
    water.append(dict(radius_m=R,assumed_angle_deg=theta,entry_pressure_Pa=dp,water_head_m=dp/1000/g))
filler=[]
for target in [1000,1050,1100]:
    weight=(1/target-1/z['solid_density_kg_m3'])/(1/2710-1/z['solid_density_kg_m3'])
    filler.append(dict(target_skeletal_density=target,ideal_calcite_mass_fraction=weight))
rain_inflow=[dict(slope_area_m2=area,rain_mm_h=100,vertical_rain_m3_h=area*math.cos(math.radians(30))*0.1,upstream_runon_included=False) for area in [a,e['large_area_m2']]]
large=[]
for rho in [100,180,300]:
    mass=e['large_area_m2']*h*rho
    material=mass*600
    large.append(dict(area_m2=e['large_area_m2'],rho=rho,mass_kg=mass,material_yen_at_600=material,material_plus_groomer_yen_before_site_costs=material+e['large_groomer_yen_tax_excluded']))
thickness_sensitivity=[]
for thickness in [0.45,0.6,0.8]:
    M=a*thickness*120; price=500; lam=0.02
    thickness_sensitivity.append(dict(thickness_m=thickness,mass_kg=M,material_yen=M*price,equivalent_annual_yen=(M*price+e['nonmaterial_initial_yen'])/AF+e['annual_other_yen']+M*price*lam))
required_throughput=[]
for feed in pr['feed_price_scenarios_yen_kg']:
    allowance=500-feed/pr['good_yield']-pr['delivery_qc_yen_kg']
    required_throughput.append(dict(feed_yen_kg=feed,finished_price_target=500,remaining_conversion_yen_kg=allowance,required_good_kg_h=(pr['line_charge_yen_h']/allowance if allowance>0 else None)))
nonmaterial_sensitivity=[]
M=a*h*120; lam=0.02
for I,O in itertools.product([20000000,50000000,100000000],[4000000,8000000,12000000]):
    cap=((e['annual_contribution_yen']-O)*AF-I)/(M*(1+lam*AF))
    nonmaterial_sensitivity.append(dict(nonmaterial_initial_yen=I,annual_other_yen=O,algebraic_price_cap_yen_kg=cap,positive_material_allowance=cap>0))
max_nonmaterial_at_target=(e['annual_contribution_yen']-e['annual_other_yen']-0.02*M*500)*AF-M*500
# Independent arithmetic checks: inverse annuity formula and total NPV.
for row in prices:
    rhs=e['nonmaterial_initial_yen']+row['mass_kg']*row['Pmax_yen_kg']+(e['annual_other_yen']+row['mass_kg']*row['Pmax_yen_kg']*row['replacement'])*AF
    assert math.isclose(rhs,e['annual_contribution_yen']*AF,rel_tol=1e-12)
assert math.isclose(beam(E,2*t,L,delta)['F_N'],8*base['F_N'],rel_tol=1e-12)
assert math.isclose(beam(E,t,2*L,delta)['F_N'],base['F_N']/8,rel_tol=1e-12)
assert all(x['good_kg_h']<=x['gross_kg_h'] for x in production)
result=dict(status=p['status'],AF=AF,material_NPV_allowance_yen=net,price_caps=prices,filler_density_screen=filler,cost_cases=cases,beam_baseline=base,beam_grid=beam_grid,particle_mass_kg=particle_mass,particle_count_at_162t=162000/particle_mass,wind_dynamic_pressure_Pa=q,isolated_particle_drag_N=force,local_retention_screen_N=w['screening_load_factor']*force,wind_layers=wind_rows,production=production,rain=rain,water_entry=water,large_course=large,vertical_rain_inflow=rain_inflow,thickness_sensitivity=thickness_sensitivity,required_throughput=required_throughput,nonmaterial_sensitivity=nonmaterial_sensitivity,max_nonmaterial_initial_at_target=max_nonmaterial_at_target,validation=dict(financial_inverse_cases=len(prices),beam_cases=len(beam_grid),cost_cases=len(cases),rain_cases=len(rain),physical_tests=0,full_DEM_or_FE_performed=False,market_quotes_obtained=0,checks_passed=True))
(D/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(AF=AF,price_caps=prices,beam=base,wind_q_Pa=q,particle_drag_mN=force*1000,production=production,large_course=large,validation=result['validation']),ensure_ascii=False,indent=2))
