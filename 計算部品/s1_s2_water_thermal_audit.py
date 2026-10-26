"""S1/S2 independent conditional arithmetic, 2026-10-26. No empirical data.
No optimization, fitting, Monte Carlo or success probabilities.
Sources and the epistemic status of every input are in the companion report.
Run: python3 -B 計算部品/s1_s2_water_thermal_audit.py > audit_results.json
"""
import json, math
from fractions import Fraction

def thod(c,h,o):
    mol_mass=c*12.011+h*1.008+o*15.999
    return (c+h/4-o/2)*31.998/mol_mass

def annual_balance(area_m2,depth_m,bulk_kg_m3,rain_m,runoff,loss,capture=0,bypass=0,organic=1):
    inventory=area_m2*depth_m*bulk_kg_m3
    gross=inventory*loss
    escaped=gross*(bypass+(1-bypass)*(1-capture))
    flow=area_m2*rain_m*runoff
    return dict(inventory_kg=inventory,gross_to_drain_kg=gross,
                gross_organic_kg=gross*organic,recovered_kg=gross-escaped,
                released_total_kg=escaped,released_organic_kg=escaped*organic,
                water_m3=flow,total_material_mg_L=escaped*1000/flow)

def droplet_time(d,rho,cp,latent,initial,crystal,air,k_air=0.027,Nu=2):
    if crystal<=air:return None
    sensible=cp*math.log((initial-air)/(crystal-air))
    return rho*d*d/(6*Nu*k_air)*(sensible+latent/(crystal-air))

def run():
    factors={k:thod(*v) for k,v in dict(palmitic=(16,32,2),stearic=(18,36,2),behenyl_alcohol=(22,46,1),PCL_repeat=(6,10,2)).items()}
    scenarios=[]
    for loss in (.001,.01,.05):
        z=annual_balance(10000,.45,500,2,.8,loss)
        c=z['total_material_mg_L']
        z.update(loss=loss,S1_95pct_organic_kg=z['gross_to_drain_kg']*.95,
                 S1_ThOD_mg_L=c*.95*factors['palmitic'],PCL_ThOD_mg_L=c*factors['PCL_repeat'])
        scenarios.append(z)
    capture=[]
    for eta,b in [(.95,0),(.99,0),(.999,0),(.999,.01)]:
        z=annual_balance(10000,.45,500,2,.8,.01,eta,b)
        c=z['total_material_mg_L']
        z.update(capture=eta,bypass=b,S1_ThOD_mg_L=c*.95*factors['palmitic'],
                 PCL_ThOD_mg_L=c*factors['PCL_repeat'])
        capture.append(z)
    thermal=[]
    for tc in (62.25,55):
        for ta in (35,50):
            thermal.append(dict(crystallization_C_assumed=tc,air_C=ta,
                   times_ms={str(d):1000*droplet_time(d*1e-6,900,2400,53900/.256424,75,tc,ta) for d in (20,50,80)}))
    heat=[]
    for T0 in (30,50):
        E=0.05*20000*10*(1/10) # diagnostic mu=0.05, p=20 kPa, v=10, 1m transit
        depth=E/(900*(2000*(62.25-T0)+53900/.256424))
        heat.append(dict(initial_C=T0,friction_energy_J_m2=E,adiabatic_melt_upper_um=depth*1e6))
    drift=[]
    for d in (20,50,80):
        va=900*9.81*(d*1e-6)**2/(18*1.9e-5)
        drift.append(dict(d_um=d,stokes_settling_m_s=va,from_1m_s=1/va,wind_2m_s_distance_m=2/va))
    viscosity=[]
    for mu_liq in (.005,1,1000):
        viscosity.append(dict(viscosity_Pa_s=mu_liq,mu_Couette_at_h10um=mu_liq*10/(20000*1e-5)))
    checks={}
    checks['inventory']=scenarios[0]['inventory_kg']==2250000
    checks['water']=scenarios[0]['water_m3']==16000
    checks['one_tonne_concentration']=1000*1000/16000==62.5
    checks['PCL_oxygen_balance']=Fraction(6)+Fraction(10,4)-Fraction(2,2)==Fraction(15,2)
    checks['PA_oxygen_balance']=16+32/4-2/2==23
    checks['capture_mass_closed']=all(abs(z['gross_to_drain_kg']-z['recovered_kg']-z['released_total_kg'])<1e-6 for z in capture)
    checks['drop_d2_scaling']=abs(thermal[0]['times_ms']['80']/thermal[0]['times_ms']['20']-16)<1e-10
    checks['bypass_floor']=capture[-1]['released_total_kg']>=225
    capex=[[1500,4000],[3000,8000],[1000,2500],[2000,5000],[500,1500]]
    opex=[[60,140],[50,200],[100,400],[120,300],[100,250],[100,300]]
    checks['cost_sums']=sum(x[0] for x in capex)==8000 and sum(x[1] for x in capex)==21000 and sum(x[0] for x in opex)==530 and sum(x[1] for x in opex)==1590
    assert all(checks.values())
    return dict(status='conditional calculations only; physical experiments=0',
       thod_kgO2_kg=factors,annual=scenarios,capture_sensitivity=capture,
       thermal_reference_not_actual_S1=thermal,friction_adiabatic_upper=heat,
       mist_drift_sphere_still_air_assumptions=drift,Couette_diagnostic=viscosity,
       storm=dict(area_m2=10000,rain_mm_h=100,runoff=1,inflow_m3_h=1000,
                  treatment_m3_h=20,one_hour_storage_m3=980,six_hour_storage_m3=5880,
                  treatment_1000m3_hours=50,ten_min_untreated_m3=1000/6),
       fire=dict(PCL_MCC_MJ_kg_literature=26.45,PCL_with_10pct_inert_MJ_kg_dilution_only=26.45*.9),
       reported_decay_endpoint_diagnostic_days=29*math.log(2)/math.log(536/3.7),
       calcium_carbonate_5g_PA_consumption_upper_g=5/(40.078+12.011+3*15.999)*2*(16*12.011+32*1.008+2*15.999),
       costs_man_yen_unverified=dict(initial_items=capex,initial_total_before_contingency=[sum(x[i] for x in capex) for i in (0,1)],with_20pct_contingency=[sum(x[i] for x in capex)*1.2 for i in (0,1)],annual_items=opex,annual_total=[sum(x[i] for x in opex) for i in (0,1)]),
       arithmetic_checks=checks)
if __name__=='__main__':
    print(json.dumps(run(),ensure_ascii=False,indent=2))
