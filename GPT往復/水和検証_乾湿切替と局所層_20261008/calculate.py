"""Requirements screening, Python standard library. No experimental probability.
All geometric/material inputs are hypotheses stated in inputs.json.
"""
from pathlib import Path
import json, math, itertools
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8-sig'))
G,L,O,R,S,F,W,B=(I[k] for k in ('grain','layer','operation','reservoir','switch','friction','water','budget'))
pi=math.pi
D=G['equivalent_diameter_um']*1e-6
mg=pi/6*D**3*G['apparent_density_kg_m3']
Mbed=O['area_m2']*O['depth_m']*O['bulk_density_kg_m3']
Ng=Mbed/mg
sphere_area=Ng*pi*D**2

def inventory(n,r_um,t_nm,lam,depth_mm,pocket_um):
    patch=n*pi*(r_um*1e-6)**2
    total_area=Ng*patch
    dry_volume=total_area*t_nm*1e-9
    water_volume=dry_volume*(lam-1)
    pocket_volume=total_area*pocket_um*1e-6
    active_fraction=depth_mm*1e-3/O['depth_m']
    coat_water_kg=water_volume*L['water_density_kg_m3']
    pocket_water_kg=pocket_volume*L['water_density_kg_m3']
    top_water_kg_m2=(coat_water_kg+pocket_water_kg)*active_fraction/O['area_m2']
    return dict(patches=n,radius_um=r_um,dry_thickness_nm=t_nm,swelling=lam,
       active_depth_mm=depth_mm,pocket_depth_um=pocket_um,
       patch_area_per_grain_m2=patch,treated_area_m2=total_area,
       sphere_reference_area_fraction=total_area/sphere_area,
       dry_coating_mass_kg=dry_volume*L['dry_density_kg_m3'],
       all_layer_water_kg=coat_water_kg,all_pocket_water_kg=pocket_water_kg,
       active_water_g_m2=top_water_kg_m2*1000,
       maximum_loss_for_4h_g_m2_h=top_water_kg_m2*1000/O['required_interval_h'],
       wet_thickness_um=t_nm*lam/1000,
       ideal_capillary_pressure_kPa=2*R['surface_tension_N_m']/(r_um*1e-6)/1000)

inv=[inventory(*x) for x in itertools.product(G['patch_counts'],G['patch_radii_um'],
    L['dry_thicknesses_nm'],L['swelling_ratios'],O['active_depths_mm'],R['depths_um'])]
refs=[inventory(4,20,100,10,1,p) for p in R['depths_um']]
# Recess requirement. At zero unsafe-state load the film must remain below rim.
# At target wet load the film must protrude even after compression.
def switch(t_nm,theta_bad,M_MPa,force_mN,unc_nm,clearance_nm=0):
    A=G['reference_patch_count']*pi*(G['reference_patch_radius_um']*1e-6)**2
    p=force_mN*1e-3*S['target_wet_load_fraction']/A
    hwet=t_nm*S['wet_swelling']
    hbad=t_nm*(1+(S['wet_swelling']-1)*theta_bad)
    strain=p/(M_MPa*1e6)
    lower=hbad+unc_nm+clearance_nm
    upper=hwet*(1-strain)-unc_nm
    return dict(dry_thickness_nm=t_nm,unsafe_hydration_max=theta_bad,M_MPa=M_MPa,
       normal_force_mN=force_mN,uncertainty_nm=unc_nm,clearance_nm=clearance_nm,pressure_MPa=p/1e6,
       wet_compression_strain=strain,linear_diagnostic_ok=strain<=S['linear_strain_diagnostic_max'],
       recess_lower_nm=lower,recess_upper_nm=upper,interval_width_nm=upper-lower,
       algebraic_interval_exists=upper>lower,
       reference_850nm_in_interval=lower<S['reference_recess_nm']<upper)
windows=[switch(*x) for x in itertools.product(S['dry_thicknesses_nm'],S['unsafe_hydration_max'],
    S['effective_compressive_moduli_MPa'],S['normal_group_forces_mN'],S['total_height_uncertainties_nm'],S['minimum_noncontact_clearances_nm'])]
window_refs=[switch(100,.8,m,6.48,10) for m in [1,5,8,10,50]]

# Actual normal load share in an additional ideal rigid-rim / linear-pad model.
# Constant modulus over hydration is assumed solely for this kinematic example.
share_path=[]
Aref=G['reference_patch_count']*pi*(G['reference_patch_radius_um']*1e-6)**2
for mod,theta in itertools.product([8,10],[j/100 for j in range(101)]):
    h=100e-9*(1+9*theta)
    gap=h-850e-9
    capacity=max(0,mod*1e6*Aref*gap/h)
    share_path.append(dict(M_MPa=mod,theta=theta,height_nm=h*1e9,
       coating_load_fraction=min(1,capacity/.00648),rigid_rim_load_fraction=max(0,1-capacity/.00648)))

# Contact switching cannot be replaced by area-weighted friction.
friction=[]
for bare,bad,w in itertools.product(F['bare_coefficients'],F['unsafe_coefficients'],F['coating_load_fractions']):
    mu_wet=F['other_drag_coefficient']+(1-w)*bare+w*F['wet_coefficient']
    mu_bad=F['other_drag_coefficient']+(1-w)*bare+w*bad
    limit=(F['total_target']-F['other_drag_coefficient']-bare)/(bad-bare)
    friction.append(dict(bare_mu=bare,unsafe_mu=bad,coat_load_fraction=w,
        total_wet_mu=mu_wet,total_unsafe_mu=mu_bad,
        bare_dry_total_mu=F['other_drag_coefficient']+bare,
        maximum_unsafe_load_fraction=max(0,min(1,limit)) if limit>=0 else None,
        dry_baseline_within_assumed_target=F['other_drag_coefficient']+bare<=F['total_target']+1e-12))
# No evaporation prediction: report finite inventory versus specified losses.
water=[]
for ref,flux in itertools.product(refs,W['specified_loss_flux_kg_m2_h']):
    water.append(dict(pocket_depth_um=ref['pocket_depth_um'],loss_flux_kg_m2_h=flux,
       inventory_exhaustion_seconds_if_loss_constant=ref['active_water_g_m2']/1000/flux*3600,
       gross_floor_supply_L_day_before_application_loss=flux*O['area_m2']*O['operating_h_day']))
energy=[]
for ref,frac in itertools.product(refs,W['evaporation_energy_fractions']):
    flux=frac*W['reference_available_heat_W_m2']/W['latent_heat_J_kg']*3600
    energy.append(dict(pocket_depth_um=ref['pocket_depth_um'],hypothetical_energy_fraction=frac,
        implied_loss_g_m2_h=flux*1000,inventory_exhaustion_seconds_if_loss_constant=ref['active_water_g_m2']/1000/flux*3600))
# Shared hypothetical annual margin, same material mass as prior cycles.
i,n=B['discount'],B['years']
crf=i*(1+i)**n/((1+i)**n-1)
base=(B['nonmaterial_capital_JPY']+Mbed*B['material_JPY_kg'])*crf+B['annual_fixed_JPY']+Mbed*B['material_JPY_kg']*B['annual_material_replacement_fraction']
margin=B['annual_budget_JPY']-base
cost=[]
areas=[('patches',n,r,Ng*n*pi*(r*1e-6)**2) for n,r in itertools.product(G['patch_counts'],G['patch_radii_um'])]
areas.append(('smooth_sphere_reference',None,None,sphere_area))
for kind,n,r,area in areas:
    for rate in I['cost']['recoat_area_fractions_per_closure']:
        gamma=rate*O['closures_per_year']
        factor=crf+B['annual_material_replacement_fraction']+gamma
        cost.append(dict(kind=kind,patch_count=n,patch_radius_um=r,area_m2=area,
             area_recoat_fraction_per_closure=rate,annual_existing_area_recoat_fraction=gamma,
             maximum_all_in_treatment_JPY_m2=margin/(area*factor),
             annual_treated_area_m2=area*(B['annual_material_replacement_fraction']+gamma)))
# Pressure transmitted to a reservoir cannot be assumed retained by capillarity.
pressure=window_refs[0]['pressure_MPa']*1e6
capillary=[]
for r in G['patch_radii_um']:
    pc=2*R['surface_tension_N_m']/(r*1e-6)
    capillary.append(dict(radius_um=r,ideal_Pa=pc,maximum_pressure_transmission_fraction=pc/pressure))
checks=[]
def ck(name,ok):checks.append(dict(name=name,ok=bool(ok)))
def near(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12)
ck('Bed inventory reconstructed',near(Ng*mg,Mbed) and near(Mbed,108000))
ck('Patch area per mass cancels density-volume correctly',near(refs[0]['treated_area_m2'],27648))
ck('Uniform top layer is volume fraction, not full-bed water stock',near(refs[0]['all_layer_water_kg']*.001/.45/2000*1000,refs[0]['active_water_g_m2']))
ck('Water balance for full layer volume',all(near(x['all_layer_water_kg']/1000,(x['swelling']-1)*x['dry_coating_mass_kg']/L['dry_density_kg_m3']) for x in inv))
ck('Pockets add liquid without inventing polymer mass',all(near(x['dry_coating_mass_kg'],refs[0]['dry_coating_mass_kg']) for x in refs))
ck('Depth proportional reservoir storage',near(refs[2]['all_pocket_water_kg'],4*refs[1]['all_pocket_water_kg']))
ck('Reference pressure is force divided by all patch area',near(pressure*refs[0]['patch_area_per_grain_m2'],.00648*.8))
ck('Soft layer counterexample closes switch interval',switch(100,.8,1,6.48,10)['interval_width_nm']<0)
ck('Reference modulus10 permits narrow algebraic interval',switch(100,.8,10,6.48,10)['reference_850nm_in_interval'])
ck('Unsafe state extending to95percent closes same interval',switch(100,.95,10,6.48,10)['interval_width_nm']<0)
ck('Tripled force closes same interval',switch(100,.8,10,19.44,10)['interval_width_nm']<0)
ck('Tolerance subtracts twice from allowable interval',near(switch(100,.8,10,6.48,0)['interval_width_nm']-switch(100,.8,10,6.48,50)['interval_width_nm'],100))
ck('Specified100nm clearance removes reference optimistic interval',switch(100,.8,10,6.48,10,100)['interval_width_nm']<0)
ck('Rigid rim shares conserve normal force',all(near(x['coating_load_fraction']+x['rigid_rim_load_fraction'],1) for x in share_path))
ck('Retreated pads carry zero compression, not proof of zero adhesion',all(x['coating_load_fraction']==0 for x in share_path if x['height_nm']<=850))
ck('Friction endpoints recover bare and coated cases',all(near(x['total_unsafe_mu'],F['other_drag_coefficient']+x['bare_mu']) for x in friction if x['coat_load_fraction']==0) and all(near(x['total_wet_mu'],F['other_drag_coefficient']+F['wet_coefficient']) for x in friction if x['coat_load_fraction']==1))
ck('Friction unsafe load boundary meets target',all(near(F['other_drag_coefficient']+(1-x['maximum_unsafe_load_fraction'])*x['bare_mu']+x['maximum_unsafe_load_fraction']*x['unsafe_mu'],F['total_target']) for x in friction if x['maximum_unsafe_load_fraction'] is not None))
ck('Cost allowance consumes same shared margin',all(near(x['maximum_all_in_treatment_JPY_m2']*x['area_m2']*(crf+.02+x['annual_existing_area_recoat_fraction']),margin) for x in cost))
ck('Narrower pore raises ideal capillary pressure',capillary[0]['ideal_Pa']>capillary[1]['ideal_Pa']>capillary[2]['ideal_Pa'])
ck('Energy inventory loss matches initial stock',all(near(x['implied_loss_g_m2_h']*x['inventory_exhaustion_seconds_if_loss_constant']/3600,next(r['active_water_g_m2'] for r in refs if r['pocket_depth_um']==x['pocket_depth_um'])) for x in energy))
result=dict(evidence=I['evidence'],grain_mass_kg=mg,grain_count=Ng,bed_mass_kg=Mbed,
    whole_sphere_reference_area_m2=sphere_area,reference_inventories=refs,inventory_cases=inv,
    reference_switch_windows=window_refs,switch_windows=windows,ideal_switch_load_path=share_path,friction_cases=friction,
    water_loss_scenarios=water,energy_loss_scenarios=energy,capillary_requirements=capillary,
    annual_baseline_JPY=base,remaining_annual_JPY=margin,CRF=crf,cost_cases=cost)
validation=dict(physical_tests=0,physical_success_probability=None,checks=checks,all_checks_ok=all(x['ok'] for x in checks),
   check_count=len(checks),counts=dict(inventory=len(inv),switch=len(windows),friction=len(friction),cost=len(cost)),
   scope='Mass/force conservation, limiting requirements and constructed counterexamples; no wet/dry/ice qualification.')
for fn,obj in [('results.json',result),('validation.json',validation)]:
    (P/fn).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
assert validation['all_checks_ok'],[x for x in checks if not x['ok']]
print(json.dumps(dict(counts=validation['counts'],checks=len(checks),all_checks_ok=True,physical_tests=0),ensure_ascii=False))
