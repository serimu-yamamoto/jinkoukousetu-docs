"""Cycle 73 reproducible diagnostic models. No physical experiments or success probability."""
from pathlib import Path
import json,csv,math
D=Path(__file__).resolve().parent
I=json.loads((D/'inputs.json').read_text(encoding='utf-8'))
checks=[]
def check(name,ok):
    assert ok,name
    checks.append({'name':name,'passed':True})
def near(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-11)
def save(name,rows):
    with (D/(name+'.csv')).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def phi(w):
    return (w/I['density_kg_m3']['EC'])/((1-w)/I['density_kg_m3']['LL']+w/I['density_kg_m3']['EC'])
def rho(w):
    return 1/((1-w)/I['density_kg_m3']['LL']+w/I['density_kg_m3']['EC'])
def coat(r,h,w):
    q=(w/I['density_kg_m3']['EC'])/((1-w)/I['density_kg_m3']['LL'])
    lo,hi=0,max(r,h)
    for _ in range(100):
        t=(lo+hi)/2
        if (r+t)**2*(h+2*t)>r*r*h*(1+q):hi=t
        else:lo=t
    return (lo+hi)/2
d=I['diagnostic'];mc,mb,mo,mt=[d[k] for k in ('mu_crystal','mu_binder','mu_other','mu_target')]
fmax=(mt-mo-mc)/(mb-mc)
check('surface_budget_boundary',near(mo+mc+(mb-mc)*fmax,mt))
check('surface_budget_is_1_over_35',near(fmax,1/35))
check('density_limit_pure_LL',near(rho(0),1200))
check('density_limit_pure_EC',near(rho(1),1140))
composition=[]
for w in [0.01,0.03,0.05,0.10,0.20]:
    v=phi(w);rr=rho(w)
    composition.append({'binder_mass_fraction':w,'binder_volume_fraction':v,'ideal_density_kg_m3':rr,'random_cut_equal_pressure_mu':mo+mc+(mb-mc)*v,'surface_fraction_budget':fmax})
check('density_5pct_harmonic_mean',1140<rho(.05)<1200)
check('density_5pct_volume',near(rho(.05)*(.95/1200+.05/1140),1))
check('mass_not_volume_fraction',phi(.05)>.05)
save('composition',composition)
coats=[]
for r in [5,10]:
    for h in [.2,1,2]:
        for w in [.01,.03,.05,.10]:
            t=coat(r,h,w);q=(w/1140)/((1-w)/1200)
            coats.append({'radius_um':r,'crystal_thickness_um':h,'binder_mass_fraction':w,'equivalent_closed_coat_nm':t*1000,'thin_coat_estimate_nm':q/(2/r+2/h)*1000})
            assert near((r+t)**2*(h+2*t)/(r*r*h),1+q)
check('all_24_coat_volume_residuals',len(coats)==24)
check('zero_binder_zero_coat',abs(coat(10,1,0))<1e-12)
check('more_binder_thicker_coat',coat(10,1,.1)>coat(10,1,.05))
save('closed_coats',coats)
coupled=[]
for p in [1,2,4,8]:
    for strength in [.5,1,2,5,8.4,10,20]:
        den=strength-d['shear_factor']*p*(mb-mc)
        f=d['shear_factor']*p*mc/den if den>0 else None
        valid=f is not None and 0<=f<=1
        mu=mo+mc+(mb-mc)*f if valid else None
        coupled.append({'pressure_MPa':p,'wet_allowable_shear_MPa_assumed':strength,'min_anchor_and_surface_fraction':f if valid else None,'min_mu_under_coupled_geometry':mu,'both_diagnostic_constraints_met':valid and f<=fmax+1e-12})
        if valid:assert near(strength*f,d['shear_factor']*p*(mc+(mb-mc)*f))
check('all_coupled_equilibria',len(coupled)==28)
critical=d['shear_factor']*d['pressure_MPa']*(mt-mo)/fmax
check('critical_strength_8p4_MPa',near(critical,8.4))
check('five_MPa_coupled_min_fraction',near(next(x for x in coupled if x['pressure_MPa']==4 and x['wet_allowable_shear_MPa_assumed']==5)['min_anchor_and_surface_fraction'],1/18))
save('coupled_binder',coupled)
separated=[]
for p in [2,4,8]:
    for fs in [0,.01,.02]:
        for fa in [.02,.05,.10]:
            mu=mo+mc+(mb-mc)*fs
            tau=d['shear_factor']*p*(mu-mo)/fa
            separated.append({'pressure_MPa':p,'binder_surface_load_fraction':fs,'anchor_projected_area_fraction':fa,'diagnostic_mu':mu,'required_wet_shear_MPa':tau})
check('separated_reference_4p28_MPa',near(next(x for x in separated if x['pressure_MPa']==4 and x['binder_surface_load_fraction']==.01 and x['anchor_projected_area_fraction']==.05)['required_wet_shear_MPa'],4.28))
check('separated_reference_mu',near(mo+mc+(mb-mc)*.01,.03675))
save('separated_binder',separated)
dry=I['drying'];s=(dry['HEC_g']+dry['Tyr_g'])/1000
water=dry['water_mL']/1000*dry['water_density_kg_L']/s
dryrows=[]
for factor in [1,10,50]:
    for eff in dry['efficiencies']:
        q=water/factor
        kwh=q*dry['latent_MJ_kg']/3.6/eff
        dryrows.append({'hypothetical_concentration_factor':factor,'water_kg_per_kg_dry_composite':q,'efficiency_assumed':eff,'purchased_heat_kWh_per_kg_if_resistance_heated':kwh,'energy_JPY_per_kg':kwh*dry['JPY_kWh'],'published_recipe_ratio':factor==1})
check('published_water_ratio',near(water,2000/13))
check('tenfold_concentration_divides_water',near(dryrows[2]['water_kg_per_kg_dry_composite']*10,water))
check('efficiency_scaling',near(dryrows[0]['energy_JPY_per_kg'],2*dryrows[1]['energy_JPY_per_kg']))
save('drying_scenarios',dryrows)
course=I['course'];area=course['particle_count']*course['pads_per_particle']*math.pi*(course['pad_diameter_um']*1e-6/2)**2
costs=[]
for t in [1,5,10]:
    m=area*t*1e-6*rho(.05)
    for price in I['cost']['LL_JPY_kg']:
        for process in I['cost']['coat_JPY_m2']:
            raw=m*(.95*price+.05*I['cost']['EC_JPY_kg'])/I['cost']['yield']
            forming=area*process
            costs.append({'pad_thickness_um':t,'pad_area_m2':area,'pad_composite_kg':m,'retained_LL_kg':m*.95,'LL_price_JPY_kg_assumed':price,'raw_purchase_JPY':raw,'forming_JPY_m2_assumed':process,'forming_JPY':forming,'partial_initial_JPY_ex_tax':raw+forming,'annual_10pct_replacement_JPY_ex_tax':.1*(raw+forming),'ethanol_circulated_kg_at_0p25':.25*m,'ethanol_makeup_kg_at_95pct_recovery':.25*m*.05})
check('course_inventory_108t',near(course['area_m2']*course['depth_m']*course['dry_bulk_kg_m3'],108000))
check('pad_area_independent_diameter',near(area,course['particle_count']*6*math.pi*(150e-6)**2/4))
check('pad_mass_scales_with_thickness',near(costs[-1]['pad_composite_kg'],10*costs[0]['pad_composite_kg']))
check('raw_mass_cost_direct_sum',near(costs[0]['raw_purchase_JPY'],(costs[0]['retained_LL_kg']*1000+(costs[0]['pad_composite_kg']-costs[0]['retained_LL_kg'])*2000)/.8))
check('forming_area_not_course_area',area>100*course['area_m2'])
save('pad_costs',costs)
manufacturing=[]
for active_fraction in [.05,.2,.5]:
    web_area=area/active_fraction
    speed=web_area/(100*16*60)
    manufacturing.append({'active_pad_fraction_on_1m_web':active_fraction,'web_area_m2':web_area,'web_speed_m_min_100days_16h':speed,'individual_pad_sites_per_second':course['particle_count']*6/(100*16*3600)})
check('web_area_conservation',all(near(x['web_area_m2']*x['active_pad_fraction_on_1m_web'],area) for x in manufacturing))
check('web_line_time_area',all(near(x['web_speed_m_min_100days_16h']*100*16*60,x['web_area_m2']) for x in manufacturing))
save('manufacturing',manufacturing)
result={'physical_trials':0,'success_probability':None,'computed_rows':len(composition)+len(coats)+len(coupled)+len(separated)+len(dryrows)+len(costs)+len(manufacturing),'math_checks':len(checks),'binder_surface_load_budget':fmax,'uniform_5pct_coat_r10_h1_nm':1000*coat(10,1,.05),'critical_coupled_wet_strength_MPa':critical,'separated_reference':next(x for x in separated if x['pressure_MPa']==4 and x['binder_surface_load_fraction']==.01 and x['anchor_projected_area_fraction']==.05),'drying_reference':dryrows[:2],'pad_area_m2':area,'pad_5um_cost_min':min(x['partial_initial_JPY_ex_tax'] for x in costs if x['pad_thickness_um']==5),'pad_5um_cost_max':max(x['partial_initial_JPY_ex_tax'] for x in costs if x['pad_thickness_um']==5),'pad_5um_mass_kg':next(x['pad_composite_kg'] for x in costs if x['pad_thickness_um']==5)}
(D/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
(D/'checks.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(result))
