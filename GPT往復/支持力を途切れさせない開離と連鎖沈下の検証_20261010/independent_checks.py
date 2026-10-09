#!/usr/bin/env python3
"""Independent stable-prefix solver and boundary-condition checks."""
from pathlib import Path
import importlib.util,json,math,sys
D=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('cycle101',D/'reproduce.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def prefix(k,d,beta,F):
    order=sorted(range(len(k)),key=lambda i:d[i])
    # Enumerate all threshold-prefix states instead of following failure waves.
    for count in range(len(k)+1):
        chosen=set(order[:count]);K=sum(ki*(beta if i in chosen else 1.) for i,ki in enumerate(k))
        if not K:continue
        x=F/K
        implied={i for i,di in enumerate(d) if di<=x+1e-12}
        if implied==chosen:return dict(status='equilibrium',x=x,changed=count)
    return dict(status='no_finite_equilibrium',x=None)
checks=[]
def test(name,ok):
    if not ok:raise AssertionError(name)
    checks.append(name)
for n in m.I['n']:
 for name in m.I['families']:
  k,d=m.family(n,name)
  for beta in m.I['betas']:
   for factor in [.4,.6,.8,1.,1.2,1.8,3.]:
    a=m.target_drop(k,d,beta,n*factor);b=prefix(k,d,beta,n*factor)
    test(f'prefix_{n}_{name}_{beta}_{factor}',a['status']==b['status'] and (a['x'] is None or m.near(a['x'],b['x'])))
weighted=[]
# a=.5, b=1.5, mean stiffness=1. Critical beta = 1-1/max_x[S(x)+x*k(x)*p(x)].
for name,critical,point in [('D',.6,1.5),('KDpositive',9/13,1.5),('KDnegative',19/43,4/3)]:
 def g(x):
    if name=='D':return (x-.5)+x
    if name=='KDpositive':return (x*x-.25)/2+x*x
    return 2*(x-.5)-(x*x-.25)/2+x*(2-x)
 maximum=g(point)
 test('weighted_critical_'+name,m.near(1-1/maximum,critical))
 test('weighted_max_'+name,all(g(.5+j/1000)<=maximum+1e-12 for j in range(1001)))
 weighted.append(dict(family=name,critical_beta=critical,maximum_weighted_tangent_term=maximum,location=point,scope='continuum fixed initial stiffness; not material threshold'))
machine=[]
for beta in [.25,.6,.75]:
 for relative_machine_stiffness in [0,.1,1,10,1e6]:
  r=relative_machine_stiffness
  ratio=(r+1)/(r+beta)
  if r>0:
   y=(r+1)/r
   test(f'machine_force_balance_{beta}_{r}',m.near(r*(y-ratio),beta*ratio,1e-8))
  else:test(f'force_limit_{beta}',m.near(ratio,1/beta))
  machine.append(dict(beta=beta,machine_stiffness_over_initial_bundle=r,x_after_over_before=ratio,jump_ratio=ratio-1))
# Cost cap as a decision equation, NOT a quote: 1 t, 3 years, un-discounted.
cost=[]
for extra_yen_per_kg in [50,100,300]:
 cost.append(dict(reference_mass_kg=1000,extra_yen_per_kg=extra_yen_per_kg,extra_capital_yen=1000*extra_yen_per_kg,years=3,minimum_annual_saving_yen=1000*extra_yen_per_kg/3,excluded=['tooling','yield loss','maintenance','disposal','financing','inflation','tax differences']))
out=dict(passed=True,checks=len(checks),check_names=checks,weighted_thresholds=weighted,machine_sensitivity=machine,cost_sensitivity=cost,physical_trials=0,success_probability=None)
raw=(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
if '--check' in sys.argv:assert (D/'independent_checks.json').read_bytes()==raw
else:(D/'independent_checks.json').write_bytes(raw)
print(json.dumps(dict(checks=len(checks),weighted=weighted,machine_beta025=[r for r in machine if r['beta']==.25])))
