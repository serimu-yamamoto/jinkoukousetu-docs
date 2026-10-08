"""Cycle 17: branched-polyethylene feed, mass basis and hypothetical coating.
Product water content is not resin absorption or outdoor equilibrium moisture.
No physical trials, selected recipe or current price quote.
"""
import json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CURRENT="https://jp.mitsuichemicals.com/en/special/swp/product/"
APPLICATION="https://www.minifibers.com/files/literature/Technology-of-Fybrel%C2%AE-in-Fiber-Cement.pdf"

def moisture_row(label,grade,melting,length,w,source,dry_kg=108000):
    water=w/(1-w); latent=water*2450000/3600000
    return dict(dataset=label,grade=grade,source=source,listed_melting_C=melting,
      listed_fiber_length_mm=length,listed_product_water_percent=w*100,
      product_water_fraction_wet_basis_for_calculation=w,
      listed_appearance='Hydrous sheet',comparison_dry_mass_kg=dry_kg,
      wet_feed_mass_kg=dry_kg/(1-w),water_per_dry_kg=water,
      latent_only_kWh_per_dry_kg=latent,
      illustrative_electric_JPY_per_dry_kg_at_20JPY_kWh_80percent_efficiency=latent*20/.8,
      limitations='Representative supplier data, not guaranteed lot specifications, 50C creep, loose-grain quality or outdoor retained water; drying heat excludes sensible heat and equipment.')

def build():
    current=[moisture_row('Mitsui SWP current public reference','E400',135,.9,.63,CURRENT),
      moisture_row('Mitsui SWP current public reference','E524',135,1.2,.57,CURRENT),
      moisture_row('Mitsui SWP current public reference','E620',135,1.2,.64,CURRENT),
      moisture_row('Mitsui SWP current public reference','E690',135,1.3,.53,CURRENT),
      moisture_row('Mitsui SWP current public reference','E790',135,1.5,.50,CURRENT),
      moisture_row('Mitsui SWP current public reference','EST-8',135,.9,.59,CURRENT),
      moisture_row('Mitsui SWP current public reference','NL491',100,1.0,.55,CURRENT),
      moisture_row('Mitsui SWP current public reference','AU690',120,1.2,.52,CURRENT)]
    for row in current:
        row['trade_air_dry_ADkg']=row['comparison_dry_mass_kg']/.9
        row['arbitrary_500JPY_per_ADkg_to_JPY_per_dry_kg_not_quote']=500/.9
    old=[moisture_row('Fybrel application technical paper; wet basis assumed','E600',132,1.3,.60,APPLICATION),
      moisture_row('Older Fybrel technical paper; wet basis assumed','E620',132,1.3,.65,APPLICATION),
      moisture_row('Older Fybrel technical paper; wet basis assumed','E380',132,.7,.68,APPLICATION)]
    coatings=[]
    for nm in [10,100,1000]:
        for fraction in [1,.1,.01]:
            mass=10000*(nm*1e-9)*1000*fraction
            coatings.append(dict(hypothetical_thickness_nm=nm,covered_area_fraction=fraction,
                family_specific_surface_m2_kg=10000,hypothetical_coating_density_kg_m3=1000,
                coating_kg_per_dry_fiber_kg=mass,coating_fraction_of_total_coated_mass=mass/(1+mass),
                source_of_area=APPLICATION,
                note='Family-level illustrative area, NOT a verified value for each current SWP grade'))
    checks=0
    for row in current+old:
        w=row['product_water_fraction_wet_basis_for_calculation']
        wet=row['wet_feed_mass_kg']; dry=row['comparison_dry_mass_kg']
        assert math.isclose(wet*(1-w),dry,rel_tol=1e-12); checks+=1
        assert math.isclose(wet*w/dry,row['water_per_dry_kg'],rel_tol=1e-12); checks+=1
        if 'trade_air_dry_ADkg' in row:
            assert math.isclose(wet*(100-row['listed_product_water_percent'])/90,row['trade_air_dry_ADkg'],rel_tol=1e-12); checks+=1
    for row in coatings:
        # A 1 g sample at the assumed specific area has 10 m2 exposed area.
        test_kg=10*(row['hypothetical_thickness_nm']/1e9)*1000*row['covered_area_fraction']
        assert math.isclose(test_kg/.001,row['coating_kg_per_dry_fiber_kg'],rel_tol=1e-12); checks+=1
    return dict(physical_tests=0,physical_success_probability=None,numerical_checks=checks,
      current_swp=current,application_fybrel=old,coating_inventory=coatings,
      basis_note='ADkg includes 10% moisture. Quoted JPY/ADkg divided by 0.9 gives JPY/kg dry polymer. Application-reference and current grade values are not merged.',
      thermal_bonding_note='135C vs 100/120C representative melting points motivate a two-phase comparison; they do not establish a temperature window, bond strength, reuse or safety.',
      warning='No fiber diameter or airborne fraction is inferred from specific surface area. No coating or blend has been selected or manufactured.')

if __name__=='__main__':
    r=build()
    (ROOT/'pulp_scale.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(numerical_checks=r['numerical_checks'],physical_tests=0,physical_success_probability=None)))
