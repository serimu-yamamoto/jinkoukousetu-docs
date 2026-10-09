from pathlib import Path
import sys,json,math,hashlib
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from crystal_platelet_inventory import *
checks=[]
def check(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def close(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10)
dep='GPT往復/結晶接触材の粒度基準と保持量監査_20261010/results.json'
prior=json.loads((R/dep).read_text());ref=prior['reference_localized_coating']
area=ref['core_kg']*ref['coatable_area_m2_per_kg_core']*ref['target_area_fraction']
check('inherited functional area',close(area,267300))
inputs=json.loads((D/'inputs.json').read_text());t=inputs['reported']['platelet_thickness_m'];mw=inputs['assumed']['nominal_guanine_molecular_mass_g_mol']
platelets=[]
for rho in inputs['assumed']['density_kg_m3']:
 for layers in inputs['assumed']['whole_platelet_layers']:
  for yp in inputs['assumed']['placement_yield']:
   p=platelet_inventory(area,rho,t,layers,yp)
   check('placement mass balance '+str((rho,layers,yp)),close(p['formed_crystal_required_kg']*yp,p['net_crystal_kg']))
   platelets.append(p)
reference=next(p for p in platelets if p['density_kg_m3_assumed']==1800 and p['whole_platelet_layers_assumed']==1 and p['placement_yield_assumed']==1)
feeds=[]
for label,m in [('legacy1350kg',1350),('monolayer_reference',reference['formed_crystal_required_kg']),('placement_yield_half',2*reference['formed_crystal_required_kg'])]:
 for c in inputs['reported']['precursor_concentrations_mM']:
  for yc in inputs['assumed']['crystal_yield']:
   f=feed_inventory(m,c,mw,yc,1);f['comparison_basis']=label;feeds.append(f)
   check('feed mass closure '+str((label,c,yc)),close(f['initial_guanine_kg']*yc,m))
   check('feed unit conversion '+str((label,c,yc)),close(f['batch_equivalent_feed_liquid_m3']*1000*c/1000*mw/1000*yc,m))
check('0.66mM nominal mass concentration',close(feed_inventory(1,.66,mw,1,1)['input_guanine_kg_m3'],.0997458))
check('42nm whole platelet counted once',close(reference['net_crystal_kg'],20.20788))
check('thickness linearity',close(platelet_inventory(area,1800,2*t,1,1)['net_crystal_kg'],2*reference['net_crystal_kg']))
check('three whole platelets triples mass',close(platelet_inventory(area,1800,t,3,1)['net_crystal_kg'],3*reference['net_crystal_kg']))
aspect=inputs['reported']['platelet_length_m']/t
check('aspect arithmetic',close(aspect,47.61904761904761))
for func,args in [(platelet_inventory,(area,1800,t,1,0)),(feed_inventory,(1,.66,mw,1.1,1)),(feed_inventory,(1,0,mw,1,1))]:
 try:func(*args)
 except ValueError:check('invalid input '+str(args),True)
 else:raise AssertionError('invalid accepted')
data=dict(cycle=114,physical_trials=0,success_probability=None,dependency_hashes={dep:hashlib.sha256((R/dep).read_bytes()).hexdigest()},
 reported_geometry=inputs['reported'],inherited_reference=ref,platelet_scenarios=platelets,feed_scenarios=feeds,
 reference_platelet=reference,aspect_ratio_length_to_thickness=aspect,
 limiting_feed_reference=next(f for f in feeds if f['comparison_basis']=='legacy1350kg' and f['precursor_guanine_mM']==.66 and f['crystal_yield_assumed']==1),
 monolayer_feed_reference=next(f for f in feeds if f['comparison_basis']=='monolayer_reference' and f['precursor_guanine_mM']==.66 and f['crystal_yield_assumed']==1),
 caution='No actual coating coverage, crystal retention,50C friction, environmental compatibility or commercial price demonstrated.')
validation=dict(count=len(checks),checks=checks,passed=True,physical_validation=False,
 scope='Geometry and feed inventory arithmetic only; not crystallization yield, optical quality or snow-ski behavior.')
def enc(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for p,v in [('results.json',data),('validation.json',validation)]:
 if '--check' in sys.argv:assert (D/p).read_bytes()==enc(v)
 else:(D/p).write_bytes(enc(v))
print(json.dumps(dict(checks=len(checks),platelet_conditions=len(platelets),feed_conditions=len(feeds),reference_platelet=reference,
 legacy_feed=data['limiting_feed_reference'],thin_feed=data['monolayer_feed_reference'],reproduced='--check' in sys.argv),ensure_ascii=False))
