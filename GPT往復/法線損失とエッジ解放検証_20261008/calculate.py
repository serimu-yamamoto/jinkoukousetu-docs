"""H32: energy bookkeeping and prescribed-pressure sensitivity, not material prediction.
Python standard library only. All non-source constitutive parameters are hypotheses.
"""
from pathlib import Path
import math, json
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
checks=[]
def check(name,ok,detail):
    checks.append(dict(name=name,passed=bool(ok),detail=detail))
    if not ok: raise AssertionError(name+': '+str(detail))
def dump(name,value):
    (P/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def trap(y,dt): return dt*(sum(y)-.5*(y[0]+y[-1]))
def pulse(k,tau,v,n=4000,x0=0.):
    m=I['normal_model']; T=m['length_m']/v; omega=math.pi/T; a=omega*tau
    p0=m['load_N']*math.pi/(2*m['width_m']*m['length_m']); dt=T/n
    ts=[i*dt for i in range(n+1)]
    ps=[p0*math.sin(omega*t) for t in ts]
    xs=[p0/k*(math.sin(omega*t)-a*math.cos(omega*t)+a*math.exp(-t/tau))/(1+a*a)+x0*math.exp(-t/tau) for t in ts]
    dxs=[(p-k*x)/(k*tau) for p,x in zip(ps,xs)]
    ds=[p/m['instantaneous_stiffness_Pa_m']+x for p,x in zip(ps,xs)]
    work_quad=trap([p*dx for p,dx in zip(ps,dxs)],dt)
    diss=trap([k*tau*dx*dx for dx in dxs],dt)
    stored=.5*k*(xs[-1]**2-xs[0]**2)
    w=p0*p0/k*(math.pi*a/(2*(1+a*a))-a*a*(1+math.exp(-T/tau))/(1+a*a)**2)
    if x0: w-=p0*x0*a*(1+math.exp(-T/tau))/(1+a*a)
    return dict(K1_Pa_m=k,tau_s=tau,v_m_s=v,T_s=T,a=a,p0_Pa=p0,W_J_m2=w,W_quadrature_J_m2=work_quad,contact_dissipation_J_m2=diss,stored_energy_change_J_m2=stored,
                delta_mu=m['width_m']*w/m['load_N'],max_sink_mm=1000*max(ds),exit_sink_mm=1000*xs[-1],x_end_m=xs[-1],normal_load_check_N=trap(ps,dt)*v*m['width_m'])
def ode_work(k,tau,v,n):
    # Independent RK4 integration of x'=(p-K1*x)/eta and W'=p*x'.
    m=I['normal_model']; T=m['length_m']/v; p0=m['load_N']*math.pi/(2*m['width_m']*m['length_m']); dt=T/n
    x=w=0.
    def f(t,z):
        p=p0*math.sin(math.pi*t/T); dx=(p-k*z)/(k*tau)
        return dx,p*dx
    for j in range(n):
        t=j*dt; a,wa=f(t,x); b,wb=f(t+dt/2,x+a*dt/2); c,wc=f(t+dt/2,x+b*dt/2); d,wd=f(t+dt,x+c*dt)
        x+=dt*(a+2*b+2*c+d)/6; w+=dt*(wa+2*wb+2*wc+wd)/6
    return x,w
s=I['source_reference']; u=s['loop_energy_J']/s['area_m2']; drag=s['width_m']*u; power=drag*s['velocity_m_s']; total=s['friction_coefficient']*s['load_N']*s['velocity_m_s']
source=dict(U_A_J_m2=u,drag_N=drag,power_W=power,delta_mu=drag/s['load_N'],friction_power_W=total,ratio=power/total,calibration=False)
check('source_energy_conversion',abs(u-.86)<1e-12,source)
check('source_power_arithmetic',abs(power-1.204)<1e-12,power)
m=I['normal_model']; cases=[pulse(k,t,v) for k in m['delayed_stiffness_Pa_m'] for t in m['relaxation_s'] for v in m['speed_m_s']]
errW=max(abs(c['W_J_m2']-c['W_quadrature_J_m2'])/max(1e-12,abs(c['W_J_m2'])) for c in cases)
errE=max(abs(c['W_J_m2']-c['contact_dissipation_J_m2']-c['stored_energy_change_J_m2'])/max(1e-12,abs(c['W_J_m2'])) for c in cases)
check('quadrature_all_48',errW<3e-5,dict(max_relative_error=errW))
check('energy_balance_all_48',errE<3e-5,dict(max_relative_error=errE))
check('normal_load_integral',max(abs(c['normal_load_check_N']-m['load_N']) for c in cases)<.001,'integral b*v*p(t) dt = N')
check('positive_dissipation_all_48',all(c['W_J_m2']>0 and c['contact_dissipation_J_m2']>0 for c in cases),'no negative fresh-pulse energy')
check('stored_energy_is_not_returned_to_departed_ski',all(c['stored_energy_change_J_m2']>0 for c in cases),'post-passage recovery is unloaded; total eventual heat equals pulse work')
for v in m['speed_m_s']:
    a=pulse(3e5,.05,v); b=pulse(1e6,.05,v)
    check('inverse_stiffness_scaling_v'+str(v),math.isclose(a['W_J_m2']/b['W_J_m2'],1e6/3e5,rel_tol=1e-12),'linear model only')
rk=[]
for k,tau,v in [(3e5,.005,2),(3e5,.05,20),(5e6,5,20)]:
    c=pulse(k,tau,v); x,w=ode_work(k,tau,v,4000); x2,w2=ode_work(k,tau,v,8000)
    err=abs(w-c['W_J_m2'])/c['W_J_m2']; err2=abs(w2-c['W_J_m2'])/c['W_J_m2']
    record=dict(K1=k,tau_s=tau,v_m_s=v,relative_error_4000=err,relative_error_8000=err2,x_error_m=abs(x2-c['x_end_m']))
    rk.append(record); check('independent_RK4_'+str((k,tau,v)),err<2e-6 and err2<2e-6 and abs(x2-c['x_end_m'])<1e-9,record)
# Low/high a limits have zero energy per passage in this ideal linear model.
lo=pulse(1e6,1e-7,20); mid=pulse(1e6,.08/math.pi,20); hi=pulse(1e6,1e6,20)
check('relaxation_limits_not_global_material_optimum',lo['W_J_m2']<mid['W_J_m2']/1000 and hi['W_J_m2']<mid['W_J_m2']/1000,'both extremes give low model loss, not guaranteed snow feel')
budget=m['additional_mu_budget']*m['load_N']/m['width_m']
check('budget_roundtrip',math.isclose(m['width_m']*budget/m['load_N'],m['additional_mu_budget']),budget)
sh=I['shear_model']; A=sh['engagement_depth_m']*sh['edge_length_m']; shear=[]
for d in sh['release_distance_m']:
    for residual in sh['residual_traction_Pa']:
        # Traction decreases linearly from peak at zero additional slip to residual at d.
        # This is a post-peak release law; pre-peak energy is NOT included.
        peak=sh['peak_traction_Pa']; G=.5*(peak+residual)*d+residual*sh['post_release_travel_m']
        cohesive=.5*(peak-residual)*d
        shear.append(dict(release_distance_m=d,residual_Pa=residual,peak_force_N=peak*A,residual_force_N=residual*A,post_peak_work_J_m2=G,above_residual_release_work_J_m2=cohesive,post_peak_work_J=G*A,area_m2=A))
check('same_peak_different_work',len({s['peak_force_N'] for s in shear})==1,'same 250 N peak across 9 hypothetical laws')
z=[q for q in shear if q['residual_Pa']==0]
check('zero_residual_triangle',all(math.isclose(q['post_peak_work_J_m2'],.5*sh['peak_traction_Pa']*q['release_distance_m']) for q in z),'triangle exact')
check('release_work_100x',math.isclose(z[-1]['post_peak_work_J']/z[0]['post_peak_work_J'],100),'10 um versus 1 mm, same peak')
check('residual_worsens_work',all(q['post_peak_work_J_m2']>.5*sh['peak_traction_Pa']*q['release_distance_m'] for q in shear if q['residual_Pa']>0),'short drop alone does not remove residual plough/grain force')
r=I['repeat_model']; repeats=[]
for tau in r['tau_s']:
    for period in r['pass_period_s']:
        first=pulse(r['K1_Pa_m'],tau,r['speed_m_s']); T=first['T_s']; assert period>T
        g=first['x_end_m']; decay=math.exp(-period/tau); gap=math.exp(-(period-T)/tau)
        steady=g*gap/(-math.expm1(-period/tau)); x=0
        for _ in range(r['load_count']): x=decay*x+g*gap
        c=pulse(r['K1_Pa_m'],tau,r['speed_m_s'],x0=steady)
        repeats.append(dict(tau_s=tau,period_s=period,steady_preload_sink_mm=steady*1000,iterated_preload_sink_mm=x*1000,first_max_sink_mm=first['max_sink_mm'],steady_max_sink_mm=c['max_sink_mm'],steady_delta_mu=c['delta_mu'],period_mean_sink_mm=1000*first['p0_Pa']*2*T/(math.pi*period*r['K1_Pa_m'])))
check('repeated_pulse_fixed_point',max(abs(a['steady_preload_sink_mm']-a['iterated_preload_sink_mm']) for a in repeats)<1e-9,'2000 recurrence iterations versus analytic fixed point; not physical cycles')
check('long_tau_accumulation_counterexample',next(a for a in repeats if a['tau_s']==50 and a['period_s']==2)['steady_max_sink_mm']>next(a for a in repeats if a['tau_s']==50 and a['period_s']==2)['first_max_sink_mm'],'low first-pass loss is not zero remaining sink')
check('no_success_probability',I['physical_tests']==0 and I['physical_success_probability'] is None,'numerical checks do not count as material validation')
result=dict(schema='h32-results-v1',physical_tests=0,physical_success_probability=None,source_arithmetic=source,illustrative_component_budget_J_m2=budget,normal_cases=cases,shear_cases=shear,repeat_cases=repeats,independent_ode_checks=rk)
dump('results.json',result); dump('validation.json',dict(scope='numerical verification only; NOT physical experiments',check_count=len(checks),passed_count=sum(q['passed'] for q in checks),checks=checks))
print(json.dumps(dict(numerical_checks=len(checks),normal_cases=len(cases),shear_cases=len(shear),repeat_cases=len(repeats),max_quadrature_error=errW,max_energy_balance_error=errE,physical_tests=0,physical_success_probability=None),ensure_ascii=False))
