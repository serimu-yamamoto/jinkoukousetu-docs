"""Conditional design budgets, not empirical material performance."""
import json, math
from pathlib import Path
from itertools import product
ROOT=Path(__file__).resolve().parent
I=json.loads((ROOT/'inputs.json').read_text(encoding='utf-8'))
M=I['machine']; A=I['material']; P=I['processing']; S=I['evidence']
normal=M['mass_kg']*M['g_m_s2']*math.cos(math.radians(M['slope_deg']))
footprint=M['width_m']*M['contact_length_m']
nominal=normal/footprint
roller=[]
for pressure in M['comparison_pressures_MPa']:
    force=pressure*1e6*footprint
    roller.append(dict(pressure_MPa=pressure,required_force_N=force,equivalent_gravity_mass_kg=force/(M['g_m_s2']*math.cos(math.radians(M['slope_deg']))),force_ratio_to_reference=force/normal,maximum_force_concentration_area_fraction=normal/force))
materials=[]; budgets=[]; costs=[]
for area,frac in product(A['area_m2'],A['final_added_phase_mass_fraction']):
    volume=area*A['depth_m']; host=volume*A['host_bulk_density_kg_m3']; phase=host*frac/(1-frac); total=host+phase
    void=1-(host/A['host_solid_density_kg_m3']+phase/A['added_phase_density_kg_m3'])/volume
    materials.append(dict(area_m2=area,phase_fraction=frac,host_kg=host,phase_kg=phase,total_kg=total,phase_volume_m3=phase/A['added_phase_density_kg_m3'],geometric_total_void_fraction=void))
    for price in A['added_phase_prices_JPY_kg']:
        costs.append(dict(area_m2=area,phase_fraction=frac,phase_price_JPY_kg=price,phase_purchase_JPY=phase*price/A['usable_yield'],host_purchase_JPY=host*A['host_price_JPY_kg']/A['usable_yield'],combined_purchase_JPY=(phase*price+host*A['host_price_JPY_kg'])/A['usable_yield']))
    for repaired,scope in product(P['repair_stock_fraction'],['whole_attached_particle','phase_only_if_separable']):
        batch_mass=(total if scope=='whole_attached_particle' else phase)*repaired
        # Dense processing feed is a stated machine-sizing reference, not a claim
        # that an open particle survives this operation. Each scope uses the same
        # assumed dense processing density to isolate the inventory effect.
        feed_vol=batch_mass/A['added_phase_density_kg_m3']
        annual_mass=batch_mass*P['annual_events']
        hyd=P['pressure_MPa']*1e6*(feed_vol*P['assumed_press_volume_reduction_fraction'])/(3.6e6*P['hydraulic_efficiency'])
        heat=batch_mass*P['cp_kJ_kg_K']*P['temperature_rise_K']/(3600*P['heater_efficiency'])
        for dwell,time in product(P['assumed_dwell_s'],P['available_s']):
            waves=math.floor(time/(dwell+P['handling_s']))
            chamber_volume=feed_vol/waves if waves else None
            ram_area=chamber_volume/P['effective_chamber_depth_m'] if waves else None
            force=P['pressure_MPa']*1e6*ram_area if waves else None
            budgets.append(dict(area_m2=area,phase_fraction=frac,repair_fraction=repaired,scope=scope,processed_kg=batch_mass,dense_feed_m3=feed_vol,assumed_dwell_s=dwell,available_s=time,completed_equal_batches=waves,reference_chamber_volume_m3=chamber_volume,reference_ram_area_m2=ram_area,reference_ram_force_N=force,annual_throughput_kg=annual_mass,annual_allowance_JPY_kg=P['illustrative_additional_annual_allowance_JPY']/annual_mass,idealized_press_work_kWh=hyd,assumed_material_heating_kWh=heat,work_plus_heat_JPY=(hyd+heat)*P['electricity_JPY_kWh'],idle_JPY_if_powered_entire_window=[k*time/3600*P['electricity_JPY_kWh'] for k in P['idle_power_kW']],time_arithmetic_allows_at_least_one_batch=bool(waves)))
md=S['S4'];freq=md['omega_reduced']/(2*math.pi*md['LJ_time_s']); duration=md['cycles']/freq
# Nominal composition in the paper is retained rather than silently replacing it
# with the NMR-measured hard fraction. Flow is NOT a 50 C safety boundary.
blend=[dict(nominal_additive_fraction=f,nominal_total_PLLA_fraction=1-0.6*f,flow_C=t) for f,t in zip(S['S2']['nominal_blend_additive_fraction'],S['S2']['reported_flow_temperature_C'])]
R=dict(schema='pressure-reforming-results-v1',physical_tests=0,physical_success_probability=None,reference_machine=dict(normal_force_N=normal,footprint_m2=footprint,nominal_pressure_Pa=nominal,contact_time_s=M['contact_length_m']/M['speed_m_s']),roller_pressure_budget=roller,material_inventory=materials,purchase_costs=costs,processing_budgets=budgets,literature_blend_data=blend,MD_optional_unit_mapping=dict(frequency_Hz=freq,period_s=1/freq,cycles_time_s=duration,example_crack_diameter_m=md['LJ_length_m'],particle_to_example_crack_length_ratio=450e-6/md['LJ_length_m'],warning='illustrative author mapping, not a calibrated polymer or roller setting'))
local=[]
particle_host_mass=math.pi/6*A['assumed_particle_envelope_diameter_m']**3*A['assumed_host_envelope_density_kg_m3']
for inv in materials:
    for rr,tt in product(P['repair_stock_fraction'],P['available_s']):
        count=inv['host_kg']*rr/particle_host_mass
        local.append(dict(area_m2=inv['area_m2'],phase_fraction=inv['phase_fraction'],repair_fraction=rr,available_s=tt,affected_particle_count=count,required_particle_handling_rate_s=count/tt,scope='if attached grains are individually presented to local tooling; orientation yield and selective pressing unproven'))
R['localized_tooling_handling']=local
C=[]
def check(name,actual,expected,rel=1e-10,abs_tol=1e-10):
    ok=math.isclose(actual,expected,rel_tol=rel,abs_tol=abs_tol)
    C.append(dict(name=name,actual=actual,expected=expected,passed=ok))
    assert ok,name
check('1MPa_on_1m2_is_1MN',1e6*footprint,1e6)
check('reference_force',normal,33971.232104,
      rel=1e-6)
check('10MPa_force',roller[1]['required_force_N'],10e6)
check('force_budget_area_fraction',roller[1]['maximum_force_concentration_area_fraction']*10e6,normal)
check('roller_residence',R['reference_machine']['contact_time_s'],1/12)
check('pressure_time_invariant',nominal*M['contact_length_m']/M['speed_m_s'],normal/(M['width_m']*M['speed_m_s']))
base=next(x for x in materials if x['area_m2']==2000 and x['phase_fraction']==0.02)
check('host_reference_108t',base['host_kg'],108000)
check('phase_is_2percent_final_mass',base['phase_kg']/base['total_kg'],0.02)
check('phase_to_host_2_over_98',base['phase_kg']/base['host_kg'],2/98)
check('volume_conservation',base['geometric_total_void_fraction']*900+base['host_kg']/950+base['phase_kg']/1250,900)
big=next(x for x in materials if x['area_m2']==20000 and x['phase_fraction']==0.02)
check('tenfold_area_mass',big['total_kg']/base['total_kg'],10)
def pick(scope='whole_attached_particle',dwell=300,time=2400):
    return next(x for x in budgets if x['area_m2']==2000 and x['phase_fraction']==0.02 and x['repair_fraction']==0.01 and x['scope']==scope and x['assumed_dwell_s']==dwell and x['available_s']==time)
a=pick();b=pick('phase_only_if_separable');night=pick(dwell=3600,time=28800)
check('attached_mass_factor',a['processed_kg']/b['processed_kg'],50)
check('five_minute_40minute_batches',a['completed_equal_batches'],6)
check('one_hour_cannot_complete_in_40min',pick(dwell=3600)['completed_equal_batches'],0)
check('one_hour_8hour_batches',night['completed_equal_batches'],7)
check('14hour_cannot_complete_8hour',pick(dwell=50400,time=28800)['completed_equal_batches'],0)
check('batch_chamber_mass_conservation',a['reference_chamber_volume_m3']*1250*a['completed_equal_batches'],a['processed_kg'])
check('force_area_backcheck',a['reference_ram_force_N']/a['reference_ram_area_m2'],10e6)
check('annual_processing_mass',a['annual_throughput_kg'],a['processed_kg']*200)
check('same_allowance_for_both_scopes',a['annual_allowance_JPY_kg']*a['annual_throughput_kg'],b['annual_allowance_JPY_kg']*b['annual_throughput_kg'])
check('nominal_50percent_blend_PLLA',blend[-1]['nominal_total_PLLA_fraction'],0.7)
check('10percent_blend_PLLA',blend[0]['nominal_total_PLLA_fraction'],0.94)
check('angular_to_cycles',freq*2*math.pi*md['LJ_time_s'],0.1)
check('72cycle_time_backcheck',duration*freq,72)
check('MD_length_ratio',R['MD_optional_unit_mapping']['particle_to_example_crack_length_ratio'],900000)
check('heating_kWh',a['assumed_material_heating_kWh'],a['processed_kg']/120)
check('press_work_unit',10e6*0.1/(3.6e6*0.7),0.3968253968253968)
check('scope_cost_ceiling_factor',b['annual_allowance_JPY_kg']/a['annual_allowance_JPY_kg'],50)
loc=next(x for x in local if x['area_m2']==2000 and x['phase_fraction']==0.02 and x['repair_fraction']==0.01 and x['available_s']==28800)
check('localized_handling_mass_conservation',loc['affected_particle_count']*particle_host_mass,1080)
check('localized_handling_rate_conservation',loc['required_particle_handling_rate_s']*28800,loc['affected_particle_count'])
for name,obj in [('results.json',R),('validation.json',dict(check_count=len(C),all_passed=all(c['passed'] for c in C),scope='arithmetic, units, mass, schedule and geometry only; no physical performance',checks=C))]:
    (ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'checks':len(C),'all_passed':True,'rows':{'inventory':len(materials),'cost':len(costs),'processing':len(budgets)},'representative':a,'overnight':night},ensure_ascii=False))
