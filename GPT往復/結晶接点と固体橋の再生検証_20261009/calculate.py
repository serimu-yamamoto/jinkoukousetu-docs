"""Cycle62: inverse bridge-network, process and inventory bounds. No experimental data fitting."""
from pathlib import Path
import math,json,csv
P=Path(__file__).resolve().parent; I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
b=I['bed'];m=I['mechanics'];p=I['process'];s=I['sensitivity'];life=I['lifecycle'];V=b['area_m2']*b['depth_m']
checks=[]
def ck(name,a,e,tol=1e-10):
    assert abs(a-e)<=tol,(name,a,e)
    checks.append(dict(name=name,actual=a,expected=e,tolerance=tol,passed=True))
def csvout(name,rows):
    with (P/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def network(d=b['grain_diameter_m'],z=b['contacts_per_grain'],stress=m['network_stress_Pa'],strength=m['bridge_tensile_strength_Pa'],rho=1000,eff=1):
    vp=math.pi*d**3/6; np=b['packing_fraction']/vp;nc=np*z/2
    # Upper normal-stress scale from sigma=(1/V) sum F*l*n_i*n_j, <n_x^2>=1/3.
    # eff<=1 represents additional unknown load-sharing losses, not calibrated.
    force=stress/(eff*nc*d/3);area=force/strength;radius=math.sqrt(area/math.pi)
    volume=nc*V*area*m['bridge_length_m'];mass=volume*rho
    area_fraction=z*area/(math.pi*d*d)
    work_density=nc*area*m['fracture_energy_J_m2']
    return dict(diameter_um=d*1e6,contacts_per_grain=z,stress_target_kPa=stress/1000,
        effective_bridge_strength_MPa=strength/1e6,bridge_density_kg_m3=rho,load_sharing_efficiency=eff,
        grain_count=np*V,contact_count=nc*V,contact_force_mN=force*1000,neck_radius_um=radius*1e6,
        active_bridge_mass_kg=mass,geometric_contact_area_fraction=area_fraction,
        single_break_work_J_m3=work_density,triangular_failure_opening_um=2*m['fracture_energy_J_m2']/strength*1e6,
        geometry_warning=radius/d>.1)
A=network(rho=m['crystal_density_kg_m3_assumed']);B=network(rho=m['particulate_bridge_bulk_density_kg_m3_assumed'])
window_s=(p['closure_min']-p['handling_min'])*60
heat_W=b['area_m2']*p['net_drying_heat_W_m2'];cap=heat_W*window_s/p['latent_heat_J_kg_assumed']
rows=[]
for stress in s['network_stress_Pa']:
    for strength in s['bridge_strength_Pa']:
        for d in s['diameters_m']:
            rows.append(network(d=d,stress=stress,strength=strength))
for z in [4,8]:rows.append(network(z=z))
for eff in [.5,.25]:rows.append(network(eff=eff))
# Supply of dissolved precursor; liquid volume approximated as carrier-water mass at 1 kg/L.
solution=[]
for f in s['renewed_fraction']:
    for eta in s['selectivity']:
        solid=A['active_bridge_mass_kg']*f/eta
        litres=solid/(p['precursor_Mg_mol_L_assumed']*p['nesquehonite_molar_mass_kg_mol'])
        for retain in s['retained_solution_water_fraction']:
            water=litres*p['liquid_water_kg_L_assumed']*retain
            solution.append(dict(renewed_fraction=f,overall_selectivity=eta,retained_carrier_water_fraction=retain,
                equivalent_total_precipitate_kg=solid,solution_L=litres,water_dose_mm=litres/b['area_m2'],
                retained_water_kg=water,ideal_drying_min=water*p['latent_heat_J_kg_assumed']/heat_W/60,
                drying_energy_bound_within_window=water<=cap,
                chemistry_rate_verified=False))
slurry=[]
for f in s['renewed_fraction']:
    for strength in s['bridge_strength_Pa']:
        for eta in s['selectivity']:
            for c in s['slurry_solids_mass_fraction']:
                active=network(strength=strength)['active_bridge_mass_kg']*f
                feed=active/eta;water=feed*(1-c)/c
                # Conservative water dose: no free drainage credited, no all-water-drying claim for solution route.
                slurry.append(dict(renewed_fraction=f,bridge_strength_MPa=strength/1e6,selectivity=eta,
                    solids_mass_fraction=c,solid_feed_kg=feed,carrier_water_kg=water,
                    ideal_drying_min=water*p['latent_heat_J_kg_assumed']/heat_W/60,
                    drying_energy_bound_within_window=water<=cap,assembly_rate_verified=False))
# Coupled inverse requirement sigma_bridge*eta, including all bridge inventory for f=1.
requirements=[]
for f in s['renewed_fraction']:
    for eff in [1,.5,.25]:
        for c in s['slurry_solids_mass_fraction']:
            req=3*m['particulate_bridge_bulk_density_kg_m3_assumed']*V*m['network_stress_Pa']*m['bridge_length_m']/b['grain_diameter_m']
            req*=f*(1-c)/c/cap/eff
            requirements.append(dict(renewed_fraction=f,load_sharing_efficiency=eff,solids_mass_fraction=c,
                minimum_strength_times_selectivity_MPa=req/1e6))
# Uniform-film null model; all grain area coated to half the neck length.
null_eta=B['geometric_contact_area_fraction'];uniform_feed=B['active_bridge_mass_kg']/null_eta
uniform_from_area=B['grain_count']*math.pi*b['grain_diameter_m']**2*m['bridge_length_m']/2*m['particulate_bridge_bulk_density_kg_m3_assumed']
# Debris ledger: active bridges replenished; old broken bridges plus off-target new solids become debris.
# At each cycle collect a fraction of the full debris pool AFTER generation. No release to environment modeled.
inv=[];hist=[]
for f in life['renewed_fraction']:
    gross=B['active_bridge_mass_kg']*f/p['baseline_selectivity']
    for collect in life['debris_collection_fraction']:
        residual=0.;removed=0.
        for n in range(1,life['cycles']+1):
            available=residual+gross;take=collect*available;removed+=take;residual=available-take
            hist.append(dict(renewed_fraction=f,collection_fraction=collect,cycle=n,
                cumulative_gross_added_kg=gross*n,cumulative_collected_kg=removed,remaining_debris_kg=residual))
        for reuse in life['potential_reuse_fraction']:
            net=gross*life['cycles']-reuse*removed
            inv.append(dict(renewed_fraction=f,collection_fraction=collect,potential_reuse_fraction=reuse,
                cycles=life['cycles'],gross_handled_kg=gross*life['cycles'],collected_kg=removed,
                resident_debris_kg=residual,potential_net_fresh_material_kg=net,
                raw_material_cost_yen_tax_excluded=net*life['bridge_price_yen_kg_assumed'],
                recovery_and_reuse_unverified=True,environmental_release_not_estimated=True))
        ck('inventory closure f='+str(f)+' collection='+str(collect),residual+removed,gross*life['cycles'],1e-7)
cost=[]
for rho in life['carrier_density_kg_m3_assumed']:
    for price in life['carrier_price_yen_kg_assumed']:
        mass=V*b['packing_fraction']*rho
        cost.append(dict(foam_grain_envelope_density_kg_m3=rho,material_price_yen_kg_assumed=price,
            carrier_mass_kg=mass,raw_carrier_cost_yen_tax_excluded=mass*price,quote=False))
# Same density/strength/contact geometry comparison isolates supply format.
same_feed=A['active_bridge_mass_kg']/p['baseline_selectivity']
same_water=same_feed*(1-p['slurry_solids_mass_fraction'])/p['slurry_solids_mass_fraction']
same_solution_L=same_feed/(p['precursor_Mg_mol_L_assumed']*p['nesquehonite_molar_mass_kg_mol'])
format_ratio=same_solution_L*p['liquid_water_kg_L_assumed']/same_water
ck('same-density solid feed same for two supply routes',same_feed*p['baseline_selectivity'],A['active_bridge_mass_kg'],1e-10)
ck('supply-format water ratio independent of network mass',format_ratio,p['liquid_water_kg_L_assumed']*p['slurry_solids_mass_fraction']/(p['precursor_Mg_mol_L_assumed']*p['nesquehonite_molar_mass_kg_mol']*(1-p['slurry_solids_mass_fraction'])),1e-10)
# Independent algebraic and limiting-case checks.
ck('network sphere count from volume',B['grain_count']*math.pi*b['grain_diameter_m']**3/6,V*b['packing_fraction'],1e-9)
ck('contacts not double counted',B['contact_count'],B['grain_count']*b['contacts_per_grain']/2,.01)
ck('mass eliminated analytic',B['active_bridge_mass_kg'],3*1000*V*m['network_stress_Pa']*m['bridge_length_m']/(b['grain_diameter_m']*m['bridge_tensile_strength_Pa']),1e-9)
ck('required mass independent of z at fixed stress',network(z=8)['active_bridge_mass_kg'],network(z=4)['active_bridge_mass_kg'],1e-9)
ck('doubling diameter halves required mass',network(d=.001)['active_bridge_mass_kg'],B['active_bridge_mass_kg']/2,1e-9)
ck('half load sharing doubles material',network(eff=.5)['active_bridge_mass_kg'],2*B['active_bridge_mass_kg'],1e-9)
ck('uniform coating identity',uniform_feed,uniform_from_area,1e-6)
ck('renewal cycle does not double active inventory',B['active_bridge_mass_kg']*.1+(B['active_bridge_mass_kg']*.1/p['baseline_selectivity']-B['active_bridge_mass_kg']*.1),B['active_bridge_mass_kg']*.1/p['baseline_selectivity'],1e-10)
ck('200 kg drying capacity',cap,200,1e-10)
ck('50 wt% solids -> equal carrier water',B['active_bridge_mass_kg']/.25*(1-.5)/.5,B['active_bridge_mass_kg']/.25,1e-10)
ck('20 wt% solids -> four times carrier water',(1-.2)/.2,4)
ck('G fracture includes both surfaces once',B['single_break_work_J_m3'],3*m['network_stress_Pa']*m['fracture_energy_J_m2']/(b['grain_diameter_m']*m['bridge_tensile_strength_Pa']),1e-10)
ck('geometric selectivity inversion',B['geometric_contact_area_fraction'],m['network_stress_Pa']/(b['packing_fraction']*m['bridge_tensile_strength_Pa']),1e-14)
ck('zero recollection accumulates every addition',inv[0]['resident_debris_kg'],inv[0]['gross_handled_kg'],1e-8)
# Chemical stoichiometry: Mg(HCO3)2 + 2H2O -> MgCO3.3H2O + CO2.
# Element counts are exact; molar masses only approximate inputs.
left={'Mg':1,'H':2+4,'C':2,'O':6+2};right={'Mg':1,'H':6,'C':1+1,'O':6+2}
for e in left:ck('precipitation element balance '+e,left[e],right[e],0)
nomS=next(x for x in slurry if x['renewed_fraction']==1 and x['bridge_strength_MPa']==10 and x['selectivity']==.25 and x['solids_mass_fraction']==.5)
nomA=next(x for x in solution if x['renewed_fraction']==1 and x['overall_selectivity']==.25 and x['retained_carrier_water_fraction']==1)
R=dict(cycle=62,physical_tests=0,success_probability=None,crystal_route=A,particulate_route=B,
    nominal_solution=nomA,nominal_slurry=nomS,drying_window_min=window_s/60,drying_capacity_water_kg=cap,
    same_density_feed_compare=dict(solid_feed_kg=same_feed,slurry_water_kg=same_water,solution_L=same_solution_L,water_ratio=format_ratio,ideal_slurry_drying_min=same_water*p['latent_heat_J_kg_assumed']/heat_W/60),
    coupled_requirements=requirements,uniform_coating_null=dict(selectivity=null_eta,total_solid_kg=uniform_feed,
        ratio_vs_selective_feed=uniform_feed/nomS['solid_feed_kg'],ideal_drying_hours_at_50wt=uniform_feed*p['latent_heat_J_kg_assumed']/heat_W/3600),
    nominal_minimum_effective_strength_MPa=next(x['minimum_strength_times_selectivity_MPa'] for x in requirements if x['renewed_fraction']==1 and x['load_sharing_efficiency']==1 and x['solids_mass_fraction']==.5)/p['baseline_selectivity'],
    comparison_compression_work_J_m3=m['reference_compression_Pa']*m['reference_compression_strain'],
    lifecycle=inv,carrier_material_cost=cost,
    warnings=I['warnings'])
for name,rs in [('network_bounds.csv',rows),('solution_route.csv',solution),('slurry_route.csv',slurry),('coupled_requirements.csv',requirements),('debris_inventory.csv',inv),('debris_history.csv',hist),('carrier_cost.csv',cost)]:csvout(name,rs)
(P/'results.json').write_text(json.dumps(R,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(P/'numerical_checks.json').write_text(json.dumps(dict(passed=len(checks),checks=checks,physical_tests=0),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(checks=len(checks),rows=len(rows)+len(solution)+len(slurry)+len(requirements)+len(inv)+len(hist)+len(cost),bridge_mass_B=B['active_bridge_mass_kg'],slurry_water=nomS['carrier_water_kg'],slurry_drying_min=nomS['ideal_drying_min'],solution_L=nomA['solution_L'],min_strength_MPa=R['nominal_minimum_effective_strength_MPa']),ensure_ascii=False))
