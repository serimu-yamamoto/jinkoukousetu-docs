from pathlib import Path
import json,math,hashlib,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from formation_conditioning import size_match,sphere_totals,mixture,schedule_minutes,residual_inventory
a=json.loads((D/'inputs.json').read_text());checks=[]
def ck(n,b):
 if not b:raise AssertionError(n)
 checks.append(n)
def eq(x,y):return math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-12)
eb=a['source_ebs'];pairs=[]
for row in eb['pairs']:
 label=str(row['M'])+'/'+str(row['S']);x=size_match(row['d50_M_um'],row['d50_S_um'],eb['additive_g'],eb['iron_g'])
 m=sphere_totals(eb['additive_g']*.001,a['hypothetical']['sphere_density_kg_m3'],row['d50_M_um']*1e-6)
 s=sphere_totals(eb['additive_g']*.001,a['hypothetical']['sphere_density_kg_m3'],row['d50_S_um']*1e-6)
 ck('count ratio '+label,eq(s['number']/m['number'],x['number_ratio_S_over_M_same_mass']))
 ck('area ratio '+label,eq(s['area']/m['area'],x['area_ratio_S_over_M_same_mass']))
 y=sphere_totals(x['S_mass_same_area']*.001,a['hypothetical']['sphere_density_kg_m3'],row['d50_S_um']*1e-6)
 z=sphere_totals(x['S_mass_same_number']*.001,a['hypothetical']['sphere_density_kg_m3'],row['d50_S_um']*1e-6)
 ck('area matching '+label,eq(y['area'],m['area']))
 ck('number matching '+label,eq(z['number'],m['number']))
 ck('cannot match both by dose '+label,not eq(y['number'],m['number']) and not eq(z['area'],m['area']))
 ck('source true mass fraction '+label,eq(x['source_mass_fraction'],.006))
 ck('dose denominator '+label,eq(x['same_area_mass_fraction']/(1-x['same_area_mass_fraction']),x['S_mass_same_area']/eb['iron_g']))
 ck('ordering '+label,0<x['same_number_mass_fraction']<x['same_area_mass_fraction']<x['source_mass_fraction'])
 reverse=size_match(row['d50_S_um'],row['d50_M_um'],eb['additive_g'],eb['iron_g'])
 ck('ratio reversal '+label,eq(reverse['number_ratio_S_over_M_same_mass']*x['number_ratio_S_over_M_same_mass'],1))
 same=size_match(row['d50_M_um'],row['d50_M_um'],3,497)
 ck('equal size control '+label,eq(same['S_mass_same_area'],3) and eq(same['S_mass_same_number'],3))
 pairs.append(dict(source_pair=row,conditional_sphere_matching=x))
pa=a['source_pa'];initial=mixture(pa['polymer_feed_g'],pa['initial_auxiliary_g']);other=dict(pa['initial_auxiliary_g'])
for key,value in pa['nonsolvent_g'].items():other[key]=other.get(key,0)+value
full=mixture(pa['polymer_feed_g'],other);times=schedule_minutes(pa['fixed_stages_min'])
ck('initial mass',eq(initial['total'],115))
ck('initial percent round',round(initial['polymer_fraction']*100,2)==1.74)
ck('combined mass',eq(full['total'],138.5))
ck('auxiliary closure',eq(sum(full['auxiliaries_per_polymer'].values())+1,full['total_per_polymer']))
ck('phenol per feed polymer',eq(full['auxiliaries_per_polymer']['phenol'],49))
ck('combined polymer dilution',full['polymer_fraction']<initial['polymer_fraction'])
ck('stated times',eq(times['minutes'],4780))
ck('hours decomposition',eq(times['hours'],79+40/60))
ck('formation hold exceeds60min',pa['fixed_stages_min']['waiting_to_cloud_after_mixing']>60)
ck('time excludes unknowns',a['hypothetical']['additional_fixed_time_min']==0)
inventories=[]
for f in a['hypothetical']['local_fractions']:
 M=a['hypothetical']['installed_product_kg']*f
 before=residual_inventory(M,pa['residual_phenol_before_ppm']);after=residual_inventory(M,pa['residual_phenol_after_ppm'])
 ck('residual ratio '+str(f),eq(before/after,2000))
 ck('unit ppm '+str(f),eq(after/M,3e-6))
 ck('removed mass balance '+str(f),eq((before-after)+after,before))
 inventories.append(dict(product_fraction=f,product_kg=M,before_kg=before,after_kg=after,interpretation='inventory only, not predicted release'))
ck('local proportional inventory',eq(inventories[1]['before_kg']/inventories[0]['before_kg'],.01))
ck('zero inventory',residual_inventory(0,6000)==0)
ck('ppm mass saturation',residual_inventory(1,1e6)==1)
ck('Kelvin difference',eq((eb['cure_temperature_K']-273.15)-(eb['DSC_peak_about_K']-273.15),6))
for fn,args in [(size_match,(0,1,1,1)),(sphere_totals,(-1,1,1)),(mixture,(1,{'bad':-1})),(schedule_minutes,({'bad':-1},)),(residual_inventory,(1,1e6+1))]:
 try:fn(*args)
 except ValueError:ck('invalid '+str(args),True)
 else:raise AssertionError('invalid accepted')
deps=['GPT往復/重合時結晶網と密度履歴検証_20261008/sources.md','GPT往復/液中形状形成と母液循環の濃度管理_20261010/model.md','GPT往復/雪の永久変形と粒接点の再配置設計_20261010/model.md']
data=dict(cycle=128,physical_trials=0,success_probability=None,dependency_hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in deps},size_matching=pairs,PA_feed=dict(initial=initial,combined=full,fixed_stage_sum=times),residual_inventory=inventories,limits=a['limits'])
v=dict(count=len(checks),passed=True,checks=checks,physical_validation=False)
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for name,x in [('results.json',data),('validation.json',v)]:
 if '--check' in sys.argv:assert (D/name).read_bytes()==enc(x)
 else:(D/name).write_bytes(enc(x))
print(json.dumps(dict(checks=len(checks),size_matching=pairs,PA_feed=data['PA_feed'],residual_inventory=inventories),ensure_ascii=False))
