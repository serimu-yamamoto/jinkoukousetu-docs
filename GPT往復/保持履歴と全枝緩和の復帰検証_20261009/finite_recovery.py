"""Finite energy enclosure avoids treating floating-point zero as recovery."""
from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parent
D=P.parents[1]/'.research96/deps'
if D.exists():sys.path.insert(0,str(D))
import numpy as np
from scipy.integrate import solve_ivp

def run(lam,beta,x0,hold,method,rtol):
    a=beta/(1-beta);De=100;lim=.1*x0
    e=lambda x:.5*x*(x-2)
    U=lambda x:e(x)**2+.5*lam*x*x
    threshold=min(U(lim),U(-lim))*(1-1e-6)
    initial=[x0,0,a*x0*math.exp(-hold),a*e(x0)*math.exp(-hold),0]
    def energy(z):
        x,v,qv,qs,d=z
        return .5*(v/De)**2+U(x)+.5*lam*qv*qv/a+qs*qs/a
    def rhs(t,z):
        x,v,qv,qs,d=z
        return [v,De**2*(-2*(e(x)+qs)*(x-1)-lam*(x+qv)),a*v-qv,a*(x-1)*v-qs,lam*qv*qv/a+2*qs*qs/a]
    def event(t,z):return energy(z)-threshold
    event.terminal=True;event.direction=-1
    s=solve_ivp(rhs,[0,150],initial,method=method,rtol=rtol,atol=rtol*.01,events=event)
    E=energy(s.y);err=max(abs(E+s.y[4]-E[0]))/E[0]
    assert s.success and err<2e-6
    t=float(s.t_events[0][0]) if len(s.t_events[0]) else None
    return {'lambda':lam,'beta':beta,'X_initial':x0,'hold_T':hold,'method':method,'energy_enclosure_T':t,'position_band':[-lim,lim],'energy_threshold':threshold,'end_X':float(s.y[0,-1]),'end_V':float(s.y[1,-1]),'end_energy':float(E[-1]),'relative_energy_balance_error':float(err),'steady_potential_monotone_for_positive_X':lam>.25,'physical_recovery_seconds':None}

def main():
    lam=.4*.95**2/1.05**4;x0=1.2*1.05/.95**2
    cases=[];checks=[]
    pairs=[(b,h) for b in [.25,.5,.75] for h in [10,100]]
    part=int(sys.argv[sys.argv.index('--pair')+1]) if '--pair' in sys.argv else None
    if '--assemble' in sys.argv:
      for i in range(6):
        obj=json.loads((P.parents[1]/'.git'/('finite96_'+str(i)+'.json')).read_text())
        cases.extend(obj['cases']);checks.extend(obj['independent_comparisons'])
      pairs=[]
    elif part is not None:pairs=[pairs[part]]
    for beta,hold in pairs:
        pair=[run(lam,beta,x0,hold,m,r) for m,r in [('DOP853',2e-9),('Radau',2e-10)]]
        a,b=pair;t=a['energy_enclosure_T'];u=b['energy_enclosure_T']
        same=(t is None)==(u is None)
        err=None if t is None or u is None else abs(t-u)/u
        good=same and err is not None and err<2e-5
        checks.append({'beta':beta,'hold_T':hold,'relative_time_difference':err,'passed':good})
        assert good
        cases.extend(pair)
    obj={'physical_experiments':0,'success_probability':None,'band_fraction_of_initial_indentation':.1,'meaning':'passive unforced model position enclosure, not complete relaxation or physical product recovery','cases':cases,'independent_comparisons':checks,'all_passed':all(x['passed'] for x in checks)}
    raw=(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode()
    path=P/'finite_recovery.json' if part is None else P.parents[1]/'.git'/('finite96_'+str(part)+'.json')
    if '--check' in sys.argv:assert path.read_bytes()==raw
    else:path.write_bytes(raw)
    print(json.dumps({'finite_energy_cases':len(cases),'independent_comparisons':len(checks),'all_passed':obj['all_passed']}))
if __name__=='__main__':main()
