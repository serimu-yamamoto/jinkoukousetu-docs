from pathlib import Path
import sys,json,math,itertools,time
P=Path(__file__).resolve().parent
dep=P.parents[1]/'.deps'
if dep.exists():sys.path.insert(0,str(dep))
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
I=json.loads((P/'inputs.json').read_text(encoding='utf8'));T=I['thermal'];W=I['wet'];F=I['factory']
checks=[]
def check(name,condition):checks.append({'name':name,'passed':bool(condition)})
rho,cp,k=T['rho_kg_m3'],T['cp_J_kgK'],T['k_W_mK']
u0=T['Tm_C']-T['T0_C'];u1=u0+T['latent_J_kg']/cp
def temperature(u):
    a=np.asarray(u)
    return T['T0_C']+np.where(a<u0,a,np.where(a<=u1,u0,a-(u1-u0)))
def lumped_times(r_um,h):
    r=r_um*1e-6;tau=rho*cp*r/(2*h)
    onset=tau*math.log((T['gas_C']-T['T0_C'])/(T['gas_C']-T['Tm_C']))
    melt=onset+rho*r*T['latent_J_kg']/(2*h*(T['gas_C']-T['Tm_C']))
    return onset,melt
def solve(r_um,L_um,h,nb,n=None,rtol=None,method='BDF',couple=True,profiles=False):
    n=n or T['cells'];rtol=rtol or T['rtol'];r=r_um*1e-6;L=L_um*1e-6
    rr=T['root_radius_um']*1e-6;lr=T['root_length_um']*1e-6;dx=L/n
    area=math.pi*r*r;mass=rho*area*dx;rootmass=rho*math.pi*rr*rr*lr
    # Root side surface only, matching cycle27's long-cylinder convention.
    root_area=2*math.pi*rr*lr-(nb*area if couple else 0)
    conv=np.full(n,h*2*math.pi*r*dx)
    if T['tip_convection']:conv[-1]+=h*area
    g=k*area/dx;gbase=2*g if couple else 0
    totalmass=rootmass+nb*mass*n
    def rhs(t,y):
        temp=temperature(y[:n+1]);tr=temp[0];tb=temp[1:]
        p=conv*(T['gas_C']-tb)
        flux=g*(tb[1:]-tb[:-1]);p[:-1]+=flux;p[1:]-=flux
        qb=gbase*(tr-tb[0]);p[0]+=qb
        rootgas=h*root_area*(T['gas_C']-tr)
        rootpower=rootgas-nb*qb
        qgas=rootgas+nb*np.sum(conv*(T['gas_C']-tb))
        return np.r_[rootpower/(rootmass*cp),p/(mass*cp),qgas/(totalmass*cp)]
    def stop(t,y):return y[0]-u0
    stop.terminal=True;stop.direction=1
    y0=np.zeros(n+2)
    sol=solve_ivp(rhs,[0,T['max_time_s']],y0,method=method,rtol=rtol,atol=T['atol_K_equivalent'],dense_output=True,events=stop,max_step=0.0004)
    if not sol.success:raise RuntimeError(sol.message)
    end=float(sol.t[-1]);sample=np.linspace(0,end,501);yv=sol.sol(sample)
    balance=(rootmass*yv[0]+nb*mass*np.sum(yv[1:n+1],axis=0))/totalmass-yv[-1]
    relative_energy_error=float(np.max(np.abs(balance))/max(1,np.max(np.abs(yv[-1]))))
    # Root crossing is located by the event solver. Each cell's first melt completion by dense-output bisection.
    melt_times=[]
    for j in range(n):
        if sol.y[j+1,-1]<u1:melt_times.append(None)
        else:melt_times.append(float(brentq(lambda t:sol.sol(t)[j+1]-u1,0,end,xtol=1e-12)))
    windows=[]
    for eta in T['viscosities_Pa_s']:
        shape=eta*r/T['surface_tension_N_m'];upper=end/(1+T['residence_uncertainty'])
        finish=[None if t is None else (t+shape)/(1-T['residence_uncertainty']) for t in melt_times]
        qualified=sum(x is not None and x<upper for x in finish)
        windows.append(dict(eta_Pa_s=eta,shape_scale_s=shape,nominal_upper_s=upper,tip_nominal_lower_s=finish[-1],tip_window_exists=finish[-1] is not None and finish[-1]<upper,qualified_length_fraction=qualified/n,qualified_length_um=qualified/n*L_um))
    ell=math.sqrt(k*r/(2*h));Lcrit=ell*math.acosh((T['gas_C']-T['T0_C'])/(T['gas_C']-T['Tm_C']))
    wet_limit=math.sqrt(3*W['E_MPa']*1e6*r**3*W['max_deflection_over_length']/(8*W['gamma_N_m']*W['force_factor']))
    ans=dict(radius_um=r_um,length_um=L_um,h_W_m2K=h,parallel_branches=nb,cells=n,root_onset_s=end,root_event_reached=bool(len(sol.t_events[0])),tip_full_melt_s=melt_times[-1],base_cell_full_melt_s=melt_times[0],melt_times_s=melt_times,windows=windows,energy_relative_error=relative_energy_error,root_mass_kg=rootmass,total_fine_mass_kg=nb*mass*n,fin_length_um=ell*1e6,cold_root_steady_tip_melt_length_um=Lcrit*1e6,wet_small_deflection_max_length_um=wet_limit*1e6,wet_slender_min_length_um=r_um*W['min_slenderness'],coupled=couple)
    if profiles:
        times=[0,.25*end,.5*end,.75*end,end]
        ans['profiles']={'x_um':((np.arange(n)+.5)*dx*1e6).tolist(),'times_s':times,'temperatures_C':[temperature(sol.sol(t)[1:n+1]).tolist() for t in times],'root_temperatures_C':[float(temperature(sol.sol(t)[0])) for t in times]}
    return ans
def run():
    cases=[]
    for r,L,h,nb in itertools.product(T['fine_radii_um'],T['lengths_um'],T['h_W_m2K'],T['parallel_branches']):
        cases.append(solve(r,L,h,nb,profiles=(r==.5 and L in [10,50] and h==500 and nb==12)))
    # Disconnected analytical limit verifies the phase-change and thermal integration.
    disconnected=solve(.5,50,500,12,couple=False)
    a,b=lumped_times(.5,500);ar,_=lumped_times(T['root_radius_um'],500)
    check('disconnected branch melting matches lumped latent solution',abs(disconnected['tip_full_melt_s']-b)/b<2e-5)
    check('disconnected root onset matches analytical value',abs(disconnected['root_onset_s']-ar)/ar<2e-5)
    convergence=[solve(.5,50,500,12,n=n,rtol=5e-8) for n in [16,32,64]]
    independent=solve(.5,50,500,12,n=32,rtol=5e-8,method='Radau')
    for x in cases:
        if not x['root_event_reached']:raise RuntimeError('root event missing')
    check('all root onset events reached',all(x['root_event_reached'] for x in cases))
    check('global energy conservation',max(x['energy_relative_error'] for x in cases)<1e-6)
    check('connected root does not melt later than disconnected comparison',all(x['root_onset_s']<=lumped_times(T['root_radius_um'],x['h_W_m2K'])[0]*1.0001 for x in cases))
    check('positive mass and melt ordering',all(x['root_mass_kg']>0 and x['total_fine_mass_kg']>0 and all(t is None or t>0 for t in x['melt_times_s']) for x in cases))
    check('tip is earliest to fully melt in monotone fine branch',all(x['tip_full_melt_s'] is None or all(t is None or t>=x['tip_full_melt_s']-1e-8 for t in x['melt_times_s']) for x in cases))
    check('temperature enthalpy relation at latent endpoints',math.isclose(float(temperature(u0)),T['Tm_C']) and math.isclose(float(temperature(u1)),T['Tm_C']))
    check('finer spatial mesh changes root onset less than 0.1 percent',abs(convergence[-1]['root_onset_s']/convergence[-2]['root_onset_s']-1)<.001)
    check('finer spatial mesh changes tip melt less than 1 percent',abs(convergence[-1]['tip_full_melt_s']/convergence[-2]['tip_full_melt_s']-1)<.01)
    check('Radau agrees with BDF root onset',abs(independent['root_onset_s']/convergence[1]['root_onset_s']-1)<1e-4)
    check('Radau agrees with BDF tip melt',abs(independent['tip_full_melt_s']/convergence[1]['tip_full_melt_s']-1)<1e-4)
    check('higher viscosity never increases qualified length',all(x['windows'][0]['qualified_length_fraction']>=x['windows'][1]['qualified_length_fraction'] for x in cases))
    # Dimensionally independent steady-fin test with a fixed cold root and insulated tip.
    for x in cases:
        ell=x['fin_length_um'];lc=x['cold_root_steady_tip_melt_length_um']
        check('steady fin threshold %g %g %g %g'%(x['radius_um'],x['length_um'],x['h_W_m2K'],x['parallel_branches']),math.isclose(T['gas_C']-(T['gas_C']-T['T0_C'])/math.cosh(lc/ell),T['Tm_C']))
    dry=[];flow=[]
    for cake,y,hr in itertools.product(F['cake_solid_mass_fractions'],F['good_yields'],F['heat_recovery']):
        retained=(1-cake)/cake
        evaporate=max(0,retained-F['final_water_kg_per_polymer_kg'])
        ideal=evaporate*F['latent_water_kWh_kg']
        supplied=ideal*(1-hr)/F['heat_conversion_efficiency']
        added=supplied*F['electric_JPY_kWh']/y
        total=(F['reference_base_JPY_per_feed_kg']+supplied*F['electric_JPY_kWh'])/y
        dry.append(dict(cake_solids=cake,yield_good=y,heat_recovery=hr,evaporated_water_kg_per_feed_kg=evaporate,latent_kWh_per_feed_kg=ideal,supplied_kWh_per_feed_kg=supplied,extra_drying_JPY_per_good_kg=added,hypothetical_base_plus_drying_JPY_per_good_kg=total,remaining_to_500_JPY_kg=F['price_comparator_JPY_good_kg']-total))
    for rate,y in itertools.product(F['good_rates_kg_h'],F['good_yields']):
        feed=rate/y;slurry=feed/F['initial_slurry_mass_fraction'];water=slurry-feed
        flow.append(dict(good_kg_h=rate,yield_good=y,feed_kg_h=feed,slurry_kg_h=slurry,water_in_slurry_kg_h=water,tunnel_gas_boundary_m3_h=feed*F['gas_m3_per_polymer_kg_lower_boundary'],nitrogen_from_other_example_ratio_kg_h=feed*F['nitrogen_to_polymer_kg_ratio'],note='Two different patent routes, not simultaneous or transferable operation. Gas volume is at patent tunnel conditions.'))
    check('slurry mass closes',all(math.isclose(x['slurry_kg_h'],x['feed_kg_h']+x['water_in_slurry_kg_h']) for x in flow))
    check('10x good rate produces 10x slurry',math.isclose(flow[3]['slurry_kg_h']/flow[0]['slurry_kg_h'],10))
    check('drying cost includes yield',all(math.isclose(x['extra_drying_JPY_per_good_kg']*x['yield_good'],x['supplied_kWh_per_feed_kg']*F['electric_JPY_kWh']) for x in dry))
    check('mechanical water removal lowers modeled latent heat',dry[0]['latent_kWh_per_feed_kg']>dry[6]['latent_kWh_per_feed_kg']>dry[12]['latent_kWh_per_feed_kg'])
    check('physical success remains unmeasured',I['evidence']['physical_tests']==0 and I['evidence']['physical_success_probability'] is None)
    result=dict(evidence=I['evidence'],thermal_cases=cases,disconnected=disconnected,convergence=convergence,independent_method=independent,drying_cases=dry,flow_cases=flow)
    valid=dict(numerical_checks=len(checks),all_passed=all(x['passed'] for x in checks),checks=checks,limitations=['fixed geometry after melting is counterfactual','root is isothermal and gas uniform','viscosity and heat transfer uncalibrated','no rounding or breakup simulation','patent fibres are not ski grains','water processing and plant cost unquoted'])
    for name,value in [('results.json',result),('validation.json',valid)]:
        (P/name).write_bytes((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8'))
    print(json.dumps(dict(thermal_cases=len(cases),checks=len(checks),passed=valid['all_passed'],max_energy_error=max(x['energy_relative_error'] for x in cases),reference=next(x for x in cases if x['radius_um']==.5 and x['length_um']==50 and x['h_W_m2K']==500 and x['parallel_branches']==12)['windows'])))
    if not valid['all_passed']:raise SystemExit('validation failed')
if __name__=='__main__':run()
