"""Cycle 61. Standard-library only; no experimental or probability output.
Run: python calculate.py ; plots separately require matplotlib.
Dimensions: s=t*sqrt(k0/m), u=x/x0, z=q/(k0*x0), w=du/ds.
The friction event and free-return experiments have independent initial states.
"""
from pathlib import Path
import csv, json, math
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
K=I['k0_N_m']; X=I['x0_um']*1e-6; M=I['modal_mass_kg']; O=math.sqrt(K/M)
Escale=K*X*X
F=(I['mu_kinetic']*I['N_first_slip_uN']+I['tangential_adhesion_uN'])*1e-6/(K*X)
checks=[]
def check(name,value,target,tol):
    assert abs(value-target)<=tol,(name,value,target,tol)
    checks.append(dict(name=name,actual=value,expected=target,tolerance=tol,passed=True))
def writecsv(name,rows):
    if not rows: return
    with (P/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def energy(y,a):
    u,v,z,dv,df=y
    return .5*(u*u+v*v+(z*z/a if a else 0))
def deriv(y,a,r,fr):
    u,v,z,dv,df=y
    return (v,-u-z+fr,a*v-z/r,z*z/(a*r) if a else 0,fr*abs(v))
def step(y,h,a,r,fr):
    a1=deriv(y,a,r,fr)
    a2=deriv([v+h*k/2 for v,k in zip(y,a1)],a,r,fr)
    a3=deriv([v+h*k/2 for v,k in zip(y,a2)],a,r,fr)
    a4=deriv([v+h*k for v,k in zip(y,a3)],a,r,fr)
    return [v+h*(b+2*c+2*d+e)/6 for v,b,c,d,e in zip(y,a1,a2,a3,a4)]
def friction(a,r,h):
    y=[1.,0.,0.,0.,0.];s=0.;maxe=0.;peakkin=0.
    for _ in range(round(200/h)):
        new=step(y,h,a,r,F)
        if y[1]<0 and new[1]>=0:
            lo=0.;hi=h
            for _ in range(45):
                mid=(lo+hi)/2
                if step(y,mid,a,r,F)[1]<0:lo=mid
                else:hi=mid
            he=(lo+hi)/2;y=step(y,he,a,r,F);s+=he
            maxe=max(maxe,abs(energy(y,a)+y[3]+y[4]-.5))
            return dict(alpha=a,r=r,first_stop_us=s/O*1e6,x_stop_um=y[0]*X*1e6,q_stop_uN=y[2]*K*X*1e6,
                elastic_energy_nJ=energy(y,a)*Escale*1e9,viscous_loss_nJ=y[3]*Escale*1e9,
                friction_loss_nJ=y[4]*Escale*1e9,peak_kinetic_nJ=peakkin*Escale*1e9,
                static_hold_at_stop=abs(y[0]+y[2])<=1+1e-9,static_hold_after_relax=abs(y[0])<=1+1e-9,
                max_energy_residual_nJ=maxe*Escale*1e9,force_plateau_is_assumed=True)
        y=new;s+=h;peakkin=max(peakkin,.5*y[1]**2)
        maxe=max(maxe,abs(energy(y,a)+y[3]+y[4]-.5))
    raise RuntimeError('No first stop within window; model must report instead of extrapolate')
def free(c,h=.005,m=M,keep=False):
    a,r=c['alpha'],c['r']; y=[1.,0.,c.get('z0',0.),0.,0.]
    e0=energy(y,a);om=math.sqrt(K/m);s=0.;lastbad=0.;maxerr=0.;history=[];minu=1.
    end=I['dimensionless_end'];n=round(end/h); stride=max(1,round(.1/h))
    for j in range(n+1):
        en=energy(y,a);minu=min(minu,y[0]);maxerr=max(maxerr,abs(en+y[3]-e0))
        # E/E0 <= 1% bounds every future |x|<=0.1*x0 only for relaxed z0=0.
        # For unrelaxed initial states, also impose absolute E<=0.005.
        ok=abs(y[0])<=.1 and en<=min(.01*e0,.005)
        if not ok:lastbad=s
        if keep and j%stride==0:
            history.append(dict(case=c['name'],time_us=s/om*1e6,x_um=y[0]*X*1e6,
                velocity_m_s=y[1]*X*om,maxwell_force_uN=y[2]*K*X*1e6,
                energy_nJ=en*Escale*1e9,loss_nJ=y[3]*Escale*1e9))
        if j<n:y=step(y,h,a,r,0.);s=(j+1)*h
    settle=(lastbad+h)/om*1e6 if lastbad+h<=end else None
    return dict(case=c['name'],alpha=a,r=r,modal_mass_kg=m,tau_us=r/om*1e6,
        initial_energy_nJ=e0*Escale*1e9,settle_energy_and_position_us=settle,
        min_x_um=minu*X*1e6,energy_remaining_fraction=energy(y,a)/e0,
        max_energy_residual_nJ=maxerr*Escale*1e9,window_us=end/om*1e6),history
# Check solver against independent analytic elastic trajectory and first friction stop.
y=[1.,0.,0.,0.,0.]
for j in range(1000):y=step(y,.005,0,1,0)
check('elastic displacement vs cos(5)',y[0],math.cos(5),1e-8)
check('elastic velocity vs -sin(5)',y[1],-math.sin(5),1e-8)
friction_rows=[friction(a,r,I['dimensionless_step']) for a,r in [(0,1),(.25,1),(1,1),(4,1),(1,.1),(1,10)]]
fr0=friction_rows[0]
check('first stop analytic displacement',fr0['x_stop_um'],(2*F-1)*X*1e6,1e-7)
check('first stop analytic time',fr0['first_stop_us'],math.pi/O*1e6,1e-7)
check('unresolved H60 energy becomes peak kinetic',fr0['peak_kinetic_nJ'],.5*(1-F)**2*Escale*1e9,2e-6)
check('friction first slip energy accounting',fr0['friction_loss_nJ']+fr0['elastic_energy_nJ'],.5*Escale*1e9,1e-8)
for c in friction_rows:
    check('friction energy balance alpha='+str(c['alpha'])+' r='+str(c['r']),c['max_energy_residual_nJ'],0,1e-7)
    assert c['static_hold_at_stop'] and c['static_hold_after_relax']
free_rows=[];hist=[]
for c in I['free_cases']:
    row,rs=free(c,keep=True);free_rows.append(row);hist.extend(rs)
    check('free energy balance '+c['name'],row['max_energy_residual_nJ'],0,1e-7)
# Timestep halving, independent limit, and material-memory sensitivity.
base=next(x for x in free_rows if x['case']=='balanced')
fine,_=free(dict(name='balanced',alpha=1,r=1),h=.0025)
check('settling time step halving',base['settle_energy_and_position_us'],fine['settle_energy_and_position_us'],.06)
check('elastic energy retained',free_rows[0]['energy_remaining_fraction'],1,1e-7)
assert free_rows[0]['settle_energy_and_position_us'] is None
assert free_rows[-1]['initial_energy_nJ']>base['initial_energy_nJ']
checks.append(dict(name='initial material memory changes stored energy',passed=True))
# Actual tau fixed for mass sensitivity, not constant r.
mass_rows=[];fixed_tau=1/O
for m in I['modal_mass_scan_kg']:
    om=math.sqrt(K/m);r=fixed_tau*om
    row,_=free(dict(name='fixed_tau_mass',alpha=1,r=r),m=m)
    row.update(f0_Hz=om/(2*math.pi),first_friction_stop_us=math.pi/om*1e6)
    mass_rows.append(row)
# Sensitivity of the exact undamped first stop to kinetic/static ratio.
ratio_rows=[]
for ta in [4,40]:
    ta_fraction=ta*1e-6/(K*X)
    for ratio in [.2,.5,.8,.95]:
        fr=ratio*(1-ta_fraction)+ta_fraction
        xs=(2*fr-1)*X*1e6
        ratio_rows.append(dict(adhesion_uN=ta,mu_kinetic_over_static=ratio,
            x_first_stop_um=xs,negative_offset_requires_reverse_clearance=xs<0,
            within_1um_at_first_stop=abs(xs)<=1,probability=None))
aa=I['tangential_adhesion_uN']*1e-6/(K*X)
ratio_window=[(.45-aa)/(1-aa),(.55-aa)/(1-aa)]
# Dynamic stiffness of one Maxwell branch in parallel with k0.
freq_rows=[]
for c in I['free_cases']:
    if 'unrelaxed' in c['name']:continue
    tau=c['r']/O;a=c['alpha']
    for j in range(81):
        hz=10**(j/16);q=2*math.pi*hz*tau
        kp=K*(1+a*q*q/(1+q*q));kl=K*a*q/(1+q*q)
        freq_rows.append(dict(case=c['name'],frequency_Hz=hz,k_storage_N_m=kp,k_loss_N_m=kl,loss_factor=kl/kp))
# Analytic peak and limits of single branch; no damping-ratio shortcut.
a=1.;q=1/math.sqrt(1+a)
loss=(a*q/(1+q*q))/(1+a*q*q/(1+q*q))
check('SLS peak loss factor',loss,a/(2*math.sqrt(1+a)),1e-14)
# Uniform shear energy lower bound: kd*x^2 = deltaG*V*gamma^2.
g=I['geometry'];ng=g['course_area_m2']*g['bed_depth_m']*g['packing_fraction']/(g['W_um']**2*g['H_um']*1e-18)
co=I['cost'];cost_rows=[]
for dg in co['deltaG_Pa']:
    for strain in co['strain_limits']:
        vol=K*X**2/(dg*strain**2)
        mass=vol*g['modules_per_grain']*ng*co['density_kg_m3_assumed']
        cost_rows.append(dict(deltaG_MPa=dg/1e6,strain_limit=strain,volume_um3_per_module=vol*1e18,
            added_mass_kg=mass,material_yen_tax_excluded=mass*co['price_yen_kg_assumed'],lower_bound=True))
        check('shear-energy lower bound '+str(dg)+' '+str(strain),dg*vol*strain**2,K*X**2,1e-20)
padV=math.prod(co['small_pad_um'])*1e-18
pad_gamma=math.sqrt(K*X**2/(1e6*padV))
# Table 1 real observations, no interpolation called a measurement.
raw=list(csv.DictReader((P/'source_table_TPU.csv').open(encoding='utf-8')))
source_means=[]
for row in raw:
    values=[float(row['specimen_'+str(j)+'_MPa']) for j in range(1,7)]
    source_means.append(dict(temperature_C=float(row['temperature_C']),frequency_Hz=50,
        mean_MPa=sum(values)/6,min_MPa=min(values),max_MPa=max(values)))
R=dict(cycle=61,physical_tests=0,success_probability=None,omega0_rad_s=O,f0_Hz=O/(2*math.pi),
    baseline_mass_is_unmeasured=True,initial_return_spring_energy_nJ=.5*Escale*1e9,
    first_friction_event=friction_rows,free_return=free_rows,mass_sensitivity=mass_rows,
    first_stop_friction_ratio_window_for_1um=ratio_window,
    friction_ratio_sensitivity=ratio_rows,stiffness_peak=dict(alpha=1,loss_factor_max=loss,f_peak_Hz=O/(2*math.pi*math.sqrt(2))),
    grain_count=ng,small_pad=dict(volume_um3=padV*1e18,required_shear_strain_at_deltaG_1MPa=pad_gamma,
        hypothetical_added_mass_kg=padV*4*ng*co['density_kg_m3_assumed']),
    side_branch_required_deltaG_over_Ginf_min=1/co['static_stiffness_allowance_fraction'],
    cost_lower_bounds=cost_rows,source_table_means=source_means,
    first_slip_pressure_change_during_stop_kPa=I['normal_unloading_assumed_kPa_s']*math.pi/O,
    local_passage_us_at_10m_s=g['W_um']/10,
    ski_envelope_us_at_10m_s=1/10*1e6,
    warning='No full grain dynamics, ski contact, warm spray crystallization or wet 50 C material verification. Cases are deterministic hypotheses, not success probability.')
writecsv('friction_ratio_sensitivity.csv',ratio_rows);writecsv('friction_events.csv',friction_rows);writecsv('free_return.csv',free_rows);writecsv('mass_sensitivity.csv',mass_rows)
writecsv('time_history.csv',hist);writecsv('frequency_response.csv',freq_rows);writecsv('damping_volume_cost.csv',cost_rows)
(P/'results.json').write_text(json.dumps(R,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(P/'numerical_checks.json').write_text(json.dumps(dict(passed=len(checks),checks=checks,physical_tests=0),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(checks=len(checks),friction_stop_um=fr0['x_stop_um'],friction_stop_us=fr0['first_stop_us'],free_balanced_us=base['settle_energy_and_position_us'],csv_rows=len(hist)+len(freq_rows)+len(friction_rows)+len(free_rows)+len(mass_rows)+len(cost_rows)+len(raw)+len(ratio_rows)),ensure_ascii=False))
