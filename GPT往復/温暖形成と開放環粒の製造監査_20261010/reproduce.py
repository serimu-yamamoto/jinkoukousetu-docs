from pathlib import Path
import json,sys,math,os,hashlib
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
sys.path.insert(0,os.environ.get('FIRN_COMMON_LIB',str(R/'計算部品')))
import formation_routes as f
checks=[]
def ck(name,value):assert value,name;checks.append(name)
g=f.grain();mass=2000*.45*150
ck('bed dry mass 135 t',mass==135000)
ck('annular blank subtraction',math.isclose(g['blank_volume_mm3'],math.pi*.6*(1-.49)))
ck('two rims plus six webs',math.isclose(g['volume_mm3'],math.pi*.51/3))
ck('machining yield 5/9',math.isclose(g['machining_yield'],5/9))
ck('one mm cube at 900 kg/m3 is 0.9 mg',math.isclose(1e-9*900*1e6,.9))
# Connected solid paths: each web crosses both rims; no physical strength inference.
for j in range(6):
    a=j*math.pi/3
    ck('continuous web '+str(j),all(f.contains(.85*math.cos(a),.85*math.sin(a),z,g) for z in [0,.05,.1,.2,.3,.4,.5,.55,.6]))
    w=a+math.pi/6
    ck('open radial window '+str(j),not any(f.contains(q*math.cos(w),q*math.sin(w),.3,g) for q in [.0,.3,.6,.75,.85,1.,1.1]))
ck('open axial bore',not any(f.contains(0,0,z,g) for z in [0,.1,.3,.5,.6]))
ck('closed upper rim path',all(f.contains(.85*math.cos(j*math.pi/180),.85*math.sin(j*math.pi/180),.05,g) for j in range(360)))
rate=f.spray_rate(.06,.02);water=f.feed_water_per_kg(.02)
ck('source feed unit conversion',math.isclose(rate,.000072))
ck('water accounting at assumed density',math.isclose(water,49.))
ck('energy conversion',f.heat_kWh(1,3600)==1)
route=dict(source_feed_ml_min=.06,source_solids_g_ml=.02,
 dry_feed_kg_h_per_nozzle=rate,water_kg_per_kg_solid_assumed_density=water,
 evaporative_kWh_per_kg_solid=f.heat_kWh(water),
 ideal_nozzles_for_135kg_h=(mass/1000)/rate,
 ideal_initial_evaporation_kWh=f.heat_kWh(water*mass),
 one_percent_replacement_kg=mass*.01,
 one_percent_feed_L=mass*.01/.02,
 one_percent_water_kg=mass*.01*water,
 one_percent_one_hour_evaporation_kW=f.heat_kWh(mass*.01*water),
 disclaimer='feed-solid upper bound, not usable grain production; assumes all feed water evaporated, excludes bath and wash water')
prod=[f.production(mass,1000,g,quality=q,recovery=r) for q in [.8,1.] for r in [0.,.5,.9]]
for p in prod:
    ck('virgin mass balance '+str((p['quality_yield'],p['recovery_fraction'])),
       math.isclose(p['virgin_kg'],mass+(1-p['recovery_fraction'])*(p['processed_kg']-mass)))
    ck('nozzle throughput balance '+str((p['quality_yield'],p['recovery_fraction'])),
       math.isclose(p['equivalent_heads']*p['nominal_head_kg_h']*1000,p['processed_kg']))
cake=[dict(solids_mass_fraction=c,water_kg_per_kg_solid=(1-c)/c,
 remaining_evaporation_kWh_per_kg=f.heat_kWh((1-c)/c)) for c in [.02,.1,.3,.6]]
# Scale relation checked independently of source geometry.
ck('geometry scaling mass cubic',math.isclose(f.grain(2.,1.4,1.2,.2)['mass_kg']/g['mass_kg'],8.))
out=dict(cycle=105,physical_trials=0,success_probability=None,
 inputs=dict(area_m2=2000,bed_depth_m=.45,dry_bulk_density_kg_m3=150,
 solid_density_kg_m3=900,manufacturing_hours=1000,assumption_not_quote=True),
 geometry=g,bed_dry_mass_kg=mass,
 implied_envelope_volume_fraction=150/(900*g['envelope_solid_fraction']),
 wet_ring=route,production=prod,dewatering_sensitivity=cake,
 source_module_sha256=hashlib.sha256((R/'計算部品/formation_routes.py').read_bytes()).hexdigest())
val=dict(checks=checks,count=len(checks),status='passed',physical_trials=0,success_probability=None,
 limitations=['geometry continuity is not stiffness or rain drainage proof','source strand throughput not demonstrated at candidate dimensions','spray feed solids not saleable dry product','no 50 C friction/wear/wet strength/health/environment measurements'])
if '--check' in sys.argv:
    assert out==json.loads((D/'results.json').read_text())
    assert val==json.loads((D/'validation.json').read_text())
else:
    for name,data in [('results.json',out),('validation.json',val)]:
        (D/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(checks=len(checks),geometry=g,wet_ring=route,production=prod[:3],
 implied_packing=out['implied_envelope_volume_fraction']),ensure_ascii=False))
