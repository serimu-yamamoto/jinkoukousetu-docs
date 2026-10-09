#!/usr/bin/env python3
from pathlib import Path
import json,math,sys,os,hashlib,importlib.util,platform
D=Path(__file__).resolve().parent;R=D.parents[1]
source=Path(os.environ.get('FIRN_COMMON_LIB',str(R/'計算部品')))/'handover_contacts.py'
spec=importlib.util.spec_from_file_location('handover',source);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
I=json.loads((D/'inputs.json').read_text())
checks=[]
def check(name,ok):
    if not ok:raise AssertionError(name)
    checks.append(name)
def near(a,b,tol=1e-9):return abs(a-b)<=tol*max(1.,abs(a),abs(b))
cams=[]
for c in [0.,1.]:
 for eta in I['eta']:
    trace=[h.cam_state(j/200,eta,c) for j in range(201)]
    for row in trace:check(f'cam_force_{c}_{eta}_{row["w"]}',near(row['total_normal'],eta))
    for w in [.17,.37,.63,.83]:
        eps=1e-6;a=h.cam_state(w-eps,eta,c);b=h.cam_state(w+eps,eta,c);z=h.cam_state(w,eta,c)
        check(f'cam_virtual_work_{c}_{eta}_{w}',near((b['potential']-a['potential'])/(2*eps),z['Q'],1e-8))
    if eta==1:
        check(f'cam_height_{c}',near(max(r['y'] for r in trace)-min(r['y'] for r in trace),c/4))
        check(f'cam_resistance_{c}',near(max(abs(r['Q']) for r in trace),1-c))
    cams.append(dict(c=c,eta=eta,height_span=max(r['y'] for r in trace)-min(r['y'] for r in trace),
                     peak_Q_over_F_per_delta0_over_L=max(abs(r['Q']) for r in trace)/eta,
                     residual_A_fraction_at_exit=trace[-1]['A']/eta,trace=trace))
areas=[];worst_force=0.;worst_moment=0.;worst_energy=0.
for gamma in I['gamma']:
 for free in [False,True]:
    trace=[]
    for j in range(201):
        u=j/200;intervals=h.overlap_intervals(u,gamma)
        check(f'area_sum_{gamma}_{free}_{u}',near(sum(b-a for _,a,b in intervals),1))
        row=h.normal_contact(intervals,rotation_free=free);assert row['status']=='equilibrium'
        row['u']=u
        worst_force=max(worst_force,abs(row['force']-1))
        if free:
            worst_moment=max(worst_moment,abs(row['moment']))
            check(f'zero_moment_{gamma}_{u}',abs(row['moment'])<1e-9)
        else:check(f'locked_moment_{gamma}_{u}',near(row['moment'],gamma*(u-.5)))
        worst_energy=max(worst_energy,abs(row['energy']-.5*row['delta']))
        check(f'positive_reactions_{gamma}_{free}_{u}',all(r['force']>=-1e-12 for r in row['reactions']))
        check(f'energy_{gamma}_{free}_{u}',near(row['energy'],.5*row['delta']))
        trace.append(row)
    a=trace[0]
    if free:
        expected=1+3*gamma*gamma if gamma<=1/3 else 8/(9*(1-gamma))
        peak=1+3*gamma if gamma<=1/3 else 4/(3*(1-gamma))
        length=1 if gamma<=1/3 else 1.5*(1-gamma)
        check(f'endpoint_delta_{gamma}',near(a['delta'],expected,1e-8))
        check(f'endpoint_peak_{gamma}',near(a['peak_line_load'],peak,1e-8))
        check(f'endpoint_active_length_{gamma}',near(a['active_length'],length,1e-8))
        for j in [0,23,65,100]:
            check(f'mirror_{gamma}_{j}',near(trace[j]['delta'],trace[-1-j]['delta']))
    else:check(f'locked_delta_{gamma}',all(near(r['delta'],1) for r in trace))
    slopes=[]
    for j in range(1,200):
        u=j/200;eps=1e-5
        left=h.normal_contact(h.overlap_intervals(u-eps,gamma),rotation_free=free)['delta']
        right=h.normal_contact(h.overlap_intervals(u+eps,gamma),rotation_free=free)['delta']
        slopes.append(-.5*(right-left)/(2*eps))
    areas.append(dict(gamma=gamma,rotation_free=free,delta_span=max(r['delta'] for r in trace)-min(r['delta'] for r in trace),
                      max_delta=max(r['delta'] for r in trace),peak_pressure=max(r['peak_line_load'] for r in trace),
                      min_active_length=min(r['active_length'] for r in trace),peak_internal_Q_over_F_per_delta0_over_L=max(abs(x) for x in slopes),
                      geometric_slot_fraction=gamma/(2+gamma),
                      max_theta_per_delta0_over_L=max(abs(r['theta']) for r in trace),trace=trace))
# Independent full-contact 2x2 solution; exclude partial-contact fixtures.
independent=[]
for gamma in [0.,.1,.25]:
 for u in [0.,.13,.5,.87,1.]:
    ints=h.overlap_intervals(u,gamma)
    A=sum(b-a for _,a,b in ints);M1=sum((b*b-a*a)/2 for _,a,b in ints);M2=sum((b**3-a**3)/3 for _,a,b in ints)
    delta=M2/(A*M2-M1*M1);theta=-M1/(A*M2-M1*M1)
    got=h.normal_contact(ints)
    check(f'linear_closed_form_{gamma}_{u}',near(delta,got['delta']) and near(theta,got['theta']))
    independent.append(dict(gamma=gamma,u=u,delta=delta,theta=theta))
# Independent midpoint quadrature: full and verified partial contact.
quad=[]
for label,u in [('full',.09),('partial',0.)]:
    base=h.normal_contact(h.overlap_intervals(u,.75))
    if label=='partial':check('quadrature_fixture_is_partial',base['active_length']<.5)
    rows=[]
    for n in [100,400,1600]:
        F=0.;M=0.;U=0.
        for _,a,b in h.overlap_intervals(u,.75):
            step=(b-a)/n
            for j in range(n):
                r=a+(j+.5)*step;p=max(0.,base['delta']+base['theta']*r)
                F+=p*step;M+=p*r*step;U+=.5*p*p*step
        rows.append(dict(n_per_interval=n,force_error=abs(F-1),moment_error=abs(M),energy_error=abs(U-.5*base['delta'])))
    check('quadrature_absolute_'+label,rows[-1]['force_error']<1e-5 and rows[-1]['moment_error']<1e-6 and rows[-1]['energy_error']<2e-6)
    check('quadrature_convergence_'+label,max(rows[-1][k] for k in ['force_error','moment_error','energy_error'])<=max(1e-12,max(rows[0][k] for k in ['force_error','moment_error','energy_error'])/50))
    quad.append(dict(fixture=label,u=u,active_length=base['active_length'],rows=rows))
# Loads scale in this linear layer model; no material calibration implied.
scaling=[]
for eta in [.25,1.,2.]:
    got=h.normal_contact(h.overlap_intervals(.27,.4),force=eta)
    ref=h.normal_contact(h.overlap_intervals(.27,.4),force=1)
    check(f'load_scaling_{eta}',near(got['delta'],eta*ref['delta']) and near(got['theta'],eta*ref['theta']))
    scaling.append(dict(force=eta,delta=got['delta'],theta=got['theta']))
cost=[]
for g in I['gamma']:
    # Hold complete pad-pair outline length W=2L+gap constant.
    relative_area=2/(2+g)
    cost.append(dict(gamma=g,fixed_outline_support_area_relative_to_g0=relative_area,
                     pressure_multiplier_for_same_force=1/relative_area,
                     required_width_multiplier_to_restore_area=1/relative_area,
                     note='geometry only, no price or manufacturing quote'))
out=dict(physical_trials=0,success_probability=None,cams=cams,area_handover=areas,independent_full_contact=independent,
         quadrature=quad,load_scaling=scaling,cost_geometry=cost,
         residuals=dict(force=worst_force,free_rotation_moment=worst_moment,energy=worst_energy))
v=dict(passed=True,count=len(checks),checks=checks,python=platform.python_version(),
       dependencies='standard library',common_library_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
       driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
for name,obj in [('results.json',out),('validation.json',v)]:
    raw=(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    if '--check' in sys.argv:assert (D/name).read_bytes()==raw,name
    else:(D/name).write_bytes(raw)
print(json.dumps({'checks':len(checks),'cam_summaries':[{k:v for k,v in x.items() if k!='trace'} for x in cams],
                  'area_summaries':[{k:v for k,v in x.items() if k!='trace'} for x in areas if x['rotation_free']],
                  'residuals':out['residuals'],'quadrature':quad},ensure_ascii=False))
