"""Two-dimensional steady chip momentum and power diagnostic in SI units.
Not a calibrated snow cutting law. No normal force, edge tilt, chip vertical motion,
microfracture, friction, initial static shear strength, or ski trajectory prediction.
"""
import math
def transport(rho,L,depth,speed,attack_deg,q0,rate_coeff,chi):
    positive=[rho,L,depth,speed]
    if not all(math.isfinite(x) and x>0 for x in positive):
        raise ValueError("positive finite density dimensions and speed required")
    if not math.isfinite(attack_deg) or not 0<attack_deg<=90:
        raise ValueError("0<attack<=90; zero attack is not this cutting regime")
    if not all(math.isfinite(x) and x>=0 for x in [q0,rate_coeff]) or not math.isfinite(chi) or not 0<=chi<=2:
        raise ValueError("nonnegative resistance; passive one-direction chi in [0,2]")
    g=math.radians(attack_deg);sn,cs=math.sin(g),math.cos(g)
    area=L*depth;vn=speed*sn;mdot=rho*area*vn;u=chi*vn
    fi=mdot*u;fs=(q0+rate_coeff*vn*vn)*area;fc=fi+fs
    braking=fc*sn;turning=fc*cs;kinetic=.5*mdot*u*u
    pi=fi*vn;ps=fs*vn
    return dict(area_m2=area,cross_edge_speed_m_s=vn,mass_flow_kg_s=mdot,
      outgoing_normal_speed_m_s=u,transport_force_N=fi,structural_force_N=fs,
      total_cross_edge_force_N=fc,braking_N=braking,turning_N=turning,
      reaction_xy_N=[-braking,turning],transport_power_W=pi,
      outgoing_kinetic_power_W=kinetic,transport_dissipation_W=pi-kinetic,
      structural_dissipation_W=ps,total_tool_power_W=braking*speed,
      effective_quadratic_coefficient_kg_m3=rate_coeff+rho*chi)

def outgoing_distribution(rho,area,vn,chi_weights):
    if not all(math.isfinite(x) and x>0 for x in [rho,area,vn]):
        raise ValueError("positive flow parameters")
    if not chi_weights or any(not math.isfinite(c) or not 0<=c<=2 or not math.isfinite(w) or w<0 for c,w in chi_weights):
        raise ValueError("passive nonnegative distribution")
    if not math.isclose(sum(w for c,w in chi_weights),1,abs_tol=1e-12):
        raise ValueError("mass fractions must sum to one")
    mean=sum(c*w for c,w in chi_weights);second=sum(c*c*w for c,w in chi_weights)
    mdot=rho*area*vn;force=mdot*vn*mean;work=force*vn;ke=.5*mdot*vn*vn*second
    return dict(mean_chi=mean,second_moment_chi=second,force_N=force,work_W=work,kinetic_W=ke,dissipation_W=work-ke)

def impulse_parcels(rho,area,vn,chi_weights,duration,parcels=1000):
    """Accumulate independent outgoing particle impulse and kinetic energy.
    Equal mass parcels per species; the stationary inlet has zero lab momentum.
    """
    if duration<=0 or parcels<1:raise ValueError("positive time and parcel count")
    total_m=rho*area*vn*duration;I=K=0.
    for chi,weight in chi_weights:
        dm=total_m*weight/parcels;u=chi*vn
        for _ in range(parcels):
            I+=dm*u;K+=.5*dm*u*u
    return dict(force_N=I/duration,kinetic_W=K/duration,work_W=I*vn/duration)
