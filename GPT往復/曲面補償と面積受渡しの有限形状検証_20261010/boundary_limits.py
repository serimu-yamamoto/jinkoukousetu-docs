#!/usr/bin/env python3
from pathlib import Path
import importlib.util,json,sys
D=Path(__file__).resolve().parent;R=D.parents[1]
spec=importlib.util.spec_from_file_location('contact',R/'計算部品/handover_contacts.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
rows=[]
for gamma in [.1,.25,.4,.75]:
    at0=h.normal_contact(h.overlap_intervals(0,gamma))
    incoming=at0['delta']+at0['theta']*(1+gamma)/2
    near=[]
    for eps in [1e-2,1e-4,1e-6,1e-8]:
        v=h.normal_contact(h.overlap_intervals(eps,gamma))
        b=next(r for r in v['reactions'] if r['label']=='B')
        near.append(dict(u=eps,incoming_peak=b['peak_line_load'],incoming_total_force=b['force'],
                         Q_right_derivative_estimate=-.5*(v['delta']-at0['delta'])/eps))
    assert abs(near[-1]['incoming_peak']-incoming)<1e-5*max(1,incoming)
    assert near[-1]['incoming_total_force']<1e-5
    exact_Q=None
    if gamma<=1/3:
        exact_Q=6*gamma*gamma*(1+3*gamma+3*gamma*gamma)
        assert abs(near[-1]['Q_right_derivative_estimate']-exact_Q)<1e-5
    rows.append(dict(gamma=gamma,endpoint_delta=at0['delta'],incoming_pressure_limit=incoming,
                     exact_endpoint_Q_per_delta0_over_L=exact_Q,approach=near))
out=dict(passed=True,scope='Winkler surrogate: finite entrance pressure with vanishing patch force; not real edge stress',rows=rows)
raw=(json.dumps(out,indent=2,allow_nan=False)+'\n').encode()
if '--check' in sys.argv:assert (D/'boundary_limits.json').read_bytes()==raw
else:(D/'boundary_limits.json').write_bytes(raw)
print(json.dumps({'boundary_limits':[{k:v for k,v in x.items() if k!='approach'} for x in rows]}))
