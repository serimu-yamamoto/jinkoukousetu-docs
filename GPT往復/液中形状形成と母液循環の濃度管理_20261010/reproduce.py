from pathlib import Path
import json,sys,math,hashlib
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from precipitation_bath_balance import feed_inventory,growing_bath,product_at_bath_fraction,steady_balance
a=json.loads((D/'inputs.json').read_text());s=a['source'];h=a['assumed'];checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def eq(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10)
f=feed_inventory(1,s['polymer_feed_wt_fraction'])
ck('feed mass conservation',eq(f['solution_kg'],f['solvent_kg']+1))
ck('2percent feed interpretation',eq(f['solvent_kg'],49))
uncontrolled=[]
for c in h['diagnostic_target_fractions']:
 m=product_at_bath_fraction(h['initial_bath_kg'],c,s['polymer_feed_wt_fraction']);v=feed_inventory(m,s['polymer_feed_wt_fraction']);b=growing_bath(h['initial_bath_kg'],v['solvent_kg'])
 ck('target inverse '+str(c),eq(b['solvent_mass_fraction'],c))
 # Independently accumulate discrete material additions without a concentration recursion.
 M=h['initial_bath_kg'];S=0
 for i in range(100):S+=v['solvent_kg']/100;M+=v['solvent_kg']/100
 ck('discrete mass accumulation '+str(c),eq(S/M,c))
 uncontrolled.append(dict(target_fraction=c,product_kg=m,**b))
rows=[]
for c in h['diagnostic_target_fractions']:
 for eta in h['recovered_incoming_load_fractions']:
  z=steady_balance(f['solvent_kg'],eta,c);key=str((c,eta))
  ck('solvent leaves via recovery and purge '+key,eq(z['recovered_solvent_kg']+z['purge_solution_kg']*c,f['solvent_kg']))
  ck('fixed bath total mass balance '+key,eq(f['solvent_kg']+z['fresh_carrier_makeup_kg'],z['recovered_solvent_kg']+z['purge_solution_kg']))
  rows.append(dict(target_fraction=c,recovery_fraction=eta,**z))
full=feed_inventory(h['full_material_kg'],s['polymer_feed_wt_fraction'])
local=feed_inventory(h['full_material_kg']*h['localized_material_mass_fraction'],s['polymer_feed_wt_fraction'])
ck('localized scaling',eq(local['solvent_kg']/full['solvent_kg'],h['localized_material_mass_fraction']))
ck('fresh bath zero',growing_bath(1000,0)['solvent_mass_fraction']==0)
ck('ideal complete recovery zero purge',steady_balance(49,1,.05)['purge_solution_kg']==0)
for fun,args in [(feed_inventory,(1,0)),(growing_bath,(1000,-1)),(steady_balance,(49,1.1,.05)),(product_at_bath_fraction,(1000,1,.02))]:
 try:fun(*args)
 except ValueError:ck('invalid '+str(args),True)
 else:raise AssertionError('invalid input accepted')
for r in s['flow_table']:ck('published flow ratio '+str(r['ratio']),eq(r['Qc_uL_min']/r['Qd_uL_min'],r['ratio']))
ck('solvent concentration can cross reportedPe100',s['continuous_solvent_table_at_ratio10'][2]['Pe']>100 and s['continuous_solvent_table_at_ratio10'][3]['Pe']<100)
deps=['GPT往復/枝状粒形成検証_熱選別と回収収支_20261008/sources.md','GPT往復/温暖形成と開放環粒の製造監査_20261010/sources.json']
data=dict(cycle=122,physical_trials=0,success_probability=None,dependency_hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in deps},
 unit_feed=f,uncontrolled_bath=uncontrolled,steady_balances_per_kg_polymer=rows,
 full_scenario=full,local_scenario=local,
 recovery99_at_target5=dict(full=steady_balance(full['solvent_kg'],.99,.05),local=steady_balance(local['solvent_kg'],.99,.05)),
 scope='Ideal manufacturing mass balance; not morphology prediction at30C or50C ski performance',limits=a['limits'])
v=dict(count=len(checks),passed=True,checks=checks,physical_validation=False)
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for n,x in [('results.json',data),('validation.json',v)]:
 if '--check' in sys.argv:assert (D/n).read_bytes()==enc(x)
 else:(D/n).write_bytes(enc(x))
print(json.dumps(dict(checks=len(checks),unit=f,uncontrolled=uncontrolled,at5=[r for r in rows if r['target_fraction']==.05],scenarios=dict(full=full,local=local)),ensure_ascii=False))
