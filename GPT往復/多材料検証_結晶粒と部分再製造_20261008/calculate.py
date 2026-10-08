"""Reproducible cycle 19 diagnostic; standard library only. No physical calibration."""
import json, math
from pathlib import Path
from decimal import Decimal, getcontext
ROOT = Path(__file__).resolve().parent
P = json.loads((ROOT/'inputs.json').read_text(encoding='utf-8'))
o, b, t, g = P['operation'], P['budget'], P['latent_comparison'], P['formation']
M = o['area_m2'] * o['depth_m'] * o['bulk_density_kg_m3']
r,n = b['discount'], b['years']
crf = r*(1+r)**n/((1+r)**n-1)
base = (M*b['material_JPY_kg']+b['nonmaterial_capital_JPY'])*crf + b['annual_fixed_JPY'] + M*b['material_JPY_kg']*b['annual_material_replacement_fraction']
headroom = b['annual_budget_JPY']-base
A = t['MJ_per_kg_water']/3.6*t['electricity_JPY_kWh']/t['heater_efficiency']
rho_grain = g['bed_bulk_density_kg_m3']/g['packing_fraction']
formation=[]
for w in P['feed_dry_mass_fractions']:
    ratio=(1-w)/w
    rho_feed=1/(w/g['cellulose_solid_density_kg_m3']+(1-w)/g['water_density_kg_m3'])
    diameter=g['final_equivalent_diameter_um']*(rho_grain/(w*rho_feed))**(1/3)
    formation.append(dict(w=w,water_kg_per_kg_dry=ratio,latent_MJ_per_kg_dry=ratio*t['MJ_per_kg_water'],latent_heater_JPY_per_kg_dry=A*ratio,ideal_feed_density_kg_m3=rho_feed,droplet_diameter_um=diameter))
scenarios=[]
for f in o['reform_fractions']:
    m=M*f
    annual=m*o['closures_per_year']
    fee=headroom/annual
    kg_h=m/(o['processing_minutes']/60)
    for q in formation:
        for node in [1]+P['node_dry_mass_fractions']:
            water=q['water_kg_per_kg_dry']*node
            cost=q['latent_heater_JPY_per_kg_dry']*node
            scenarios.append(dict(reform_fraction=f,node_fraction=node,w=q['w'],processed_grain_kg_per_closure=m,processed_grain_kg_per_year=annual,processed_grain_kg_h=kg_h,node_dry_kg_h=kg_h*node,water_kg_h=kg_h*water,latent_thermal_kW=kg_h*water*t['MJ_per_kg_water']/3.6,latent_heater_JPY_per_kg_processed_grain=cost,annual_latent_heater_JPY=annual*cost,all_in_fee_ceiling_JPY_kg=fee,remaining_JPY_kg_before_all_other_costs=fee-cost,fresh_node_price_ceiling_before_all_other_costs_JPY_kg=(fee-cost)/node))
thresholds=[]
for f in o['reform_fractions']:
    fee=headroom/(M*f*o['closures_per_year'])
    thresholds.append(dict(reform_fraction=f,all_in_fee_ceiling_JPY_kg=fee,whole_grain_w_if_all_fee_spent_on_latent= A/(A+fee),node_bmax_energy_only_by_w={str(q['w']):min(1,fee/q['latent_heater_JPY_per_kg_dry']) for q in formation}))
pe=P['peclet']
peclet=[dict(radius_m=x,Pe=x*x/(pe['diffusion_m2_s']*pe['drying_s'])) for x in pe['radii_m']]
d=P['dewatering']; wi,wo=d['feed_w'],d['after_w']
dewatering=dict(water_in_kg_kg_dry=(1-wi)/wi,water_after_kg_kg_dry=(1-wo)/wo,water_removed_mechanically_kg_kg_dry=1/wi-1/wo,solids_recovery_assumed=d['solids_recovery_assumed'])
z=P['buffer']
buffer_mass=M*z['reform_fraction']*z['inventory_multiplier']
buffer_capital=buffer_mass*b['material_JPY_kg']
buffer_annual=buffer_capital*(crf+b['annual_material_replacement_fraction'])
buffer=dict(reform_fraction=z['reform_fraction'],inventory_multiplier_assumed=z['inventory_multiplier'],dry_inventory_kg=buffer_mass,storage_bulk_density_assumed_kg_m3=o['bulk_density_kg_m3'],storage_volume_m3=buffer_mass/o['bulk_density_kg_m3'],inventory_capital_JPY=buffer_capital,incremental_inventory_annual_JPY=buffer_annual,remaining_headroom_JPY=headroom-buffer_annual,all_in_reform_fee_after_inventory_JPY_kg=(headroom-buffer_annual)/(M*z['reform_fraction']*o['closures_per_year']),offline_process_hours_assumed=z['offline_process_hours'],offline_latent_thermal_kW_at_w0045_b001=(M*z['reform_fraction']*z['node_fraction']*(1/z['feed_w']-1)*t['MJ_per_kg_water']/3.6)/z['offline_process_hours'],notes='Storage, transfer, extra dryer, labour and inventory losses beyond inherited 2% not included; no recovery-time proof.')
results=dict(buffer=buffer,evidence=P['evidence'],bed_dry_mass_kg=M,crf=crf,baseline_annual_JPY=base,annual_headroom_JPY=headroom,latent_heater_JPY_kg_water=A,grain_apparent_density_assumed_kg_m3=rho_grain,internal_porosity_assumed=1-rho_grain/g['cellulose_solid_density_kg_m3'],formation=formation,process_scenarios=scenarios,thresholds=thresholds,peclet=peclet,dewatering=dewatering)
(ROOT/'results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
# Independent identities: reconstruct input feed/dry mass, energy/time units,
# lifetime present value, and inverse feasibility boundaries. These do not validate physics.
getcontext().prec=45
checks=[]
def check(name, ok):
    if not ok: raise AssertionError(name)
    checks.append(name)
def close(a,b): return math.isclose(float(a),float(b),rel_tol=2e-11,abs_tol=1e-8)
D=Decimal
pv_factor=sum((D(1)+D(str(r)))**(-k) for k in range(1,n+1))
cap=D(str(M))*D(str(b['material_JPY_kg']))+D(str(b['nonmaterial_capital_JPY']))
rec=D(str(b['annual_fixed_JPY']))+D(str(M))*D(str(b['material_JPY_kg']))*D(str(b['annual_material_replacement_fraction']))
check('discounted_annuity_equals_upfront_plus_recurring',close(D(str(base))*pv_factor,cap+rec*pv_factor))
check('dry_mass_area_depth_density',M==108000)
check('budget_partition',close(base+headroom,b['annual_budget_JPY']))
check('grain_packing_density',close(rho_grain*g['packing_fraction'],g['bed_bulk_density_kg_m3']))
check('internal_solid_fraction',close((1-results['internal_porosity_assumed'])*g['cellulose_solid_density_kg_m3'],rho_grain))
for i,q in enumerate(formation):
    w=q['w']
    check('feed_mass_balance_'+str(i),close(1/(1+q['water_kg_per_kg_dry']),w))
    wet_volume=math.pi/6*(q['droplet_diameter_um']*1e-6)**3
    dry_volume=math.pi/6*(g['final_equivalent_diameter_um']*1e-6)**3
    check('droplet_solid_mass_'+str(i),close(wet_volume*q['ideal_feed_density_kg_m3']*w/dry_volume,rho_grain))
for i,s in enumerate(scenarios):
    # Joules over closure divided by seconds equals reported thermal watts.
    seconds=o['processing_minutes']*60
    water=s['processed_grain_kg_per_closure']*s['node_fraction']*(1/s['w']-1)
    check('closure_energy_power_'+str(i),close(water*t['MJ_per_kg_water']*1e6/seconds,s['latent_thermal_kW']*1000))
    check('annual_budget_balance_'+str(i),close(base+s['annual_latent_heater_JPY']+s['remaining_JPY_kg_before_all_other_costs']*s['processed_grain_kg_per_year'],b['annual_budget_JPY']))
for i,x in enumerate(thresholds):
    w=x['whole_grain_w_if_all_fee_spent_on_latent']
    check('threshold_inversion_'+str(i),close(A*(1/w-1),x['all_in_fee_ceiling_JPY_kg']))
check('dewatering_water_conservation',close(dewatering['water_removed_mechanically_kg_kg_dry']+dewatering['water_after_kg_kg_dry'],dewatering['water_in_kg_kg_dry']))
check('Pe_radius_squared',close(peclet[3]['Pe']/peclet[2]['Pe'],4))
check('Pe_diffusivity_inverse',close(pe['radii_m'][0]**2/(2*pe['diffusion_m2_s']*pe['drying_s']),peclet[0]['Pe']/2))
check('buffer_inventory_volume_mass',close(buffer['storage_volume_m3']*o['bulk_density_kg_m3'],buffer_mass))
check('buffer_capital_annualization',close(buffer_annual,buffer_capital/float(pv_factor)+buffer_capital*b['annual_material_replacement_fraction']))
check('physical_evidence_not_promoted',results['evidence']['physical_tests']==0 and results['evidence']['physical_success_probability'] is None)
validation=dict(check_count=len(checks),all_passed=True,checks=checks,scope='Numerical identities only; no physical specimen or performance test')
(ROOT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n',encoding='utf-8')
summary={k:results[k] for k in ['bed_dry_mass_kg','baseline_annual_JPY','annual_headroom_JPY','formation','thresholds','peclet','dewatering']}
summary['representative_node_cases']=[s for s in scenarios if s['reform_fraction']==.01 and s['w']==.045 and s['node_fraction'] in [.01,.03]]
summary['validation_check_count']=len(checks)
print(json.dumps(summary,indent=2))
