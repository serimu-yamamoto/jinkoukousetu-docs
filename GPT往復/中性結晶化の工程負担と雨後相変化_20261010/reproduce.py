from pathlib import Path
import sys,json,hashlib,math
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from enzyme_crystal_process import inventory,reactor_inventory
i=json.loads((D/'inputs.json').read_text());p=i['reported'];a=i['assumed'];checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def close(x,y):return math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-9)
dep='GPT往復/生体分子結晶の接触相と製造物量_20261010/results.json'
prior=json.loads((R/dep).read_text());mass=prior['reference_platelet']['net_crystal_kg']
rows=[]
for label,m in [('prior_mass_budget_only',mass),('legacy_mass_budget_only',1350)]:
 for yc in a['isolation_yields']:
  for yp in a['placement_yields']:
   r=inventory(m,p['guanosine_mM'],p['phosphate_mM'],a['guanine_MW_g_mol'],a['guanosine_MW_g_mol'],yc,yp,p['enzyme_U']/p['stirred_volume_mL'])
   r['basis']=label
   r['hypothetical_stirred_reactor_working_m3']=reactor_inventory(r['batch_equivalent_liquid_m3'],24,a['production_days'],a['uptime_fraction'])
   r['hypothetical_static_reactor_working_m3']=reactor_inventory(r['batch_equivalent_liquid_m3'],48,a['production_days'],a['uptime_fraction'])
   ck('guanine mass closure '+str((m,yc,yp)),close(r['guanine_generated_kg'],m+r['isolation_loss_kg']+r['placement_loss_kg']))
   ck('phosphorus atom balance '+str((m,yc,yp)),close(r['phosphate_input_mol'],r['inorganic_phosphate_remaining_mol']+r['ribose1phosphate_generated_mol']))
   ck('precursor product mole relation '+str((m,yc,yp)),close(r['guanosine_input_kg']/a['guanosine_MW_g_mol'],r['guanine_generated_kg']/a['guanine_MW_g_mol']))
   ck('unit charge volume conversion '+str((m,yc,yp)),close(r['enzyme_charge_units_if_lab_loading_preserved'],r['batch_equivalent_liquid_m3']*1000*50))
   ck('time inventory ratio '+str((m,yc,yp)),close(r['hypothetical_static_reactor_working_m3'],2*r['hypothetical_stirred_reactor_working_m3']))
   rows.append(r)
ref=rows[0]
ck('inherited budget only',close(mass,20.20788))
ck('phosphate mol ratio',close(ref['phosphate_input_mol']/ref['phosphate_consumed_mol'],31.25))
ck('two distinct losses multiply feed',close(rows[3]['batch_equivalent_liquid_m3'],4*ref['batch_equivalent_liquid_m3']))
ck('mass concentration',close(1.6*151.13/1000,.241808))
for args in [(1,1.6,50,151.13,283.24,0,1,.05),(1,1.6,1,151.13,283.24,1,1,.05)]:
 try:inventory(*args)
 except ValueError:ck('invalid boundary '+str(args),True)
 else:raise AssertionError('Invalid accepted')
cost=inventory(1,1.6,50,151.13,283.24,1,1,.05)
data=dict(cycle=115,physical_trials=0,success_probability=None,dependency_hashes={dep:hashlib.sha256((R/dep).read_bytes()).hexdigest()},reference=ref,scenarios=rows,cost_coefficients_per_retained_kg_ideal=cost,
 schedule_assumptions=dict(production_days=a['production_days'],uptime_fraction=a['uptime_fraction'],stirred_hours=24,static_hours=48),
 exclusions=['Morphology of2023 platelets not assigned to2025 enzyme crystals','No measured enzyme reuse or yield','U loading not reaction-rate prediction','No current price quote','No new water or discharge volume inferred','No ski performance or safety outcome'])
validation=dict(count=len(checks),checks=checks,passed=True,physical_validation=False,scope='Stoichiometric and conditional factory inventory arithmetic only')
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for name,obj in [('results.json',data),('validation.json',validation)]:
 if '--check' in sys.argv:assert (D/name).read_bytes()==enc(obj)
 else:(D/name).write_bytes(enc(obj))
print(json.dumps(dict(checks=len(checks),reference=ref,cost_coefficients=cost),ensure_ascii=False))
