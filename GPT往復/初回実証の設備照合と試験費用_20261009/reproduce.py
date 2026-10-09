"""Cycle 82: auditable experiment logistics, geometry and metrology; no material validation."""
from pathlib import Path
import json,math,random
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf8'))
T=I['test']; checks=[]
def ck(name,ok):
 if not ok: raise AssertionError(name)
 checks.append({'name':name,'passed':True})
def save(name,obj):
 (P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
area=math.pi*(T['diameter_mm']/2)**2
force=T['nominal_pressure_MPa']*area
runs=len(T['materials'])*len(T['states'])*T['replicates']
duration=T['distance_m']/T['speed_m_s']
ck('18_independent_runs',runs==18)
ck('force_units_MPa_equals_N_per_mm2',abs(force-3.7699111843077517)<1e-12)
ck('200_seconds_per_run',duration==200)
geometry=[]
for rmm in I['geometry']['radii_mm']:
 for v in I['geometry']['speeds_m_s']:
  r=rmm/1000; w=I['geometry']['candidate_contact_width_mm']/1000
  circumference=2*math.pi*r; rpm=60*v/circumference
  row={'radius_mm':rmm,'speed_m_s':v,'rpm':rpm,'disk_centerline_revisit_s':circumference/v,'disk_centerline_contact_duration_s_approx':w/v,'disk_centerline_duty_approx':w/circumference,'pin_contact_duration_s':T['distance_m']/v,'disk_revolutions':T['distance_m']/circumference,'speed_min_over_4mm_radial_patch_m_s':v*(r-w/2)/r,'speed_max_over_4mm_radial_patch_m_s':v*(r+w/2)/r,'floor_contact_per_1p6m_ski_s':I['geometry']['ski_length_m']/v}
  ck('rpm_distance_'+str(len(geometry)),math.isclose(rpm/60*row['pin_contact_duration_s'],row['disk_revolutions'],rel_tol=1e-12))
  geometry.append(row)
wear=[]
for k in I['wear_assumptions']['k_mm3_Nm']:
 volume=k*force*T['distance_m']; depth_um=volume/area*1000
 mass_mg=volume*I['wear_assumptions']['density_g_cm3']
 ck('archard_equivalent_'+str(k),math.isclose(depth_um,k*T['nominal_pressure_MPa']*T['distance_m']*1000,rel_tol=1e-12))
 wear.append({'assumed_k_mm3_Nm':k,'depth_um':depth_um,'volume_mm3':volume,'mass_mg_at_assumed_density':mass_mg,'measurement':False})
U=I['uncertainty_assumptions'];mu=U['mu']
umu=math.sqrt((U['u_tangential_force_N']/force)**2+(mu*U['u_normal_force_N']/force)**2)
uncertainty={'force_N':force,'illustrative_tangential_force_N':mu*force,'u_mu_from_force_terms_only':umu,'k2_u_mu_from_force_terms_only':2*umu,'not_total_uncertainty':True,'measured':False}
ck('uncertainty_positive',umu>0)
prices=I['prices']; costs=[{'case':'6_pilot_each_base','runs':6,'basic_units':6,'additional_condition_units':0,'published_tariff_subtotal_yen':6*prices['kistec_base_yen'],'quote':False}, {'case':'18_independent_each_base','runs':18,'basic_units':18,'additional_condition_units':0,'published_tariff_subtotal_yen':18*prices['kistec_base_yen'],'quote':False},{'case':'24_pilot_plus_main_each_base','runs':24,'basic_units':24,'additional_condition_units':0,'published_tariff_subtotal_yen':24*prices['kistec_base_yen'],'quote':False}]
# Alternative is billing interpretation only, never a permission to reuse worn specimens.
costs.append({'case':'18_only_if_3_admin_groups_accepted','runs':18,'basic_units':3,'additional_condition_units':15,'published_tariff_subtotal_yen':3*prices['kistec_base_yen']+15*prices['kistec_add_condition_yen'],'quote':False,'applicability':'unconfirmed; requires acceptance for eighteen independent specimens'})
ck('tariff_18',costs[1]['published_tariff_subtotal_yen']==150480)
ck('tariff_24',costs[2]['published_tariff_subtotal_yen']==200640)
ck('no_false_total',all(c['quote'] is False for c in costs))
time=[]
for prep in I['processing_assumptions']['setup_minutes_per_run']:
 for scan in I['processing_assumptions']['profile_minutes_per_scan']:
  slide=runs*duration/3600; prep_h=runs*prep/60; shape=runs*2*scan/60
  time.append({'runs':runs,'setup_minutes_per_run_assumed':prep,'minutes_per_profile_assumed':scan,'pure_sliding_hours':slide,'setup_hours':prep_h,'profile_hours':shape,'serial_hours_excluding_overhead':slide+prep_h+shape,'not_machine_reservation_or_quote':True})
ck('pure_motion_one_hour',all(x['pure_sliding_hours']==1 for x in time))
# One independent dry/wet coupon for every material in each replicate block.
plan=[];rng=random.Random(82)
for rep in range(1,4):
 block=[(mat,state) for mat in T['materials'] for state in T['states']];rng.shuffle(block)
 for mat,state in block:
  seq=len(plan)+1;plan.append({'run_id':f'M82-{seq:02d}','replicate_block':rep,'material':mat,'state':state,'candidate_coupon_id':f'C82-{seq:02d}','new_counterface_id':f'S82-{seq:02d}','temperature_C':50,'speed_m_s':1,'nominal_pressure_MPa':.3,'target_distance_m':200,'orientation':'candidate fixed pin; UHMWPE moving track, provisional pending pilot','status':'not_run','data':None})
ck('new_candidate_each_run',len({x['candidate_coupon_id'] for x in plan})==18)
ck('new_counterface_each_run',len({x['new_counterface_id'] for x in plan})==18)
ck('balanced_blocks',all(sum(x['replicate_block']==r for x in plan)==6 for r in range(1,4)))
ck('no_simulated_measurements',all(x['status']=='not_run' and x['data'] is None for x in plan))
summary={'cycle':82,'physical_experiments':0,'success_probability':None,'equipment_or_collaborators_secured':False,'provider_contacts_sent':0,'purchase_orders':0,'main_runs_planned':18,'optional_setup_pilot_runs':6,'area_mm2':area,'force_N':force,'main_motion_hours':runs*duration/3600,'kistec_18_basic_tariff_subtotal_yen':costs[1]['published_tariff_subtotal_yen'],'main_total_cost_yen':None,'numeric_checks':len(checks),'calculation_rows':len(geometry)+len(wear)+len(costs)+len(time),'goal_complete':False}
for name,obj in [('geometry.json',geometry),('wear_detection.json',wear),('force_uncertainty.json',uncertainty),('cost_scenarios.json',costs),('time_scenarios.json',time),('main_run_plan.json',plan),('checks.json',checks),('summary.json',summary)]:save(name,obj)
print(json.dumps(summary,ensure_ascii=False))
