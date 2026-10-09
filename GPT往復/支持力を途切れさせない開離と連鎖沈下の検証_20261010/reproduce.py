#!/usr/bin/env python3
"""Dimensionless screening, NOT measured snow or a material-success model."""
from pathlib import Path
import json,math,sys,hashlib,platform
D=Path(__file__).resolve().parent
I=json.loads((D/'inputs.json').read_text())
checks=[]
def check(name,condition):
    if not condition: raise AssertionError(name)
    checks.append(name)
def near(a,b,tol=1e-10): return abs(a-b)<=tol*max(1.,abs(a),abs(b))
def family(n,name):
    d=[.5+j/(n-1) for j in range(n)] if n>1 else [1.]
    if name=='U': return [1.]*n,[1.]*n
    if name=='K': return d,[1.]*n
    if name=='D': return [1.]*n,d
    if name=='KDpositive': return d,d
    if name=='KDnegative': return [2-x for x in d],d
    raise ValueError(name)
def drop(k,d,beta):
    """Quasistatic force control; simultaneous threshold ties, no healing.
    After transition f_i=beta*k_i*x. Beta is stiffness fraction, not
    constant residual fraction of threshold force in Raischel et al. 2006.
    Collapse => no finite static equilibrium; never replace with zero.
    """
    state=[False]*len(k);events=[];K=sum(k);Fprev=0.;balance_error=0.
    while not all(state):
        x0=min(d[i] for i in range(len(k)) if not state[i]);F=K*x0
        if F<Fprev-1e-9: raise AssertionError('nonmonotonic load')
        pending=[i for i in range(len(k)) if not state[i] and d[i]<=x0+1e-12]
        initial=len(pending);changed=[];waves=[];energy=0.;x=x0;collapsed=False
        while pending:
            Kold=K;xold=x
            for i in pending: state[i]=True
            changed.extend(pending);waves.append(pending)
            K=sum(ki*(beta if s else 1) for ki,s in zip(k,state))
            if K==0:
                collapsed=True;x=None;energy=None;break
            x=F/K
            work=F*(x-xold);du=.5*K*x*x-.5*Kold*xold*xold
            dissipatable=work-du
            balance_error=max(balance_error,abs(dissipatable-.5*F*(x-xold)))
            if dissipatable < -1e-9: raise AssertionError('negative energy')
            energy+=max(0.,dissipatable)
            pending=[i for i in range(len(k)) if not state[i] and d[i]<=x+1e-12]
        events.append(dict(F=F,x_before=x0,x_after=x,initial_changes=initial,
                           secondary_changes=len(changed)-initial,changed=changed,waves=waves,
                           stiffness_after=K,collapsed=collapsed,
                           required_settling_dissipation=energy))
        Fprev=F
        if collapsed: break
    finite=[e for e in events if not e['collapsed']]
    return dict(events=events,max_changes=max(len(e['changed']) for e in events),
                max_secondary=max(e['secondary_changes'] for e in events),
                max_finite_jump_ratio=max([e['x_after']/e['x_before']-1 for e in finite] or [0.]),
                collapsed=events[-1]['collapsed'],max_energy_balance_error=balance_error)
def force(k,d,beta,x):
    return sum(ki*(min(x,di)+beta*max(0.,x-di)) for ki,di in zip(k,d))
def potential(k,d,beta,x):
    return sum(.5*ki*x*x if x<=di else ki*(.5*di*di+di*(x-di)+.5*beta*(x-di)**2) for ki,di in zip(k,d))
def continuous(k,d,beta):
    events=[dict(x=x,F=force(k,d,beta,x),changes=sum(near(di,x,1e-12) for di in d),
                 slope_after=sum(ki*(beta if di<=x+1e-12 else 1) for ki,di in zip(k,d))) for x in sorted(set(d))]
    # Beta=0 has a final plateau: load above it has no finite equilibrium.
    return dict(events=events,max_jump=0.,final_slope=beta*sum(k),
                final_plateau_load=force(k,d,beta,max(d)) if beta==0 else None,
                interpretation='continuous loading envelope only; unloading/reset unspecified')
def target_drop(k,d,beta,Ftarget):
    r=drop(k,d,beta);state=[False]*len(k)
    for e in r['events']:
        if e['F']>Ftarget+1e-10: break
        for i in e['changed']:state[i]=True
        if e['collapsed']:return dict(status='no_finite_equilibrium',x=None)
    K=sum(ki*(beta if s else 1) for ki,s in zip(k,state))
    return dict(status='equilibrium',x=Ftarget/K,changed=sum(state))
def target_cont(k,d,beta,Ftarget):
    if beta==0 and Ftarget>=force(k,d,beta,max(d))-1e-12:
        cap=force(k,d,beta,max(d))
        return dict(status='plateau_nonunique' if near(Ftarget,cap) else 'no_finite_equilibrium',x=None)
    lo=0.;hi=max(d)+Ftarget/(max(beta,1e-12)*sum(k))
    for _ in range(100):
        mid=(lo+hi)/2
        if force(k,d,beta,mid)<Ftarget:lo=mid
        else:hi=mid
    x=(lo+hi)/2
    return dict(status='equilibrium',x=x,residual=force(k,d,beta,x)-Ftarget)
def uniform_drop(a,b,beta,x):
    P=min(1.,max(0.,(x-a)/(b-a)))
    return x*(1-(1-beta)*P)
def uniform_cont(a,b,beta,x):
    if x<=a:return x
    if x>=b:return beta*x+(1-beta)*(a+b)/2
    return x-(1-beta)*(x-a)**2/(2*(b-a))
def main():
    rows=[]
    for n in I['n']:
      for name in I['families']:
       k,d=family(n,name)
       check(f'stiffness_budget_{n}_{name}',near(sum(k),n))
       for beta in I['betas']:
        r=drop(k,d,beta);c=continuous(k,d,beta)
        check(f'energy_{n}_{name}_{beta}',r['max_energy_balance_error']<1e-7)
        check(f'all_states_{n}_{name}_{beta}',sum(len(e['changed']) for e in r['events'])==n)
        if name in ['U','K']:
            check(f'fixed_gap_synchronous_{n}_{name}_{beta}',len(r['events'])==1 and r['max_changes']==n)
            if beta:check(f'fixed_gap_jump_{n}_{name}_{beta}',near(r['events'][0]['x_after'],1/beta))
        if beta==1:
            check(f'no_drop_{n}_{name}',near(r['max_finite_jump_ratio'],0))
        for event in c['events']:
            x=event['x'];eps=1e-7
            check(f'continuity_{n}_{name}_{beta}_{x}',abs(force(k,d,beta,x+eps)-force(k,d,beta,x-eps))<=2.01*n*eps)
        rows.append(dict(n=n,family=name,beta=beta,drop=r,continuous=c,
                         target_F_equals_initial_total_stiffness=dict(drop=target_drop(k,d,beta,n),continuous=target_cont(k,d,beta,n))))
    # Independent continuum derivative and finite-N convergence of fixed-displacement force.
    continuum=[]
    for a,b in I['continuum_ranges']:
      beta_critical=b/(2*b-a)
      for beta in I['betas']:
        right_slope=1-(1-beta)*(2*b-a)/(b-a)
        x=(a+b)/2;eps=1e-6
        deriv=(uniform_drop(a,b,beta,x+eps)-uniform_drop(a,b,beta,x-eps))/(2*eps)
        check(f'continuum_derivative_{a}_{beta}',near(deriv,1-(1-beta)*(2*x-a)/(b-a),1e-8))
        continuum.append(dict(a=a,b=b,beta=beta,beta_critical=beta_critical,
                              minimum_interior_slope=right_slope,negative_tangent_exists=right_slope < -1e-12))
    convergence=[]
    for n in [25,101,401]:
      k,d=family(n,'D')
      for beta in [.25,.6,.75]:
        maxerr=0.;maxerrc=0.
        for j in range(601):
            x=2*j/600
            f=sum(ki*x*(beta if x>=di else 1.) for ki,di in zip(k,d))/n
            maxerr=max(maxerr,abs(f-uniform_drop(.5,1.5,beta,x)))
            maxerrc=max(maxerrc,abs(force(k,d,beta,x)/n-uniform_cont(.5,1.5,beta,x)))
        rr=drop(k,d,beta)
        check(f'quadrature_{n}_{beta}',maxerr<=2/n and maxerrc<=2/n)
        convergence.append(dict(n=n,beta=beta,drop_force_max_abs_error=maxerr,continuous_force_max_abs_error=maxerrc,
                                max_secondary=rr['max_secondary'],max_changes=rr['max_changes'],
                                max_finite_jump_ratio=rr['max_finite_jump_ratio']))
    # Independent N=1 energy calculation and conservative-envelope derivative.
    one=drop([2.],[3.],.5)['events'][0]
    check('one_spring_force',near(one['F'],6.))
    check('one_spring_new_x',near(one['x_after'],6.))
    check('one_spring_settling_energy',near(one['required_settling_dissipation'],9.))
    k,d=family(25,'D')
    for beta in [0,.25,.75,1]:
      for x in [.3,.72,1.7]:
        eps=1e-6;deriv=(potential(k,d,beta,x+eps)-potential(k,d,beta,x-eps))/(2*eps)
        check(f'potential_derivative_{beta}_{x}',near(deriv,force(k,d,beta,x),1e-8))
    coupling=[]
    for kn,kt,c in [(1,.1,0),(1,.1,.2),(1,.1,.4),(1,-.05,0),(1,-.05,.2)]:
      for machine_kt in [0,.2]:
        det=kn*(kt+machine_kt)-c*c
        coupling.append(dict(kn=kn,kt=kt,c=c,machine_kt=machine_kt,determinant=det,
                             positive_definite=kn>0 and det>0))
    # Cantilever same geometric release gap: T/k is unchanged despite root-thickness differences.
    beam=[]
    for t in [.8,1.,1.2]:
        ki=t**3;gap=1.;T=ki*gap
        check(f'thickness_not_release_gap_{t}',near(T/ki,gap))
        beam.append(dict(relative_thickness=t,relative_stiffness=ki,relative_force_threshold=T,release_gap=T/ki))
    out=dict(scope='unmeasured dimensionless screening',physical_trials=0,success_probability=None,
             rows=rows,continuum=continuum,convergence=convergence,coupling=coupling,beam_example=beam)
    valid=dict(passed=True,check_count=len(checks),checks=checks,
               runtime=dict(python=platform.python_version(),dependencies='standard library only'),
               code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    outputs={'results.json':out,'validation.json':valid}
    for name,obj in outputs.items():
        raw=(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
        if '--check' in sys.argv:
            if (D/name).read_bytes()!=raw:raise AssertionError('stored output mismatch '+name)
        else:(D/name).write_bytes(raw)
    chosen=[r for r in rows if r['n']==25 and r['family'] in ['U','K','D'] and r['beta'] in [.25,.6,.75]]
    print(json.dumps(dict(cases=len(rows),checks=len(checks),chosen=[dict(family=r['family'],beta=r['beta'],max_changes=r['drop']['max_changes'],secondary=r['drop']['max_secondary'],jump=r['drop']['max_finite_jump_ratio'],target=r['target_F_equals_initial_total_stiffness']) for r in chosen]),ensure_ascii=False))
if __name__=='__main__':main()
