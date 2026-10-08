"""Reproduce source heat-kernel integrals and conditional contact/wear diagnostics.
Not a physical experiment or a calibrated success-probability estimator.
"""
import sys,json,csv,math,importlib.metadata
from pathlib import Path
from functools import lru_cache
ROOT=Path(__file__).resolve().parent
repo=ROOT.parents[1]
if (repo/'.deps').exists(): sys.path.insert(0,str(repo/'.deps'))
import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.optimize import minimize_scalar
from scipy.integrate import quad
I=json.loads((ROOT/'inputs.json').read_text(encoding='utf-8'));B=I['base'];checks=[]
def check(name,ok):
    if not ok: raise AssertionError(name)
    checks.append(name)
@lru_cache(None)
def nodes(n): return leggauss(n)
def hertz_kernel(x,y=0.,n=128):
    x=np.asarray(x);y=np.asarray(y)
    s=np.sqrt(np.maximum(0,1-y*y));top=np.sqrt(np.maximum(0,x+s));u,w=nodes(n)
    angle=(u+1)*np.pi/4
    z=top[...,None]*np.sin(angle)
    return (np.pi/2)*top*np.sum(w*np.cos(angle)*np.sqrt(np.maximum(0,1-(x[...,None]-z*z)**2-y[...,None]**2)),axis=-1)
pref=3/(2*np.pi*np.sqrt(np.pi));convergence=[]
for n in (32,64,128):
    u,w=nodes(n);ys=u[:,None];s=np.sqrt(1-ys*ys);xs=s*u[None,:];jac=s*w[:,None]*w[None,:]
    ff=hertz_kernel(xs,ys,n);pressure=np.sqrt(np.maximum(0,1-xs*xs-ys*ys))
    peak=minimize_scalar(lambda x:-float(hertz_kernel(x,0,n)),bounds=(-1,1),method='bounded',options={'xatol':1e-10})
    convergence.append({'quadrature_order':n,'max_coefficient':float(-pref*peak.fun),'area_average_coefficient':float(pref*(jac*ff).sum()/np.pi),'pressure_weighted_coefficient':float(pref*(jac*ff*pressure).sum()/(2*np.pi/3)),'max_x_over_a':float(peak.x)})
C=convergence[-1]
# Independent reduction y integral * adaptive x quadrature, rather than the 2-D grid.
y_factor=quad(lambda y:(1-y*y)**1.75,-1,1,epsabs=1e-11)[0]
x_factor=quad(lambda x:float(hertz_kernel(x,0.,256))*np.sqrt(max(0.,1-x*x)),-1,1,epsabs=1e-10)[0]
weighted_reduced=pref*y_factor*x_factor/(2*np.pi/3)
check('kernel at leading edge is zero',abs(float(hertz_kernel(-1.)))<1e-12)
check('trailing edge kernel exact integral',abs(float(hertz_kernel(1.))-2/3*2**1.5)<1e-12)
check('maximum coefficient convergence',abs(convergence[-1]['max_coefficient']-convergence[-2]['max_coefficient'])<1e-6)
check('area coefficient convergence',abs(convergence[-1]['area_average_coefficient']-convergence[-2]['area_average_coefficient'])<1e-6)
check('weighted coefficient independent integration',abs(weighted_reduced-C['pressure_weighted_coefficient'])<2e-7)
check('published maximum coefficient within 0.1 percent',abs(C['max_coefficient']/.590-1)<.001)
check('published area average coefficient within 0.1 percent',abs(C['area_average_coefficient']/.323-1)<.001)
# The published pressure-weighted value .352 does NOT meet this precision.
difference={'published':.352,'two_dimensional_integration':C['pressure_weighted_coefficient'],'independent_reduced_integration':float(weighted_reduced),'relative_difference_percent':100*(weighted_reduced/.352-1),'status':'unresolved source coefficient discrepancy; not silently adjusted','used_for_design':False}
def write_csv(name,rows):
    with (ROOT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def peak_temp(tau0,beta,p,a,v,e):
    scale=np.sqrt(a*v)/(e*np.sqrt(np.pi))
    def temperature(x): return scale*(2*tau0*np.sqrt(max(0,1+x))+beta*1.5*p*float(hertz_kernel(x)))
    opt=minimize_scalar(lambda x:-temperature(x),bounds=(-1,1),method='bounded')
    positions=[-1.,float(opt.x),1.];x=max(positions,key=temperature)
    return temperature(x),x
check('zero shear generates zero heat',peak_temp(0,0,1e7,1e-5,10,800)[0]==0)
check('uniform flux exact trailing maximum',abs(peak_temp(1e6,0,1e7,1e-5,10,800)[0]-2e6*np.sqrt(2e-5*10)/(800*np.sqrt(np.pi)))<1e-10)
a0=B['contact_radius_m'];p0=B['mean_contact_pressure_Pa'];E=B['effective_modulus_Pa'];e=B['thermal_effusivity_J_m2_K_sqrt_s'];D=B['thermal_diffusivity_m2_s']
F0=p0*np.pi*a0*a0;R0=4*E*a0/(3*np.pi*p0)
check('Hertz force and prescribed pressure consistent',abs(4*E*a0**3/(3*R0)/F0-1)<1e-12)
rows=[]
for interface in I['interfaces']:
    tau0=interface['tau0_Pa'];beta=interface['beta']
    for policy in ['fixed_pressure_and_total_area','fixed_crown_curvature']:
        for m in B['split_counts']:
            F=F0/m
            if policy=='fixed_pressure_and_total_area': a=a0/np.sqrt(m);R=R0/np.sqrt(m)
            else: a=a0/m**(1/3);R=R0
            p=F/(np.pi*a*a);indent=a*a/R;mu=tau0/p+beta
            # Specific wear law only: h[mm]=k[mm^3/(N m)] * p[N/mm^2] * sliding[m].
            # Allowance is a chosen shape-drift diagnostic, not a safety or life criterion.
            allowance_mm=indent*1000*B['wear_allowance_fraction_of_hertz_indentation']
            kmax=allowance_mm/(B['local_loaded_passes']*(p/1e6)*B['ski_length_m'])
            for v in B['speed_m_s']:
                rise,x=peak_temp(tau0,beta,p,a,v,e)
                power_one=(tau0*np.pi*a*a+beta*F)*v
                rows.append({'interface':interface['id'],'policy':policy,'split_count':m,'speed_m_s':v,'patch_force_N':F,'contact_radius_um':a*1e6,'crown_curvature_um':R*1e6,'mean_pressure_MPa':p/1e6,'Hertz_max_pressure_MPa':1.5*p/1e6,'indentation_um':indent*1e6,'total_real_area_ratio':m*a*a/(a0*a0),'interface_mu':mu,'peak_rise_K':rise,'diagnostic_peak_C':B['background_C']+rise,'peak_x_over_a':x,'Pe_va_over_D':v*a/D,'total_power_W':m*power_one,'kmax_shape_mm3_Nm':kmax,'grain_contact_path_m':B['ski_length_m'],'sole_point_contact_time_s':2*a/v,'status':'assumed geometry and properties; uncalibrated all-heat-to-moving-solid model'})
write_csv('contact_cases.csv',rows)
write_csv('coefficient_convergence.csv',convergence)
check('case count',len(rows)==54)
check('thermal energy equals interface friction work',all(abs(r['total_power_W']-r['interface_mu']*F0*r['speed_m_s'])<1e-12 for r in rows))
check('all example Peclet numbers at least 25',min(r['Pe_va_over_D'] for r in rows)>=25-1e-10)
check('all contact radii small relative to curvature',max(r['contact_radius_um']/r['crown_curvature_um'] for r in rows)<.1)
for name,law in [('initial','POM_UHMWPE_initial_counterfactual'),('late','POM_UHMWPE_late_counterfactual'),('target','hypothetical_low_shear_target')]:
    rs=[r for r in rows if r['interface']==law and r['policy']=='fixed_pressure_and_total_area' and r['speed_m_s']==10];base=rs[0]
    check('fixed-area heat scaling '+name,all(abs(r['peak_rise_K']/base['peak_rise_K']-r['split_count']**(-.25))<1e-9 for r in rs))
    check('fixed-area friction invariant '+name,all(abs(r['interface_mu']-base['interface_mu'])<1e-12 for r in rs))
check('fixed-curvature splitting increases adhesion contribution',all(r['interface_mu']>r['tau_base'] for r in [{'interface_mu':x['interface_mu'],'tau_base':next(i for i in I['interfaces'] if i['id']==x['interface'])['tau0_Pa']/p0+next(i for i in I['interfaces'] if i['id']==x['interface'])['beta']} for x in rows if x['policy']=='fixed_crown_curvature' and x['split_count']>1]))
target=[r for r in rows if r['interface']=='hypothetical_low_shear_target' and r['policy']=='fixed_pressure_and_total_area' and r['speed_m_s']==10]
check('splitting by 16 halves isolated flash rise',abs(target[-1]['peak_rise_K']/target[0]['peak_rise_K']-.5)<1e-10)
check('splitting by 16 quarters shape wear allowance',abs(target[-1]['kmax_shape_mm3_Nm']/target[0]['kmax_shape_mm3_Nm']-.25)<1e-12)
# Mean heat over a ski, kept separate from single-patch peak to avoid double counting.
bulk=[]
for r in [r for r in rows if r['speed_m_s']==10]:
    A=B['ski_length_m']*B['ski_width_m'];Q=r['interface_mu']*B['ski_load_N']*10;t=B['slope_length_m']/10;q=Q/A
    bulk.append({'interface':r['interface'],'policy':r['policy'],'split_count':r['split_count'],'interface_mu':r['interface_mu'],'moving_ski_power_W':Q,'run_time_s':t,'heat_J':Q*t,'mean_flux_W_m2':q,'uniform_halfspace_rise_K':2*q*np.sqrt(t)/(e*np.sqrt(np.pi)),'status':'separate mean-heating scenario; do not add as an exact result to local peak'})
check('run work equals friction force times distance',all(abs(x['heat_J']-x['interface_mu']*B['ski_load_N']*B['slope_length_m'])<1e-10 for x in bulk))
write_csv('mean_heating.csv',bulk)
c=I['cost'];af=(1-(1+c['discount_rate'])**(-c['years']))/c['discount_rate'];caps=[]
for lam in c['annual_new_fraction']:
    price=c['material_budget_JPY_year']/(c['bed_mass_kg']*(1/af+lam))
    caps.append({'annual_new_fraction':lam,'finished_price_cap_JPY_kg':price})
check('cost cap recreates assumed annual budget',all(abs(c['bed_mass_kg']*r['finished_price_cap_JPY_kg']*(1/af+r['annual_new_fraction'])-c['material_budget_JPY_year'])<1e-6 for r in caps))
write_csv('cost_caps.csv',caps)
summary={'schema':'cycle41-results-v1','physical_tests':0,'physical_success_probability':None,'conditional_cases':54,'numeric_checks_passed':len(checks),'checks':checks,'coefficient_comparison':difference,'peak_coefficient':C['max_coefficient'],'target_v10_fixed_area':target,'base_force_N':F0,'base_curvature_um':R0*1e6,'note':'No material measured or calibrated. Source weighted-average discrepancy is explicitly retained.'}
(ROOT/'results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(ROOT/'environment.json').write_text(json.dumps({'python':sys.version,'packages':{k:importlib.metadata.version(k) for k in ['numpy','scipy','matplotlib']}},indent=2)+'\n',encoding='utf-8',newline='\n')
if '--no-plots' not in sys.argv:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(1,3,figsize=(13.5,4.6),layout='constrained')
    for policy,col,label in [('fixed_pressure_and_total_area','#0f766e','Preserve pressure / real area'),('fixed_crown_curvature','#b45309','Preserve crown curvature')]:
        rr=[r for r in rows if r['interface']=='hypothetical_low_shear_target' and r['policy']==policy and r['speed_m_s']==10]
        mm=[r['split_count'] for r in rr]
        ax[0].plot(mm,[r['peak_rise_K'] for r in rr],'o-',color=col,label=label)
        ax[1].plot(mm,[r['interface_mu'] for r in rr],'o-',color=col)
        ax[2].plot(mm,[r['kmax_shape_mm3_Nm'] for r in rr],'o-',color=col)
    ax[0].set(ylabel='Isolated moving-side peak rise (K)',title='Local heat');ax[0].legend(fontsize=8)
    ax[1].set(ylabel='Interface friction coefficient',title='Adhesion cost of more contact area')
    ax[2].set(ylabel='Required specific wear rate upper bound\n(mm3 / N m)',title='100 loaded passes: chosen shape limit',yscale='log')
    for a in ax:a.set(xscale='log',xlabel='Number of patches sharing original load');a.set_xticks([1,4,16],['1','4','16']);a.grid(alpha=.2)
    fig.suptitle('H41: contact splitting trades lower local heating against geometry lifetime',fontsize=13)
    fig.supxlabel('Assumed low-shear interface; 10 m/s; all heat to moving half-space. No wet test, bulk damage, or real-life success rate.',fontsize=9)
    fig.savefig(ROOT/'splitting_tradeoff.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8.5,5),layout='constrained');x=np.linspace(-1,1,500)
    for it,col,label in zip(I['interfaces'],['#b91c1c','#d97706','#0f766e'],['POM fit: initial (extrapolation)','POM fit: late (extrapolation)','Hypothetical low-shear target']):
        temp=np.sqrt(a0*10)/(e*np.sqrt(np.pi))*(2*it['tau0_Pa']*np.sqrt(1+x)+it['beta']*1.5*p0*hertz_kernel(x))
        ax.plot(x,temp,label=label,color=col)
    ax.set(xlabel='Position along a contact: entry -1, exit +1',ylabel='Local moving-side temperature rise (K)',title='Heat from adhesion and pressure-dependent shear');ax.legend(fontsize=9);ax.grid(alpha=.2)
    fig.supxlabel('a=10 um; mean pressure=10 MPa; effusivity=800; speed=10 m/s. Inputs are not a 50 C ski-material calibration.',fontsize=8)
    fig.savefig(ROOT/'contact_heat_profiles.png',dpi=180);plt.close(fig)
print(json.dumps({'checks':len(checks),'conditional_cases':len(rows),'physical_tests':0,'source_weighted_coefficient_difference_percent':round(difference['relative_difference_percent'],4)}))
