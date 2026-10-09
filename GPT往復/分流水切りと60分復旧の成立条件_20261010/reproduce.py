from pathlib import Path
import sys,json,hashlib,math,os
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
sys.path.insert(0,os.environ.get('FIRN_COMMON_LIB',str(R/'計算部品')))
import restoration_process as p
import formation_routes as g
checks=[]
def ck(name,v):assert v,name;checks.append(name)
T=p.available_seconds();ck('60-22-2 = 36 minutes',T==2160)
old=R/'GPT往復/雨後凝集の解離と60分復旧検証_20261009/inputs.json'
v76=json.loads(old.read_text())['parameters'];ck('prior allocation preserved',v76['closed_s']==3600 and v76['other_s']==1320)
rows=[p.load(A,d,f,seconds=T) for A in [2000,20000] for d in [.05,.3,.45] for f in [.01,.1,1.]]
for r in rows:
 ck('mass and throughput '+str((r['area_m2'],r['depth_m'],r['area_fraction'])),
    math.isclose(r['required_t_h']*1000*T/3600,r['dry_mass_kg']))
 ck('independent volume balance '+str((r['area_m2'],r['depth_m'],r['area_fraction'])),
    math.isclose(r['required_m3_h']*T/3600,r['dry_mass_kg']/150))
caps=[dict(area_m2=A,**p.capacity(q,A*.45*150,T)) for A in [2000,20000] for q in [5,20,50,150]]
ck('20 t/h handles 12 t in 36 min',p.capacity(20,135000,T)['processable_kg']==12000)
ck('whole 20000m2 is 2250 t/h',p.load(20000,.45,1.,seconds=T)['required_t_h']==2250.)
carriers=[p.carrier(q,t,h) for q in [5,20,50] for t in [10,30,60] for h in [.005,.01,.03]]
for c in carriers:ck('carrier inventory '+str((c['q_dry_t_h_assumed'],c['residence_s_assumed'],c['layer_m_assumed'])),
 math.isclose(c['active_area_m2']*c['layer_m_assumed']*150,c['q_dry_t_h_assumed']*1000/3600*c['residence_s_assumed']))
rotors=[p.centrifuge(G,h) for G in [10,50,100] for h in [.005,.01,.03]]
for r in rotors:
 ck('rpm acceleration '+str((r['G_assumed'],r['layer_m_assumed'])),
  math.isclose((r['rpm']*2*math.pi/60)**2*r['R_m_assumed'],r['G_assumed']*9.81))
ref=R/'GPT往復/開放環粒の三次元支持と毛管残水の比較_20261010/results.json'
r106=json.loads(ref.read_text());scales=[x for x in r106['capillary_scales'] if x['assumed_angle_deg']==60.]
eqG=[dict(path=x['path'],web_fraction=x.get('web_fraction'),pressure_scale_Pa=x['pressure_magnitude_Pa'],
 acceleration_equivalent_G=x['pressure_magnitude_Pa']/p.centrifuge(1.,.01)['water_radial_pressure_scale_Pa'],
 interpretation='pressure-scale equivalence only; not drainage threshold or specified rotor acceleration') for x in scales]
screens=[dict(slot_mm=s,angle_from_edge_on_deg=a,envelope_width_mm=p.projected_width(a),
 rigid_long_slot_pass_geometrically_possible=p.projected_width(a)<=s)
 for s in [.3,.5,.6,1.,1.4] for a in [0,10,20,30,45,90]]
ck('edge-on width is thickness',p.projected_width(0)==.6)
ck('face-on width is diameter',math.isclose(p.projected_width(90),2.))
ck('1.4mm slit admits 20deg counterexample',p.projected_width(20)<1.4)
grain=g.grain();V=grain['volume_mm3']*1e-9
buoy=dict(solid_density_assumed=900.,fluid_density_assumed=1000.,solid_volume_m3=V,
 dry_outward_bodyforce_100G_N=900*V*100*9.81,
 submerged_relative_outward_force_100G_N=(900-1000)*V*100*9.81,
 assumptions='rigid fully wetted open grain; no trapped gas; co-rotating liquid; force sign is relative to fluid, no rotor/lifter contact')
ck('buoyancy counterexample direction',buoy['submerged_relative_outward_force_100G_N']<0)
ck('buoyancy force identity',math.isclose(buoy['dry_outward_bodyforce_100G_N']-1000*V*981,buoy['submerged_relative_outward_force_100G_N']))
loss=[p.loss_budget(12000,200,x,500) for x in [.0001,.001,.01]]
ck('100ppm contained loss mass',loss[0]['contained_reject_kg_y']==240)
ck('hypothetical raw cost units',loss[0]['raw_replacement_JPY_y_assumed']==120000)
water=dict(incoming_water_kg_per_dry_kg_assumed=.2,outgoing_water_kg_per_dry_kg_assumed=.02,
 dry_kg_per_closure=12000,water_removed_kg_per_closure=12000*(.2-.02),
 water_removed_t_h=(20*(.2-.02)),claim='water-content target unqualified for ski performance; not achieved')
out=dict(cycle=107,physical_trials=0,success_probability=None,processing_seconds=T,
 scopes=rows,qualified_capacity_scenarios=caps,carrier_scenarios=carriers,
 centrifugal_scales=rotors,capillary_equivalent_acceleration=eqG,
 screen_geometry=screens,buoyancy_counterexample=buoy,
 annual_contained_losses=loss,water_balance=water,
 dependencies={str(x.relative_to(R)):hashlib.sha256(x.read_bytes()).hexdigest() for x in [old,ref,R/'計算部品/formation_routes.py',R/'計算部品/restoration_process.py']})
val=dict(status='arithmetic_and_geometry_checks_passed',count=len(checks),checks=checks,
 physical_trials=0,success_probability=None,limitations=['no actual dewatering residual water or attrition data','device mass ratings are not qualified firn capacity','screen geometry only; no retention guarantee under deformation','pressure and acceleration scales not drainage onset criteria'])
if '--check' in sys.argv:
 assert out==json.loads((D/'results.json').read_text());assert val==json.loads((D/'validation.json').read_text())
else:
 for name,o in [('results.json',out),('validation.json',val)]: (D/name).write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(checks=len(checks),whole_bed=[r for r in rows if r['depth_m']==.45 and r['area_fraction']==1.],
 q20=[r for r in caps if r['q_dry_t_h_assumed']==20],carrier20=next(r for r in carriers if r['q_dry_t_h_assumed']==20 and r['residence_s_assumed']==30 and r['layer_m_assumed']==.01),
 equivalent_G=eqG,rotor100=next(r for r in rotors if r['G_assumed']==100 and r['layer_m_assumed']==.01),buoyancy=buoy)))
