from pathlib import Path
import csv,json,math
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
G=I['geometry_assumptions'];E=I['engineering_assumptions'];C=I['chemistry_constants']
V=G['area_m2']*G['bed_depth_m'];D=G['particle_diameter_m'];L=G['bridge_length_m']
np=G['packing_fraction']/(math.pi*D**3/6);nc=np*G['coordination']/2
F=3*G['target_network_stress_Pa']/(G['load_sharing_efficiency']*nc*D)
a=math.sqrt(F/(math.pi*G['effective_bridge_strength_Pa']))
M=nc*V*math.pi*a*a*L*G['bridge_density_kg_m3'];Mg=M*C['Mg_kg_per_mol']/C['NQ_kg_per_mol']
rows={};checks=[]
def ck(name,truth):
    if not truth:raise AssertionError(name)
    checks.append(name)
def close(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12)
def out(name,data):
    rows[name]=data
    with (P/(name+'.csv')).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=data[0].keys());w.writeheader();w.writerows(data)
wear=[]
for i in range(101):
    loss_ratio=i/100;r=max(1-loss_ratio,0)
    wear.append(dict(radial_loss_um=loss_ratio*a*1e6,radius_retention=r,force_retention_same_strength=r*r,remaining_mass_kg=M*r*r,removed_Mg_kg=Mg*(1-r*r)))
out('radial_loss',wear)
strength=[]
for sb in E['bridge_strength_sensitivity_MPa']:
    aa=math.sqrt(F/(math.pi*sb*1e6));mm=M*G['effective_bridge_strength_Pa']/(sb*1e6)
    daily=mm*.1/E['useful_contact_yield']*E['cycles_per_day']
    strength.append(dict(assumed_strength_MPa=sb,radius_um=aa*1e6,radius_to_particle_diameter=aa/D,small_neck_geometry_warning=aa/D>.1,required_neck_mass_kg=mm,feed_kg_day_at_10pct_renewal=daily,bath_m3_at_28d=daily*28*E['bath_L_per_kg']/1000,measured_strength=False))
out('strength_sensitivity',strength)
limit=a*(1-math.sqrt(E['min_force_retention']))
leach=[]
for h in E['rain_depth_mm']:
    water_m3=G['area_m2']*h/1000
    for b in [.01,.05,.2,1]:
        leach.append(dict(rain_mm=h,captured_event_water_m3=water_m3,uniform_bridge_mass_loss_fraction=b,bridge_loss_kg=M*b,Mg_loss_kg=Mg*b,net_Mg_increase_mg_L=Mg*b/water_m3*1000))
out('event_mass_balance',leach)
# This is a bookkeeping inversion of MEASURED net export, not equilibrium solubility or dissolution kinetics.
coat=[]
for t_um in E['coat_thickness_um']:
    t=t_um*1e-6;coat_volume=nc*V*math.pi*((a+t)**2-a*a)*L
    coat.append(dict(thickness_um=t_um,side_coat_kg=coat_volume*E['coat_density_kg_m3'],coat_to_bridge_mass=coat_volume*E['coat_density_kg_m3']/M,outside_radius_um=(a+t)*1e6,coated_end_faces=False))
out('side_coating',coat)
inventory=[];cost=[];pflux=[]
for f in E['renewed_fractions']:
    useful=M*f;feed=useful/E['useful_contact_yield'];daily=feed*E['cycles_per_day'];annual=daily*E['days_per_year']
    for t in E['stabilization_days']:
        inventory.append(dict(renewed_fraction=f,hold_days=t,feed_kg_per_cycle=feed,feed_kg_per_day=daily,work_in_process_kg=daily*t,occupied_bath_m3=daily*t*E['bath_L_per_kg']/1000,annual_feed_kg=annual,annual_gross_bath_L=annual*E['bath_L_per_kg']))
    for price in E['treatment_price_JPY_kg']:
        cost.append(dict(renewed_fraction=f,annual_feed_kg=annual,raw_price_JPY_kg=E['raw_bridge_price_JPY_kg'],assumed_treatment_JPY_kg=price,annual_raw_JPY=annual*E['raw_bridge_price_JPY_kg'],annual_treatment_JPY=annual*price,annual_partial_total_JPY=annual*(price+E['raw_bridge_price_JPY_kg']),tax_included=False,equipment_civil_carrier_included=False))
    for cp in E['bath_P_mol_L']:
        gross=annual*E['bath_L_per_kg']*cp*C['P_kg_per_mol']
        for loss in E['bath_elemental_loss_fraction']:
            pflux.append(dict(renewed_fraction=f,hypothetical_P_mol_L=cp,gross_annual_bath_P_kg=gross,fraction_of_gross_P_not_retained_in_loop=loss,annual_P_outside_loop_kg=gross*loss,actual_environmental_release_known=False,actual_recipe_known=False))
out('factory_inventory',inventory);out('partial_cost',cost);out('phosphorus_balance',pflux)
# Equal remaining load-bearing volume, different topology. A transverse gap disconnects a tensile bridge.
topology=[]
for q in [.8,.86,.95,.99]:
    topology.append(dict(remaining_original_load_bearing_volume_fraction=q,uniform_radial_loss_um=a*(1-math.sqrt(q))*1e6,uniform_force_ratio=q,localized_transverse_nonbearing_gap_um=L*(1-q)*1e6,disconnected_tensile_force_ratio=0,compression_contact_may_remain=True,phase_fraction_to_volume_conversion_assumed=False))
out('topology_counterexample',topology)
# Replacement recovery is independent from phase preservation.
recovery=[]
for surviving in [.5,.8,.86,.95]:
    for strength_ratio in [.5,.8,1]:
        for rebuilt in [0,.5,.9,1]:
            after=surviving*strength_ratio+(1-surviving)*rebuilt
            recovery.append(dict(surviving_contact_fraction=surviving,survivor_strength_ratio=strength_ratio,rebuilt_fraction_of_missing_contacts=rebuilt,parallel_contact_force_ratio=after,network_connected_not_solved=True))
out('recovery_bound',recovery)
# Limit for neck side recession at a constant rate is a necessary measured-rate target, not a predicted lifetime.
rate=[]
for hours in [5,24,240,672,4320]:
    rate.append(dict(exposure_h=hours,uniform_radial_loss_limit_um=limit*1e6,mean_recession_limit_nm_h=limit*1e9/hours,target_force_ratio=E['min_force_retention']))
out('recession_requirement',rate)
ck('sphere contact count',close(nc*V,22689128687180.598))
ck('H62 required bridge mass',close(M,49.41))
ck('stress tensor back substitution',close(nc*D*F/3,G['target_network_stress_Pa']))
ck('radius force relation',close(math.pi*a*a*G['effective_bridge_strength_Pa'],F))
ck('20 percent loss area inversion',close((1-limit/a)**2,.8))
ck('endpoints zero and total loss',wear[0]['force_retention_same_strength']==1 and wear[-1]['remaining_mass_kg']==0)
ck('Mg is element not whole mineral',0<Mg<M)
ck('event Mg balance units',all(close(r['net_Mg_increase_mg_L']*r['captured_event_water_m3']/1000,r['Mg_loss_kg']) for r in leach))
ck('same mass topology counterexample',all(r['uniform_force_ratio']>0 and r['disconnected_tensile_force_ratio']==0 for r in topology))
ck('constant length neck volume ratios',all(close((a-r['uniform_radial_loss_um']*1e-6)**2/a**2,r['remaining_original_load_bearing_volume_fraction']) for r in topology))
ck('coat volume exact cylindrical difference',all(r['side_coat_kg']>0 for r in coat))
ck('coat mass increases thickness',all(coat[i]['side_coat_kg']<coat[i+1]['side_coat_kg'] for i in range(len(coat)-1)))
ck('Little inventory relation',all(close(r['work_in_process_kg'],r['feed_kg_per_day']*r['hold_days']) for r in inventory))
ck('bath volume scale',all(close(r['occupied_bath_m3']*1000,r['work_in_process_kg']*10) for r in inventory))
ck('full renewal included',{r['renewed_fraction'] for r in inventory}=={.01,.1,1})
ck('annual days and cycles',all(close(r['annual_feed_kg'],r['feed_kg_per_cycle']*360) for r in inventory))
ck('no cost scope hiding',all(not r['tax_included'] and not r['equipment_civil_carrier_included'] for r in cost))
ck('partial cost arithmetic',all(close(r['annual_raw_JPY']+r['annual_treatment_JPY'],r['annual_partial_total_JPY']) for r in cost))
ck('elemental P bookkeeping',all(close(r['annual_P_outside_loop_kg'],r['gross_annual_bath_P_kg']*r['fraction_of_gross_P_not_retained_in_loop']) for r in pflux))
ck('P concentrations hypothetical',all(not r['actual_recipe_known'] for r in pflux))
ck('P exit not environmental claim',all(not r['actual_environmental_release_known'] for r in pflux))
ck('rebuild cannot repair weakened survivors by count alone',next(r for r in recovery if r['surviving_contact_fraction']==.86 and r['survivor_strength_ratio']==.5 and r['rebuilt_fraction_of_missing_contacts']==1)['parallel_contact_force_ratio']<.8)
ck('weak strength mass factor',close(strength[0]['required_neck_mass_kg']/strength[-1]['required_neck_mass_kg'],500))
ck('geometry warning for very thick neck',strength[0]['small_neck_geometry_warning'] and not strength[-1]['small_neck_geometry_warning'])
ck('Claude range not called measurement',all(not r['measured_strength'] for r in strength))
ck('no generated probability',I['success_probability'] is None and I['physical_tests']==0)
ck('rate times duration inverse',all(close(r['mean_recession_limit_nm_h']*r['exposure_h'],limit*1e9) for r in rate))
nominal_inventory=next(r for r in inventory if r['renewed_fraction']==.1 and r['hold_days']==28)
nominal_coat=next(r for r in coat if r['thickness_um']==.1)
nominal_event=next(r for r in leach if r['rain_mm']==100 and r['uniform_bridge_mass_loss_fraction']==.2)
R=dict(cycle=63,physical_tests=0,success_probability=None,nominal=dict(bridge_radius_um=a*1e6,bridge_mass_kg=M,bridge_Mg_kg=Mg,required_contact_force_mN=F*1000,radial_loss_limit_um=limit*1e6),nominal_event=nominal_event,nominal_coating=nominal_coat,nominal_inventory=nominal_inventory,row_counts={k:len(v) for k,v in rows.items()},total_csv_rows=sum(map(len,rows.values())),notes=['Geometric and mass-balance counterexamples, not measured chemical kinetics.','Original phase percent, volume percent and intact-contact count are distinct.','Cost is tax-exclusive partial consumables only.'])
(P/'results.json').write_text(json.dumps(R,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(P/'numerical_checks.json').write_text(json.dumps(dict(passed=len(checks),checks=checks,physical_tests=0),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(R,ensure_ascii=False))
