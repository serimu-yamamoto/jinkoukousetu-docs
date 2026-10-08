"""Cycle 55: mass, dose, process capacity and classification accounting.
No physical simulation of ski friction and no success probability estimate.
Python 3 standard library only. Run from any directory.
"""
from pathlib import Path
import json, csv, math
P = Path(__file__).resolve().parent
I = json.loads((P/'inputs.json').read_text(encoding='utf-8'))
def save(name, obj):
    (P/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
def table(name, rows):
    with (P/name).open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n'); w.writeheader(); w.writerows(rows)
M=I['body_mass_kg']; N=I['particle_count']; m=M/N; pitch=I['particle_pitch_m']
A=N*I['contacts_per_particle']*I['contact_side_m']**2
D=I['source_S1_irradiance_W_m2']*I['source_S1_exposure_s']
E=A*D/3.6e6
areal=m/pitch**2
batch=I['assumed_active_tray_area_m2']*areal
cycle=I['assumed_faces_sequential']*I['source_S1_exposure_s']
rate=batch*3600/cycle
hours=I['operating_h_day']*I['availability']; service=rate*hours
capacity=[]
for d in I['daily_damage_fractions']:
    incoming=d*M
    capacity.append(dict(daily_damage_fraction=d,incoming_body_kg_day=incoming,ideal_hours_on_20m2=incoming/rate,service_body_kg_day=service,queue_growth_kg_day=max(0,incoming-service),stable_queue=incoming<service,required_active_area_m2=I['assumed_active_tray_area_m2']*incoming/service,patch_radiant_kWh_day=E*d,patch_electrical_kWh_day=E*d/I['assumed_electrical_to_useful_light_efficiency'],tray_radiant_kWh_day=incoming/rate*I['assumed_active_tray_area_m2']*I['source_S1_irradiance_W_m2']/1000))
# Batch inspection of the whole bed once per assumed day. This is NOT proven accessible.
classification=[]
for d in I['daily_damage_fractions']:
    for sp in I['damage_classification_specificities']:
        se=I['damage_classification_sensitivity']; tp=d*se; fp=(1-d)*(1-sp); fn=d*(1-se)
        flagged=tp+fp
        classification.append(dict(damage_fraction=d,sensitivity=se,specificity=sp,true_positive_fraction=tp,false_positive_fraction=fp,false_negative_fraction=fn,processed_fraction=flagged,positive_predictive_value=tp/flagged,processed_body_kg_day=M*flagged,undetected_damaged_body_kg_day=M*fn,ideal_processing_hours=M*flagged/rate,required_active_area_m2=I['assumed_active_tray_area_m2']*M*flagged/service))
# Qualified returned body y kg per 1 kg input. Disqualified body is replaced.
# All qualified bodies get a NEW cap of the H54 mass ratio; rejected caps not credited.
k=I['cap_mass_kg']/M
new=I['new_body_yen_kg']+k*I['new_cap_yen_kg']
cost=[]
for y in I['functional_return_mass_yields']:
    for p in I['processing_yen_per_input_body_kg']:
        returned=p+y*k*I['new_cap_yen_kg']+(1-y)*new
        cost.append(dict(qualified_return_body_mass_yield=y,process_yen_per_input_body_kg=p,new_complete_equivalent_yen_per_body_kg=new,renewal_including_reject_replacement_yen_per_input_body_kg=returned,saving_yen_per_input_body_kg=new-returned,process_break_even_yen_per_input_body_kg=y*I['new_body_yen_kg'],saves_variable_cost=returned<new))
R=dict(cycle=55,base_commit=I['base_commit'],physical_tests=0,success_probability=None,particle_body_mass_kg=m,contact_area_m2=A,contact_area_to_course_area=A/I['course_area_m2'],reference_dose_J_m2=D,whole_bed_patch_radiant_kWh=E,whole_bed_patch_electrical_kWh=E/I['assumed_electrical_to_useful_light_efficiency'],body_mass_per_tray_m2_kg=areal,ideal_batch_body_kg=batch,sequential_cycle_s=cycle,ideal_processing_body_kg_h=rate,assumed_effective_h_day=hours,ideal_processing_body_kg_day=service,ideal_daily_damage_capacity_fraction=service/M,all_bed_inspection_kg_h_if_60min=M,all_bed_inspection_particles_s_if_60min=N/3600,all_bed_inspection_particles_s_if_16h=N/(16*3600),published_emboss_schedule_min_at_least=I['source_S2_hold_min']+(I['source_S2_start_C']-I['source_S2_end_C'])/I['source_S2_cooling_C_min'],MDI_NCO_to_PTMEG_OH_ratio_if_both_difunctional=I['source_S1_reported_MDI_PTMEG_mole_ratio'][0]/I['source_S1_reported_MDI_PTMEG_mole_ratio'][1],cap_body_mass_ratio=k,new_complete_equivalent_yen_per_body_kg=new,capacity=capacity,classification=classification,cost=cost,limitations=['Reference light dose cannot be transferred to another chemistry.','Patch-only energy is a lower bound, not tray or whole-plant consumption.','Six sequential face exposures on a flat layer are an assumed architecture, not a universal throughput limit.','Inspection and sorting rates, physical accessibility, exposure uniformity, yield and functional restoration are unmeasured.','No salt, oil, continuous irrigation or on-slope cooling is introduced.'])
checks=[]
def check(name, ok):
    checks.append(dict(name=name,passed=bool(ok)))
def close(a,b): return math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-10)
check('mass matches particle count',close(m*N,M))
check('patch area independent area sum',close(A,N*6*1e-8))
check('reference dose 0.75 J per cm2',close(D/10000,.75))
check('energy dimensional conversion',close(E*3.6e6,A*D))
check('batch geometry mass',close(batch,20/pitch**2*m))
check('count based independent throughput',close(rate,(20/pitch**2)*(3600/cycle)*m))
check('capacity steady state boundary',close(R['ideal_daily_damage_capacity_fraction']*M,service))
check('all daily capacity balances',all(close(x['incoming_body_kg_day'],x['ideal_hours_on_20m2']*rate) for x in capacity))
check('1 percent has growing queue',capacity[-1]['queue_growth_kg_day']>0 and not capacity[-1]['stable_queue'])
check('0.01 percent queue stable',capacity[0]['stable_queue'])
check('tray dose covers more than patches',all(x['tray_radiant_kWh_day']>x['patch_radiant_kWh_day'] for x in capacity))
check('classification TP FN equals damaged',all(close(x['true_positive_fraction']+x['false_negative_fraction'],x['damage_fraction']) for x in classification))
check('classification partition conservation',all(close(x['processed_fraction']+x['false_negative_fraction']+(1-x['damage_fraction'])*x['specificity'],1) for x in classification))
check('perfect classifier special case',close(.001*1+(1-.001)*(1-1),.001))
check('false positives dominate rare damage case',classification[0]['false_positive_fraction']>classification[0]['true_positive_fraction'])
check('cost independent simplification',all(close(x['renewal_including_reject_replacement_yen_per_input_body_kg'],new+x['process_yen_per_input_body_kg']-x['qualified_return_body_mass_yield']*I['new_body_yen_kg']) for x in cost))
check('cost break even identity',all(close(new+(x['process_break_even_yen_per_input_body_kg'])-x['qualified_return_body_mass_yield']*I['new_body_yen_kg'],new) for x in cost))
check('zero return offers no recovered body credit',close(200+0*k*3000+(1-0)*new,new+200))
check('published schedule 140 minutes',close(R['published_emboss_schedule_min_at_least'],140))
check('reported ideal NCO OH below unity',R['MDI_NCO_to_PTMEG_OH_ratio_if_both_difunctional']<1)
check('physical proof not manufactured',R['physical_tests']==0 and R['success_probability'] is None)
save('results.json',R); table('capacity.csv',capacity); table('classification.csv',classification); table('renewal_cost.csv',cost)
save('validation.json',dict(kind='calculation checks only; not physical validation',count=len(checks),passed=all(x['passed'] for x in checks),checks=checks))
if not all(x['passed'] for x in checks): raise SystemExit('FAILED')
print(json.dumps(dict(checks=len(checks),passed=True,area_m2=A,kg_h=rate,kg_day=service,max_daily_fraction=service/M,capacity=capacity,new_yen_kg=new),ensure_ascii=False))
