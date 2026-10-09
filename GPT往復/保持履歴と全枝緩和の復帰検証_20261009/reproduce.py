"""Nonlinear SLS truss comparison; conditional mechanics, not product validation."""
from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parent; R=P.parents[1]
dep=R/'.research96/deps'
if dep.exists():sys.path.insert(0,str(dep))
import numpy as np
from scipy.integrate import solve_ivp
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
def strain(x):return .5*x*(x-2)
def simulate(lam,beta,X0,hold,mode,De=100,Tmax=150,method='DOP853',rtol=2e-9,trajectory=False,max_step=np.inf):
    a=beta/(1-beta); shared=mode=='all_SLS'
    qv=a*X0*math.exp(-hold);qs=a*strain(X0)*math.exp(-hold) if shared else 0
    def rhs(T,z):
        X,V,qv,qs,D=z
        return [V,De**2*(-2*(strain(X)+qs)*(X-1)-lam*(X+qv)),a*V-qv,a*(X-1)*V-qs if shared else 0,lam*qv*qv/a+(2*qs*qs/a if shared else 0)]
    def event(T,z):return z[0]
    event.terminal=True;event.direction=-1
    sol=solve_ivp(rhs,[0,Tmax],[X0,0,qv,qs,0],method=method,rtol=rtol,atol=rtol*.01,events=event,dense_output=trajectory,max_step=max_step)
    X,V,qv,qs,D=sol.y
    E=.5*(V/De)**2+strain(X)**2+.5*lam*X*X+.5*lam*qv*qv/a+(qs*qs/a if shared else 0)
    end=float(sol.t[-1]);cross=float(sol.t_events[0][0]) if len(sol.t_events[0]) else None
    out={'lambda':lam,'beta':beta,'X_initial':X0,'hold_T':hold,'mode':mode,'De':De,'T_limit':Tmax,'first_zero_T':cross,'status':'first_zero_crossing' if cross is not None else 'no_crossing_within_limit','end_T':end,'end_X':float(X[-1]),'end_V':float(V[-1]),'end_qv':float(qv[-1]),'end_qs':float(qs[-1]),'initial_energy':float(E[0]),'end_energy':float(E[-1]),'dissipated_energy':float(D[-1]),'relative_energy_balance_error':float(max(abs(E+D-E[0]))/E[0]),'energy_increase_max':float(max(np.diff(E),default=0)),'solver_success':sol.success,'nfev':sol.nfev,'measured':False,'settled_recovery_time':None}
    if trajectory:
        tt=np.unique(np.r_[0,np.geomspace(1e-6,end,260),end]);zz=sol.sol(tt)
        out['trajectory']=[{'T':float(t),'X':float(zz[0,k]),'V':float(zz[1,k])} for k,t in enumerate(tt)]
    return out
def tolerance(lam,x,tol):
    factor=(1-tol)**2/(1+tol)**4
    return {'nominal_lambda':lam,'nominal_cap_X':x,'relative_dimension_tolerance':tol,'lambda_min':lam*factor,'cap_X_max':x*(1+tol)/(1-tol)**2,'lambda_static_margin':lam*factor-.25,'cap_margin_to_1_5':1.5-x*(1+tol)/(1-tol)**2,'interpretation':'worst-case independent geometric bounds; not probability or true process capability'}
def main():
    if '--revalidate-saved' in sys.argv:
        saved=json.loads((P/'results.json').read_text(encoding='utf-8'))
        rows=saved['cases'];margins=saved['tolerance_cases'];worst=saved['worst_case_candidate'];candidates=saved['candidate_cases'];convergence=saved['independent_solver_comparisons']
    else:
        rows=[]
        for lam in I['lambda_values']:
          for x in I['indentation_values']:
           for hold in I['hold_values']:
            for mode in ['vertical_SLS','all_SLS']:
             selected=lam==.2501 and hold==10 and x in [1.3,1.5,1.7]
             rows.append(simulate(lam,.5,x,hold,mode,trajectory=selected))
        margins=[tolerance(lam,x,tol) for lam in [.30,.40] for x in [1.2,1.3] for tol in [.01,.03,.05]]
        worst=tolerance(.40,1.2,.05)
        candidates=[]
        for beta in [.25,.5,.75]:
          for hold in [10,100]:
           candidates.append(simulate(worst['lambda_min'],beta,worst['cap_X_max'],hold,'all_SLS'))
        convergence=[]
        for lam,x,hold,mode in [(.2501,1.5,10,'vertical_SLS'),(.2501,1.5,10,'all_SLS'),(.24,1.5,10,'all_SLS'),(worst['lambda_min'],worst['cap_X_max'],100,'all_SLS')]:
            base=simulate(lam,.5,x,hold,mode)
            alt=simulate(lam,.5,x,hold,mode,method='Radau',rtol=2e-10)
            same_status=base['status']==alt['status']
            error=None if base['first_zero_T'] is None or alt['first_zero_T'] is None else abs(base['first_zero_T']-alt['first_zero_T'])/alt['first_zero_T']
            convergence.append({'parameters':{k:base[k] for k in ['lambda','beta','X_initial','hold_T','mode']},'DOP853_T':base['first_zero_T'],'Radau_T':alt['first_zero_T'],'same_status':same_status,'relative_time_difference':error,'end_X_difference':abs(base['end_X']-alt['end_X'])})
    for row in rows+candidates:
        row['zero_event_timing_usable']=row['first_zero_T'] is not None and row['end_V'] < -1e-5
        row['zero_event_is_physical_recovery']=False
    checks=[]
    def ck(n,b):
        checks.append({'name':n,'passed':bool(b)})
        if not b:raise AssertionError(n)
    for k,row in enumerate(rows+candidates):
        ck('solver_success_'+str(k),row['solver_success'])
        ck('energy_balance_'+str(k),row['relative_energy_balance_error']<2e-6)
    for k,c in enumerate(convergence):
        ck('independent_solver_'+str(k),c['same_status'] and (c['relative_time_difference'] is None or c['relative_time_difference']<2e-5) and c['end_X_difference']<2e-5)
    for lam in [.10,.24,.25]:
        xp=(3+math.sqrt(1-4*lam))/2
        ck('analytic_equilibrium_'+str(lam),abs(2*strain(xp)*(xp-1)+lam*xp)<1e-12)
    # Equilibrium stability is a property of the zero-force polynomial, not a recovery-time test.
    ck('monostable_positive_discriminant_removed',1-4*.40<0)
    ck('fold_exact',abs(2*strain(1.5)*(.5)+.25*1.5)<1e-12)
    # Independent differential check: derivative of potential equals restoring force.
    for x in [.2,.8,1.3,1.7]:
        h=1e-6;pot=lambda z:strain(z)**2+.5*.3*z*z
        ck('potential_force_'+str(x),math.isclose((pot(x+h)-pot(x-h))/(2*h),2*strain(x)*(x-1)+.3*x,rel_tol=1e-7,abs_tol=1e-8))
    ck('zero_tolerance_identity',tolerance(.4,1.2,0)['lambda_min']==.4 and tolerance(.4,1.2,0)['cap_X_max']==1.2)
    force_cases=[]
    for lam in [.2501,.30,.40]:
        xp=1-math.sqrt((1-lam)/3);peak=2*strain(xp)*(xp-1)+lam*xp
        cap=1.2;residual=2*strain(cap)*(cap-1)+lam*cap
        ck('peak_derivative_'+str(lam),abs(3*xp*xp-6*xp+2+lam)<1e-12)
        force_cases.append({'lambda':lam,'peak_X':xp,'peak_force':peak,'cap_X':cap,'cap_force':residual,'cap_to_peak_ratio':residual/peak})
    validation={'all_passed':all(c['passed'] for c in checks),'count':len(checks),'checks':checks,'meaning':'equation and numerical validation only'}
    results={'physical_experiments':0,'success_probability':None,'actual_material_parameters':None,'actual_50C_recovery_seconds':None,'actual_ski_response':None,'first_zero_is_settled_recovery':False,'cases':rows,'tolerance_cases':margins,'worst_case_candidate':worst,'candidate_cases':candidates,'independent_solver_comparisons':convergence,'steady_force_cases':force_cases,'cost_cases':[{'extra_finished_kg_cost_JPY':q,'finished_kg':135000,'increment_JPY':q*135000,'quoted':False} for q in [50,150,300]],'actual_yield_and_life':None}
    for name,obj in [('results.json',results),('validation.json',validation)]:
        b=(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode()
        if '--check' in sys.argv:
            if (P/name).read_bytes()!=b:raise AssertionError('Reproduction changed '+name)
        else:(P/name).write_bytes(b)
    print(json.dumps({'cases':len(rows),'candidate_cases':len(candidates),'convergence_pairs':len(convergence),'checks':len(checks),'all_passed':validation['all_passed'],'physical_experiments':0}))
if __name__=='__main__':main()
