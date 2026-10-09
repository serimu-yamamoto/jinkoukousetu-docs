"""Closed-loop restoration balances. Scenario inputs are not device ratings or material tests."""
import math
def available_seconds(closed=3600.,other=1320.,tail=120.):
    t=closed-other-tail
    if t<=0:raise ValueError('No processing window')
    return t
def load(area,depth,fraction,density=150.,seconds=2160.):
    volume=area*depth*fraction;mass=volume*density
    return dict(area_m2=area,depth_m=depth,area_fraction=fraction,dry_mass_kg=mass,
        volume_m3=volume,required_t_h=mass/seconds*3.6,required_m3_h=volume/seconds*3600)
def capacity(q_t_h,bed_mass,seconds=2160.):
    mass=q_t_h*1000*seconds/3600
    return dict(q_dry_t_h_assumed=q_t_h,processable_kg=mass,
        fraction_of_bed=min(1.,mass/bed_mass),uncapped_fraction=mass/bed_mass)
def carrier(q_t_h,residence_s,layer_m,density=150.):
    hold=q_t_h*1000/3600*residence_s
    return dict(q_dry_t_h_assumed=q_t_h,residence_s_assumed=residence_s,layer_m_assumed=layer_m,
        dry_holdup_kg=hold,active_area_m2=hold/(density*layer_m))
def centrifuge(G,layer_m,R=.5,water_ratio=.2,dry_bulk=150.,pore_path_m=.0006):
    a=G*9.81;omega=math.sqrt(a/R)
    return dict(G_assumed=G,layer_m_assumed=layer_m,R_m_assumed=R,
        rpm=omega*60/(2*math.pi),tip_speed_m_s=omega*R,
        water_radial_pressure_scale_Pa=1000*.5*omega**2*(R**2-(R-pore_path_m)**2),
        wet_layer_bodyforce_scale_Pa=dry_bulk*(1+water_ratio)*.5*omega**2*(R**2-(R-layer_m)**2))
def projected_width(angle_deg,diameter_mm=2.,height_mm=.6):
    a=math.radians(angle_deg)
    return height_mm*abs(math.cos(a))+diameter_mm*abs(math.sin(a))
def loss_budget(processed_kg,passes,loss_fraction,price):
    mass=processed_kg*passes*loss_fraction
    return dict(processed_kg_per_pass=processed_kg,passes_per_year_assumed=passes,
        loss_fraction_assumed=loss_fraction,contained_reject_kg_y=mass,
        raw_replacement_JPY_y_assumed=mass*price)
