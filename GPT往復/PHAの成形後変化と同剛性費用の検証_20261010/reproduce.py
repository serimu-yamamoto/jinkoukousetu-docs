"""Source-fit arithmetic and conditional cost bounds; not ski validation."""
from pathlib import Path
import json,math,sys
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
def drift(age,hours,b):
 if age<=0 or hours<0 or b<=0:raise ValueError('outside model domain')
 return math.expm1(b*math.log1p(hours/age))
def min_age(hours,b,delta):return hours/math.expm1(math.log1p(delta)/b)
def main():
 checks=[]
 def ck(name,b):
  checks.append({'name':name,'passed':bool(b)})
  if not b:raise AssertionError(name)
 mats=I['source']['materials'];aging=[];windows=[];source_ratios=[]
 for m in mats:
  b=m['power_exponent'];unc=m['exponent_reported_plus_minus']
  source_ratios.append({'material':m['name'],'G_10day_to_5min':m['rubbery_G_MPa'][-1]/m['rubbery_G_MPa'][0],'yield_parameter_10day_to_5min':m['yield_parameter_MPa'][-1]/m['yield_parameter_MPa'][0],'interpretation':'reported fit parameters, not recovery or 50C modulus'})
  for age in I['aging']['diagnostic_age_hours']:
   for H in I['aging']['operating_hours']:
    aging.append({'material':m['name'],'start_age_hours':age,'run_hours':H,'nominal_fractional_drift':drift(age,H,b),'lower_exponent_drift':drift(age,H,b-unc),'upper_exponent_drift':drift(age,H,b+unc),'all_ages_within_5min_10day':age>=1/12 and age+H<=240,'actual_50C_prediction':False})
  for H in I['aging']['operating_hours']:
   for tol in I['aging']['allowable_fractional_stiffness_drift']:
    for exponent in [b-unc,b,b+unc]:
     age=min_age(H,exponent,tol)
     windows.append({'material':m['name'],'run_hours':H,'assumed_drift_limit':tol,'exponent':exponent,'minimum_age_hours':age,'within_age_window':age>=1/12 and age+H<=240,'actual_50C_prediction':False})
     ck('age_inverse_'+str(len(windows)),math.isclose(drift(age,H,exponent),tol,rel_tol=1e-12))
 e=I['economics'];rho0=e['reference_PE_density_kg_m3'];M0=e['reference_PE_mass_kg'];E0=e['reference_PE_50C_modulus_MPa_assumed'];p0=e['reference_PE_price_JPY_kg_assumed']
 economy=[];same_geometry=[];boundaries=[];ceilings=[]
 for m in mats:
  rho=m['density_kg_m3'];rr=rho/rho0
  same_geometry.append({'material':m['name'],'mass_kg_same_solid_volume':M0*rr,'mass_ratio':rr})
  for E in e['PHA_50C_moduli_MPa_assumed']:
   maxprice=p0/rr*(E/E0)**(1/3)
   ceilings.append({'material':m['name'],'assumed_E50_MPa':E,'max_raw_price_JPY_kg_for_parity':maxprice,'actual_price_JPY_kg':None})
   ck('price_ceiling_'+m['name']+'_'+str(E),math.isclose(rr*(E0/E)**(1/3)*maxprice/p0,1,rel_tol=1e-12))
  for price in e['PHA_prices_JPY_kg_assumed']:
   bound=E0*(rr*price/p0)**3
   boundaries.append({'material':m['name'],'assumed_PHA_price_JPY_kg':price,'required_PHA_modulus_MPa_for_raw_cost_parity':bound,'actual_modulus_MPa':None})
   ck('price_parity_'+m['name']+'_'+str(price),math.isclose(rr*(E0/bound)**(1/3)*price/p0,1,rel_tol=1e-12))
   for E in e['PHA_50C_moduli_MPa_assumed']:
    tr=(E0/E)**(1/3);mr=rr*tr;cr=mr*price/p0
    economy.append({'material':m['name'],'assumed_E50_MPa':E,'assumed_price_JPY_kg':price,'thickness_ratio':tr,'mass_ratio':mr,'finished_mass_kg':M0*mr,'raw_resin_cost_JPY':M0*mr*price,'raw_cost_ratio_to_PE':cr,'quoted':False,'qualified_geometry':False})
    ck('equal_EI_'+str(len(economy)),math.isclose(E*tr**3,E0,rel_tol=1e-12))
 c=I['conditioning'];holding=[];days=c['nominal_hold_days'];Q=c['production_kg_day_assumed'];stock=Q*days
 for density in c['bulk_density_kg_m3_assumed']:
  for unit in c['warehouse_JPY_m3_day_assumed']:
   storage=unit*days/density;capital=c['PHA_price_JPY_kg_assumed']*c['annual_capital_rate_assumed']*days/365
   holding.append({'assumed_hold_days':days,'assumed_bulk_density_kg_m3':density,'assumed_storage_JPY_m3_day':unit,'work_in_process_kg':stock,'work_in_process_m3':stock/density,'storage_JPY_per_finished_kg':storage,'capital_JPY_per_finished_kg':capital,'partial_holding_JPY_per_kg':storage+capital,'heat_energy_and_equipment_included':False})
   ck('holding_flow_balance_'+str(len(holding)),math.isclose((stock/density)*unit/Q,storage,rel_tol=1e-12))
 ck('zero_operating_interval',drift(24,0,.095)==0)
 ck('older_material_drifts_less',drift(72,8,.095)<drift(24,8,.095)<drift(1,8,.095))
 ck('larger_exponent_drifts_more',drift(72,8,.186)>drift(72,8,.095))
 ck('age_relation_homogeneous',math.isclose(min_age(8,.186,.02),2*min_age(4,.186,.02),rel_tol=1e-12))
 ck('no_unit_dependence',math.isclose(drift(72,8,.186),drift(72*3600,8*3600,.186),rel_tol=1e-12))
 ck('age_solutions_in_window',all(x['within_age_window'] for x in windows))
 speed=I['source']['scratch_speed_mm_min']/1000/60
 ck('scratch_speed_conversion',math.isclose(speed,1/12000,rel_tol=1e-12))
 result={'physical_experiments':0,'success_probability':None,'actual_50C_modulus':None,'actual_ski_friction':None,'aging_cases':aging,'conditioning_windows':windows,'source_ratios':source_ratios,'same_geometry_mass':same_geometry,'equal_bending_cost_cases':economy,'raw_cost_parity_boundaries':boundaries,'raw_price_ceilings':ceilings,'holding_cost_cases':holding,'scratch_speed_m_s':speed,'illustrative_5m_s_to_scratch_speed_ratio':5/speed,'scratch_coefficients_used_for_ski':False,'lifetime_cost_known':False}
 validation={'all_passed':all(c['passed'] for c in checks),'count':len(checks),'checks':checks,'meaning':'arithmetic and source-fit consistency only; not physical tests'}
 for name,obj in [('results.json',result),('validation.json',validation)]:
  raw=(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode()
  if '--check' in sys.argv:assert (P/name).read_bytes()==raw,name
  else:(P/name).write_bytes(raw)
 print(json.dumps({'aging_cases':len(aging),'conditioning_windows':len(windows),'cost_cases':len(economy),'checks':len(checks),'all_passed':validation['all_passed'],'physical_experiments':0}))
if __name__=='__main__':main()
