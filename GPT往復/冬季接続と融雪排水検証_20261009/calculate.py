"""H48: uncalibrated winter interface, series drainage, sensible heat and cost budgets.
Run: python -X utf8 calculate.py. Only standard library; inputs/outputs SI unless labelled.
No measured success probability is estimated.
"""
import json, math
from pathlib import Path
from itertools import product
P=Path(__file__).resolve().parent
x=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
g=x['gravity_m_s2']; b=math.radians(x['slope_deg']); l=x['load']
D=l['snow_density_kg_m3']*g*l['snow_depth_normal_m']*math.sin(b)
N=l['snow_density_kg_m3']*g*l['snow_depth_normal_m']*math.cos(b)
loads=[]
for u in l['pore_pressure_Pa']:
 c=max(0,l['load_factor']*D-l['friction_hypothesis']*(N-u)) if u<N else None
 loads.append(dict(u_Pa=u,driving_Pa=D,normal_Pa=N,additional_resistance_budget_Pa=c,contact_model_valid=u<N))
c0=loads[0]['additional_resistance_budget_Pa']
e=x['engagement']; area=math.pi*e['particle_diameter_m']**2/4
eng=[]
for p,r,offset in product(e['active_fractions'],e['neck_radii_m'],e['eccentricities_m']):
 n=e['projected_coverage']*p/area; force=c0/n
 A=math.pi*r*r; limit=e['allowable_normal_stress_hypothesis_Pa']
 # Axial force with an eccentric line of action: sigma=F/A+F*e*r/I.
 # Not a transverse short-cantilever formula; arbitrary loading requires a 3D model.
 Fmax=limit*A/(1+4*offset/r)
 maxoffset=(limit*A/force-1)*r/4 if force<=limit*A else None
 eng.append(dict(active_fraction=p,neck_radius_m=r,eccentricity_m=offset,engaged_count_m2=n,required_force_N=force,section_force_limit_N=Fmax,force_ratio=Fmax/force,max_eccentricity_m=maxoffset))
entry=[dict(opening_m=o,sphere_m=d,ratio=o/d,rigid_sphere_has_clearance=o>d,boundary_contact=o==d) for o,d in product(x['entry']['opening_m'],x['entry']['snow_sphere_m'])]
h=x['drainage']; L=h['bed_depth_normal_m']; K=h['bulk_conductivity_m_h']; drains=[]
for z,ratio,q in product(h['skin_depths_m'],h['skin_to_bulk_K'],h['normal_inflow_m_h']):
 eff=L/(z/(K*ratio)+(L-z)/K) if ratio>0 else 0
 cap=eff*math.cos(b)
 # Required surface head above a saturated bed with atmospheric, freely draining outlet.
 # A diagnostic head demand, NOT predicted field pore pressure or time to ponding.
 head=max(0,L*(q/eff-math.cos(b))) if eff>0 else None
 drains.append(dict(skin_depth_m=z,skin_K_ratio=ratio,inflow_normal_m_h=q,effective_K_m_h=eff,zero_head_capacity_m_h=cap,head_demand_m=head,unblocked_fraction_of_K=eff/K))
hh=x['heat']; heat=[]
for v,T in product(hh['water_volume_fractions'],hh['initial_above_zero_K']):
 ms=hh['dry_bulk_density_kg_m3']*hh['bed_depth_normal_m']; mw=hh['water_density_kg_m3']*hh['bed_depth_normal_m']*v
 E=(ms*hh['solid_heat_capacity_hypothesis_J_kgK']+mw*hh['water_heat_capacity_J_kgK'])*T
 # All initial positive sensible heat transferred to snow is a one-reservoir upper allocation.
 # No ground flux, solar input, exchange, freeze latent heat, or natural-ground comparison.
 melt=E/hh['latent_heat_J_kg']
 heat.append(dict(water_volume_fraction=v,initial_temperature_above_zero_K=T,solid_kg_m2=ms,water_kg_m2=mw,sensible_J_m2=E,potential_melt_kg_m2=melt,potential_water_equivalent_mm=melt))
c=x['preparation']; crf=c['discount_rate']*(1+c['discount_rate'])**c['years']/((1+c['discount_rate'])**c['years']-1)
mix=[dict(depth_m=z,volume_m3=z*c['area_slope_m2'],dry_material_in_mixed_zone_kg=z*c['area_slope_m2']*c['dry_bulk_density_kg_m3']) for z in c['mix_depths_m']]
cost=[]
for extra in c['added_tool_cost_including_tax_JPY']:
 total=c['existing_equipment_budget_including_tax_JPY']+extra
 cost.append(dict(additional_capital_including_tax_JPY=extra,capital_plus_legacy_cap_JPY=total,excess_above_ceiling_JPY=max(0,total-c['ceiling_including_tax_JPY']),additional_annual_cash_equivalent_JPY=crf*extra+c['added_annual_operating_hypothesis_JPY']))
checks=[]
def check(name,condition):
 checks.append(dict(name=name,passed=bool(condition)))
 if not condition: raise AssertionError(name)
def near(a,b): return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10)
check('driving_equals_half_weight_at30deg',near(D,450*9.81/2))
check('load_budget_closes',near(c0+l['friction_hypothesis']*N,l['load_factor']*D))
check('pore_pressure_weakens_friction',loads[2]['additional_resistance_budget_Pa']>loads[1]['additional_resistance_budget_Pa']>c0)
check('contact_loss_not_certified',loads[-1]['additional_resistance_budget_Pa'] is None)
check('engagement_area_force_closes',all(near(v['required_force_N']*v['engaged_count_m2'],c0) for v in eng))
check('axial_eccentric_section_reconstructs_stress',all(near(v['section_force_limit_N']/(math.pi*v['neck_radius_m']**2)*(1+4*v['eccentricity_m']/v['neck_radius_m']),e['allowable_normal_stress_hypothesis_Pa']) for v in eng))
check('eccentricity_bound_reconstructs_required_force',all(v['max_eccentricity_m'] is None or near(v['required_force_N']/(math.pi*v['neck_radius_m']**2)*(1+4*v['max_eccentricity_m']/v['neck_radius_m']),e['allowable_normal_stress_hypothesis_Pa']) for v in eng))
check('fullengagement_force_tenth_of_pointone',near(eng[0]['required_force_N'],10*eng[18]['required_force_N']))
check('zeroeccentricity_area_scaling',near(eng[6]['section_force_limit_N']/eng[0]['section_force_limit_N'],4))
check('larger_offset_reduces_section_limit',eng[0]['section_force_limit_N']>eng[1]['section_force_limit_N']>eng[2]['section_force_limit_N'])
check('spherefit_uses_strictclearance',all(v['rigid_sphere_has_clearance']==(v['opening_m']>v['sphere_m']) for v in entry))
check('entry_equal_is_not_clearance',sum(v['boundary_contact'] for v in entry)==1)
check('unobstructed_layer_reduces_to_bulkK',all(near(v['effective_K_m_h'],K) for v in drains if v['skin_K_ratio']==1))
check('sealed_layer_has_zero_capacity',all(v['zero_head_capacity_m_h']==0 and v['head_demand_m'] is None for v in drains if v['skin_K_ratio']==0))
check('series_conductivity_bounded',all(K*v['skin_K_ratio']<=v['effective_K_m_h']+1e-12<=K+1e-12 for v in drains))
check('series_darcy_head_closes',all(v['head_demand_m']==0 or near(v['effective_K_m_h']*(math.cos(b)+v['head_demand_m']/L),v['inflow_normal_m_h']) for v in drains if v['head_demand_m'] is not None))
check('clogged10mm_example',near(next(v['effective_K_m_h'] for v in drains if v['skin_depth_m']==.01 and v['skin_K_ratio']==.001),.45/(.01/.0003+.44/.3)))
check('dry_bed_mass_is54kgm2',all(near(v['solid_kg_m2'],54) for v in heat))
check('sensible_energy_latent_conversion_closes',all(near(v['potential_melt_kg_m2']*hh['latent_heat_J_kg'],v['sensible_J_m2']) for v in heat))
check('20percent_water_is90kgm2',all(near(v['water_kg_m2'],90) for v in heat if v['water_volume_fraction']==.2))
check('sensible_energy_proportional_to_deltaT',near(heat[2]['sensible_J_m2']/heat[0]['sensible_J_m2'],5))
check('mix_volume_conserved',all(near(v['volume_m3'],v['depth_m']*c['area_slope_m2']) for v in mix))
check('mix_mass_conserved',all(near(v['dry_material_in_mixed_zone_kg'],v['volume_m3']*120) for v in mix))
check('capital_recovery_discounted_sum',near(crf*sum((1+c['discount_rate'])**(-j) for j in range(1,c['years']+1)),1))
check('legacy_budget_headroom_is2M',c['ceiling_including_tax_JPY']-c['existing_equipment_budget_including_tax_JPY']==2000000)
check('cost_grid_excesses', [v['excess_above_ceiling_JPY'] for v in cost]==[0,1000000,4000000])
check('no_invented_probability',x['physical_tests']==0 and x['success_probability'] is None)
result=dict(status=x['status'],physical_tests=0,success_probability=None,loads=loads,engagement=eng,entry=entry,drainage=drains,heat=heat,mixing=mix,cost=cost,capital_recovery_factor=crf,counts=dict(loads=len(loads),engagement=len(eng),entry=len(entry),drainage=len(drains),heat=len(heat),mixing=len(mix),cost=len(cost)))
for fn,v in [('results.json',result),('validation.json',dict(checks=checks,count=len(checks),all_passed=True,scope='Algebra and bookkeeping only; no material or snow validation'))]:
 (P/fn).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(checks=len(checks),counts=result['counts'],additional_budget_Pa=c0,representative_engagement=[v for v in eng if v['active_fraction']==.3 and v['neck_radius_m']==.00003],drain_10mm_0p001=[v for v in drains if v['skin_depth_m']==.01 and v['skin_K_ratio']==.001],heat_at10K=[v for v in heat if v['initial_temperature_above_zero_K']==10],cost=cost),ensure_ascii=False))
