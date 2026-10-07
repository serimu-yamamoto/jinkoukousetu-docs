"""Conditional material/contact screening. Python standard library only.
No measured ski coefficient, no 50C material pass, no physical success rate.
"""
from pathlib import Path
import math,json,itertools
HERE=Path(__file__).resolve().parent
P=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
def main():
 c=P['contact'];contacts=[]
 for p,phi,R,E in itertools.product(c['pressure_Pa'],c['active_fraction'],c['tip_radius_m'],c['effective_modulus_Pa']):
  F=p*c['pitch_m']**2/phi
  a=(3*F*R/(4*E))**(1/3)
  area=math.pi*a*a;delta=a*a/R;pmax=3*F/(2*area);mean=F/area
  # Hertz integral int_0^a 2*pi*r*pmax*sqrt(1-(r/a)^2) dr = F
  restored_force=2*math.pi*pmax*a*a/3
  contacts.append(dict(nominal_pressure_Pa=p,active_fraction=phi,R_m=R,E_star_Pa=E,force_N=F,contact_radius_m=a,indentation_m=delta,maximum_pressure_Pa=pmax,mean_pressure_Pa=mean,a_over_R=a/R,minimum_halfspace_thickness_heuristic_m=3*a,small_contact_screen=a/R<=c['small_contact_radius_ratio_limit'],adhesive_shear_budget_Pa=(c['illustrative_friction_budget']-c['reserved_other_resistance_budget'])*mean,force_integral_error_N=abs(restored_force-F),material_yield_checked=False,friction_predicted=False))
 coats=[]
 r=P['coating']['strand_radius_m']
 for t,q in itertools.product(P['coating']['thickness_m'],P['coating']['coating_core_modulus_ratio']):
  assert 0<t<r
  outer=(1+t/r)
  fixed_core_ratio=(1-t/r)
  coats.append(dict(t_m=t,E_coat_over_core=q,additive_volume_fraction=outer**2-1,additive_EI_ratio=1+q*(outer**4-1),fixed_outer_skin_volume_fraction=1-fixed_core_ratio**2,fixed_outer_EI_ratio=fixed_core_ratio**4+q*(1-fixed_core_ratio**4),two_sided_gap_reduction_m=2*t))
 C=P['cost'];af=(1-(1+C['r'])**(-C['T_year']))/C['r'];mats=[];beams=[]
 for m in P['materials']:
  if 'rho_kg_m3' in m:rho=m['rho_kg_m3']
  else:rho=1/sum(w/d for w,d in zip(m['mass_fractions'],m['component_densities_kg_m3']))
  ratio=rho/P['materials'][0]['rho_kg_m3'];bulk=C['rho_g3_pe_kg_m3']*ratio;M=C['A_m2']*C['h_m']*bulk
  cap=((C['B_yen_year']-C['O_yen_year'])*af-C['I_yen'])/(M*(1+C['lambda_year']*af))
  eac=(C['I_yen']+M*C['P_yen_kg'])/af+C['O_yen_year']+C['lambda_year']*M*C['P_yen_kg']
  mats.append(dict(id=m['id'],rho_kg_m3=rho,same_geometry_number_bulk_kg_m3=bulk,mass_kg=M,EAC_at_500_yen=eac,finished_price_cap_yen_kg=cap,bending_modulus_ratio_to_break_even_mass=ratio**2,packability_validated=False))
  for eq in P['beam']['modulus_ratios']:
   d_ratio=eq**(-.25)
   beams.append(dict(id=m['id'],E_ratio=eq,diameter_ratio=d_ratio,mass_ratio_equal_stiffness=ratio*d_ratio*d_ratio,stress_ratio_equal_load=1/d_ratio**3,required_allowable_stress_ratio=eq**.75,stiffness_ratio_check=eq*d_ratio**4,creep_or_fatigue_pass=False))
 powers=[dict(N_N=P['thermal']['normal_load_N'],v_m_s=v,mu=mu,loss_power_W=P['thermal']['normal_load_N']*v*mu) for v,mu in itertools.product(P['thermal']['velocity_m_s'],P['thermal']['friction_coefficients'])]
 checks={
 'contact_force_conserved':max(x['force_integral_error_N'] for x in contacts)<1e-12,
 'surface_force_from_contact_count':all(math.isclose(x['force_N']*x['active_fraction']/c['pitch_m']**2,x['nominal_pressure_Pa']) for x in contacts),
 'hertz_pressure_radius_scaling':all(math.isclose(y['maximum_pressure_Pa']/x['maximum_pressure_Pa'],3**(-2/3),rel_tol=1e-12) for x in contacts for y in contacts if x['R_m']==.00005 and y['R_m']==.00015 and all(x[k]==y[k] for k in ['nominal_pressure_Pa','active_fraction','E_star_Pa'])),
 'fixed_outer_equal_modulus_unchanged':all(math.isclose(x['fixed_outer_EI_ratio'],1) for x in coats if x['E_coat_over_core']==1),
 'equal_beam_stiffness':all(math.isclose(x['stiffness_ratio_check'],1) for x in beams),
 'same_volume_blend_between_densities':945<mats[2]['rho_kg_m3']<1410,
 'POM_heavier_at_same_geometry':mats[1]['mass_kg']>mats[0]['mass_kg'],
 'price_cap_reconstitutes_budget':all(math.isclose((C['I_yen']+x['mass_kg']*x['finished_price_cap_yen_kg'])/af+C['O_yen_year']+C['lambda_year']*x['mass_kg']*x['finished_price_cap_yen_kg'],C['B_yen_year'],rel_tol=1e-12) for x in mats)}
 assert all(checks.values())
 out=dict(scope=P['scope'],physical_test_count=0,physical_success_probability=None,contact_sweep=contacts,coating_sweep=coats,materials_cost=mats,equal_stiffness_beam_comparison=beams,mechanical_loss_power=powers)
 (HERE/'results.json').write_text(json.dumps(out,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
 (HERE/'validation.json').write_text(json.dumps(dict(checks=checks,contact_cases=len(contacts),coating_cases=len(coats),beam_cases=len(beams),material_validation=False),indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(materials=mats,checks=checks)))
if __name__=='__main__':main()
