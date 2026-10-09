from pathlib import Path
import json,math,hashlib,sys,itertools
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from compound_contact_inventory import mixture,replacement_inventory,source_comparison,inclusion_scale
from material_beam_screen import local_replacement
a=json.loads((D/'inputs.json').read_text());s=a['source_reported'];h=a['assumed'];checks=[]
def ck(n,b):
 if not b:raise AssertionError(n)
 checks.append(n)
def eq(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10)
ck('feed mass closes',eq(s['pk_feed_kg_h']+s['uhmwpe_feed_kg_h'],s['compound_feed_kg_h']))
w=s['uhmwpe_feed_kg_h']/s['compound_feed_kg_h']
mixes=[]
for rho in [*s['uhmwpe_density_range_kg_m3'],935]:
 x=mixture(w,s['pk_density_kg_m3'],rho);x['input_additive_density']=rho
 ck('density lies between phases '+str(rho),rho<x['ideal_density_kg_m3']<s['pk_density_kg_m3'])
 ck('unit kg volume closes '+str(rho),eq(1/x['ideal_density_kg_m3'],(1-w)/s['pk_density_kg_m3']+w/rho))
 ck('volume fraction mass backsolve '+str(rho),eq(x['additive_volume_fraction']*rho/x['ideal_density_kg_m3'],w))
 mixes.append(x)
x=next(x for x in mixes if x['input_additive_density']==935)
rows=[]
for label,rho_ref in [('PE_reference_assumed',h['reference_solid_density_kg_m3']),('PK_reference_assumed',s['pk_density_kg_m3'])]:
 for f in h['compound_solid_volume_fractions']:
  key=label+str(f)
  y=replacement_inventory(h['reference_mass_kg'],rho_ref,f,x['ideal_density_kg_m3'],w,s['compound_feed_kg_h']);y['compound_solid_volume_fraction']=f;y['reference_label']=label;y['reference_density_kg_m3']=rho_ref
  ck('total mass split '+key,eq(y['total_kg'],y['compound_kg']+y['retained_reference_kg']))
  ck('source phase mass '+key,eq(y['additive_kg']/y['compound_kg'],w))
  z=local_replacement(f,x['ideal_density_kg_m3']/rho_ref)
  ck('reuse120 inventory '+key,eq(z['mass_ratio']*h['reference_mass_kg'],y['total_kg']))
  ck('throughput hours identity '+key,eq(y['lab_throughput_equivalent_h']*s['compound_feed_kg_h'],y['compound_kg']))
  rows.append(y)
comparisons={}
for measure in ['mu','wear_coefficient_reported_numbers']:
 for phase in ['full','steady']:
  b=s['tribology'][measure]['plain'][phase];v=s['tribology'][measure]['compound'][phase]
  c=source_comparison(b,v);comparisons[measure+'_'+phase]=c
  ck('ratio plus reduction '+measure+phase,eq(c['after_over_before']+c['reduction_fraction'],1))
wear=s['tribology']['wear_coefficient_reported_numbers'];whole_steady={k:v['full']/v['steady'] for k,v in wear.items()}
ck('whole/steady compound exceeds3',whole_steady['compound']>3)
scales=[]
for t,d in itertools.product(h['root_thickness_um'],h['inclusion_diameters_um']):
 y=inclusion_scale(t,d);scales.append(y)
 ck('single sphere cover '+str((t,d)),eq(2*y['centered_cover_each_side_um']+d,t) if y['fits_single_sphere'] else y['centered_cover_each_side_um']==0)
for fun,args in [(mixture,(-.1,1240,935)),(replacement_inventory,(135000,935,1.1,1220,.05,20)),(inclusion_scale,(0,38))]:
 try:fun(*args)
 except ValueError:ck('invalid '+str(args),True)
 else:raise AssertionError('invalid accepted')
deps=['計算部品/material_beam_screen.py','GPT往復/素材とスキー双方の履歴を分ける乾式接点検証_20261009/model.md','GPT往復/耐摩耗候補と枝の柔らかさを両立する材料選定_20261010/sources.json']
data=dict(cycle=121,physical_trials=0,success_probability=None,dependency_hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in deps},
 source_ratios=comparisons,whole_over_steady_wear_number=whole_steady,feed_additive_fraction=w,
 ideal_mixtures=mixes,inventories=rows,inclusion_scales=scales,
 limits=a['limits'],scope='Source arithmetic and ideal composition/inventory, no friction or lifetime model')
v=dict(count=len(checks),checks=checks,passed=True,physical_validation=False)
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for n,o in [('results.json',data),('validation.json',v)]:
 if '--check' in sys.argv:assert (D/n).read_bytes()==enc(o)
 else:(D/n).write_bytes(enc(o))
print(json.dumps(dict(checks=len(checks),ratios=comparisons,whole_steady=whole_steady,mixture=x,inventory10=[r for r in rows if r['compound_solid_volume_fraction']==.1]),ensure_ascii=False))
