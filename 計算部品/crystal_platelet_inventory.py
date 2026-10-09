"""Conditional precursor/platelet inventory; no synthesis or ski-performance prediction."""
import math
def pos(v):
 if not math.isfinite(v) or v<=0:raise ValueError('finite positive input required')
 return v
def fraction(v):
 if not math.isfinite(v) or not 0<v<=1:raise ValueError('yield must lie in (0,1]')
 return v
def platelet_inventory(area_m2,density_kg_m3,thickness_m,whole_platelet_layers,placement_yield):
 a=pos(area_m2);rho=pos(density_kg_m3);t=pos(thickness_m);n=pos(whole_platelet_layers);y=fraction(placement_yield)
 net=a*rho*t*n
 return dict(functional_area_m2=a,density_kg_m3_assumed=rho,platelet_thickness_m=t,
  whole_platelet_layers_assumed=n,placement_yield_assumed=y,net_crystal_kg=net,
  formed_crystal_required_kg=net/y,placement_loss_kg=net/y-net,
  interpretation='Volume-equivalent projected coverage, not proven monolayer formation or retained sliding surface.')
def feed_inventory(formed_crystal_kg,guanine_mM,molecular_mass_g_mol,crystal_yield,polymer_mg_mL):
 m=pos(formed_crystal_kg);c=pos(guanine_mM);mw=pos(molecular_mass_g_mol);y=fraction(crystal_yield);p=pos(polymer_mg_mL)
 # 1 mM=1 mol/m3; mg/mL=g/L=kg/m3.
 ckg=c*mw/1000
 volume=m/(ckg*y)
 return dict(formed_crystal_required_kg=m,precursor_guanine_mM=c,nominal_molecular_mass_g_mol=mw,
  input_guanine_kg_m3=ckg,crystal_yield_assumed=y,batch_equivalent_feed_liquid_m3=volume,
  polymer_input_mg_mL=p,polymer_input_kg=volume*p,initial_guanine_kg=volume*ckg,
  unconverted_or_unrecovered_guanine_kg=volume*ckg-m,
  interpretation='Cumulative batch-equivalent feed liquid; not fresh-water demand, tank size, recovered polymer, or final residue.')
