"""Uncalibrated winter load-path diagnostic; no avalanche safety prediction."""
from pathlib import Path
import json,math
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
A=I['assumptions']; B=I['comparison']
def save(name,obj):
 (P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def load(h,z,theta,slope=None):
 if min(h,z,theta)<0 or z>A['bed_depth_m'] or theta>1:raise ValueError('Out of geometric diagnostic range')
 beta=math.radians(A['slope_deg'] if slope is None else slope)
 ms=A['snow_density_kg_m3']*h
 ma=A['artificial_dry_bulk_density_kg_m3']*z
 mw=A['water_density_kg_m3']*theta*z
 return {'snow_mass_kg_m2':ms,'artificial_mass_kg_m2':ma,'water_mass_kg_m2':mw,'total_mass_kg_m2':ms+ma+mw,'N_Pa':(ms+ma+mw)*A['g_m_s2']*math.cos(beta),'D_Pa':(ms+ma+mw)*A['g_m_s2']*math.sin(beta)}
def assess(h,z,theta,c=0,r=0,mu=None,slope=None):
 if c<0 or r<0:raise ValueError('Nonnegative c and r required')
 mu=A['mu_residual'] if mu is None else mu
 if mu<0:raise ValueError('Negative friction')
 l=load(h,z,theta,slope);n=l['N_Pa'];d=l['D_Pa'];u=r*n
 row={'h_m':h,'z_m':z,'theta':theta,'c_Pa':c,'mu':mu,'r':r,**l,'u_Pa':u}
 if n<=0 or u>=n:
  return {**row,'valid_contact':False,'resistance_Pa':None,'ratio_R_over_D':None,'c_required_Pa':None}
 R=c+mu*(n-u)
 return {**row,'valid_contact':True,'resistance_Pa':R,'ratio_R_over_D':R/d if d>0 else None,'c_required_Pa':max(0,A['diagnostic_load_ratio']*d-mu*(n-u))}
def inverse_r(h,z,theta,c,mu=None):
 mu=A['mu_residual'] if mu is None else mu
 l=load(h,z,theta);n=l['N_Pa'];d=l['D_Pa'];need=A['diagnostic_load_ratio']*d-c
 if n<=0:return {'status':'no_contact','raw_r_max':None}
 if mu==0:return {'status':'any_r_below_one' if need<=0 else 'no_r_feasible','raw_r_max':None}
 if mu<0:raise ValueError('Negative friction')
 raw=1-need/(mu*n)
 return {'status':'no_r_feasible' if raw<0 else 'any_r_below_one' if raw>=1 else 'bounded_r','raw_r_max':raw}
checks=[]
def ck(name,ok):
 checks.append({'name':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
def close(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10)
base=load(1,0,0)
ck('one_metre_snow_mass',close(base['total_mass_kg_m2'],450))
ck('snow_driving_force',close(base['D_Pa'],2207.25))
ck('zero_snow_and_depth_no_contact',not assess(0,0,0)['valid_contact'])
ck('pore_pressure_contact_loss_rejected',not assess(1,.45,.1,r=1)['valid_contact'])
ck('pressure_above_normal_rejected',not assess(1,.45,.1,r=1.01)['valid_contact'])
ck('horizontal_no_division_by_zero',assess(1,.45,0,slope=0)['ratio_R_over_D'] is None)
ck('zero_mu_support_only_c',close(assess(1,.45,.1,c=1000,mu=0)['resistance_Pa'],1000))
ck('zero_mu_inverse_impossible',inverse_r(1,.45,.1,0,mu=0)['status']=='no_r_feasible')
ck('zero_mu_inverse_sufficient',inverse_r(1,.45,.1,100000,mu=0)['status']=='any_r_below_one')
dy=load(.1,.45,0);wet=load(.1,.45,.1);top=load(.1,0,0)
ck('thin_snow_dry_base_2point2_top_load',close(dy['D_Pa']/top['D_Pa'],2.2))
ck('thin_snow_wet_base_3point2_top_load',close(wet['D_Pa']/top['D_Pa'],3.2))
ck('bed_water_mass45',close(wet['water_mass_kg_m2'],45))
ck('dry_bed_mass54',close(dy['artificial_mass_kg_m2'],54))
# Independent cell sum of the normal-depth slab.
m_cells=450+sum((120+1000*.1)*(.45/1000) for _ in range(1000))
ck('mass_integral_matches_cell_sum',close(load(1,.45,.1)['total_mass_kg_m2'],m_cells))
ck('uniform_weight_D_over_N',close(load(1,.45,.1)['D_Pa']/load(1,.45,.1)['N_Pa'],math.tan(math.pi/6)))
rows=[assess(h,z,th) for h in I['snow_normal_depths_m'] for th in I['water_volume_fractions'] for z in I['cut_depths_m']]
peak=[assess(B['snow_normal_depth_m'],z,B['water_volume_fraction'],c,B['pore_pressure_fraction']) for z,c in zip(I['cut_depths_m'],B['assumed_peak_c_Pa'])]
residual=[assess(B['snow_normal_depth_m'],z,B['water_volume_fraction'],c,B['pore_pressure_fraction']) for z,c in zip(I['cut_depths_m'],B['assumed_residual_c_Pa'])]
ck('peak_example_above_diagnostic_budget',min(r['ratio_R_over_D'] for r in peak)>A['diagnostic_load_ratio'])
ck('residual_internal_plane_below_weight',residual[1]['ratio_R_over_D']<1)
ck('surface_and_base_not_limiting_in_counterexample',min(residual[0]['ratio_R_over_D'],residual[2]['ratio_R_over_D'])>A['diagnostic_load_ratio'])
lim=min(range(len(residual)),key=lambda k:residual[k]['ratio_R_over_D'])
ck('interior_plane_limits',lim==1)
surface=[]
for c in range(0,8001,50):
 R0=assess(1,0,.1,c,B['pore_pressure_fraction'])['ratio_R_over_D']
 surface.append({'surface_c_Pa':c,'minimum_ratio':min(R0,*[r['ratio_R_over_D'] for r in residual[1:]])})
ck('surface4_to8kPa_no_system_gain',close(surface[80]['minimum_ratio'],surface[160]['minimum_ratio']))
inv=inverse_r(1,.225,.1,B['constant_internal_c_Pa_for_drainage_inverse'])
ck('drainage_alone_cannot_meet_example_budget',inv['status']=='no_r_feasible')
cneed=residual[1]['c_required_Pa'];repaired=assess(1,.225,.1,cneed,B['pore_pressure_fraction'])
ck('inverse_c_returns_exact_budget',close(repaired['ratio_R_over_D'],A['diagnostic_load_ratio']))
ck('inverse_r_recovers_original_r',close(inverse_r(1,.225,.1,cneed)['raw_r_max'],B['pore_pressure_fraction']))
ck('pressure_increases_required_c',assess(1,.225,.1,r=.5)['c_required_Pa']>assess(1,.225,.1,r=0)['c_required_Pa'])
ck('water_mass_increases_D_at_fixed_r',assess(1,.45,.1)['D_Pa']>assess(1,.45,0)['D_Pa'])
ck('surface_load_independent_of_bed_water',close(assess(1,0,.1)['D_Pa'],assess(1,0,0)['D_Pa']))
# Recover the previous interface-only equation without inventing a measured c.
ck('H48_surface_equation_recovered',close(assess(1,0,0)['c_required_Pa'],1.5*2207.25-.2*450*9.81*math.cos(math.pi/6)))
e=I['equipment_budget_context'];rem=e['cap_tax_included_yen']-e['provisional_tax_included_yen']
ck('equipment_remaining2million',rem==2000000)
ck('area_allowance100yen',close(rem/e['course_area_m2'],100))
ck('not_a_success_estimate',I['evidence_status']['success_probability'] is None)
R={'physical_experiments':0,'success_probability':None,'all_strengths_assumed':True,'load_rows':rows,'peak_counterexample':peak,'residual_counterexample':residual,'limiting_plane_depth_m':residual[lim]['z_m'],'minimum_peak_ratio':min(r['ratio_R_over_D'] for r in peak),'minimum_residual_ratio':min(r['ratio_R_over_D'] for r in residual),'drainage_inverse_counterexample':inv,'required_internal_c_example_Pa':cneed,'surface_only_strength_sweep':surface,'equipment_budget_context':{'remaining_yen':rem,'equivalent_remaining_yen_per_m2':rem/e['course_area_m2'],'additional_works_quote_yen':None},'limitations':I['not_modelled']}
save('results.json',R)
save('validation.json',{'kind':'numerical_diagnostic_checks_not_experiments','count':len(checks),'all_passed':all(x['passed'] for x in checks),'checks':checks})
print(json.dumps({'checks':len(checks),'physical_experiments':0,'minimum_peak_ratio':R['minimum_peak_ratio'],'minimum_residual_ratio':R['minimum_residual_ratio'],'required_internal_c_Pa':cneed,'inverse_r_raw':inv['raw_r_max']}))
