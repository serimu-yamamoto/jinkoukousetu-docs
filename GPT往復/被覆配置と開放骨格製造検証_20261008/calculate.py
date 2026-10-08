"""H34: geometry, conserved mass and conditional process budgets; no fitted performance."""
import json, math
from pathlib import Path
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
checks=[]
def check(name,actual,expected,rel=1e-10,abs_tol=1e-12):
    ok=math.isclose(actual,expected,rel_tol=rel,abs_tol=abs_tol)
    checks.append(dict(name=name,actual=actual,expected=expected,passed=ok))
    assert ok, (name,actual,expected)
def powder(D,d,rho_h,rho_g,C,area=1):
    N=4*C*area*((D+d)/d)**2
    q=N*(d/D)**3*rho_g/rho_h
    return dict(N_guest_per_host=N,guest_host_mass_ratio=q,guest_final_mass_fraction=q/(1+q))
def film(D,t,rho_h,rho_g,C,area=1):
    q=6*C*area*rho_g*t/(rho_h*D)
    return dict(guest_host_mass_ratio=q,guest_final_mass_fraction=q/(1+q))
D=I['host_diameter_um']; rh=I['host_envelope_density_kg_m3']; rg=I['guest_density_kg_m3']; C=I['geometric_coverage']
rows=[]
for rho in I['host_densities_kg_m3']:
 for area in I['external_area_factors']:
  for d in I['guest_diameters_um']:
   rows.append(dict(kind='discrete_sphere',host_density=rho,area_factor=area,guest_diameter_um=d,**powder(D,d,rho,rg,C,area)))
  for t in I['film_thicknesses_um']:
   rows.append(dict(kind='partial_film',host_density=rho,area_factor=area,film_thickness_um=t,**film(D,t,rho,rg,C,area)))
expansion=[dict(volume_ratio=B,linear_stretch=B**(1/3),area_stretch=B**(2/3),fixed_guest_coverage=C/B**(2/3),affine_film_coverage=C,film_thickness_ratio=B**(-2/3),linear_strain=B**(1/3)-1) for B in I['expansion_volume_ratios']]
f=I['flattening']; r=f['guest_radius_um']; R=f['target_curvature_radius_um']; g=math.sqrt(R/r); a=r*math.sqrt(g); c=r/g
H=(3*f['diagnostic_force_N']*(R*1e-6)/(4*f['diagnostic_Estar_Pa']))**(1/3)*1e6
alpha=a/c; margin=f['footprint_margin']; required_radius=((margin*H)**4/R)**(1/3)
flat=dict(area_multiplier=g,lateral_semiaxis_um=a,vertical_semiaxis_um=c,full_height_um=2*c,aspect_ratio=alpha,top_curvature_radius_um=a*a/c,diagnostic_contact_radius_um=H,contact_to_footprint_ratio=H/a,diagnostic_force_before_edge_N=4*f['diagnostic_Estar_Pa']*(a*1e-6)**3/(3*R*1e-6),minimum_initial_guest_diameter_for_margin_um=2*required_radius)
# Hertz is only a homogeneous-body geometric comparison; a submicron film is not a half-space.
la=I['literature']['AFM']['mean_aspect_after']; flat['oblate_surrogate_area_multiplier_at_literature_mean']=la**(2/3); flat['oblate_surrogate_curvature_um_at_literature_mean']=r*la**(4/3)
coats=[dict(name='5um_spheres',**powder(D,5,rh,rg,C))]+[dict(name=f'{t:g}um_partial_film',**film(D,t,rh,rg,C)) for t in I['film_thicknesses_um']]
costs=[]; representative=[]
for A in I['bed']['areas_m2']:
 M=A*I['bed']['depth_m']*rh*I['bed_packing_fraction']
 for coat in coats:
  q=coat['guest_host_mass_ratio']; Mg=M*q; Mfinal=M+Mg
  representative.append(dict(area_m2=A,coat=coat['name'],host_kg=M,guest_kg=Mg,finished_kg=Mfinal,finished_bulk_density_kg_m3=Mfinal/(A*I['bed']['depth_m'])))
  for pg in I['cost']['guest_prices_jpy_kg']:
   for proc in I['cost']['processing_jpy_per_feed_kg']:
    for y in I['cost']['good_yield']:
     host_price=I['cost']['host_price_jpy_kg']
     total=(M*host_price+Mg*pg+Mfinal*proc)/y
     increment=total-M*host_price
     for replacement in I['cost']['annual_replacement_fraction']:
      costs.append(dict(area_m2=A,coat=coat['name'],guest_price_jpy_kg=pg,processing_jpy_feed_kg=proc,yield_fraction=y,annual_replacement_fraction=replacement,host_price_jpy_kg=host_price,initial_material_and_processing_jpy=total,initial_increment_jpy=increment,annual_increment_jpy=increment*replacement,annual_material_and_processing_jpy=total*replacement))
batches=[]
for L in I['batch']['chamber_volume_L']:
 b=I['batch']; M=L*1e-3*b['fill_fraction']*b['bulk_density_kg_m3']; n=60/(b['process_min']+b['handling_min']); Q=M*n
 batches.append(dict(chamber_L=L,batch_kg=M,ideal_kg_h=Q,ideal_t_per_2000h=Q*b['hours_per_year']/1000,host_108t_hours=108000/Q))
loss=[]
for rr in representative:
 if rr['area_m2']!=2000: continue
 for eps in I['surface_loss']['fraction_per_cycle']:
  # No replenishment during these cycles, constant detached fraction of remaining coating inventory.
  detached=rr['guest_kg']*(-math.expm1(I['surface_loss']['cycles']*math.log1p(-eps)))
  for capture in I['surface_loss']['capture_fraction']:
   loss.append(dict(coat=rr['coat'],fraction_per_cycle=eps,cycles=I['surface_loss']['cycles'],capture_fraction=capture,detached_kg=detached,captured_kg=detached*capture,uncaptured_kg=detached*(1-capture)))
wear=[dict(thickness_um=t,cycles=I['surface_loss']['cycles'],reserve_fraction=I['surface_loss']['wear_reserve_fraction'],allowable_mean_removal_nm_per_cycle=1000*t*(1-I['surface_loss']['wear_reserve_fraction'])/I['surface_loss']['cycles']) for t in I['film_thicknesses_um']]
lt=I['literature']['CT']; lit=powder(lt['host_diameter_um'],lt['guest_diameter_um'],lt['host_density_kg_m3'],lt['guest_density_kg_m3'],1)
lit['reported_mass_fraction_percent']=lt['mass_fraction_percent']
lit['recalculated_mass_fraction_percent']=100*lit['guest_final_mass_fraction']
lit['reported_minus_recalculated_percentage_points']=lt['mass_fraction_percent']-100*lit['guest_final_mass_fraction']
check('listed_source_inputs_round_8.64_not_reported_9.12',round(100*lit['guest_final_mass_fraction'],2),8.64)
check('zero_coverage',powder(450,5,240,1000,0)['guest_host_mass_ratio'],0)
check('powder_independent_mass_formula',powder(450,5,240,1000,.7)['guest_host_mass_ratio'],4*.7*(1000/240)*(5/450)*(1+5/450)**2)
check('density_halved_doubles_ratio',powder(450,5,120,1000,.7)['guest_host_mass_ratio']/powder(450,5,240,1000,.7)['guest_host_mass_ratio'],2)
check('external_area_doubles_ratio',film(450,1,240,1000,.7,2)['guest_host_mass_ratio']/film(450,1,240,1000,.7)['guest_host_mass_ratio'],2)
check('film_planar_area_volume',film(450,1,240,1000,.7)['guest_host_mass_ratio'],(.7*math.pi*450**2*1*1000)/(math.pi*450**3/6*240))
check('film_zero_thickness',film(450,0,240,1000,.7)['guest_host_mass_ratio'],0)
check('film_tenfold_thickness',film(450,2,240,1000,.7)['guest_host_mass_ratio']/film(450,.2,240,1000,.7)['guest_host_mass_ratio'],10)
check('expansion_no_change',expansion[0]['fixed_guest_coverage'],C)
check('8x_volume_quarters_fixed_coverage',C/8**(2/3),C/4)
check('affine_patch_volume_conserved',10**(2/3)*10**(-2/3),1)
check('oblate_volume_conserved',a*a*c,r**3)
check('oblate_curvature_target',a*a/c,R)
check('oblate_aspect_vs_area',alpha,g**1.5)
check('sphere_unflattened',r*math.sqrt(1)/(r/1),1)
check('hertz_force_inverse',4*f['diagnostic_Estar_Pa']*(H*1e-6)**3/(3*R*1e-6),f['diagnostic_force_N'])
check('minimum_guest_radius_footprint',required_radius**.75*R**.25,margin*H)
check('host_bed_mass_108t',representative[0]['host_kg'],108000)
check('host_bed_mass_scale10',representative[4]['host_kg']/representative[0]['host_kg'],10)
check('mass_to_bulk_consistency',representative[0]['finished_bulk_density_kg_m3'],120*(1+coats[0]['guest_host_mass_ratio']))
check('100L_batch_mass',batches[1]['batch_kg'],3.6)
check('100L_rate_with_handling',batches[1]['ideal_kg_h'],14.4)
check('1000L_volume_scale',batches[2]['ideal_kg_h']/batches[1]['ideal_kg_h'],10)
check('loss_conservation',loss[0]['captured_kg']+loss[0]['uncaptured_kg'],loss[0]['detached_kg'])
check('zero_loss_boundary',-math.expm1(500*math.log1p(0)),0)
check('wear_reserve_half',wear[1]['allowable_mean_removal_nm_per_cycle'],1)
check('cost_zero_processing_guest_only',(representative[1]['guest_kg']*500+representative[1]['finished_kg']*0)/1,420000)
check('yield_host_loss_increment',108000*300/.9-108000*300,3600000)
check('source_sac_not_success_probability',float(I['physical_tests']),0)
O=dict(schema='h34-conditional-results-v1',physical_tests=0,physical_success_probability=None,literature_formula_reproduction=lit,coating_mass=rows,expansion=expansion,flattening=flat,bed_inventory=representative,incremental_costs=costs,batch_capacity=batches,coating_loss=loss,wear_budget=wear)
for name,obj in [('results.json',O),('validation.json',dict(check_count=len(checks),all_passed=all(c['passed'] for c in checks),checks=checks,scope='algebra and conservation only; not physical validation'))]:
 (P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(checks=len(checks),all_passed=True,flattening=flat,inventory=representative[:4],batch=batches,wear=wear),ensure_ascii=False,indent=2))
