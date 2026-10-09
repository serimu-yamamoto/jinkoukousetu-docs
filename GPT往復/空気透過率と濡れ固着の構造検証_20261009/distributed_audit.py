"""Distributed beam/meniscus comparison for the assumed fully wet ideal slot.
Not an independent physical validation. The lumped minimum-gap model is a bound.
"""
from pathlib import Path
import sys,json
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D.parents[1]/'.deps'))
import numpy as np
from reproduce import capillary,wj
def distributed(lam,n):
    pts,w=np.polynomial.legendre.leggauss(n);x=(pts+1)/2;w=w/2
    xx=x[:,None];ss=x[None,:]
    G=np.where(ss<=xx,ss*ss*(3*xx-ss)/6,xx*xx*(3*ss-xx)/6)*w[None,:]
    gt=x*x*(3-x)/6*w
    A=8*lam;u=np.zeros(n);status='iteration_limit'
    for iteration in range(10000):
        if np.max(u)>=.999:status='gap_closed_in_iteration';break
        nxt=A*(G@(1/(1-u)))
        if np.max(nxt)>=.999:status='gap_closed_in_iteration';u=nxt;break
        if np.max(np.abs(nxt-u))<1e-12:status='converged_minimal_equilibrium';u=nxt;break
        u=nxt
    if status.startswith('converged'):
        tip=float(A*np.sum(gt/(1-u)))
        jac=A*G/(1-u)[None,:]**2
        spectral=float(max(abs(np.linalg.eigvals(jac))))
        residual=float(np.max(np.abs(u-A*(G@(1/(1-u))))))
        return dict(n=n,Lambda=lam,status=status,iterations=iteration+1,tip_closure_fraction=tip,
                    jacobian_spectral_radius=spectral,residual=residual)
    return dict(n=n,Lambda=lam,status=status,iterations=iteration+1,tip_closure_fraction=None,
                jacobian_spectral_radius=None,residual=None)
def main():
    rows=[];checks=[]
    for span in [100.,150.,200.]:
        c=capillary(1e9,10e-6,span*1e-6,40e-6)
        rr=[distributed(c['Lambda'],n) for n in [32,64]]
        for r in rr:
            r['span_um']=span;r['lumped_closure_fraction']=c['gap_closure_fraction'];rows.append(r)
        assert rr[0]['status']==rr[1]['status']
        checks.append({'name':'status_grid_consistency_'+str(span),'passed':True})
        if rr[1]['tip_closure_fraction'] is not None:
            delta=abs(rr[0]['tip_closure_fraction']-rr[1]['tip_closure_fraction'])
            assert delta<1e-6 and rr[1]['jacobian_spectral_radius']<1 and rr[1]['residual']<1e-10
            checks.append({'name':'resolved_stable_equilibrium_'+str(span),'passed':True,'grid_abs_difference':delta})
        if c['gap_closure_fraction'] is not None and rr[1]['tip_closure_fraction'] is not None:
            assert rr[1]['tip_closure_fraction']<=c['gap_closure_fraction']+1e-8
            checks.append({'name':'lumped_min_gap_conservative_'+str(span),'passed':True})
    wj('distributed_audit.json',{'rows':rows,'checks':checks,'total_checks':len(checks),'physical_validation':False,
        'failure_scope':'iteration gap closure is only failure of this ideal full-wet beam model/iteration, not proof of a real material failure'})
    print(json.dumps({'checks':len(checks),'rows':rows}))
if __name__=='__main__':main()
