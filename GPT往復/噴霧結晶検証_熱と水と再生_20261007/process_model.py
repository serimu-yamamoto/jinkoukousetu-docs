"""Cycle 16: explicit scenario balances. No snow-performance prediction."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def cooling(d, ambient, nu, t):
    """Lumped sphere; prescribed isothermal crystallization, no kinetic law."""
    exit_temp = max(t['T_exit_C'], ambient+t['exit_above_ambient_K'])
    if not ambient < exit_temp < t['T_cryst_C'] < t['T_feed_C']:
        raise ValueError('Temperature ordering')
    h = nu*t['k_air_W_mK']/d
    tau = t['rho_kg_m3']*t['cp_J_kgK']*d/(6*h)
    pre = tau*math.log((t['T_feed_C']-ambient)/(t['T_cryst_C']-ambient))
    phase = t['rho_kg_m3']*t['latent_J_kg']*d/(6*h*(t['T_cryst_C']-ambient))
    post = tau*math.log((t['T_cryst_C']-ambient)/(exit_temp-ambient))
    bi = h*(d/6)/t['k_polymer_W_mK']
    return dict(diameter_um=d*1e6, ambient_C=ambient, Nu=nu,
                exit_C=exit_temp, pre_s=pre, phase_s=phase, post_s=post,
                total_s=pre+phase+post, Bi=bi, lumped_screen=bi <= .1)


def hydration(product, wt, a):
    hemi = product*a['hemihydrate_M_g_mol']/a['gypsum_M_g_mol']
    bound = product-hemi
    feed_water = hemi*(1/wt-1)
    free = feed_water-bound
    if free < -1e-12:
        raise ValueError('Not enough water for assumed full hydration')
    return dict(product_kg=product, hemi_kg=hemi, bound_water_kg=bound,
                feed_water_kg=feed_water, free_water_kg=max(free, 0),
                slurry_wt=wt, latent_evaporation_kWh=max(free,0)*a['water_latent_J_kg']/3.6e6)


def calculate(p):
    b,t,a,g,c = [p[k] for k in ['bed','thermal','aqueous','bridge','baseline_cost']]
    seconds=b['process_minutes']*60
    crf=c['discount']*(1+c['discount'])**c['years']/((1+c['discount'])**c['years']-1)
    q_heat=t['cp_J_kgK']*(t['T_feed_C']-t['T_start_C'])+t['latent_J_kg']
    q_reject=t['cp_J_kgK']*(t['T_feed_C']-t['T_exit_C'])+t['latent_J_kg']
    out={'scope':p['provenance'],'cooling':[], 'beds':[], 'reforming':[],
         'solution':[], 'bridges':[], 'rain':[], 'drying':[], 'costs':[],
         'heat_J_kg':q_heat,'reject_J_kg':q_reject,'crf':crf}
    out['cooling']=[cooling(d*1e-6,ta,nu,t) for d in t['diameters_um']
                    for ta in t['ambient_C'] for nu in t['Nu']]
    for area in b['areas_m2']:
        for depth in b['depths_m']:
            mass=area*depth*b['bulk_density_kg_m3']
            initial=mass*c['finished_grain_JPY_kg']
            annual=(initial+c['initial_other_JPY'])*crf+c['annual_other_JPY']+initial*c['replacement_fraction_year']
            out['beds'].append(dict(area_m2=area,depth_m=depth,mass_kg=mass,
                                   material_initial_JPY=initial,EAC_JPY=annual,
                                   added_annual_headroom_JPY=c['annual_budget_JPY']-annual))
            for f in b['reform_fractions']:
                reform=mass*f
                air=reform*q_reject/(t['air_cp_J_kgK']*t['air_rise_K'])
                r=dict(area_m2=area,depth_m=depth,fraction=f,mass_kg=reform,
                       rate_kg_h=reform/seconds*3600,ideal_heat_kWh=reform*q_heat/3.6e6,
                       reject_kWh=reform*q_reject/3.6e6,ideal_heat_kW=reform*q_heat/seconds/1000,
                       air_mass_kg=air,air_flow_m3_s=air/(t['air_density_kg_m3']*seconds))
                out['reforming'].append(r)
                for eff in t['heat_efficiency']:
                    for price in t['electricity_JPY_kWh']:
                        energy=r['ideal_heat_kWh']/eff
                        out['costs'].append(dict(area_m2=area,depth_m=depth,fraction=f,
                            efficiency=eff,tariff=price,heat_input_kWh=energy,
                            heat_input_JPY_event=energy*price,
                            heat_input_JPY_year=energy*price*g['rebuilds_per_day']*g['days_per_year']))
                for wt in a['solution_solids_wt']:
                    water=reform*(1/wt-1)
                    out['solution'].append(dict(area_m2=area,depth_m=depth,fraction=f,wt=wt,
                        solid_kg=reform,water_kg=water,latent_kWh=water*a['water_latent_J_kg']/3.6e6,
                        latent_kW=water*a['water_latent_J_kg']/seconds/1000))
            for flux in a['net_evaporation_flux_W_m2']:
                out['drying'].append(dict(area_m2=area,depth_m=depth,flux_W_m2=flux,
                    water_energy_capacity_kg=area*seconds*flux/a['water_latent_J_kg']))
            for f in g['product_mass_fractions']:
                for treated in g['treated_fractions']:
                    product=mass*f*treated
                    for wt in g['hemihydrate_slurry_wt']:
                        h=hydration(product,wt,a)
                        out['bridges'].append(dict(area_m2=area,depth_m=depth,
                            product_fraction=f,treated_fraction=treated,**h,
                            ideal_latent_kW=h['latent_evaporation_kWh']*3600/seconds,
                            annual_product_kg=product*g['rebuilds_per_day']*g['days_per_year'],
                            annual_material_JPY={str(price):product*g['rebuilds_per_day']*g['days_per_year']*price
                                                  for price in g['gypsum_product_equiv_price_JPY_kg']}))
                # Rain exposure concerns all existing bridges, not just newly treated area.
                inventory=mass*f
                for rain in g['rain_mm']:
                    for alpha in g['effective_saturation_fraction']:
                        volume=area*rain/1000
                        capacity=a['gypsum_C_kg_m3']*volume*alpha
                        out['rain'].append(dict(area_m2=area,depth_m=depth,product_fraction=f,
                            inventory_kg=inventory,rain_mm=rain,effective_saturation=alpha,
                            water_m3=volume,capacity_kg=capacity,
                            capped_loss_kg=min(inventory,capacity),
                            capacity_equiv_rain_mm=inventory/(a['gypsum_C_kg_m3']*alpha*area)*1000))
    # A pure saturated feed deposits only its dissolved content if all water evaporates.
    out['saturated_solution']={'water_m3_per_kg_gypsum':1/a['gypsum_C_kg_m3'],
        'water_kg_per_kg_gypsum':1000/a['gypsum_C_kg_m3'],
        'latent_kWh_per_kg_gypsum':1000/a['gypsum_C_kg_m3']*a['water_latent_J_kg']/3.6e6}
    molal_approx=a['gypsum_C_kg_m3']/a['gypsum_M_g_mol']
    out['dilute_freezing_scale']=[{'i':i,'molal_approx':molal_approx,
        'depression_K':i*a['water_Kf']*molal_approx} for i in a['solute_i']]
    # Algebraic illustration only: no inputs here are actual marginal probabilities.
    out['dependence_examples']=[{'n':12,'hypothetical_each':x,
        'frechet_low':max(0,12*x-11),'frechet_high':x,'if_independent':x**12}
        for x in [.9,.95,.99]]
    return out


if __name__=='__main__':
    p=json.loads((ROOT/'inputs.json').read_text(encoding='utf-8'))
    out=calculate(p)
    (ROOT/'results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:len(v) for k,v in out.items() if isinstance(v,list)},ensure_ascii=False))
