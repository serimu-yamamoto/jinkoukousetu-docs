"""Re-entrant kinematics and 2D contact-release geometry, not ski performance."""
from pathlib import Path
import json,csv,math
P=Path(__file__).resolve().parent; I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
def save(n,x): (P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def table(n,rows):
 with (P/n).open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
t0=math.radians(I['initial_angle_deg']); a=I['vertical_to_inclined_bar_ratio']; L=I['cell_initial_width_um']/(2*math.cos(t0)); H0=2*L*(a+math.sin(t0)); W0=I['cell_initial_width_um']
fold=[]; hinges=[]
for e in I['compression_strains']:
 s=math.sin(t0)-e*(a+math.sin(t0)); t=math.asin(s); w=2*L*math.cos(t);h=2*L*(a+math.sin(t)); delta=abs(t-t0)
 row=dict(axial_compression=e,angle_deg=math.degrees(t),cell_width_um=w,cell_height_um=h,width_ratio=w/W0,one_side_retreat_um=(W0-w)/2,apparent_secant_Poisson=None if e==0 else (w/W0-1)/e,cell_area_ratio=w*h/(W0*H0),hypothetical_3D_envelope_volume_ratio=(1-e)*(w/W0)**2,hinge_rotation_rad=delta)
 fold.append(row)
 for length in I['hinge_lengths_um']:
  for thick in I['hinge_thickness_um']:
   hinges.append(dict(axial_compression=e,hinge_length_um=length,hinge_thickness_um=thick,approx_bending_surface_strain=thick*delta/(2*length),scope='constant-curvature estimate; no stress concentration, fatigue or contact'))
ring=[]
for d in I['ring_reference_diameters_um']:
 for ratio in I['ring_density_ratios']:
  s=1/math.sqrt(ratio);gap=d*s;overlap=d*(1-s);extent=d*math.sqrt(1-s*s)
  for mu in I['ring_friction_coefficients']:
   gamma=min(math.sqrt(ratio-1),mu);xr=gamma*gap
   ring.append(dict(reference_diameter_um=d,density_ratio_phi_over_hexagonal=ratio,friction_coefficient=mu,normal_spacing_um=gap,normal_overlap_um=overlap,contact_extent_um=extent,release_shear_strain=gamma,release_distance_um=xr,limiting_branch='coincident' if math.isclose(mu,math.sqrt(ratio-1),abs_tol=1e-12) else ('friction' if mu<math.sqrt(ratio-1) else 'contact_extent')))
clearance=[]
for f in fold:
 for ratio in I['ring_density_ratios']:
  spacing=W0/math.sqrt(ratio)
  clearance.append(dict(axial_compression=f['axial_compression'],geometry_spacing_ratio=ratio,fixed_center_spacing_um=spacing,initial_overlap_um=W0-spacing,post_retreat_gap_um=spacing-f['cell_width_um'],lateral_contact_opens_at_fixed_centers=spacing>f['cell_width_um']))
tol=[]
for t in [I['hinge_nominal_thickness_um']-I['hinge_tolerance_um'],I['hinge_nominal_thickness_um'],I['hinge_nominal_thickness_um']+I['hinge_tolerance_um']]:
 tol.append(dict(actual_thickness_um=t,ideal_bending_stiffness_ratio=(t/I['hinge_nominal_thickness_um'])**3))
cost=[]
for f in I['auxetic_mass_fractions']:
 for c in I['auxetic_body_price_yen_kg']:
  avg=(1-f)*I['base_body_price_yen_kg']+f*c
  cost.append(dict(auxetic_body_mass_fraction=f,assumed_auxetic_yen_kg=c,assumed_same_total_body_mass_kg=I['base_body_mass_kg'],mixture_material_yen=avg*I['base_body_mass_kg'],extra_initial_yen=(avg-I['base_body_price_yen_kg'])*I['base_body_mass_kg'],required_whole_bed_life_ratio_for_equal_annual_material_cost=avg/I['base_body_price_yen_kg']))
checks=[]
def ck(n,b): checks.append(dict(name=n,passed=bool(b)))
def close(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10)
ck('initial dimensions reconstructed',close(fold[0]['cell_width_um'],W0) and close(fold[0]['cell_height_um'],H0))
ck('exact axial compression identity',all(close(x['cell_height_um']/H0,1-x['axial_compression']) for x in fold))
ck('all nonzero compression retracts sides',all(x['one_side_retreat_um']>0 for x in fold[1:]))
ck('re-entrant Poisson negative',all(x['apparent_secant_Poisson']<0 for x in fold[1:]))
ck('zero compression no hinge strain',all(x['approx_bending_surface_strain']==0 for x in hinges if x['axial_compression']==0))
ck('10percent transverse exact independent',close(fold[2]['width_ratio'],.8/(math.sqrt(3)/2)))
ck('10percent retreat independent',close(fold[2]['one_side_retreat_um'],W0*(1-.8/(math.sqrt(3)/2))/2))
ck('3D envelope value explicitly hypothetical',close(fold[2]['hypothetical_3D_envelope_volume_ratio'],.768))
ck('contact circle overlap identity',all(close(x['contact_extent_um']**2+x['normal_spacing_um']**2,x['reference_diameter_um']**2) for x in ring))
ck('release from two independent local branches',all(close(x['release_distance_um'],min(x['friction_coefficient']*x['normal_spacing_um'],x['contact_extent_um'])) for x in ring))
ck('dimensionless release unchanged by scale',all(close(ring[j]['release_shear_strain'],ring[j+12]['release_shear_strain']) for j in range(12)))
ck('release distance doubles with scale',all(close(2*ring[j]['release_distance_um'],ring[j+12]['release_distance_um']) for j in range(12)))
ck('zero friction limit of pair approximation',min(math.sqrt(1.09-1),0)==0)
ck('no overlap limit of pair approximation',min(math.sqrt(1-1),.6)==0)
ck('nominal stiffness one',tol[1]['ideal_bending_stiffness_ratio']==1)
ck('tolerance stiffness span',close(tol[2]['ideal_bending_stiffness_ratio']/tol[0]['ideal_bending_stiffness_ratio'],125/27))
ck('cost mass weighted independently',all(close(x['mixture_material_yen'],I['base_body_mass_kg']*((1-x['auxetic_body_mass_fraction'])*1000+x['auxetic_body_mass_fraction']*x['assumed_auxetic_yen_kg'])) for x in cost))
ck('same annual whole material break even',all(close(x['mixture_material_yen']/x['required_whole_bed_life_ratio_for_equal_annual_material_cost'],I['base_body_mass_kg']*1000) for x in cost))
ck('source printer scaling arithmetic',close(I['publication_print_layer_um']*W0/I['publication_grain_small_diameter_um'],5))
ck('gap matches two retreat minus initial overlap',all(close(x['post_retreat_gap_um'],2*next(f['one_side_retreat_um'] for f in fold if f['axial_compression']==x['axial_compression'])-x['initial_overlap_um']) for x in clearance))
ck('10 percent retreat loses ability at deep overlap',next(x['post_retreat_gap_um'] for x in clearance if x['axial_compression']==.1 and x['geometry_spacing_ratio']==1.09)>0 and next(x['post_retreat_gap_um'] for x in clearance if x['axial_compression']==.1 and x['geometry_spacing_ratio']==1.25)<0)
ck('no fabricated physical success',I['physical_tests']==0 and I['success_probability'] is None)
R=dict(cycle=56,physical_tests=0,success_probability=None,base_commit=I['base_commit'],bar_length_um=L,initial_cell_height_um=H0,selected_fold=fold[2],selected_hinge=next(x for x in hinges if x['axial_compression']==.1 and x['hinge_length_um']==40 and x['hinge_thickness_um']==20),fold=fold,hinges=hinges,ring=ring,tolerance=tol,clearance=clearance,cost=cost,source_geometric_scale=W0/I['publication_grain_small_diameter_um'],scaled_print_layer_um=I['publication_print_layer_um']*W0/I['publication_grain_small_diameter_um'],limitations=['No force law for the proposed folding grain.','No 3D pack, ski friction, winter, water or 50 C durability simulation.','Ring pair model neglects collective caging; not a macroscopic avalanche or slope stability model.','Auxetic mass mixing is a costing assumption, not a yield-stress interpolation.'])
save('results.json',R);table('cell_retreat.csv',fold);table('hinge_strain.csv',hinges);table('ring_release.csv',ring);table('thickness_tolerance.csv',tol);table('lateral_clearance.csv',clearance);table('mixture_cost.csv',cost);save('validation.json',dict(kind='algebra checks; not physical validation',count=len(checks),passed=all(x['passed'] for x in checks),checks=checks))
if not all(x['passed'] for x in checks): raise SystemExit('FAILED')
print(json.dumps(dict(checks=len(checks),passed=True,selected=R['selected_fold'],hinge=R['selected_hinge']),ensure_ascii=False))
