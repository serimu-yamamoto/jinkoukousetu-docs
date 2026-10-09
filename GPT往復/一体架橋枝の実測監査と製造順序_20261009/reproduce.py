"""Reproduce arithmetic, not an experiment or success probability. Python standard library."""
from pathlib import Path
import json,math,sys
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
checks=[]
def ck(name,condition):
    checks.append({'name':name,'passed':bool(condition)})
    if not condition: raise AssertionError(name)
def near(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-8)
def yield_case(y,r,q):
    if not 0<y<=1 or not 0<=r<=1:raise ValueError('yield/recovery domain')
    m=I['manufacturing']['finished_kg'];p=I['manufacturing']['virgin_price_JPY_kg']
    gross=m/y;offcut=gross-m;reuse=r*offcut;fresh=gross-reuse
    return {'yield':y,'pre_crosslink_recovery':r,'charge_JPY_kg':q,'gross_cut_kg':gross,'offcut_kg':offcut,'reused_kg':reuse,'fresh_kg_after_cut_route':fresh,'fresh_kg_before_cut_route':gross,'irradiated_kg_after_cut_route':m,'irradiated_kg_before_cut_route':gross,'fresh_material_saving_JPY':reuse*p,'irradiation_saving_JPY':offcut*q,'combined_saving_before_extra_handling_JPY':reuse*p+offcut*q,'extra_handling_break_even_JPY_finished_kg':(reuse*p+offcut*q)/m}
T=[]
for x in I['source_table']['rows']:
    v=x['virgin_mm'];c=x['crosslinked_mm'];r=dict(x,remaining_ratio=c/v,reduction_from_virgin_percent=100*(v-c)/v,difference_divided_by_crosslinked_percent=100*(v-c)/c,virgin_terminal_strain=v/20,crosslinked_terminal_strain=c/20)
    T.append(r)
    ck('ratio_identity_'+x['label'],near(r['remaining_ratio']+r['reduction_from_virgin_percent']/100,1))
    ck('table_difference_denominator_'+x['label'],abs(r['difference_divided_by_crosslinked_percent']-x['printed_difference_percent'])<.1)
M=I['manufacturing'];C=[yield_case(y,r,q) for y in M['yields'] for r in M['pre_crosslink_offcut_recovery'] for q in M['irradiation_charge_JPY_kg']]
for k,x in enumerate(C):
    ck('mass_balance_'+str(k),near(x['fresh_kg_after_cut_route'],M['finished_kg']+x['offcut_kg']-x['reused_kg']))
    ck('cost_balance_'+str(k),near(x['combined_saving_before_extra_handling_JPY'],(x['fresh_kg_before_cut_route']-x['fresh_kg_after_cut_route'])*M['virgin_price_JPY_kg']+(x['irradiated_kg_before_cut_route']-x['irradiated_kg_after_cut_route'])*x['charge_JPY_kg']))
central=yield_case(M['central_yield'],M['central_recovery'],M['central_charge'])
E=[]
for d in I['energy']['dose_kGy']:
    e=M['finished_kg']*d/3600 # kGy=kJ/kg, kWh=3600 kJ
    for efficiency in I['energy']['absorbed_to_grid_efficiency']:
        E.append({'dose_kGy':d,'efficiency':efficiency,'absorbed_kWh':e,'grid_kWh':e/efficiency,'electricity_only_JPY':e/efficiency*I['energy']['electricity_JPY_kWh'],'ideal_beam_hours_at_reference_power':e/I['energy']['beam_power_kW_reference']})
ck('Gy_unit_reference',near(135000*120/3600,4500))
tr=I['transport'];transport=[]
for speed in tr['speed_m_min']:
    for layers in tr['layers']:
        gross=tr['density_kg_m3']*tr['sheet_thickness_m']*tr['width_m']*speed*60*layers
        net=gross*tr['yield']
        transport.append({'speed_m_min':speed,'layers':layers,'gross_capacity_kg_h':gross,'finished_capacity_kg_h':net,'ideal_running_hours':M['finished_kg']/net,'scheduled_hours_at_assumed_utilization':M['finished_kg']/net/tr['utilization']})
        ck('transport_mass_balance_'+str(speed)+'_'+str(layers),near(net*transport[-1]['ideal_running_hours'],M['finished_kg']))
L=[]
for f in I['lifetime']['annual_replacement_fraction']:
    mass=M['finished_kg']*f*I['lifetime']['years']
    L.append({'annual_fraction':f,'years':I['lifetime']['years'],'replacement_kg':mass,'raw_material_plus_assumed_irradiation_JPY':mass*(I['lifetime']['price_before_crosslink_JPY_kg']+I['lifetime']['charge_JPY_kg'])})
ck('full_yield_zero_saving',near(yield_case(1,.95,150)['combined_saving_before_extra_handling_JPY'],0))
ck('no_recovery_no_raw_saving',near(yield_case(.65,0,150)['fresh_material_saving_JPY'],0))
ck('full_recovery_fresh_equals_product',near(yield_case(.65,1,150)['fresh_kg_after_cut_route'],135000))
ck('50C_percent_uses_virgin',near(T[1]['reduction_from_virgin_percent'],36.507936507936506))
ck('post_crosslink_not_free_recycling',M['post_crosslink_same_grade_remelt_recovery']==0)
result={'physical_experiments':0,'success_probability':None,'actual_50C_creep_of_proposed_product':None,'actual_recovery':None,'actual_wear':None,'actual_ski_friction':None,'source_table_recalculation':T,'manufacturing_cases':C,'central_manufacturing_case':central,'energy_cases':E,'transport_cases':transport,'lifetime_cases':L}
validation={'all_passed':all(x['passed'] for x in checks),'count':len(checks),'checks':checks,'meaning':'arithmetic consistency only; no material success rate'}
for name,data in [('results.json',result),('validation.json',validation)]:
    content=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()
    if '--check' in sys.argv:
        if (P/name).read_bytes()!=content:raise AssertionError('Reproduction mismatch '+name)
    else:(P/name).write_bytes(content)
print(json.dumps({'numeric_checks':len(checks),'all_passed':validation['all_passed'],'manufacturing_cases':len(C),'physical_experiments':0,'success_probability':None}))
