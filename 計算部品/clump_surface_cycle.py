"""Prescribed planar sliding over a periodic row, not full DEM or ski tribology."""
import math
def force_ratio(mu,slope):
    if not math.isfinite(mu) or not math.isfinite(slope) or mu<0:raise ValueError("Invalid friction or slope")
    if mu*slope>=1:raise ValueError("No finite forward solution for prescribed constrained path")
    return (mu+slope)/(1-mu*slope)
def simpson(f,a,b,n=1000):
    if n<2 or n%2:raise ValueError("Even n required")
    h=(b-a)/n
    return h/3*(f(a)+f(b)+sum((4 if j%2 else 2)*f(a+j*h) for j in range(1,n)))
def row_cycle(bead_radius_m,probe_radius_m,pitch_m,mu,n=1000):
    if not all(math.isfinite(v) and v>0 for v in [bead_radius_m,probe_radius_m,pitch_m]) or not math.isfinite(mu) or mu<0:
        raise ValueError("Invalid inputs")
    radius=bead_radius_m+probe_radius_m
    if pitch_m>2*bead_radius_m:raise ValueError("Nonoverlapping row beyond diagnostic domain")
    half=pitch_m/2
    slope_max=half/math.sqrt(radius**2-half**2)
    if mu*slope_max>=1:raise ValueError("Prescribed-path sliding limit reached")
    def slope(u):
        x=pitch_m*u
        return -x/math.sqrt(radius**2-x**2)
    mean_force=simpson(lambda u:force_ratio(mu,slope(u)),-.5,.5,n)
    mean_heat=simpson(lambda u:mu*(1+slope(u)**2)/(1-mu*slope(u)),-.5,.5,n)
    mean_lift=simpson(slope,-.5,.5,n)
    z=half*math.sqrt(1+mu**2)/radius
    analytic=mu*math.atanh(z)/z
    positive_only=simpson(lambda u:max(0,force_ratio(mu,slope(u))),-.5,.5,n)
    return dict(bead_radius_m=bead_radius_m,probe_radius_m=probe_radius_m,pitch_m=pitch_m,
      input_contact_mu_assumed=mu,clearance_height_ripple_m=radius-math.sqrt(radius**2-half**2),
      maximum_abs_slope=slope_max,minimum_force_over_load=force_ratio(mu,-slope_max),
      maximum_force_over_load=force_ratio(mu,slope_max),
      mean_signed_force_over_load=mean_force,mean_friction_work_over_load_pitch=mean_heat,
      mean_gravitational_work_over_load_pitch=mean_lift,analytic_mean_force_over_load=analytic,
      positive_only_work_over_load_pitch=positive_only,smooth_reference_force_over_load=mu,
      note="Nonrotating probe, prescribed planar forward motion, constant vertical load, quasi-static single-contact segments. Junction cusp inertia/multicontact unresolved.")

def pitch_for_relative_peak(mu,relative_extra,bead_radius_m,probe_radius_m):
    if not all(math.isfinite(v) and v>0 for v in [mu,relative_extra,bead_radius_m,probe_radius_m]):
        raise ValueError("Positive inputs required")
    target=mu*(1+relative_extra)
    max_slope=(target-mu)/(1+target*mu)
    radius=bead_radius_m+probe_radius_m
    pitch=2*radius*max_slope/math.sqrt(1+max_slope**2)
    return dict(contact_mu_assumed=mu,relative_peak_extra_diagnostic=relative_extra,
       target_peak_force_over_load=target,max_slope=max_slope,
       maximum_pitch_m=min(pitch,2*bead_radius_m),
       scope="Numerical path-error diagnostic, not a snow-quality tolerance.")
