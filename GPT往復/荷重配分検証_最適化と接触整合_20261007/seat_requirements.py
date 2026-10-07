"""Ideal short bearing seat sizing envelope, not a validated contact geometry."""
from allocation import *

def main():
 hold=json.loads((H/'contact_audit_results.json').read_text(encoding='utf-8'));cost=json.loads((H.parent/'骨格変形検証_表面摩擦と自由粒_20261007/economics_results.json').read_text(encoding='utf-8'));rows=[];E=300.;strain=.01;width=.020;length=.020;count=6;vol=count*width*width*length
 for h in hold['holding_budgets']:
  if abs(h['mu']-.1)>1e-12 or abs(h['load_mN']-.9)>1e-12:continue
  sizes=[]
  for c in h['contacts']:
   F=c['minimum_extra_force_mN']/1000;A=F/(E*strain);sizes.append(dict(contact=c['contact'],required_force_mN=F*1000,minimum_nominal_area_um2=A*1e6,square_width_um=math.sqrt(A)*1000,stress_on_20um_square_MPa=F/(width*width),short_20um_member_displacement_um=F*length/(E*width*width)*1000))
  economics=[]
  for density in [960,1410]:
   base=next(c for c in cost['cases'] if c['name']==h['name'] and c['density_kg_m3']==density);ratio=1+vol/base['volume_upper_mm3'];mass=base['pilot_mass_kg']*ratio;A=cost['assumptions'];fixed=A['nonmaterial_initial_JPY']*A['CRF']+A['annual_operating_JPY'];econ=dict(density_kg_m3=density,added_mass_kg=mass-base['pilot_mass_kg'],added_material_JPY=(mass-base['pilot_mass_kg'])*500,conditional_EAC_JPY=fixed+mass*500*(A['CRF']+.02),conditional_price_cap_JPY_kg=(19e6-fixed)/(mass*(A['CRF']+.02)));economics.append(econ)
  rows.append(dict(name=h['name'],sizes=sizes,ideal_additional_volume_mm3=vol,economics=economics))
 out=dict(physical_tests=0,success_probability=None,assumptions=dict(E_MPa=E,nominal_strain_budget=strain,seat_width_um=width*1000,load_path_length_um=length*1000,seats_per_grain=count,mu=.1),scope='Ideal axial bearing area and volume budget, conditional on carrying the missing reaction through compression. Does not prove the requisite interlocking/undercut load path, contact patch, rounded protection, connection to skeleton, assembly, release, joint strength, actual packing, moldability or price. Holding demands extrapolated to 0.9 mN from linear all-stick trials; some exceed the original model diagnostic.',designs=rows);(H/'seat_requirements.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({'designs':len(rows),'additional_volume_mm3':vol}))
if __name__=='__main__':main()
