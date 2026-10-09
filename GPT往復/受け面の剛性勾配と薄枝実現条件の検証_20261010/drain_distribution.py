#!/usr/bin/env python3
from pathlib import Path
import importlib.util,json,math,sys,os
D=Path(__file__).resolve().parent;R=D.parents[1]
P=Path(os.environ.get('FIRN_COMMON_LIB',str(R/'計算部品')))/'handover_contacts.py'
s=importlib.util.spec_from_file_location('base',P);h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
def intervals(u,gamma,n):
    W=1+gamma;period=W/n;xc=u+W/2;end=1+W;out=[]
    for j in range(math.ceil(end/period)+1):
        left=max(u,j*period,0);right=min(u+W,j*period+1/n,end)
        if right>left:out.append((str(j),left-xc,right-xc))
    return out
rows=[];checks=0
for gamma in [.1,.25]:
 for n in [1,2,4,8]:
    period=(1+gamma)/n
    points=set(j/500 for j in range(501))
    for j in range(math.ceil(1/period)+1):
        for event in [j*period,j*period+1/n]:
            for eps in [-1e-8,0.,1e-8]:
                if 0<=event+eps<=1:points.add(event+eps)
    trace=[]
    for u in sorted(points):
        ints=intervals(u,gamma,n)
        assert abs(sum(b-a for _,a,b in ints)-1)<1e-10
        v=h.normal_contact(ints);assert v['status']=='equilibrium'
        assert abs(v['force']-1)<1e-8 and abs(v['moment'])<1e-8
        assert abs(v['energy']-.5*v['delta'])<1e-8
        if n==1:
            ref=h.normal_contact(h.overlap_intervals(u,gamma))
            assert abs(v['delta']-ref['delta'])<1e-8 and abs(v['peak_line_load']-ref['peak_line_load'])<1e-8
        checks+=1;trace.append(v|{'u':u})
    # Whole finite lower support span differs from the under-window invariant.
    end=2+gamma;whole_support=0.
    for j in range(math.ceil(end/period)+1):
        whole_support+=max(0,min(end,j*period+1/n)-j*period)
    rows.append(dict(gamma=gamma,slot_count_per_window=n,slot_width_over_L=gamma/n,
                     constant_contact_area_per_width=1.,constant_open_area_per_width_in_window=gamma,
                     total_lower_span=2+gamma,whole_lower_open_area_per_width=end-whole_support,
                     delta_span=max(v['delta'] for v in trace)-min(v['delta'] for v in trace),
                     max_delta=max(v['delta'] for v in trace),
                     peak_pressure_sampled=max(v['peak_line_load'] for v in trace),
                     max_theta_coefficient=max(abs(v['theta']) for v in trace),
                     ideal_slit_conductance_ratio=1/(n*n),
                     ideal_wetting_capillary_pressure_ratio=n,
                     traces=trace))
flare=[]
for gamma in [.1,.25]:
 for n in [1,2,4,8]:
  period=(1+gamma)/n;ligament=period-gamma;valid=ligament>0
  for fraction in [0.,.05,.1,1/7,.25,1.]:
   ratio=1/n+(n*n-1/n)*fraction
   if fraction==1:assert abs(ratio-n*n)<1e-12
   flare.append(dict(gamma=gamma,n=n,throat_depth_fraction=fraction,period_over_L=period,
                     throat_width_over_L=gamma/n,exit_width_over_L=gamma,
                     ligament_width_over_L=ligament,ligament_to_surface_support_width=ligament*n,
                     separate_exits_feasible=valid,ideal_resistance_ratio=ratio if valid else None,
                     ideal_conductance_ratio=1/ratio if valid else None,
                     maximum_throat_fraction_for_unit_resistance=None if n==1 else 1/(n*n+n+1)))
out=dict(physical_trials=0,success_probability=None,cases=len(rows),equilibrium_states_checked=checks,flared_flow=flare,
         hydrology_assumptions='independent fully developed narrow planar slits, same viscosity, flow depth, transverse length and pressure; meniscus ratio assumes same surface tension/contact angle and comparable slit curvature',
         rows=rows)
raw=(json.dumps(out,indent=2,allow_nan=False)+'\n').encode()
if '--check' in sys.argv:assert (D/'drain_distribution.json').read_bytes()==raw
else:(D/'drain_distribution.json').write_bytes(raw)
print(json.dumps({'cases':len(rows),'states':checks,'summary':[{k:v for k,v in r.items() if k!='traces'} for r in rows if r['gamma']==.25]}))
