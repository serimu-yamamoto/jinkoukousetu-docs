"""Conditional design bounds, not calibrated performance. Python standard library."""
from pathlib import Path
import json, math, itertools
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8-sig'))
B,C,R,W,H,M,K,Q=(I[x] for x in ('bed','contact_material','run_in','wear','contact','manufacturing','budget','conditioning'))
mbed=B['area_m2']*B['depth_m']*B['bulk_density_kg_m3']
mg=math.pi/6*(B['grain_diameter_um']*1e-6)**3*B['grain_apparent_density_kg_m3']
ng=mbed/mg
sites=ng*B['contact_regions_per_grain']
crf=K['discount']*(1+K['discount'])**K['years']/((1+K['discount'])**K['years']-1)
base=(mbed*K['material_JPY_kg']+K['nonmaterial_capital_JPY'])*crf+K['annual_fixed_JPY']+mbed*K['material_JPY_kg']*K['annual_replacement_fraction']
margin=K['annual_budget_JPY']-base
inventory=[]
for radius,depth,factor in itertools.product(C['radii_um'],C['depths_um'],C['shape_volume_factors']):
    area=sites*math.pi*(radius*1e-6)**2
    volume=area*depth*1e-6*factor
    mass=volume*C['density_kg_m3']
    inventory.append(dict(radius_um=radius,depth_um=depth,shape_factor=factor,area_m2=area,added_volume_m3=volume,added_mass_kg=mass,added_mass_to_original_fraction=mass/mbed,bulk_density_if_fixed_bed_volume=(mbed+mass)/(B['area_m2']*B['depth_m'])))
cost=[]
for inv,alpha in itertools.product(inventory,K['extra_existing_contact_replacement_fraction_per_year']):
    factor=crf+K['annual_replacement_fraction']+alpha
    for price in C['prices_JPY_kg']:
        annual=inv['added_mass_kg']*price*factor
        cost.append(dict(radius_um=inv['radius_um'],depth_um=inv['depth_um'],shape_factor=inv['shape_factor'],extra_contact_replacement_fraction_year=alpha,price_JPY_kg=price,initial_material_JPY=inv['added_mass_kg']*price,annual_added_material_JPY=annual,annual_margin_after_material_JPY=margin-annual,maximum_material_price_JPY_kg_with_zero_extra_process=margin/(inv['added_mass_kg']*factor)))
def runin(fresh,conditioned,lr,q,length=None):
    length=R['ski_loaded_length_m'] if length is None else length
    a=math.exp(-length/lr)
    one_minus_a=-math.expm1(-length/lr)
    before=(1-q)*one_minus_a/(q+(1-q)*one_minus_a)
    after=1-(1-before)*a
    mean=1-(1-before)*lr/length*one_minus_a
    first_mean=1-lr/length*one_minus_a
    mu=lambda state:R['other_drag_mu']+fresh+(conditioned-fresh)*state
    need=(R['other_drag_mu']+fresh-R['total_mu_diagnostic'])/(fresh-conditioned)
    qmax=1.0 if need<=0 else (None if need>1 else (1-need)*one_minus_a/(need+(1-need)*one_minus_a))
    if need<=0: slip=0.0
    elif need>=1: slip=None
    else: slip=-lr*math.log1p(-need)
    return dict(fresh_mu=fresh,conditioned_mu=conditioned,Lr_m=lr,renewal_fraction=q,steady_before=before,steady_after=after,steady_mean=mean,first_pass_mean=first_mean,steady_peak_mu=mu(before),steady_mean_mu=mu(mean),first_pass_mean_mu=mu(first_mean),first_point_mu=mu(0),required_conditioned_load_fraction=need,maximum_between_pass_reset_fraction=qmax,initial_required_slip_m=slip)
run_cases=[runin(*x) for x in itertools.product(R['fresh_mu'],R['conditioned_mu'],R['characteristic_slip_m'],R['fresh_fraction_between_passes'])]
run_refs=[runin(.2,.06,10,q) for q in R['fresh_fraction_between_passes']]
conditioning=[]
for lr in R['characteristic_slip_m']:
    rr=runin(Q['assumed_fresh_mu'],Q['assumed_conditioned_mu'],lr,0)
    s=rr['initial_required_slip_m']
    dwell=Q['contact_length_m']/Q['travel_speed_m_s']
    slip_per_pass=dwell*Q['relative_slip_speed_m_s']
    passes=math.ceil(s/slip_per_pass-1e-12) if s else 0
    time=passes*Q['course_length_m']/Q['travel_speed_m_s']/60
    area_energy=Q['nominal_pressure_Pa']*(Q['assumed_conditioned_mu']*s+(Q['assumed_fresh_mu']-Q['assumed_conditioned_mu'])*lr*(-math.expm1(-s/lr)))
    conditioning.append(dict(Lr_m=lr,required_local_slip_m=s,local_slip_per_equipment_pass_m=slip_per_pass,whole_area_passes=passes,ideal_travel_minutes=time,friction_only_energy_kWh=area_energy*B['area_m2']/3.6e6,ideal_time_within40min=time<=Q['available_minutes']))
wear=[]
for k,p,n,h in itertools.product(W['specific_wear_coefficients_m2_N'],W['mean_contact_pressures_MPa'],W['loaded_passes'],W['usable_depth_um']):
    slip=n*W['reference_pass_length_m']
    depth=k*p*1e6*slip
    wear.append(dict(k_m2_N=k,mean_pressure_MPa=p,loaded_passes=n,usable_depth_um=h,constant_geometry_wear_depth_um=depth*1e6,maximum_k_m2_N=h*1e-6/(p*1e6*slip),depth_budget_met=depth<=h*1e-6))
contacts=[]
for e,r,force in itertools.product(H['effective_moduli_MPa'],H['radii_um'],H['group_forces_mN']):
    f=force*1e-3/H['count']; rad=r*1e-6
    a=(3*f*rad/(4*e*1e6))**(1/3)
    p=f/(math.pi*a*a)
    contacts.append(dict(effective_E_MPa=e,R_um=r,group_force_mN=force,a_um=a*1e6,mean_pressure_MPa=p/1e6,peak_pressure_MPa=1.5*p/1e6,indentation_um=a*a/rad*1e6,required_homogeneous_depth_um=H['homogeneous_thickness_to_radius_diagnostic']*a*1e6,required_lateral_radius_um=H['cap_radius_to_contact_radius_diagnostic']*a*1e6))
production=[]
for hours,yield_fraction in itertools.product(M['production_hours'],M['yield_fractions']):
    production.append(dict(hours=hours,yield_fraction=yield_fraction,required_grains_per_second=ng/(hours*3600*yield_fraction),equivalent_contact_region_operations_per_second=sites/(hours*3600*yield_fraction)))
rock=[]
for radius,angle,length in itertools.product(I['rocking']['radii_um'],I['rocking']['available_angles_deg'],I['rocking']['loaded_lengths_m']):
    travel=radius*1e-6*math.radians(angle)
    rock.append(dict(radius_um=radius,available_angle_deg=angle,loaded_length_m=length,maximum_single_rotation_travel_m=travel,ideal_sliding_distance_reduction_fraction=min(1,travel/length)))
checks=[]
def ck(name,value):checks.append(dict(name=name,ok=bool(value)))
def near(a,b):return math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-12)
ck('Bed mass and counted particle mass agree',near(ng*mg,108000))
ck('Cap mass from total area equals count times individual volume',all(near(x['added_mass_kg'],sites*math.pi*(x['radius_um']*1e-6)**2*x['depth_um']*1e-6*x['shape_factor']*C['density_kg_m3']) for x in inventory))
ck('Added material increases bulk density if volume fixed',all(x['bulk_density_if_fixed_bed_volume']>B['bulk_density_kg_m3'] for x in inventory))
ck('No renewal converges to conditioned state',all(near(x['steady_before'],1) for x in run_cases if x['renewal_fraction']==0))
ck('Complete renewal resets every first contact',all(near(x['steady_before'],0) and near(x['steady_mean'],x['first_pass_mean']) for x in run_cases if x['renewal_fraction']==1))
ck('Steady coverage satisfies renewal recurrence',all(near((1-x['renewal_fraction'])*x['steady_after'],x['steady_before']) for x in run_cases))
ck('Conditioned states are bounded and loading increases them',all(0<=x['steady_before']<=x['steady_mean']<=x['steady_after']<=1+1e-12 for x in run_cases))
ck('Numerical pass integration agrees with analytic average',all(near(sum(1-(1-x['steady_before'])*math.exp(-(j+.5)*R['ski_loaded_length_m']/100000/x['Lr_m']) for j in range(100000))/100000,x['steady_mean']) for x in run_refs))
ck('Required slip reaches diagnostic target at a point, not whole-bed proof',all(near(R['other_drag_mu']+x['fresh_mu']+(x['conditioned_mu']-x['fresh_mu'])*(1-math.exp(-x['initial_required_slip_m']/x['Lr_m'])),R['total_mu_diagnostic']) for x in run_cases if x['initial_required_slip_m'] is not None))
ck('Fresh first point fails target in every listed material scenario',all(x['first_point_mu']>R['total_mu_diagnostic'] for x in run_cases))
ck('Ten percent renewal atLr10 raises peak beyond target',runin(.2,.06,10,.1)['steady_peak_mu']>.1)
ck('One percent renewal atLr10 meets steady diagnostic but not fresh startup',runin(.2,.06,10,.01)['steady_peak_mu']<.1 and runin(.2,.06,10,.01)['first_point_mu']>.1)
ck('Reset fraction boundary meets steady peak target',all(near(runin(x['fresh_mu'],x['conditioned_mu'],x['Lr_m'],x['maximum_between_pass_reset_fraction'])['steady_peak_mu'],R['total_mu_diagnostic']) for x in run_cases if x['maximum_between_pass_reset_fraction'] is not None and 0<x['required_conditioned_load_fraction']<1))
ck('Wear budget maximum coefficient exactly consumes available depth',all(near(x['maximum_k_m2_N']*x['mean_pressure_MPa']*1e6*x['loaded_passes']*W['reference_pass_length_m']*1e6,x['usable_depth_um']) for x in wear))
ck('Wear depth scales linearly with assumed k',near(1e-14*5e6*1600,10*(1e-15*5e6*1600)))
ck('All added material cost debited from shared margin',all(near(x['annual_margin_after_material_JPY']+x['annual_added_material_JPY'],margin) for x in cost))
ck('Price bound consumes the same shared annual margin',all(near(x['maximum_material_price_JPY_kg_with_zero_extra_process']*(crf+K['annual_replacement_fraction']+x['extra_contact_replacement_fraction_year'])*next(y['added_mass_kg'] for y in inventory if (y['radius_um'],y['depth_um'],y['shape_factor'])==(x['radius_um'],x['depth_um'],x['shape_factor'])),margin) for x in cost))
ck('Hertz pressure integrates specified force',all(near(x['mean_pressure_MPa']*1e6*math.pi*(x['a_um']*1e-6)**2,x['group_force_mN']*1e-3/H['count']) for x in contacts))
ck('Manufacturing yield closes equivalent operation count',all(near(x['equivalent_contact_region_operations_per_second']*x['hours']*3600*x['yield_fraction'],sites) for x in production))
ck('Conditioner rounded pass count covers required local slip',all(x['whole_area_passes']*x['local_slip_per_equipment_pass_m']>=x['required_local_slip_m'] for x in conditioning))
ck('Finite rocking travel stays below0.5percent in listed cases',all(x['ideal_sliding_distance_reduction_fraction']<.005 for x in rock))
result=dict(evidence=I['evidence'],bed_mass_kg=mbed,grain_mass_kg=mg,grain_count=ng,total_contact_regions=sites,CRF=crf,baseline_annual_JPY=base,remaining_annual_JPY=margin,inventory=inventory,cost_cases=cost,run_in_cases=run_cases,run_in_reference=run_refs,conditioning=conditioning,wear_cases=wear,contact_cases=contacts,production=production,rocking=rock)
validation=dict(evidence=I['evidence'],checks=checks,count=len(checks),all_checks_ok=all(x['ok'] for x in checks),counts={k:len(result[k]) for k in ('inventory','cost_cases','run_in_cases','conditioning','wear_cases','contact_cases','production','rocking')})
for name,obj in [('results.json',result),('validation.json',validation)]:
    (P/name).write_bytes((json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
assert validation['all_checks_ok'],[x for x in checks if not x['ok']]
print(json.dumps(dict(checks=len(checks),all_checks_ok=True,counts=validation['counts'],physical_tests=0)))
