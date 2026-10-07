"""Conditional price ceilings at unchanged grain count; not quotations."""
import json,math
from elastic_free import H

def main():
 old=json.loads((H.parent/'粒間接触検証_自由回転と濡れ_20261007/wet_cost_results.json').read_text(encoding='utf-8'));B=json.loads((H/'brace_results.json').read_text(encoding='utf-8'));A=old['cost_assumptions'];base=next(x for x in old['cost'] if x['model']=='C3');rows=[];crf=A['CRF'];fixed=A['nonmaterial_initial_JPY']*crf+A['annual_operating_JPY']
 designs=[dict(name=x['model'],v=x['volume_sum_upper_mm3'],valid=True) for x in old['cost']]+[dict(name='C3-'+x['brace']+'-'+str(round(x['brace_radius_mm']*2000)),v=base['volume_sum_upper_mm3']+x['added_volume_upper_mm3'],valid=x['clearance']['robust_noninterfering']) for x in B['cases']]
 for d in designs:
  for density in [960,1410]:
   mass=base['conditional_pilot_mass_kg']*d['v']/base['volume_sum_upper_mm3']*density/960;cap=(A['annual_budget_JPY']-fixed)/(mass*(crf+A['replenishment_fraction_per_year']));initial=mass*A['finished_grain_price_JPY_kg'];eac=fixed+initial*(crf+A['replenishment_fraction_per_year']);rows.append(dict(name=d['name'],density_kg_m3=density,volume_upper_mm3=d['v'],pilot_mass_kg=mass,material_initial_JPY=initial,conditional_EAC_JPY=eac,conditional_price_cap_JPY_kg=cap,full_20000m2_material_JPY=initial*10,saved_fixture_clearance_pass=d['valid']))
 (H/'economics_results.json').write_text(json.dumps(dict(physical_tests=0,success_probability=None,assumptions=A,density_scope='960 and 1410 kg/m3 are separate scenarios, not a blend specification or a measured finished-grain density.',cost_scope='Pretax hypothetical 2000 m2 pilot, 450 mm bed, unchanged grain count. Brace-volume intersections not subtracted. No new molds, selective coating, extra manufacturing or recovery costs added. Two percent replacement is not an allowable environmental release.',cases=rows),indent=2)+'\n',encoding='utf-8');print(json.dumps({'cases':len(rows)}))
if __name__=='__main__':main()
