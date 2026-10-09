from pathlib import Path
import sys,json,hashlib,math
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from response_identifiability import *
checks=[]
def check(n,b):
 if not b:raise AssertionError(n)
 checks.append(n)
def close(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10)
inputs=json.loads((D/'measured_inputs.json').read_text())
deps=['計算部品/viscoelastic_glide.py','GPT往復/結晶接触材の粒度基準と保持量監査_20261010/results.json']
hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in deps}
old=json.loads((R/deps[1]).read_text());core=old['reference_coating']['core_kg']
check('prior core mass basis',core==133650)
rows=inputs['rows']
a=next(r for r in rows if r['temperature_C']==30);b=next(r for r in rows if r['temperature_C']==50)
ep=a['E_storage_MPa'];eh=b['E_storage_MPa'];lp=a['E_loss_MPa'];lh=b['E_loss_MPa']
comp=geometry_compensations(ep,eh,lp,lh)
check('thickening preserves storage stiffness',close(eh*comp['circular_radius_ratio']**4,ep))
check('shorter span preserves storage stiffness',close(eh/comp['active_span_length_ratio']**3,ep))
check('parallel factor preserves storage stiffness',close(eh*comp['effective_parallel_member_ratio'],ep))
check('radius mass square',close(comp['circular_active_material_ratio'],comp['circular_radius_ratio']**2))
check('matched stiffness loss increase',close((ep/eh)*lh/lp,comp['matched_storage_loss_ratio']))
bounds=interval_ratio(eh,b['reported_spread_storage_MPa'],ep,a['reported_spread_storage_MPa'])
check('reported spread corner lower',close(bounds['low'],654/1144))
check('reported spread corner upper',close(bounds['high'],842/1008))
families=[]
freqs=[1,10,100,2000/3,1000,5000,40000]
for x in [.1,1,5]:
 fam=sls_family(eh,lh,1,x);spectra=[]
 for f in freqs:
  e=response(f,fam);spectra.append(dict(frequency_Hz=f,E_storage_MPa=e.real,E_loss_MPa=e.imag,tan_delta=e.imag/e.real))
  check('nonnegative loss x='+str(x)+' f='+str(f),e.real>0 and e.imag>=0)
 anchored=response(1,fam)
 check('one datum fit storage x='+str(x),close(anchored.real,eh))
 check('one datum fit loss x='+str(x),close(anchored.imag,lh))
 # Explicit independent formula checks shared112 implementation with identified parameters.
 omega=2*math.pi*5000
 maxwell=1/(1/fam['deltaE_MPa']+1/(1j*omega*fam['deltaE_MPa']*fam['tau_s']))
 ec=complex(fam['E0_MPa'],0)+maxwell
 check('independent series impedance x='+str(x),abs(ec-response(5000,fam))<1e-9)
 check('positive equilibrium modulus x='+str(x),fam['E0_MPa']>0)
 families.append(dict(parameters=fam,spectrum=spectra))
losses=[response(5000,f['parameters']).imag for f in families]
ratio=max(losses)/min(losses)
check('same one Hz datum does not identify high frequency',ratio>90)
check('all high frequency losses distinct',len(set(round(v,8) for v in losses))==3)
for args in [(748,93,1,9),(748,93,0,1),(748,0,1,1)]:
 try:sls_family(*args)
 except ValueError:check('invalid inverse case '+str(args),True)
 else:raise AssertionError('invalid family accepted')
cost=[]
for frac in [.1,.3,1]:
 for price in [500,2000]:
  row=partial_mass_cost(core,frac,comp['circular_active_material_ratio'],price);cost.append(row)
  check('mass cost conservation '+str((frac,price)),close(row['added_material_only_jpy'],row['added_kg']*price))
check('zero active mass no added mass',partial_mass_cost(core,0,comp['circular_active_material_ratio'],500)['added_kg']==0)
data=dict(cycle=113,physical_trials=0,success_probability=None,dependency_hashes=hashes,
 measured_source=inputs['source_url'],measurement_temperature_comparison_C=[30,50],measurement_frequency_Hz=1,
 geometric_comparison=comp,storage_ratio_reported_spread_corners=bounds,
 inverse_families=families,high_frequency_5000Hz_loss_ratio_between_examples=ratio,partial_mass_cost=cost,
 caution='Three positive SLS models fitting a single observed complex datum are nonunique examples, NOT three validated real materials or a high-frequency confidence band.')
validation=dict(count=len(checks),checks=checks,passed=True,physical_validation=False,
 scope='Transcription inputs, beam scaling, inverse-model matching, complex impedance and mass arithmetic; not ski performance verification.')
def encode(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for p,x in [('results.json',data),('validation.json',validation)]:
 if '--check' in sys.argv:assert (D/p).read_bytes()==encode(x)
 else:(D/p).write_bytes(encode(x))
print(json.dumps(dict(checks=len(checks),comparison=comp,reported_spread_corners=bounds,
 families=[dict(parameters=f['parameters'],at5000=next(s for s in f['spectrum'] if s['frequency_Hz']==5000)) for f in families],
 high_frequency_loss_ratio=ratio,cost=cost,reproduced='--check' in sys.argv),ensure_ascii=False))
