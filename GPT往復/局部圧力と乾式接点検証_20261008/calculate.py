"""H33 pressure-area bounds and compliant contact support, hypothetical geometry.
Standard library only. Source fits are replayed solely as conditional diagnostics.
"""
from pathlib import Path
import json,math
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8')); checks=[]
def check(name,ok,detail):
    checks.append(dict(name=name,passed=bool(ok),detail=detail))
    if not ok: raise AssertionError(name+': '+str(detail))
def dump(name,x): (P/name).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def contact(u,C,k):
    if u<=0: return 0.,0.
    if k is None: return C*u**1.5,u
    lo=0.; hi=u
    for _ in range(36):
        d=(lo+hi)/2; f=C*d**1.5
        if d+f/k>u: hi=d
        else: lo=d
    d=(lo+hi)/2
    return C*d**1.5,d

def bed(radius,spread,k,n):
    g=I['geometry']; A0=g['nominal_width_m']*g['nominal_length_m']; sites=A0/g['grain_pitch_m']**2*g['site_occupancy']; w=sites/n
    C=4/3*g['combined_modulus_Pa']*math.sqrt(radius); fbar=g['load_N']/sites
    heights=[spread*(-1+(2*i+1)/n) for i in range(n)]
    lo=-spread; hi=spread+(fbar/C)**(2/3)+(fbar/k if k else 0)
    for _ in range(52):
        z=(lo+hi)/2; s=w*sum(contact(z+h,C,k)[0] for h in heights)
        if s>g['load_N']: hi=z
        else: lo=z
    z=(lo+hi)/2; active=[]
    for h in heights:
        f,d=contact(z+h,C,k)
        if f>0:
            a=math.sqrt(radius*d); area=math.pi*a*a
            active.append((f,d,a,area,f/area,1.5*f/area,f/k if k else 0))
    force=w*sum(q[0] for q in active); area=w*sum(q[3] for q in active); mean=force/area
    vals=[q[0] for q in active]; mean_force=sum(vals)/len(vals); cv=math.sqrt(sum((x-mean_force)**2 for x in vals)/len(vals))/mean_force
    maxpeak=max(q[5] for q in active); maxratio=max(q[2]/radius for q in active)
    out=dict(radius_m=radius,height_half_range_m=spread,root_stiffness_N_m=k,bins=n,approach_m=z,site_count=sites,active_site_count=w*len(active),load_N=force,real_area_m2=area,real_area_fraction=area/A0,area_mean_pressure_Pa=mean,max_local_peak_pressure_Pa=maxpeak,max_root_deflection_m=max(q[6] for q in active),max_a_over_R=maxratio,max_contact_diameter_m=2*max(q[2] for q in active),active_force_CV=cv,small_contact_screen=maxratio<=g['small_contact_ratio_screen'])
    # Fits at different speed, size and history: this is a stress-test of an extrapolation, not a prediction.
    out['conditional_adhesion_fit_replay']=[dict(label=p['label'],mu=p['beta']+p['tau0_Pa']/mean) for p in I['source_fits']['pom_pe_parameters']]
    # Integral of tau0+beta*p over each contact must equal tau0*A_total+beta*N.
    p=I['source_fits']['pom_pe_parameters'][1]
    sumF=w*sum(p['tau0_Pa']*q[3]+p['beta']*q[0] for q in active)
    out['direct_adhesive_force_N']=sumF
    return out

b=I['pressure_bound']; bounds=[]; req=[]
for p in I['source_fits']['pom_pe_parameters']:
    for cap in b['local_pressure_caps_Pa']:
        bounds.append(dict(label=p['label'],local_pressure_cap_Pa=cap,adhesion_lower_bound=p['beta']+p['tau0_Pa']/cap,total_lower_bound=p['beta']+p['tau0_Pa']/cap+b['other_resistance_mu']))
    margin=b['mu_total_budget']-b['other_resistance_mu']-p['beta']
    req.append(dict(label=p['label'],minimum_pressure_cap_Pa=(p['tau0_Pa']/margin if margin>0 else None),finite_necessary_condition=margin>0,not_sufficient=True))
inverse=[]
for cap in b['local_pressure_caps_Pa']:
    for beta in b['inverse_beta']:
        inverse.append(dict(local_pressure_cap_Pa=cap,beta=beta,maximum_tau0_Pa=max(0.,(b['mu_total_budget']-b['other_resistance_mu']-beta)*cap),necessary_only=True))
check('area_pressure_bound',all(q['total_lower_bound']>=q['adhesion_lower_bound'] for q in bounds),'N <= p_cap*A; mu_adh >= beta+tau0/p_cap')
check('source_initial_threshold',math.isclose(req[0]['minimum_pressure_cap_Pa'],2e8,rel_tol=1e-12),req[0])
check('source_late_threshold',math.isclose(req[1]['minimum_pressure_cap_Pa'],7e7,rel_tol=1e-12),req[1])
check('source_osc_threshold',math.isclose(req[2]['minimum_pressure_cap_Pa'],1.681e6/.018,rel_tol=1e-12),req[2])
check('units_Pa_MPa',math.isclose(.7e6/2e7,.7/20),'same dimensionless ratio')
check('impossible_beta_floor',b['mu_total_budget']-b['other_resistance_mu']-.09<0,'if beta=0.09 in this allocation, pressure increase cannot satisfy budget')
check('inverse_limit_example',math.isclose(next(q['maximum_tau0_Pa'] for q in inverse if q['local_pressure_cap_Pa']==1e7 and q['beta']==.03),.5e6),'.5 MPa at assumed 10 MPa cap and beta .03')
g=I['geometry']; cases=[bed(r,h,k,g['quadrature_bins']) for r in g['cap_radius_m'] for h in g['height_half_range_m'] for k in g['root_stiffness_N_m']]
check('global_load_balance_all_48',max(abs(q['load_N']-g['load_N']) for q in cases)<1e-6,'sum weighted contact loads = 400 N')
check('real_area_positive',all(0<q['real_area_fraction']<1 for q in cases),'independent small contact footprints do not cover nominal area')
check('site_counts',all(0<q['active_site_count']<=q['site_count'] for q in cases),'fractional quadrature counts, not probabilities')
check('peak_exceeds_area_mean',all(q['max_local_peak_pressure_Pa']>q['area_mean_pressure_Pa'] for q in cases),'Hertz peak is not mean or nominal pressure')
check('adhesion_sum_identity',max(abs(q['direct_adhesive_force_N']-q['load_N']*q['conditional_adhesion_fit_replay'][1]['mu']) for q in cases)<1e-7,'integrated local traction equals beta*N+tau0*A')
check('conditional_bound_on_each_bed',all(q['conditional_adhesion_fit_replay'][1]['mu']>=.07+.7e6/q['max_local_peak_pressure_Pa'] for q in cases),'uses hypothetical max local pressure, not material allowable')
# All equal height, rigid roots: independent analytic inversion.
u=(g['load_N']/(g['nominal_width_m']*g['nominal_length_m']/g['grain_pitch_m']**2*g['site_occupancy'])/(4/3*g['combined_modulus_Pa']*math.sqrt(50e-6)))**(2/3)
equal=bed(50e-6,0,None,101)
check('equal_height_analytic',math.isclose(equal['approach_m'],u,rel_tol=1e-9),'F=C*delta^(3/2) with all sites equally loaded')
check('equal_height_CV',equal['active_force_CV']<1e-12,equal['active_force_CV'])
# Independent force-variable bisection checks the contact inversion equation.
inv_err=[]
for u0 in [1e-7,1e-6,1e-5]:
    C=4/3*g['combined_modulus_Pa']*math.sqrt(50e-6); k=1000; f,d=contact(u0,C,k)
    lo=0.;hi=k*u0
    for _ in range(60):
        F=(lo+hi)/2
        if (F/C)**(2/3)+F/k>u0:hi=F
        else:lo=F
    inv_err.append(abs(f-(lo+hi)/2)/f)
check('independent_force_inversion',max(inv_err)<1e-8,dict(max_relative_error=max(inv_err)))
convergence=[]
for k in [100,1000,None]:
    seq=[bed(50e-6,25e-6,k,n) for n in [101,202,404]]
    e1=abs(seq[0]['real_area_m2']-seq[-1]['real_area_m2'])/seq[-1]['real_area_m2'];e2=abs(seq[1]['real_area_m2']-seq[-1]['real_area_m2'])/seq[-1]['real_area_m2']
    convergence.append(dict(k=k,bins=[101,202,404],area_error_101_to_404=e1,area_error_202_to_404=e2,area_values_m2=[q['real_area_m2'] for q in seq]))
    check('height_quadrature_'+str(k),e1<.005 and e2<.002,convergence[-1])
# Qualitative checks at fixed radius and height distribution: softer roots enlist more sites but enlarge area.
x=[q for q in cases if q['radius_m']==50e-6 and q['height_half_range_m']==25e-6]
soft=next(q for q in x if q['root_stiffness_N_m']==100);rigid=next(q for q in x if q['root_stiffness_N_m'] is None)
check('load_sharing_tradeoff',soft['max_local_peak_pressure_Pa']<rigid['max_local_peak_pressure_Pa'] and soft['real_area_m2']>rigid['real_area_m2'],dict(soft_peak=soft['max_local_peak_pressure_Pa'],rigid_peak=rigid['max_local_peak_pressure_Pa']))
# Count nominal-cost sensitivity only; mass fraction is never substituted for load share.
c=I['cost'];cost=[]
for area in c['nominal_area_m2']:
    mass=area*c['depth_m']*c['bulk_density_kg_m3']
    for f in c['local_contact_phase_mass_fraction']:
        for premium in c['phase_premium_JPY_kg']:
            cost.append(dict(area_m2=area,bed_mass_kg=mass,phase_mass_fraction=f,phase_mass_kg=mass*f,premium_JPY_kg=premium,increment_JPY=mass*f*premium))
check('mass_cost_example',next(q['increment_JPY'] for q in cost if q['area_m2']==2000 and q['phase_mass_fraction']==.05 and q['premium_JPY_kg']==2000)==10800000,'5% of assumed 108 t times hypothetical 2000 JPY/kg premium')
# Structural identifiability: area scale and tau0 cannot be separated by friction force alone.
Ns=[10,20,40,80];As=[2e-6*(n/10)**(2/3) for n in Ns];tau=.7e6;beta=.07
f1=[tau*a+beta*n for a,n in zip(As,Ns)];f2=[(tau/2)*(2*a)+beta*n for a,n in zip(As,Ns)]
check('area_tau0_scale_ambiguity',max(abs(a-b) for a,b in zip(f1,f2))<1e-12,'double area and halve tau0: identical force data; no measured area -> no unique tau0')
check('no_physical_probability',I['physical_tests']==0 and I['physical_success_probability'] is None,'numerical checks are not material trials')
ls=I['load_sharing'];mix=[]
for low in ls['low_phase_mu']:
    budget=ls['total_mu_budget']-ls['noninterface_mu']; w=(ls['other_phase_mu']-budget)/(ls['other_phase_mu']-low)
    mix.append(dict(low_phase_mu=low,required_low_phase_load_fraction=w,required_low_phase_real_area_lower_bound_m2=w*ls['load_N']/ls['local_pressure_cap_Pa']))
check('load_fraction_not_mass_fraction',math.isclose(next(q['required_low_phase_load_fraction'] for q in mix if q['low_phase_mu']==.05),.7),'hypothetical 0.05/0.15 pair needs 70% of load for total 0.1 with other 0.02')
check('load_share_pressure_area',math.isclose(next(q['required_low_phase_real_area_lower_bound_m2'] for q in mix if q['low_phase_mu']==.05),28e-6),'minimum 28 mm2 at assumed local pressure cap 10 MPa, not actual contact area')
R=dict(schema='h33-results-v1',physical_tests=0,physical_success_probability=None,pressure_bounds=bounds,necessary_pressure_caps=req,inverse_tau0_limits=inverse,geometry_cases=cases,quadrature_convergence=convergence,equal_height_analytic_case=equal,cost_sensitivity=cost,load_sharing=mix)
dump('results.json',R);dump('validation.json',dict(scope='numerical verification, NOT empirical material performance',check_count=len(checks),passed_count=sum(q['passed'] for q in checks),checks=checks))
print(json.dumps(dict(checks=len(checks),geometry_cases=len(cases),pressure_bounds=len(bounds),inverse_bounds=len(inverse),cost_cases=len(cost),physical_tests=0,physical_success_probability=None)))
