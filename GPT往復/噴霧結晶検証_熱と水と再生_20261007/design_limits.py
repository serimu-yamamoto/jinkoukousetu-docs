"""Manufacturing capacity and recurring-cost boundaries; assumptions explicit."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=json.loads((ROOT/'inputs.json').read_text(encoding='utf-8'))
r=json.loads((ROOT/'results.json').read_text(encoding='utf-8'))
bed=next(x for x in r['beds'] if x['area_m2']==2000 and x['depth_m']==.45)
bridge=next(x for x in r['bridges'] if x['area_m2']==2000 and x['depth_m']==.45
            and x['product_fraction']==.001 and x['treated_fraction']==1 and x['slurry_wt']==.2)
out={'capacity':[], 'renewal_cost':[], 'enthalpy_sensitivity':[],
     'scope':'Manufacturing/consumption bounds, not restored ski performance.'}
for rate in [500,1000,2000,5000,10000]:
    mass=rate*p['bed']['process_minutes']/60
    out['capacity'].append(dict(rate_kg_h=rate,mass_per_window_kg=mass,
        bed_mass_fraction=mass/bed['mass_kg'],
        equivalent_full_area_depth_mm=mass/(2000*p['bed']['bulk_density_kg_m3'])*1000,
        area_300mm_damage_m2=mass/(.3*p['bed']['bulk_density_kg_m3'])))
for wt in [.2,.5,.8]:
    h=next(x for x in r['bridges'] if x['area_m2']==2000 and x['depth_m']==.45
          and x['product_fraction']==.001 and x['treated_fraction']==1 and x['slurry_wt']==wt)
    for price in [100,500,1000]:
        for treated in [.01,.1,1]:
            material=h['annual_product_kg']*price*treated
            electric=h['latent_evaporation_kWh']/.8*20*240*treated
            total=material+electric
            out['renewal_cost'].append(dict(slurry_wt=wt,product_equiv_price_JPY_kg=price,
                treated_fraction=treated,annual_new_solid_kg=h['annual_product_kg']*treated,
                annual_addition_fraction_of_bed=h['annual_product_kg']*treated/bed['mass_kg'],
                material_JPY_year=material,illustrative_electric_drying_JPY_year=electric,
                added_JPY_year=total,baseline_plus_added_JPY_year=bed['EAC_JPY']+total,
                max_treated_fraction_for_headroom=min(1,bed['added_annual_headroom_JPY']/(total/treated))))
for cp in [1800,2300,2800]:
    for latent in [100000,159600,200000]:
        for feed in [160,180,220]:
            q=cp*(feed-30)+latent
            out['enthalpy_sensitivity'].append(dict(cp_J_kgK=cp,latent_J_kg=latent,feed_C=feed,
                heat_kWh_per_kg=q/3.6e6,heat_kWh_per_one_percent=1080*q/3.6e6))
out['calcite_single_pass_solution']={'C_kg_m3':.052,'water_m3_per_kg':1/.052,
    'latent_kWh_per_kg':1000/.052*p['aqueous']['water_latent_J_kg']/3.6e6,
    'source':'Bremen PHREEQC 25 C, ambient CO2. Not reactive slurry or recirculation.'}
(ROOT/'design_limits.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:len(v) for k,v in out.items() if isinstance(v,list)}))
