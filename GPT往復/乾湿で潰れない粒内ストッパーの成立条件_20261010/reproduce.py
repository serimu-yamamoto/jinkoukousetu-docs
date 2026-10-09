from pathlib import Path
import json,sys,math,hashlib
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from drying_stop_geometry import shape_ratios,stop_geometry,mass_increment
a=json.loads((D/'inputs.json').read_text());h=a['assumed'];checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def eq(a,b):return math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-15)
shapes=[dict(id=q['id'],**shape_ratios(q['initial'],q['final'])) for q in h['synthetic_shape_pairs']]
ck('top view can hide collapse',eq(shapes[0]['xy_projected_area_ratio'],1) and eq(shapes[0]['ellipsoid_envelope_volume_ratio'],.1))
ck('uniform length not volume',eq(shapes[1]['ellipsoid_envelope_volume_ratio'],.001))
ck('wet recovery has no dry-state information',eq(shapes[2]['ellipsoid_envelope_volume_ratio'],1) and shapes[0]['ellipsoid_envelope_volume_ratio']<1)
rows=[]
for rad in h['radii_um']:
 args=[h['patch_um'][0]*1e-6,h['patch_um'][1]*1e-6,h['plate_thickness_um']*1e-6,h['gap_um']*1e-6,rad*1e-6,h['post_height_um']*1e-6,h['posts_per_face']]
 z=stop_geometry(*args);inc=mass_increment(h['base_material_kg'],h['local_reference_mass_fraction'],z['local_added_solid_fraction'])
 # Independent calculation in micrometres, then volume-unit conversion.
 post_um3=2*h['posts_per_face']*math.pi*rad**2*h['post_height_um']
 plate_um3=2*h['patch_um'][0]*h['patch_um'][1]*h['plate_thickness_um']
 ck('independent volume units '+str(rad),eq(z['added_solid_volume_m3'],post_um3*1e-18))
 ck('ratio independent units '+str(rad),eq(z['local_added_solid_fraction'],post_um3/plate_um3))
 ck('clearance partition '+str(rad),eq(z['remaining_gap_at_first_contact_m']+z['closure_before_first_contact_m'],h['gap_um']*1e-6))
 ck('reference load balance '+str(rad),eq(z['nominal_stop_stress_multiplier']*z['contact_area_m2'],z['reference_patch_area_m2']))
 ck('inventory conservation '+str(rad),eq(inc['total_kg']-h['base_material_kg'],inc['added_kg']))
 scaled=stop_geometry(*[x*2 for x in args[:6]],args[6])
 ck('geometric scale keeps ratio '+str(rad),eq(scaled['local_added_solid_fraction'],z['local_added_solid_fraction']))
 ck('geometric scale cubic volume '+str(rad),eq(scaled['added_solid_volume_m3'],8*z['added_solid_volume_m3']))
 rows.append(dict(radius_um=rad,**z,inventory=inc))
ck('radius doubles cost quadruples',eq(rows[1]['local_added_solid_fraction'],4*rows[0]['local_added_solid_fraction']))
ck('radius doubles stress quarters',eq(rows[1]['nominal_stop_stress_multiplier'],rows[0]['nominal_stop_stress_multiplier']/4))
ck('no whole-bed increment if no local phase',mass_increment(135000,0,.1)['added_kg']==0)
for name,fun,args in [('negative_dimension',shape_ratios,([1,1,1],[1,0,1])),('fraction_over_one',mass_increment,(1,2,.1)),('nan',mass_increment,(float('nan'),.1,.1)),('initial_post_contact',stop_geometry,(1,1,.1,.2,.01,.1,4)),('noninteger_post_count',stop_geometry,(1,1,.1,.2,.01,.05,1.5))]:
 try:fun(*args)
 except ValueError:ck('invalid '+name,True)
 else:raise AssertionError(name)
deps=['GPT往復/液中形状形成と母液循環の濃度管理_20261010/sources.json','GPT往復/枝状粒形成検証_熱選別と回収収支_20261008/sources.md','GPT往復/多孔質焼結と緻密薄枝の製法比較_20261009/model.md']
data=dict(cycle=123,physical_trials=0,success_probability=None,dependency_hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in deps},shape_counterexamples=shapes,stop_scenarios=rows,limits=a['limits'])
v=dict(count=len(checks),passed=True,checks=checks,physical_validation=False)
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for n,x in [('results.json',data),('validation.json',v)]:
 if '--check' in sys.argv:assert (D/n).read_bytes()==enc(x)
 else:(D/n).write_bytes(enc(x))
print(json.dumps(dict(checks=len(checks),stops=[dict(radius_um=z['radius_um'],mass_fraction=z['local_added_solid_fraction'],stress_factor=z['nominal_stop_stress_multiplier'],added_kg=z['inventory']['added_kg']) for z in rows])))
