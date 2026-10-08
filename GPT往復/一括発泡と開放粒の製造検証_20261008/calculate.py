"""Cycle 37: unit and mass balances; not material or skier simulation."""
from pathlib import Path
import json, math, csv, sys
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
g=I['geometry']; d=I['design']; s=I['literature_S1']
V=g['area_m2']*g['depth_m']; Ve=V*g['particle_envelope_packing']
rs=g['solid_density_kg_m3']; rw=g['water_density_kg_m3']; re=g['reference_envelope_density_kg_m3']
M=Ve*re; y=d['good_yield']; repair=M*d['repair_fraction']; feed=repair/y
checks=[]
def eq(name,a,b):
    ok=math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-9)
    checks.append({'name':name,'actual':a,'expected':b,'passed':ok})
    if not ok: raise AssertionError(name)
def yes(name,v):
    checks.append({'name':name,'passed':bool(v)})
    if not v: raise AssertionError(name)
wet=[]
for r in g['envelope_densities_kg_m3']:
    mass=Ve*r; vs=mass/rs; vp=Ve-vs; qmax=vp*rw/mass
    # Free immersed body, gas remains enclosed, no surface tension or anchors.
    neutral=(rw*Ve-mass)/(rw*vp)
    for sat in g['retained_pore_water_fractions']:
        water=sat*vp*rw
        wet.append({'rho_envelope_kg_m3':r,'retained_fraction':sat,'dry_kg':mass,'pore_water_kg':water,'lifted_wet_kg':mass+water,'q_water_kg_kg':water/mass,'q_internal_max_kg_kg':qmax,'neutral_saturation_free_immersed':neutral})
ref=[z for z in wet if z['rho_envelope_kg_m3']==re]
qmax=ref[-1]['q_internal_max_kg_kg']
wur=[]
for mode,q in [('Methods_formula',s['WUR_reported_mean']),('Results_prose',s['WUR_reported_mean']-1)]:
    rho=1/(1/rs+q/rw)
    wur.append({'interpretation':mode,'water_kg_kg':q,'density_if_all_water_in_fixed_internal_pores_kg_m3':rho,'ratio_to_reference_max_internal_water':q/qmax,'is_density_measurement':False})
recipe={'solvent_L_kg_feed':s['solvent_L']/s['polymer_kg'],'aqueous_L_kg_feed':(s['inner_aqueous_L']+s['outer_aqueous_L'])/s['polymer_kg'],'wash_L_kg_feed_bracket':[w/s['polymer_kg'] for w in s['wash_total_L_bracket']]}
recipe['emulsion_L_kg_feed']=recipe['solvent_L_kg_feed']+recipe['aqueous_L_kg_feed']
process=[]
for label,good,hours in [('initial',M,None),('one_percent_factory',repair,d['factory_h']),('one_percent_40min',repair,d['closure_h']-d['other_maintenance_min']/60)]:
    f=good/y; sl=f*recipe['solvent_L_kg_feed']; aq=f*recipe['aqueous_L_kg_feed']; washes=[f*w for w in recipe['wash_L_kg_feed_bracket']]
    total=[aq+w for w in washes]
    process.append({'case':label,'good_kg':good,'feed_kg':f,'solvent_circulation_m3':sl/1000,'aqueous_pre_wash_m3':aq/1000,'wash_circulation_m3_bracket':[w/1000 for w in washes],'total_aqueous_m3_bracket':[w/1000 for w in total],'solvent_makeup_m3_by_recovery':{str(r):sl*(1-r)/1000 for r in d['solvent_recovery_fractions']},'water_makeup_m3_if_reuse_feasible_bracket':[w*(1-d['water_reuse_fraction_sensitivity'])/1000 for w in total],'required_steady_feed_kg_h':None if hours is None else f/hours,'emulsion_steady_hold_m3_lower_bound':None if hours is None else (f/hours)*recipe['emulsion_L_kg_feed']*s['emulsion_hold_h_lower_bound']/1000,'empty_line_first_output_within_window':None if hours is None else hours>=s['emulsion_hold_h_lower_bound']})
pressure=[]
for dwell in d['pressure_hold_h_sensitivity']:
    # lower-scope continuous-equivalent capacity; cannot specify an autoclave from this alone.
    inventory=(feed/d['factory_h'])*dwell
    pressure.append({'hold_h':dwell,'feed_kg_in_hold':inventory,'solid_feed_m3':inventory/rs,'feed_loading_chamber_m3':inventory/rs/d['dense_feed_chamber_fill_fraction'],'is_full_equipment_volume':False})
material=[]
for yy in d['good_yield_sensitivity']:
    for price in d['raw_price_JPY_kg_sensitivity']:
        material.append({'yield':yy,'price_JPY_kg_feed':price,'raw_purchase_JPY':M/yy*price,'raw_only_JPY_good_kg':price/yy,'raw_only_JPY_m2':M/yy*price/g['area_m2']})
annual=[]
passes=d['annual_service_days_example']*d['passes_per_day_example']
for frac in d['replacement_fraction_sensitivity']:
    good=M*frac*passes
    annual.append({'fraction_per_pass':frac,'passes_year':passes,'replacement_good_kg_year':good,'finished_replacement_cost_ceiling_JPY_kg':d['annual_replacement_budget_JPY_example']/good,'raw_600_yield90_JPY_year':good/0.9*600})
opening=d['branch_diameter_um_example']+2*d['clearance_each_side_um_example']
R={'physical_tests':0,'physical_success_probability':None,'reference':{'bed_volume_m3':V,'particle_envelopes_m3':Ve,'dry_material_kg':M,'repair_good_kg':repair,'repair_feed_kg':feed,'solid_m3':M/rs,'internal_pore_m3':Ve-M/rs,'q_internal_max_kg_kg':qmax,'minimum_free_immersed_pore_saturation_to_sink':ref[-1]['neutral_saturation_free_immersed'],'maximum_trapped_fraction_of_pores_for_sinking':1-ref[-1]['neutral_saturation_free_immersed'],'material_raw_budget_JPY_example':d['material_raw_budget_JPY_example'],'raw_feed_price_ceiling_JPY_kg_at_yield90':d['material_raw_budget_JPY_example']*y/M,'hypothetical_minimum_clear_opening_um':opening},'water_sensitivity':wet,'literature_WUR_interpretations':wur,'recipe_ratios':recipe,'process_balances':process,'pressure_feed_volume_sensitivity':pressure,'material_raw_cost_sensitivity':material,'annual_replacement_sensitivity':annual}
eq('bed_volume',V,900);eq('envelope_volume',Ve,450);eq('dry_mass',M,108000);eq('repair_mass',repair,1080);eq('feed_mass',feed,1200)
eq('reference_internal_water_limit',qmax,101/30);eq('solid_volume',M/rs,86.4);eq('pore_volume',Ve-M/rs,363.6)
eq('wet10_percent',ref[1]['lifted_wet_kg'],144360);eq('wet50_percent',ref[2]['lifted_wet_kg'],289800);eq('wet100_percent',ref[3]['lifted_wet_kg'],471600)
eq('neutral_saturation',ref[-1]['neutral_saturation_free_immersed'],95/101)
eq('neutral_density',re+ref[-1]['neutral_saturation_free_immersed']*(1-re/rs)*rw,rw)
eq('S1_solvent_ratio',recipe['solvent_L_kg_feed'],20);eq('S1_aqueous_ratio',recipe['aqueous_L_kg_feed'],140);eq('S1_emulsion_ratio',recipe['emulsion_L_kg_feed'],160)
eq('initial_solvent',process[0]['solvent_circulation_m3'],2400);eq('initial_water_low',process[0]['total_aqueous_m3_bracket'][0],96800);eq('initial_water_high',process[0]['total_aqueous_m3_bracket'][1],336800)
eq('factory_hold_lower_bound',process[1]['emulsion_steady_hold_m3_lower_bound'],144);eq('40min_hold_lower_bound',process[2]['emulsion_steady_hold_m3_lower_bound'],1728)
yes('empty_line_no_40min_output',process[2]['empty_line_first_output_within_window'] is False)
eq('two_hour_feed_chamber',pressure[-1]['feed_loading_chamber_m3'],0.48);eq('raw_price_ceiling',R['reference']['raw_feed_price_ceiling_JPY_kg_at_yield90'],1250/3)
eq('annual_1_percent_mass',annual[1]['replacement_good_kg_year'],216000);eq('annual_cost_ceiling',annual[1]['finished_replacement_cost_ceiling_JPY_kg'],10000000/216000)
eq('required_clear_opening',opening,50)
yes('WUR_exceeds_internal_capacity_in_both_definitions',all(z['water_kg_kg']>qmax for z in wur))
yes('physical_probability_unassigned',R['physical_success_probability'] is None and R['physical_tests']==0)
yes('all_water_rows_conserve_mass',all(math.isclose(z['dry_kg']+z['pore_water_kg'],z['lifted_wet_kg']) for z in wet))
R['numerical_checks']=len(checks)
(P/'results.json').write_text(json.dumps(R,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(P/'validation.json').write_text(json.dumps({'passed':all(c['passed'] for c in checks),'count':len(checks),'physical_tests':0,'checks':checks},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
with (P/'water_and_mass.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(wet[0]),lineterminator='\n'); w.writeheader();w.writerows(wet)
print(json.dumps({'checks':len(checks),'physical_tests':0,'reference':R['reference'],'WUR_interpretations':wur},ensure_ascii=False))
