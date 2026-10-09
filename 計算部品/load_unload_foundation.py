"""Rate-independent, unilateral load/unload foundation diagnostic, SI units.
Not a calibrated model of snow, polymer, ski camber, or lateral cutting."""
from math import isfinite
def response(normal_N, width_m, front_m, rear_m, stiffness_Pa_m,
             recovery_fraction, dissipative_fraction=1., speed_m_s=10.):
    vals=[normal_N,width_m,front_m,rear_m,stiffness_Pa_m]
    if not all(isfinite(x) and x>0 for x in vals): raise ValueError('positive finite dimensions and load required')
    r,f=recovery_fraction,dissipative_fraction
    if not (0<r<=1 and 0<=f<=1 and isfinite(speed_m_s) and speed_m_s>=0): raise ValueError('invalid fraction or speed')
    loss=f*(1-r); C=front_m+rear_m*(1-loss)
    d=2*normal_N/(width_m*stiffness_Pa_m*C)
    peak=stiffness_Pa_m*d
    area_loss=.5*stiffness_Pa_m*d*d*loss
    drag=width_m*area_loss
    return dict(normal_N=normal_N,width_m=width_m,front_m=front_m,rear_m=rear_m,
      stiffness_Pa_m=stiffness_Pa_m,recovery_fraction=r,dissipative_fraction=f,
      speed_m_s=speed_m_s,indentation_m=d,peak_pressure_Pa=peak,
      effective_contact_length_m=C,loss_J_per_m2=area_loss,
      drag_N=drag,mu_deformation=drag/normal_N,power_W=drag*speed_m_s,
      front_slope=d/front_m,rear_slope=d/rear_m,
      small_slope_screen=d/min(front_m,rear_m)<=.1)
def pressure_z(z,depth,stiffness,r,f,loading):
    if loading: return stiffness*max(0.,z)
    virgin=stiffness*max(0.,(z-depth*(1-r))/r)
    reversible=stiffness*max(0.,z)
    return f*virgin+(1-f)*reversible
def integrate_path(case,steps=4000):
    """Independent trapezoidal force and work along the specified triangular path."""
    if steps<10: raise ValueError('insufficient quadrature')
    a,b=case['front_m'],case['rear_m'];d=case['indentation_m']
    K,r,f=case['stiffness_Pa_m'],case['recovery_fraction'],case['dissipative_fraction']
    N=F=0.
    for length,loading in [(a,True),(b,False)]:
        x0=0.;z0=0. if loading else d
        p0=pressure_z(z0,d,K,r,f,loading)
        for i in range(1,steps+1):
            x=length*i/steps;z=d*(i/steps if loading else 1-i/steps)
            p=pressure_z(z,d,K,r,f,loading)
            N+=(p+p0)*.5*(x-x0);F+=(p+p0)*.5*(z-z0)
            x0,z0,p0=x,z,p
    return dict(normal_N=N*case['width_m'],drag_N=F*case['width_m'])
def allowed_depth(mu_budget,front_m,rear_m,r,f):
    if mu_budget<0 or front_m<=0 or rear_m<=0 or not 0<r<=1 or not 0<=f<=1:
        raise ValueError('invalid geometry or budget')
    loss=f*(1-r)
    return None if loss==0 else mu_budget*(front_m+rear_m*(1-loss))/loss
