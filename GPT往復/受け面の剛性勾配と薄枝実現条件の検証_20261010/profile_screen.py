#!/usr/bin/env python3
from pathlib import Path
import json,os,importlib.util,sys
D=Path(__file__).resolve().parent;R=D.parents[1]
P=Path(os.environ.get('FIRN_COMMON_LIB',str(R/'計算部品')))/'graded_contact.py'
s=importlib.util.spec_from_file_location('graded',P);g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
us=sorted(set([j/50 for j in range(51)]+[1e-8,1e-6,1e-4,1-1e-4,1-1e-6,1-1e-8]))
def profile(ai,ao,ei,eo):return [(0.,ei),(ai,1.),(1-ao,1.),(1.,eo)]
def volume(knots):
    out=0.
    for (s0,k0),(s1,k1) in zip(knots,knots[1:]):
        mean=k0**(1/3) if k0==k1 else 3*(k1**(4/3)-k0**(4/3))/(4*(k1-k0))
        out+=(s1-s0)*mean
    return out
def evaluate(gamma,ai,ao,ei,eo,points):
    knots=profile(ai,ao,ei,eo);trace=[g.solve(g.profile_segments(u,gamma,knots))|{'u':u} for u in points]
    base=1+3*gamma*gamma;scale=trace[0]['delta']/base
    span=(max(x['delta'] for x in trace)-min(x['delta'] for x in trace))/scale
    peak=max(x['peak_line_load'] for x in trace);limit=ei*(trace[0]['delta']+trace[0]['theta']*(1+gamma)/2)
    return dict(gamma=gamma,inner_ramp=ai,outer_ramp=ao,inner_edge=ei,outer_edge=eo,
                peak_pressure_sampled=peak,entrance_pressure_limit=limit,
                normalized_delta_span=span,stiffness_scale=scale,root_volume_proxy=volume(knots)*scale**(1/3),
                peak_ratio_to_uniform=peak/(1+3*gamma+6*gamma*gamma),span_ratio_to_uniform=span/(3*gamma*gamma),
                force_residual=max(abs(x['force']-1) for x in trace),
                moment_residual=max(abs(x['moment']) for x in trace),
                trace=trace)
rows=[]
for gamma in [.1,.25]:
 for ai in [.15,.3,.45]:
  for ao in [.15,.3]:
   for ei in [.05,.2]:
    for eo in [.05,.2,1.]:
     v=evaluate(gamma,ai,ao,ei,eo,us)
     assert v['force_residual']<1e-8 and v['moment_residual']<1e-8
     rows.append(v)
# Multi-objective shortlist; no success probability or claims beyond the sampled surrogate.
selected=[]
for gamma in [.1,.25]:
    candidates=[v for v in rows if v['gamma']==gamma]
    best=min(candidates,key=lambda v:max(v['peak_ratio_to_uniform'],v['span_ratio_to_uniform']))
    refined=evaluate(gamma,best['inner_ramp'],best['outer_ramp'],best['inner_edge'],best['outer_edge'],
                     sorted(set([j/1000 for j in range(1001)]+[1e-8,1e-6,1e-4,1-1e-4,1-1e-6,1-1e-8])))
    selected.append(refined)
# Direct consistency against the inner-only function at outer stiffness 1.
for u in [0.,.037,.5,.963,1.]:
    one=g.solve(g.segments(u,.25,.15,.05));two=g.solve(g.profile_segments(u,.25,profile(.15,.15,.05,1.)))
    assert abs(one['delta']-two['delta'])<1e-8 and abs(one['peak_line_load']-two['peak_line_load'])<1e-8
out=dict(physical_trials=0,success_probability=None,design_family='two-ended grading of local contact support',
         coarse_cases=len(rows),coarse_u_count=len(us),rows=rows,selected_refined=selected,
         screening_rule='minimize larger of pressure ratio and normalized displacement-span ratio at each fixed gap',
         constraint='same normal-load endpoint sinkage via common stiffness scaling; no material equivalence assumed')
raw=(json.dumps(out,indent=2,allow_nan=False)+'\n').encode()
if '--check' in sys.argv:assert (D/'profile_screen.json').read_bytes()==raw
else:(D/'profile_screen.json').write_bytes(raw)
print(json.dumps({'coarse_cases':len(rows),'selected':[{k:v for k,v in x.items() if k!='trace'} for x in selected]}))
