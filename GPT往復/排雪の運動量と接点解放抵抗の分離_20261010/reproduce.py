from pathlib import Path
import json,sys,math,hashlib
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from chip_transport_balance import transport,outgoing_distribution,impulse_parcels
a=json.loads((D/'inputs.json').read_text());h=a['hypothetical'];checks=[]
def ck(n,b):
 if not b:raise AssertionError(n)
 checks.append(n)
def eq(x,y):return math.isclose(x,y,rel_tol=1e-9,abs_tol=1e-9)
rows=[]
for rho in h['rho_kg_m3']:
 for speed in h['speeds_m_s']:
  for g in h['attack_deg']:
   for chi in h['chi']:
    for rate in h['rate_coeff_kg_m3']:
     z=transport(rho,h['length_m'],h['depth_m'],speed,g,h['q0_Pa'],rate,chi)
     key=str((rho,speed,g,chi,rate))
     ck('energy partition '+key,eq(z['total_tool_power_W'],z['outgoing_kinetic_power_W']+z['transport_dissipation_W']+z['structural_dissipation_W']))
     ck('passive transfer '+key,z['transport_dissipation_W']>=-1e-9)
     ck('vector magnitude '+key,eq(math.hypot(*z['reaction_xy_N']),z['total_cross_edge_force_N']))
     rows.append(dict(rho_kg_m3=rho,speed_m_s=speed,attack_deg=g,chi=chi,rate_coeff_kg_m3=rate,
      paper_speed_range_only=1<=speed<=5,**z))
ident=[]
for g in [15,45,90]:
 for speed in h['speeds_m_s']:
  cases=[transport(400,h['length_m'],h['depth_m'],speed,g,h['q0_Pa'],m['rate_coeff_kg_m3'],m['chi']) for m in h['equivalent_models']]
  ck('force-only degeneracy '+str((g,speed)),all(eq(cases[0]['total_cross_edge_force_N'],x['total_cross_edge_force_N']) for x in cases))
  ident.append(dict(speed_m_s=speed,attack_deg=g,models=[dict(id=m['id'],**x) for m,x in zip(h['equivalent_models'],cases)]))
counter=[]
for m in h['equivalent_models']:
 z=transport(150,h['length_m'],h['depth_m'],10,90,h['q0_Pa'],m['rate_coeff_kg_m3'],m['chi'])
 old=transport(400,h['length_m'],h['depth_m'],10,90,h['q0_Pa'],m['rate_coeff_kg_m3'],m['chi'])
 counter.append(dict(id=m['id'],old_force_N=old['total_cross_edge_force_N'],new_force_N=z['total_cross_edge_force_N'],force_reduction_fraction=1-z['total_cross_edge_force_N']/old['total_cross_edge_force_N']))
distributions=[]
for label,dist in [('uniform',[(1,1)]),('spread',[(.5,.5),(1.5,.5)]),('elastic',[(2,1)]),('zero',[(0,1)])]:
 z=outgoing_distribution(400,.0006,5,dist);p=impulse_parcels(400,.0006,5,dist,.2)
 for k in ['force_N','kinetic_W','work_W']:ck('parcel '+label+k,eq(z[k],p[k]))
 ck('distribution passivity '+label,z['dissipation_W']>=0)
 distributions.append(dict(label=label,distribution=dist,**z))
ck('same first moment force',eq(distributions[0]['force_N'],distributions[1]['force_N']))
ck('higher second moment kinetic',eq(distributions[1]['kinetic_W']/distributions[0]['kinetic_W'],1.25))
ck('elastic limit',eq(distributions[2]['dissipation_W'],0))
z1=transport(400,.2,.003,5,30,0,0,1);z2=transport(400,.2,.003,10,30,0,0,1)
ck('transport speed squared',eq(z2['transport_force_N']/z1['transport_force_N'],4))
ck('transport power cubed',eq(z2['transport_power_W']/z1['transport_power_W'],8))
for args in [(0,.2,.003,5,30,0,0,1),(400,.2,.003,5,0,0,0,1),(400,.2,.003,5,30,0,0,3)]:
 try:transport(*args)
 except ValueError:checks.append('invalid input '+str(args))
 else:raise AssertionError('invalid accepted')
mass=[dict(rho_kg_m3=rho,mass_per_m2_kg=rho*h['bed_depth_m']) for rho in h['rho_kg_m3']]
out=dict(cycle=132,physical_trials=0,success_probability=None,rows=rows,force_identifiability=ident,counterfactual_density_only=counter,particle_distribution_diagnostics=distributions,bed_mass=mass,
 dependency_hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in a['dependencies']})
val=dict(count=len(checks),passed=True,checks=checks,physical_trials=0,success_probability=None)
def enc(x):return json.dumps(x,ensure_ascii=False,indent=2)+'\n'
if '--check' in sys.argv:
 assert (D/'results.json').read_text()==enc(out);assert (D/'validation.json').read_text()==enc(val)
else:
 (D/'results.json').write_text(enc(out),encoding='utf-8',newline='\n')
 (D/'validation.json').write_text(enc(val),encoding='utf-8',newline='\n')
print(json.dumps(dict(checks=len(checks),rows=len(rows),identifiability=len(ident),counterfactual=counter,distributions=distributions,mass=mass),ensure_ascii=False))
