"""H35: conditional crystal-neck budgets. No material selection or success probability."""
from pathlib import Path
import json,math
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
checks=[]
def ck(name,a,b,rel=1e-10,ab=1e-12):
 ok=math.isclose(a,b,rel_tol=rel,abs_tol=ab);checks.append(dict(name=name,actual=a,expected=b,passed=ok));assert ok,(name,a,b)
g=I['geometry']; D=g['D_um']*1e-6; L=g['neck_length_um']*1e-6; phi=g['packing_fraction']; z=g['coordination'];rho=g['neck_material_density_kg_m3'];S=g['neck_effective_strength_Pa'];T=g['target_isotropic_normal_budget_Pa']
n=6*phi/(math.pi*D**3); nc=n*z/2
cases=[]
for area in I['bed']['areas_m2']:
 V=area*I['bed']['depth_m']; Mh=V*phi*g['host_envelope_density_kg_m3']
 for f in g['seeded_surface_fraction']:
  p=f*f; r=D*math.sqrt(T/(z*phi*p*S)); F=S*math.pi*r*r; N=nc*p*V; M=N*math.pi*r*r*L*rho
  cases.append(dict(area_m2=area,bed_volume_m3=V,host_mass_kg=Mh,seeded_surface_fraction=f,pair_probability_hypothesis=p,mean_active_contacts_per_grain=z*p,neck_radius_um=r*1e6,neck_force_N=F,active_neck_count=N,bridge_mass_kg=M,virial_normal_budget_Pa=N*F*D/(3*V),fits_local_radius=r*1e6<=g['local_available_radius_um'],connectivity_proven=False))
base=cases[0]
solution_rows=[]
for area in I['bed']['areas_m2']:
 b=next(x for x in cases if x['area_m2']==area)
 for solution in I['solutions']:
  dc=solution['feed_kg_m3']-solution['equilibrium_kg_m3']
  for repaired in I['regrowth']['repaired_bond_fraction']:
   for new in I['regrowth']['new_crystal_fraction_of_repaired_bridge']:
    for eta in I['regrowth']['useful_precipitate_fraction']:
     M=b['bridge_mass_kg']*repaired*new; V=M/(eta*dc); max_precip=V*dc
     solution_rows.append(dict(area_m2=area,solution=solution['name'],repaired_fraction=repaired,new_fraction=new,useful_fraction=eta,required_new_bridge_kg=M,solution_volume_m3=V,feed_solute_kg=V*solution['feed_kg_m3'],mother_liquor_solute_kg=V*solution['equilibrium_kg_m3'],unhelpful_precipitate_kg=max_precip-M,water_equivalent_mm=V/area*1000,full_host_mass_precipitation_m3=b['host_mass_kg']/dc))
growth=[]
k=I['growth']
for spacing in k['terrace_spacing_nm']:
 vn=k['reported_step_velocity_nm_s']*k['reported_step_height_nm']/spacing
 for time_min in k['net_growth_time_min']:
  closed=k['two_fronts']*vn*time_min*60/1000
  for gap in k['gaps_um']:
   growth.append(dict(terrace_spacing_nm=spacing,normal_velocity_nm_s=vn,growth_time_min=time_min,gap_um=gap,geometric_closure_um=closed,gap_closure_time_min=gap*1000/(k['two_fronts']*vn*60),closes_gap_in_this_ideal_model=closed>=gap,bond_strength_proven=False,temperature_50C_proven=False))
rain=[]
for s in I['solutions']:
 for mm in I['rain']['rainfall_mm']:
  V=2000*mm/1000
  for e in I['rain']['fraction_reaching_bonds']:
   capacity=V*e*s['equilibrium_kg_m3'];rain.append(dict(solution=s['name'],rainfall_mm=mm,contact_water_fraction=e,potential_dissolution_capacity_kg=capacity,ratio_to_bridge_inventory=capacity/base['bridge_mass_kg'],actual_dissolved_mass_kg=None))
cost=[];tc=I['thermal_cost']
for rr in solution_rows:
 if rr['area_m2']!=2000 or rr['repaired_fraction']!=I['regrowth']['base_repair_fraction'] or rr['new_fraction']!=I['regrowth']['base_new_crystal_fraction']:continue
 V=rr['solution_volume_m3'];sensible=V*tc['water_density_kg_m3']*tc['water_cp_kJ_kg_K']*tc['deltaT_K']/3600
 remain=V*tc['water_density_kg_m3']*(1-tc['post_precipitation_drain_fraction'])
 drying=remain*tc['latent_kJ_kg']/3600
 for rec in tc['heat_recovery_fraction']:
  heat=sensible*(1-rec)/tc['heater_efficiency']
  for price in tc['raw_solute_jpy_kg']:
   variable=heat*tc['electricity_jpy_kWh']+V*tc['water_and_treatment_jpy_m3']+rr['feed_solute_kg']*price
   cost.append(dict(solution=rr['solution'],useful_fraction=rr['useful_fraction'],heat_recovery_fraction=rec,solute_price_jpy_kg=price,solution_m3=V,heating_electricity_kWh=heat,variable_cost_jpy_per_session=variable,variable_cost_jpy_per_year=variable*tc['sessions_per_year'],residual_water_after_drain_kg=remain,latent_heat_kWh=drying,required_drying_thermal_power_kW=drying/(tc['drying_time_min']/60),active_drying_extra_jpy_per_session=drying/tc['heater_efficiency']*tc['electricity_jpy_kWh']))
la=I['literature_audit']; audit=dict(concentration_ratio=la['cystine_concentration_mM']/la['cystine_equilibrium_mM'],relative_excess_supersaturation=la['cystine_concentration_mM']/la['cystine_equilibrium_mM']-1,reported_relative_supersaturation=la['reported_relative_supersaturation'],cystine_equilibrium_kg_m3=la['cystine_equilibrium_mM']*la['cystine_molar_mass_g_mol']/1000)
# Independent geometric, dimensional and conservation checks, not experimental validation.
ck('packing_volume_from_count',n*math.pi*D**3/6,phi)
ck('contacts_half_count',nc*2/n,z)
ck('base_radius_um',base['neck_radius_um'],4.5)
ck('virial_normal_target',base['virial_normal_budget_Pa'],T)
ck('independent_neck_mass_formula',base['bridge_mass_kg'],3*T*base['bed_volume_m3']*L*rho/(S*D))
ck('base_bridge_mass_kg',base['bridge_mass_kg'],5.22)
ck('host_mass_108t',base['host_mass_kg'],108000)
ck('random_double_seed_half_coverage',cases[1]['pair_probability_hypothesis'],.25)
ck('half_seed_doubles_radius',cases[1]['neck_radius_um']/base['neck_radius_um'],2)
ck('fixed_target_mass_independent_p',cases[3]['bridge_mass_kg'],base['bridge_mass_kg'])
ck('p09_radius_15um',cases[2]['neck_radius_um'],15)
ck('tenfold_bed_mass',cases[5]['bridge_mass_kg']/base['bridge_mass_kg'],10)
ck('required_pair_probability_20um',T/(z*phi*S*(20e-6/D)**2),.050625)
s0=solution_rows[0]
ck('feed_mass_conservation',s0['feed_solute_kg'],s0['mother_liquor_solute_kg']+s0['unhelpful_precipitate_kg']+s0['required_new_bridge_kg'])
ck('1percent_total_bridge_renewal',s0['required_new_bridge_kg'],.0522)
ck('mg_ml_equals_kg_m3',5*1e-6/1e-6,5)
ck('cystine_molar_conversion',audit['cystine_equilibrium_kg_m3'],.16821)
ck('relative_S_is_ratio_minus_one',audit['relative_excess_supersaturation'],23/7)
ck('50mm_rain_volume',2000*50/1000,100)
ck('capacity_full_contact_tyr_50mm',next(x for x in rain if x['solution']=='tyrosine_reported_feed' and x['rainfall_mm']==50 and x['contact_water_fraction']==1)['potential_dissolution_capacity_kg'],50)
ck('normal_step_conversion',11.4*5.6/100,.6384)
ck('20min_two_front_closure_um',2*.6384*20*60/1000,1.53216)
ck('gap_time_backcheck',growth[0]['gap_closure_time_min']*60*2*growth[0]['normal_velocity_nm_s']/1000,growth[0]['gap_um'])
ck('terrace10x_slows10x',(11.4*5.6/100)/(11.4*5.6/1000),10)
ck('water_sensible_per_m3_kWh',1000*4.18*70/3600,81.27777777777777)
ck('1m3_5percent_remains_kg',1000*(1-.95),50)
ck('remaining_50kg_latent_kWh',50*2400/3600,100/3)
ck('200sessions_scale',cost[0]['variable_cost_jpy_per_year']/cost[0]['variable_cost_jpy_per_session'],200)
O=dict(schema='h35-conditional-results-v1',physical_tests=0,physical_success_probability=None,neck_network=cases,solution_and_material_balance=solution_rows,growth_kinematics=growth,rain_capacity=rain,variable_costs=cost,literature_arithmetic_audit=audit)
for name,obj in [('results.json',O),('validation.json',dict(check_count=len(checks),all_passed=all(x['passed'] for x in checks),checks=checks,scope='geometry, arithmetic and mass/energy conservation only'))]:
 (P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(checks=len(checks),all_passed=True,base=base,audit=audit),ensure_ascii=False,indent=2))
