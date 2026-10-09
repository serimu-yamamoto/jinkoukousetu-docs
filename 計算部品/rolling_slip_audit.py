"""Two-surface kinematics; not a friction coefficient or temperature predictor."""
import math
def kinematics(v1,v2):
    if not math.isfinite(v1) or not math.isfinite(v2) or v1<=0 or v2<0:raise ValueError("positive v1 and nonnegative v2 required")
    return dict(relative_speed=abs(v1-v2),entrainment_speed=(v1+v2)/2,
      one_surface_fraction=(v1-v2)/v1,symmetric_fraction=2*(v1-v2)/(v1+v2),
      half_symmetric_fraction=(v1-v2)/(v1+v2))
def rpm_ratios(n1,n2,diameter_ratio=1.):
    if not all(math.isfinite(v) and v>0 for v in (n1,n2,diameter_ratio)):raise ValueError("invalid rpm or diameter ratio")
    return kinematics(1.,n2/n1*diameter_ratio)
def implied_diameter_ratio(n1,n2,label_fraction,definition):
    if not all(math.isfinite(v) and v>0 for v in (n1,n2)) or not 0<=label_fraction<1:raise ValueError("invalid values")
    s=label_fraction
    if definition=="one_surface":ratio=1-s
    elif definition=="symmetric":ratio=(2-s)/(2+s)
    elif definition=="half_symmetric":ratio=(1-s)/(1+s)
    else:raise ValueError("unknown definition")
    return ratio*n1/n2
def friction_power(mu,normal_force_N,v1_m_s,v2_m_s):
    if not math.isfinite(mu) or mu<0 or not math.isfinite(normal_force_N) or normal_force_N<=0:raise ValueError("invalid load/friction")
    z=kinematics(v1_m_s,v2_m_s)
    return mu*normal_force_N*z['relative_speed']
