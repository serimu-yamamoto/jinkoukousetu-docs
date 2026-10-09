"""Prescribed single-mode viscoelastic deformation, not calibrated ski friction."""
import math
def pos(x):
    if not math.isfinite(x) or x<=0: raise ValueError('positive finite input required')
    return x
def nonneg(x):
    if not math.isfinite(x) or x<0: raise ValueError('nonnegative finite input required')
    return x
def complex_stiffness(frequency_Hz,k_relaxed_N_m,k_increment_N_m,tau_s):
    w=2*math.pi*nonneg(frequency_Hz);k0=pos(k_relaxed_N_m);dk=nonneg(k_increment_N_m);t=pos(tau_s)
    x=w*t
    return complex(k0+dk*x*x/(1+x*x),dk*x/(1+x*x))
def sinusoidal_glide(v_m_s,wavelength_m,amplitude_m,load_N,k_relaxed_N_m,k_increment_N_m,tau_s):
    v=pos(v_m_s);lam=pos(wavelength_m);a=nonneg(amplitude_m);n=pos(load_N)
    f=v/lam;k=complex_stiffness(f,k_relaxed_N_m,k_increment_N_m,tau_s)
    work=math.pi*k.imag*a*a;force=work/lam;variation=abs(k)*a
    return dict(v_m_s=v,wavelength_m=lam,amplitude_m=a,frequency_Hz=f,period_s=1/f,
        k_storage_N_m=k.real,k_loss_N_m=k.imag,loss_tangent=k.imag/k.real,
        loss_J_per_cycle=work,drag_N=force,mu_deformation_only=force/n,
        work_rate_W=force*v,force_variation_amplitude_N_massless=variation,
        minimum_normal_force_N_massless=n-variation,
        maximum_slope=2*math.pi*a/lam,
        small_slope_diagnostic=2*math.pi*a/lam<=.2,
        continuous_contact_massless_diagnostic=variation<n,
        equilibrium_displacement_under_held_load_m=n/k_relaxed_N_m,
        calibrated=False,inertia_and_contact_rearrangement_included=False)
def matched_dynamic_stiffness(f_reference,k_target,k0,dk,tau):
    current=complex_stiffness(f_reference,k0,dk,tau)
    scale=pos(k_target)/current.real
    return dict(scale=scale,k0=k0*scale,dk=dk*scale,tau=tau,reference_Hz=f_reference)
def time_domain_work(x,steps_per_cycle=4096):
    """Independent stepwise-linear drive and exact Maxwell-arm update, with startup discarded.
    Unit period, A=.01, k0=1, delta_k=9; x=omega*tau."""
    x=pos(x)
    if not isinstance(steps_per_cycle,int) or steps_per_cycle<128:raise ValueError('resolution too low')
    dt=1/steps_per_cycle;tau=x/(2*math.pi);a=.01;k0=1;dk=9
    decay=math.exp(-dt/tau);fac=-math.expm1(-dt/tau)
    warmup=math.ceil(20*tau)+8;total=(warmup+1)*steps_per_cycle
    q=0.;z=0.;force=0.;work=0.
    for i in range(total):
        z2=a*math.sin(2*math.pi*(i+1)/steps_per_cycle)
        q2=q*decay+dk*tau*(z2-z)/dt*fac
        force2=k0*z2+q2
        if i>=warmup*steps_per_cycle:work+=(force+force2)*(z2-z)/2
        z=z2;q=q2;force=force2
    expected=math.pi*dk*x/(1+x*x)*a*a
    return dict(x=x,steps_per_cycle=steps_per_cycle,work=work,expected=expected,relative_error=abs(work/expected-1))
