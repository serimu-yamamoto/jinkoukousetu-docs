from pathlib import Path
import math,json,hashlib,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from porous_grain_process import recipe_balance,recovery_budget,solid_oblate,integrate_oblate_volume
a=json.loads((D/'inputs.json').read_text());p=a['patent'];h=a['hypothetical'];checks=[]
def ck(n,b):
 if not b:raise AssertionError(n)
 checks.append(n)
def eq(x,y):return math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-10)
rows=[];budgets=[];shapes=[];normalised_cost=[]
for rec in p['recipes']:
 ck('charge mass '+rec['id'],rec['polymer_g']+rec['solvent_g']==1200)
 ck('reported index rounding '+rec['id'],abs(rec['C_um']/rec['B_um']-rec['index_reported'])<.006)
 for y in h['yields']:
  for rr in h['recoveries']:
   z=recipe_balance(rec['polymer_g'],rec['solvent_g'],y,rr,p['hold_minutes'],rec['cool_minutes'],h['cp_polymer_kJ_kgK'],h['cp_solvent_kJ_kgK'],h['feed_C'],p['heat_C'])
   key=str((rec['id'],y,rr))
   ck('polymer closure '+key,eq(1+z['not_product_polymer_kg_per_kg_product'],z['polymer_feed_kg_per_kg_product']))
   ck('solvent closure '+key,eq(z['solvent_recovered_kg_per_kg_product']+z['fresh_solvent_kg_per_kg_product'],z['solvent_charge_kg_per_kg_product']))
   ck('unknowns retained '+key,z['total_batch_time_h'] is None and z['final_residual_solvent_ppm'] is None)
   rows.append(dict(example=rec['id'],yield_fraction=y,recovery_fraction=rr,**z))
   for price in h['solvent_to_polymer_prices']:
    normalised_cost.append(dict(example=rec['id'],yield_fraction=y,recovery_fraction=rr,price_ratio=price,feed_material_cost_over_polymer_price=z['polymer_feed_kg_per_kg_product']+price*z['fresh_solvent_kg_per_kg_product']))
 s=rec['solvent_g']/rec['polymer_g']
 for price in h['solvent_to_polymer_prices']:
  rr=recovery_budget(s,price,h['makeup_solvent_cost_budget_fraction_of_polymer_feed'])
  ck('cost budget '+str((rec['id'],price)),eq(s*(1-rr)*price,.1))
  budgets.append(dict(example=rec['id'],price_ratio=price,min_recovery_for_assumed_cost_budget=rr))
 for angle in h['view_angles_deg']:
  z=solid_oblate(rec['C_um'],rec['C_um']/rec['B_um'],angle)
  ck('solid volume '+str((rec['id'],angle)),eq(z['volume_um3'],integrate_oblate_volume(z['equatorial_um'],z['thickness_um'])))
  ck('no real void '+str((rec['id'],angle)),z['true_internal_void_fraction']==0)
  if angle==0:ck('same faceon index '+rec['id'],eq(z['diameter_index'],rec['C_um']/rec['B_um']))
  shapes.append(dict(example_index_used=rec['id'],view_angle_deg=angle,**z))
for y,rr in [(0,.99),(.9,1.1),(.9,-.1)]:
 try:recipe_balance(36,1164,y,rr,60,60)
 except ValueError:checks.append('reject '+str((y,rr)))
 else:raise AssertionError('invalid accepted')
ck('sphere limit',eq(solid_oblate(100,1,60)['diameter_index'],1))
lo=next(x for x in rows if x['example']=='1' and x['yield_fraction']==1 and x['recovery_fraction']==.99)
hi=next(x for x in rows if x['example']=='5b' and x['yield_fraction']==1 and x['recovery_fraction']==.99)
summary=dict(mother_solvent_per_polymer_low=lo['solvent_charge_kg_per_kg_product'],mother_solvent_per_polymer_high=hi['solvent_charge_kg_per_kg_product'],
 solvent_charge_reduction_fraction=1-hi['solvent_charge_kg_per_kg_product']/lo['solvent_charge_kg_per_kg_product'],
 low_concentration_sensible_heat=lo['sensible_heat_only_kWh_per_kg_product'],high_concentration_sensible_heat=hi['sensible_heat_only_kWh_per_kg_product'],
 selected_shape=next(x for x in shapes if x['example_index_used']=='4b' and x['view_angle_deg']==0))
out=dict(cycle=133,physical_trials=0,success_probability=None,rows=rows,cost_budgets=budgets,normalised_feed_material_cost=normalised_cost,shape_counterexamples=shapes,summary=summary,
 dependency_hashes={q:hashlib.sha256((R/q).read_bytes()).hexdigest() for q in a['dependencies']})
val=dict(count=len(checks),passed=True,checks=checks,physical_trials=0,success_probability=None)
def enc(x):return json.dumps(x,ensure_ascii=False,indent=2)+'\n'
if '--check' in sys.argv:
 assert (D/'results.json').read_text()==enc(out);assert (D/'validation.json').read_text()==enc(val)
else:
 (D/'results.json').write_text(enc(out),encoding='utf-8',newline='\n')
 (D/'validation.json').write_text(enc(val),encoding='utf-8',newline='\n')
print(json.dumps(dict(checks=len(checks),rows=len(rows),cost_rows=len(normalised_cost),shapes=len(shapes),summary=summary,selected_budgets=[x for x in budgets if x['price_ratio']==1]),ensure_ascii=False))
