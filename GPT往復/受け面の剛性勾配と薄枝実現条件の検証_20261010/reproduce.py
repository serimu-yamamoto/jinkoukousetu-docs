#!/usr/bin/env python3
from pathlib import Path
import json,math,os,sys,hashlib,importlib.util,platform
D=Path(__file__).resolve().parent;R=D.parents[1]
P=Path(os.environ.get('FIRN_COMMON_LIB',str(R/'計算部品')))/'graded_contact.py'
s=importlib.util.spec_from_file_location('graded',P);g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
I=json.loads((D/'inputs.json').read_text());checks=[]
def check(name,ok):
    if not ok:raise AssertionError(name)
    checks.append(name)
def near(a,b,t=1e-8):return abs(a-b)<=t*max(1,abs(a),abs(b))
us=sorted(set([j/100 for j in range(101)]+[1e-8,1e-6,1e-4,1-1e-4,1-1e-6,1-1e-8]))
rows=[]
for gamma in I['gamma']:
 for a,edge in [(0.,1.)]+[(a,e) for a in I['ramp'] for e in I['edge']]:
    trace=[];end=g.solve(g.segments(0,gamma,a,edge));baseline=g.base.normal_contact(g.base.overlap_intervals(0,gamma))
    scale=end['delta']/baseline['delta']
    incoming=edge*(end['delta']+end['theta']*(1+gamma)/2)
    for u in us:
        parts=g.segments(u,gamma,a,edge);v=g.solve(parts);v['u']=u
        check(f'balance_{gamma}_{a}_{edge}_{u}',near(v['force'],1) and abs(v['moment'])<1e-8)
        check(f'energy_{gamma}_{a}_{edge}_{u}',near(v['energy'],.5*v['delta']))
        check(f'nonnegative_{gamma}_{a}_{edge}_{u}',v['B_force']>=-1e-10 and v['peak_line_load']>=0)
        if a==0:
            old=g.base.normal_contact(g.base.overlap_intervals(u,gamma))
            check(f'legacy_{gamma}_{u}',near(v['delta'],old['delta']) and near(v['theta'],old['theta']) and near(v['peak_line_load'],old['peak_line_load']))
        trace.append(v)
    center=g.solve(g.segments(.5,gamma,a,edge))
    check(f'center_formula_{gamma}_{a}_{edge}',near(center['delta'],1/(1-a*(1-edge))) and abs(center['theta'])<1e-8)
    scaled=g.solve(g.segments(.23,gamma,a,edge),scale=scale)
    unscaled=g.solve(g.segments(.23,gamma,a,edge))
    check(f'uniform_stiffness_scaling_{gamma}_{a}_{edge}',near(scaled['delta'],unscaled['delta']/scale) and near(scaled['peak_line_load'],unscaled['peak_line_load']))
    volume=1 if not a else 1-a+a*(3*(1-edge**(4/3))/(4*(1-edge)) if edge<1 else 1)
    sensitivity=[]
    for cap in [.01,.05,.1]:
        sensitivity.append(dict(capillary_force_parameter=cap,closure_over_clearance=None if edge==0 else cap/(scale*edge)))
    at_entry=g.solve(g.segments(1e-8,gamma,a,edge))
    # Pressure on the new patch tends to edge*(d+theta*rB); a new patch can have vanishing force but finite pressure.
    new_patch_peak=0.
    parts=g.segments(1e-8,gamma,a,edge);raw=g.integrals(parts,at_entry['theta']/at_entry['delta'])
    new_patch_peak=at_entry['delta']*max([r['peak'] for r in raw if r['label']=='B'] or [0.])
    check(f'entrance_limit_{gamma}_{a}_{edge}',abs(new_patch_peak-incoming)<2e-5*max(1,abs(incoming)))
    rows.append(dict(gamma=gamma,ramp_fraction=a,edge_stiffness=edge,
                     entrance_pressure_limit=incoming,peak_pressure_sampled=max(v['peak_line_load'] for v in trace),
                     raw_delta_min=min(v['delta'] for v in trace),raw_delta_max=max(v['delta'] for v in trace),
                     delta_span=max(v['delta'] for v in trace)-min(v['delta'] for v in trace),
                     common_stiffness_multiplier_for_same_endpoint_sinkage=scale,
                     normalized_delta_span=(max(v['delta'] for v in trace)-min(v['delta'] for v in trace))/scale,
                     max_theta_coefficient=max(abs(v['theta']) for v in trace),
                     independent_root_volume_proxy=volume*scale**(1/3),
                     minimum_flexural_root_thickness_ratio=(scale*edge)**(1/3),
                     bulk_compression_thickness_ratio_at_edge=None if edge==0 else 1/(scale*edge),
                     capillary_sensitivity=sensitivity,trace=trace))
# Independent midpoint quadrature of graded pressure, without using the analytic integrals.
quad=[]
for u in [0.,.037,.5]:
    parts=g.segments(u,.25,.3,.05);v=g.solve(parts)
    vals=[]
    for n in [200,800,3200]:
        F=M=U=0.
        for label,a,b,c0,c1 in parts:
            dx=(b-a)/n
            for j in range(n):
                x=a+(j+.5)*dx;k=c0+c1*x;d=max(0.,v['delta']+v['theta']*x);p=k*d
                F+=p*dx;M+=p*x*dx;U+=.5*k*d*d*dx
        vals.append(dict(n=n,force_error=abs(F-1),moment_error=abs(M),energy_error=abs(U-.5*v['delta'])))
    check(f'quadrature_bound_{u}',max(vals[-1][z] for z in ['force_error','moment_error','energy_error'])<1e-6)
    check(f'quadrature_convergence_{u}',max(vals[-1][z] for z in ['force_error','moment_error','energy_error'])<=max(1e-12,max(vals[0][z] for z in ['force_error','moment_error','energy_error'])/50))
    quad.append(dict(u=u,values=vals))
# Same-material elementary element scaling, not actual grade properties.
realization=[]
for kappa in [0.,.05,.2,1.]:
    realization.append(dict(relative_stiffness=kappa,bending_thickness_ratio=kappa**(1/3),compression_thickness_ratio=None if not kappa else 1/kappa,
                            restoring_material_ratio='E(t,T) not measured at 50 C'))
out=dict(physical_trials=0,success_probability=None,rows=rows,independent_quadrature=quad,realization=realization)
val=dict(passed=True,count=len(checks),checks=checks,python=platform.python_version(),
         graded_library_sha256=hashlib.sha256(P.read_bytes()).hexdigest(),
         legacy_library_sha256=hashlib.sha256(P.with_name('handover_contacts.py').read_bytes()).hexdigest(),
         driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
for name,obj in [('results.json',out),('validation.json',val)]:
    data=(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    if '--check' in sys.argv:assert (D/name).read_bytes()==data,name
    else:(D/name).write_bytes(data)
chosen=[r for r in rows if r['gamma']==.25 and (r['ramp_fraction']==.15 or r['ramp_fraction']==0)]
print(json.dumps(dict(cases=len(rows),checks=len(checks),chosen=[{k:v for k,v in r.items() if k not in ['trace','capillary_sensitivity']} for r in chosen]),ensure_ascii=False))
