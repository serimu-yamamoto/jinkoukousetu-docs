from pathlib import Path
import sys,json,hashlib,itertools,math
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from material_beam_screen import same_bending,local_replacement,annual_raw_ratio,mass_budget
a=json.loads((D/'inputs.json').read_text());checks=[]
def ck(n,b):
 if not b:raise AssertionError(n)
 checks.append(n)
def close(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10)
rows=[]
for e,r,p in itertools.product(*[a['ratios'][k] for k in ['effective_bending_modulus','density','price_per_kg']]):
 x=same_bending(e,r,p);t=x['thickness_ratio'];key=str((e,r,p))
 # Independent Euler-Bernoulli rectangular cantilever with arbitrary SI reference values.
 E0=1e9;w=.0004;h=.0001;L=.001;F=.001
 I0=w*h**3/12;I1=w*(h*t)**3/12
 d0=F*L**3/(3*E0*I0);d1=F*L**3/(3*E0*e*I1)
 s0=F*L*h/(2*I0);s1=F*L*h*t/(2*I1)
 ck('equal displacement '+key,close(d0,d1))
 ck('stress ratio '+key,close(s1/s0,x['stress_ratio']))
 ck('strain ratio '+key,close((s1/(E0*e))/(s0/E0),x['strain_ratio']))
 ck('mass volume '+key,close(900*r*w*h*t*L/(900*w*h*L),x['mass_ratio']))
 ck('annual parity '+key,close(annual_raw_ratio(x['raw_cost_ratio'],x['minimum_life_ratio_for_raw_replacement_parity']),1))
 ck('price parity '+key,close(same_bending(e,r,x['price_ratio_for_initial_raw_parity'])['raw_cost_ratio'],1))
 rows.append(dict(e_ratio=e,density_ratio=r,price_ratio=p,**x))
identity=same_bending(1,1,1)
ck('identity',all(close(v,1) for v in identity.values()))
for f in [0,.1,1]:
 x=local_replacement(f,1.4,2)
 ck('two volumes conserve mass '+str(f),close(x['mass_ratio'],(1-f)*900/900+f*1260/900))
 ck('two component raw cost '+str(f),close(x['raw_cost_ratio'],((1-f)*900*500+f*1260*1000)/(900*500)))
for fun,args in [(same_bending,(0,1,1)),(same_bending,(1,-1,1)),(local_replacement,(-.1,1,1)),(annual_raw_ratio,(1,0))]:
 try:fun(*args)
 except ValueError:ck('reject invalid '+str(args),True)
 else:raise AssertionError('invalid accepted')
b=mass_budget(**a['reference']);q=a['illustration']
whole=same_bending(q['e_ratio'],q['rho_ratio'],q['price_ratio'])
local=local_replacement(q['local_volume_fraction'],q['rho_ratio'],q['price_ratio'])
for name,x in [('whole',whole),('local',local)]:
 x['scenario_mass_kg']=b['reference_mass_kg']*x['mass_ratio']
 x['scenario_raw_yen']=b['reference_raw_yen']*x['raw_cost_ratio']
 x['scenario_raw_extra_yen']=x['scenario_raw_yen']-b['reference_raw_yen']
 x['annual_raw_ratio_if_life_doubles']=annual_raw_ratio(x['raw_cost_ratio'],2)
ck('reference mass',close(b['reference_mass_kg'],135000))
ck('reference raw cost',close(b['reference_raw_yen'],67500000))
ck('local illustration ratio',close(local['raw_cost_ratio'],1.18))
ck('equal stiffness can be heavier',whole['thickness_ratio']<1 and whole['mass_ratio']>1)
deps=['GPT往復/試験材グレードと交換試片の調達仕様_20261009/sources.json']
data=dict(cycle=120,physical_trials=0,success_probability=None,dependency_hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in deps},
 reference=b,illustration=dict(whole_equal_bending=whole,local_fixed_geometry=local),conditions=rows,
 scope='Dimensionless material selection and raw replacement economics, not particle-bed or 50C validation',
 limits=['no compound data','beam fixed width length small deflection only','local replacement may change stiffness and interface durability',
 'no packing equivalence','no time-dependent modulus measurement','raw price is hypothetical','processing recovery water drainage taxes equipment excluded'])
v=dict(count=len(checks),checks=checks,passed=True,physical_validation=False)
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for n,x in [('results.json',data),('validation.json',v)]:
 if '--check' in sys.argv:assert (D/n).read_bytes()==enc(x)
 else:(D/n).write_bytes(enc(x))
print(json.dumps(dict(checks=len(checks),conditions=len(rows),illustration=data['illustration']),ensure_ascii=False))
