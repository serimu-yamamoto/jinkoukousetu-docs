"""Recipe and conditional energy/mass bounds; standard library; no fitted performance."""
from pathlib import Path
import json, math, itertools
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
B,K,M,T,D=(I[k] for k in ('bed','budget','manufacturing','thermal','phase_drift'))
mass=B['area_m2']*B['depth_m']*B['bulk_density_kg_m3']
crf=K['discount']*(1+K['discount'])**K['years']/((1+K['discount'])**K['years']-1)
annual_factor=crf+K['annual_replacement_fraction']
nonmaterial=K['nonmaterial_capital_JPY']*crf+K['annual_fixed_JPY']
baseline=nonmaterial+mass*K['material_JPY_kg']*annual_factor
margin=K['annual_budget_JPY']-baseline
price_cap=(K['annual_budget_JPY']-nonmaterial)/(mass*annual_factor)
routes=[]
for route,f in itertools.product(I['routes'],M['product_fractions']):
    product=mass*f; y=route['collection_yield']; c=route['reported_kg_per_L']
    gross=product/y; reject=gross-product; liquid=gross/c
    routes.append(dict(route=route['id'],product_fraction=f,product_kg=product,
        gross_polymer_processed_kg=gross,integrated_reject_kg=reject,recipe_liquid_L=liquid,
        recipe_liquid_L_per_kg_product=1/(y*c),average_recipe_flow_L_h=liquid/M['campaign_hours'],
        makeup_equivalent_L=[dict(recovery_fraction=r,nonreturned_recipe_liquid_L=liquid*(1-r)) for r in M['liquid_recovery_fractions']]))
recycle=[]
for r in M['reject_recovery_fractions']:
    y=0.66; gross=mass/y; reject=gross-mass
    recycle.append(dict(reject_recovery_fraction=r,gross_kg=gross,reject_kg=reject,
        recycled_kg=r*reject,virgin_kg=gross-r*reject,contained_purge_kg=(1-r)*reject))
manufacturing_cost=[]
for route,r,price,liquid_price in itertools.product(I['routes'],M['reject_recovery_fractions'],M['raw_polymer_prices_JPY_kg'],M['liquid_processing_prices_JPY_L']):
    y=route['collection_yield']; c=route['reported_kg_per_L']
    virgin_per_product=(1-r*(1-y))/y
    feed=price*virgin_per_product; liquid=liquid_price/(c*y)
    landed=feed+liquid
    manufacturing_cost.append(dict(route=route['id'],reject_recovery_fraction=r,raw_polymer_JPY_kg=price,
        liquid_processing_JPY_L=liquid_price,virgin_feed_cost_JPY_kg_product=feed,
        liquid_processing_cost_JPY_kg_product=liquid,partial_product_price_JPY_kg=landed,
        annual_margin_JPY=K['annual_budget_JPY']-(nonmaterial+mass*landed*annual_factor),
        maximum_liquid_processing_JPY_L_excluding_all_other_cost=(price_cap-feed)*c*y))
minority=[]
for f,price in itertools.product(I['minority_phase']['fractions'],I['minority_phase']['prices_JPY_kg']):
    extra=mass*f*(price-I['minority_phase']['base_JPY_kg'])*annual_factor
    minority.append(dict(fraction=f,phase_mass_kg=mass*f,phase_JPY_kg=price,
        composite_JPY_kg=(1-f)*I['minority_phase']['base_JPY_kg']+f*price,
        annual_added_material_JPY=extra,remaining_annual_JPY=margin-extra))
minority_caps=[dict(phase_JPY_kg=p,maximum_fraction_excluding_processing=(price_cap-I['minority_phase']['base_JPY_kg'])/(p-I['minority_phase']['base_JPY_kg'])) for p in I['minority_phase']['prices_JPY_kg']]
thermal=[]
sensible=T['heat_capacity_kJ_kgK']*(T['process_C']-T['initial_C'])
latent=T['low_melting_fraction']*T['latent_heat_of_low_phase_kJ_kg']
for f,h in itertools.product(T['processed_mass_fractions_per_closure'],T['sensible_heat_recovery_fractions']):
    processed=mass*f; input_kwh=processed*((1-h)*sensible+latent)/(3600*T['thermal_efficiency'])
    annual=input_kwh*T['electricity_JPY_kWh']*K['closures_per_year']
    thermal.append(dict(processed_fraction=f,sensible_recovery_fraction=h,processed_kg=processed,
        full_sensible_plus_latent_kWh=processed*(sensible+latent)/3600,
        input_energy_kWh=input_kwh,minimum_average_input_kW=input_kwh/T['available_h'],
        electricity_JPY_per_closure=input_kwh*T['electricity_JPY_kWh'],
        annual_electricity_JPY=annual,annual_remaining_before_extra_material_and_capital_JPY=margin-annual,
        maximum_processed_fraction_for_energy_only=margin/(mass*((1-h)*sensible+latent)/(3600*T['thermal_efficiency'])*T['electricity_JPY_kWh']*K['closures_per_year'])))
diffusion=[]
for d,a,t in itertools.product(T['heat_path_um'],T['thermal_diffusivities_mm2_s'],T['heating_times_s']):
    td=(d/1000)**2/a
    diffusion.append(dict(path_um=d,alpha_mm2_s=a,time_s=t,diffusion_time_s=td,Fourier_number=t/td))
drift=[]
for eta,n in itertools.product(D['conversion_fraction_per_heating'],D['cycles']):
    low=D['initial_low_fraction']*(1-eta)**n
    drift.append(dict(conversion_fraction_per_heating=eta,heatings=n,low_fraction=low,high_fraction=1-low))
drift_limits=[]
for eta in D['conversion_fraction_per_heating']:
    if eta==0: last=None
    else:
        bound=math.log(D['minimum_low_fraction']/D['initial_low_fraction'])/math.log1p(-eta)
        last=math.floor(bound+1e-12)
    drift_limits.append(dict(conversion_fraction_per_heating=eta,last_heating_at_or_above_minimum=last,first_below_minimum=None if last is None else last+1))
joint=[]
for phase,c in itertools.product(minority,thermal):
    host_fraction=1-phase['fraction']
    joint_latent=host_fraction*T['latent_heat_of_low_phase_kJ_kg']
    joint_kwh=mass*c['processed_fraction']*((1-c['sensible_recovery_fraction'])*sensible+joint_latent)/(3600*T['thermal_efficiency'])
    joint_annual=joint_kwh*T['electricity_JPY_kWh']*K['closures_per_year']
    combined=phase['remaining_annual_JPY']-joint_annual
    joint.append(dict(phase_fraction=phase['fraction'],low_melting_host_fraction=host_fraction,phase_JPY_kg=phase['phase_JPY_kg'],processed_fraction=c['processed_fraction'],sensible_recovery_fraction=c['sensible_recovery_fraction'],input_energy_kWh=joint_kwh,annual_electricity_JPY=joint_annual,annual_remaining_JPY=combined))
refs=dict(mass_kg=mass,crf=crf,baseline_annual_JPY=baseline,annual_margin_JPY=margin,maximum_finished_material_JPY_kg=price_cap,
    sensible_kJ_per_kg=sensible,latent_kJ_per_kg=latent,
    false_phase_only_heat_kJ_per_kg_total=T['low_melting_fraction']*(sensible+T['latent_heat_of_low_phase_kJ_kg']),
    whole_to_false_phase_only_energy_ratio=(sensible+latent)/(T['low_melting_fraction']*(sensible+T['latent_heat_of_low_phase_kJ_kg'])))
checks=[]
def check(name,value):
    checks.append(dict(name=name,passed=bool(value)))
check('reference108t',mass==108000)
check('baseline inherited',math.isclose(baseline,16108182.1636,abs_tol=.01))
check('finished-price boundary closes budget',math.isclose(nonmaterial+mass*price_cap*annual_factor,K['annual_budget_JPY'],abs_tol=1e-6))
check('POM w-v not wt',math.isclose(I['routes'][0]['reported_kg_per_L'],.02/1000/(100/1000)))
check('PLA w-v conversion',math.isclose(I['routes'][1]['reported_kg_per_L'],.25/1000/(100/1000)))
check('recipe mass closure',all(math.isclose(r['recipe_liquid_L']*next(z['reported_kg_per_L'] for z in I['routes'] if z['id']==r['route']),r['gross_polymer_processed_kg'],rel_tol=1e-12) for r in routes))
check('all collection closures',all(math.isclose(r['product_kg']+r['integrated_reject_kg'],r['gross_polymer_processed_kg'],rel_tol=1e-12) for r in routes))
check('fresh product purge conservation',all(math.isclose(r['virgin_kg'],mass+r['contained_purge_kg'],rel_tol=1e-12) for r in recycle))
check('full reject recovery zero purge',recycle[-1]['contained_purge_kg']==0 and math.isclose(recycle[-1]['virgin_kg'],mass))
check('zero reject recovery gross virgin',math.isclose(recycle[0]['virgin_kg'],mass/.66))
check('liquid recovery ordering',all(r['makeup_equivalent_L'][0]['nonreturned_recipe_liquid_L']>r['makeup_equivalent_L'][1]['nonreturned_recipe_liquid_L']>r['makeup_equivalent_L'][2]['nonreturned_recipe_liquid_L'] for r in routes))
check('phase replacement keeps mass',all(math.isclose(mass*(1-r['fraction'])+r['phase_mass_kg'],mass) for r in minority))
check('phase-drift conserved mass',all(math.isclose(r['low_fraction']+r['high_fraction'],1) for r in drift))
check('no conversion no drift',all(r['low_fraction']==D['initial_low_fraction'] for r in drift if r['conversion_fraction_per_heating']==0))
check('half reserve at analytical limit',all(r['last_heating_at_or_above_minimum'] is None or (D['initial_low_fraction']*(1-r['conversion_fraction_per_heating'])**r['last_heating_at_or_above_minimum']>=D['minimum_low_fraction'] and D['initial_low_fraction']*(1-r['conversion_fraction_per_heating'])**r['first_below_minimum']<D['minimum_low_fraction']) for r in drift_limits))
check('heat includes entire sensible mass',math.isclose(sensible,288) and math.isclose(latent,10))
check('no recovery first-law equality',all(math.isclose(r['input_energy_kWh']*T['thermal_efficiency'],r['full_sensible_plus_latent_kWh'],rel_tol=1e-12) for r in thermal if r['sensible_recovery_fraction']==0))
check('1percent no recovery149kWh',any(r['processed_fraction']==.01 and r['sensible_recovery_fraction']==0 and math.isclose(r['input_energy_kWh'],149) for r in thermal))
check('diffusion independent dimensional form',all(math.isclose(r['Fourier_number'],r['alpha_mm2_s']*1e-6*r['time_s']/(r['path_um']*1e-6)**2,rel_tol=1e-12) for r in diffusion))
check('whole energy exceeds phase-only lower fiction',refs['whole_to_false_phase_only_energy_ratio']>7)
check('H24B phase mass complements host',all(math.isclose(r['phase_fraction']+r['low_melting_host_fraction'],1) for r in joint))
check('H24B5percent energy recomputed not H24A',all(math.isclose(r['input_energy_kWh'],191.5) for r in joint if r['phase_fraction']==.05 and r['processed_fraction']==.01 and r['sensible_recovery_fraction']==0))
check('no invented success probability',I['evidence']['physical_tests']==0 and I['evidence']['physical_success_probability'] is None)
result=dict(evidence=I['evidence'],references=refs,route_balances=routes,reject_recycle_balances=recycle,manufacturing_cost_cases=manufacturing_cost,minority_material_costs=minority,minority_fraction_ceilings=minority_caps,thermal_regeneration_cases=thermal,diffusion_diagnostics=diffusion,phase_drift_cases=drift,phase_drift_limits=drift_limits,joint_material_energy_cases=joint)
validation=dict(numerical_checks=len(checks),all_passed=all(x['passed'] for x in checks),checks=checks,not_validated=['Actual open grain formation','50C creep and dry/wet ski contact','Branch survival and repeated phase conversion','Rain and winter bonding','Human/environment safety','Commercial costs','Success probability'])
for name,data in [('results.json',result),('validation.json',validation)]:
    (P/name).write_bytes((json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
print(json.dumps(dict(checks=len(checks),passed=validation['all_passed'],cases=dict(route=len(routes),manufacturing=len(manufacturing_cost),thermal=len(thermal),diffusion=len(diffusion),phase=len(drift),joint=len(joint)),references=refs,phase_limits=drift_limits),ensure_ascii=False))
if not validation['all_passed']: raise SystemExit('NUMERICAL CHECK FAILED')
