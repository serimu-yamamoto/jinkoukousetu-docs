"""Rate-independent contact rearrangement and finite-window recovery audit.
SI units. Hypothetical constitutive law; no calibrated snow/material parameters.
"""
import math
def finite(x,positive=False):
    if not math.isfinite(x) or (x<=0 if positive else x<0):raise ValueError("invalid nonnegative/positive input")
def design(peak_force,depth,residual_fraction,hardening_fraction):
    for x in (peak_force,depth):finite(x,True)
    q=residual_fraction;h=hardening_fraction
    if not 0<q<1 or not 0<=h<1-q:raise ValueError("requires 0<q<1 and 0<=h<1-q")
    k=peak_force/((1-q)*depth)
    dy=depth*(1-q/(1-h))
    fy=k*dy;H=k*h/(1-h);p=q*depth
    load=.5*k*dy**2+fy*(depth-dy)+.5*(k*h)*(depth-dy)**2
    returned=.5*peak_force**2/k
    return dict(k_N_m=k,H_N_m=H,yield_force_N=fy,yield_depth_m=dy,
                permanent_set_m=p,load_work_J=load,returned_work_J=returned,
                net_work_J=load-returned,frictional_dissipation_J=fy*p,
                hardening_energy_J=.5*H*p*p)
def update(z,p,k,fy,H):
    for x in (z,p,fy,H):finite(x)
    finite(k,True)
    trial=k*(z-p)
    if trial>fy+H*p:p=(k*z-fy)/(k+H)
    return max(0.,k*(z-p)),p
def cycles(peak_force,depth,q,h,n=1000,count=3):
    if not isinstance(n,int) or n<2 or not isinstance(count,int) or count<1:raise ValueError("invalid count")
    a=design(peak_force,depth,q,h);p=0.;out=[]
    for c in range(count):
        f0,_=update(0.,p,a['k_N_m'],a['yield_force_N'],a['H_N_m']);z0=0.;work=0.;peak=0.
        for j in list(range(1,n+1))+list(range(n-1,-1,-1)):
            z=depth*j/n
            f,p=update(z,p,a['k_N_m'],a['yield_force_N'],a['H_N_m'])
            work+=.5*(f+f0)*(z-z0);f0=f;z0=z;peak=max(peak,f)
        out.append(dict(cycle=c+1,work_J=work,permanent_set_m=p,peak_force_N=peak))
    return out
def recovery(t,permanent,retarded,tau):
    for x in (t,permanent,retarded):finite(x)
    finite(tau,True)
    return permanent+retarded*math.exp(-t/tau)
def fit_observation(unload,observed,time,tau):
    for x in (unload,observed,time,tau):finite(x,True)
    if observed>unload:raise ValueError("must recover")
    e=math.exp(-time/tau);p=(observed-unload*e)/(1-e)
    if p<0 or p>unload:raise ValueError("nonphysical fit")
    return dict(permanent=p,retarded=unload-p,tau=tau)
