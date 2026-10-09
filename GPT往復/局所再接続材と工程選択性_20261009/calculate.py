"""Deterministic screening only. No empirical fit or success probabilities."""
import csv, json, math
from pathlib import Path
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
g=I['geometry']; r=I['reference']; s=I['sensitivity']; k=I['kinetics']; m=I['manufacturing']; th=I['thermal']
V=g['area_m2']*g['depth_m']; D=g['grain_diameter_m']; phi=g['envelope_packing']; z=g['coordination']; rho=g['assumed_dry_patch_density_kg_m3']; ell=g['total_joined_patch_length_m']; c=g['assumed_network_strength_Pa']
N=6*phi*V/(math.pi*D**3); pairs=N*z/2; faces=2*pairs; surface=6*phi*V/D
coat=surface*g['full_coating_thickness_m']*rho
checks=[]
def check(name, cond):
    checks.append({'name':name,'passed':bool(cond)})
    if not cond: raise AssertionError(name)
def near(a,b): return math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-12)
def joint(sig,q):
    F=c*math.pi*D**2/(phi*z*q)
    a=math.sqrt(F/(math.pi*sig)); mass=pairs*math.pi*a*a*ell*rho
    check(f'mass_identity_{sig}_{q}',near(mass,3*c*V*ell*rho/(D*sig*q)))
    return {'joint_strength_Pa':sig,'active_fraction':q,'force_N':F,'radius_um':a*1e6,'radius_over_D':a/D,'installed_dry_kg':mass,'feed_dry_kg':mass/r['downstream_mass_yield'],'fermentation_m3':mass/r['downstream_mass_yield']/r['protein_titer_kg_m3'],'patch_surface_m2':mass/(rho*ell/2),'radius_diagnostic_ok':a/D<=g['diagnostic_max_radius_over_D']}
rows=[joint(sig,q) for sig in s['joint_strength_Pa'] for q in s['active_fraction']]
ref=joint(r['effective_joint_strength_Pa'],r['active_fraction'])
check('reference_mass_1404',near(ref['installed_dry_kg'],1404))
check('full_coat_mass_38610',near(coat,38610))
check('reference_patch_fraction_1_over_27_5',near(ref['installed_dry_kg']/coat,1/27.5))
check('reference_surface_fraction',near(ref['patch_surface_m2']/surface,ref['installed_dry_kg']/coat))
select=[]
for t in k['groom_dwell_s']:
    kmin=-math.log1p(-k['minimum_groom_recovery'])/t
    kmax=-math.log1p(-k['maximum_unwanted_recovery'])/k['operating_dwell_s']
    select.append({'groom_s':t,'k_groom_min_per_s':kmin,'k_unwanted_max_per_s':kmax,'required_rate_ratio':kmin/kmax,'same_rate_unwanted_h':-math.expm1(-kmin*k['operating_dwell_s'])})
check('rate_bounds_recover_0_8',near(-math.expm1(-select[2]['k_groom_min_per_s']*60),0.8))
check('rate_bounds_avoid_0_1',near(-math.expm1(-select[2]['k_unwanted_max_per_s']*18000),0.1))
check('duration_scaling',near(select[0]['required_rate_ratio']/select[2]['required_rate_ratio'],60))
cycles_year=s['passes_per_day']*s['operating_days_year']
costs=[]
for j in rows:
    for price in s['protein_price_JPY_kg']:
        for lifetime in s['contact_lifetime_cycles']:
            costs.append({'joint_strength_Pa':j['joint_strength_Pa'],'active_fraction':j['active_fraction'],'radius_diagnostic_ok':j['radius_diagnostic_ok'],'price_JPY_kg_assumed':price,'lifetime_cycles_assumed':lifetime,'initial_material_JPY':j['feed_dry_kg']*price,'annual_replacement_material_JPY':j['feed_dry_kg']*price*cycles_year/lifetime})
ref_cost=ref['feed_dry_kg']*10000
rain=[{'release_fraction':f,'released_protein_kg':ref['installed_dry_kg']*f,'added_protein_mg_L':ref['installed_dry_kg']*f*1000/th['rain_volume_m3']} for f in th['assumed_release_fractions']]
carrier_mass=V*g['nominal_carrier_bulk_density_kg_m3']; deltaT=th['activation_C']-th['carrier_start_C']
heat_patch=ref['installed_dry_kg']*th['patch_cp_J_kgK']*deltaT/3.6e6
heat_carrier=carrier_mass*th['carrier_cp_J_kgK']*deltaT/3.6e6
summary={'evidence_status':I['status'],'volume_m3':V,'grain_count':N,'potential_pairs':pairs,'patch_faces':faces,'equivalent_sphere_area_m2':surface,'full_5um_coating_dry_kg':coat,'full_coating_fermentation_m3':coat/r['downstream_mass_yield']/r['protein_titer_kg_m3'],'reference':ref,'reference_initial_material_JPY_at_10000':ref_cost,'full_coating_initial_material_JPY_at_10000':coat/r['downstream_mass_yield']*10000,'reference_annual_JPY_at_100_cycles':ref_cost*cycles_year/100,'reference_annual_JPY_at_1000_cycles':ref_cost*cycles_year/1000,'lifetime_cycles_for_10M_annual_material_only':ref_cost*cycles_year/1e7,'area_budget_JPY_m2_for_entire_equivalent_surface':m['nominal_selective_application_budget_JPY']/surface,'area_budget_JPY_m2_if_only_patch_area_processed':m['nominal_selective_application_budget_JPY']/ref['patch_surface_m2'],'max_JPY_per_face_for_20M':m['nominal_selective_application_budget_JPY']/faces,'serial_application_days':[{'faces_per_s_assumed':v,'days_continuous':faces/v/86400} for v in m['sites_per_second']],'thermal_lower_bound':{'patch_only_kWh':heat_patch,'carrier_only_kWh':heat_carrier,'total_sensible_kWh':heat_patch+heat_carrier,'whole_bed_60min_ideal_kW':heat_patch+heat_carrier,'energy_JPY_assumed':(heat_patch+heat_carrier)*th['thermal_energy_price_JPY_kWh'],'excludes':'water, evaporation, losses, equipment, kinetics and spatial heat transfer'},'kinetics':select,'rain':rain}
check('carrier_mass_108t',near(carrier_mass,108000))
check('patch_heat_15_6kWh',near(heat_patch,15.6))
check('carrier_heat_1080kWh',near(heat_carrier,1080))
check('annual_initial_relation',near(summary['reference_annual_JPY_at_100_cycles'],3.6*ref_cost))
check('rain_unit_balance',near(rain[1]['added_protein_mg_L'],7.02))
check('reference_fermentation_1170m3',near(ref['fermentation_m3'],1170))
check('reference_grain_patch_not_full_mass',ref['installed_dry_kg']<carrier_mass)
check('zero_physical_tests',I['status']['physical_tests']==0 and I['status']['success_probability'] is None)
def writecsv(name, records):
    with (P/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0])); w.writeheader(); w.writerows(records)
writecsv('joint_screen.csv',rows);writecsv('cost_screen.csv',costs);writecsv('kinetic_screen.csv',select);writecsv('release_screen.csv',rain)
(P/'results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(P/'numerical_checks.json').write_text(json.dumps({'passed':all(x['passed'] for x in checks),'checks':checks,'not_experimental_tests':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':len(checks),'rows':len(rows)+len(costs)+len(select)+len(rain),'reference':ref,'rate_ratio_60s':select[2]['required_rate_ratio'],'material_JPY':ref_cost},ensure_ascii=False))
