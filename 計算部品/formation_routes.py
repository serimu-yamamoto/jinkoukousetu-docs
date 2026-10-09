"""Manufacturing mass balances and an open two-rim/six-web grain geometry.
All scenario dimensions/density/yields are assumptions, not measured properties.
"""
import math
def grain(R_mm=1.,r_mm=.7,h_mm=.6,rim_mm=.1,web_fraction=1/3,web_count=6,density=900.):
    assert 0<r_mm<R_mm and 0<2*rim_mm<h_mm and 0<web_fraction<=1
    area=math.pi*(R_mm**2-r_mm**2)
    volume=area*(2*rim_mm+(h_mm-2*rim_mm)*web_fraction)
    blank=area*h_mm
    return dict(R_mm=R_mm,r_mm=r_mm,h_mm=h_mm,rim_mm=rim_mm,
        web_fraction=web_fraction,web_count=web_count,
        web_angle_deg=360*web_fraction/web_count,
        window_angle_deg=360*(1-web_fraction)/web_count,
        volume_mm3=volume,blank_volume_mm3=blank,
        mass_kg=volume*1e-9*density,
        envelope_solid_fraction=volume/(math.pi*R_mm**2*h_mm),
        machining_yield=volume/blank)
def spray_rate(feed_ml_min,solids_g_ml):
    return feed_ml_min*solids_g_ml*60/1000
def feed_water_per_kg(solids_g_ml,solution_density_kg_L=1.):
    return solution_density_kg_L/solids_g_ml-1
def heat_kWh(water_kg,latent_kJ_kg=2400.):
    return water_kg*latent_kJ_kg/3600
def production(mass_kg,hours,g,quality=.8,stream_g_min=.5,streams=69,recovery=0.):
    eta=g['machining_yield']*quality
    processed=mass_kg/eta
    virgin=processed-recovery*(processed-mass_kg)
    head_kg_h=stream_g_min*streams*60/1000
    pieces=mass_kg/g['mass_kg']
    return dict(quality_yield=quality,recovery_fraction=recovery,processed_kg=processed,
        virgin_kg=virgin,nominal_head_kg_h=head_kg_h,
        equivalent_heads=processed/(hours*head_kg_h),
        finished_pieces=pieces,pieces_per_second=pieces/(hours*3600),
        window_features_per_second=g['web_count']*pieces/(hours*3600),
        window_features_before_quality_per_second=g['web_count']*pieces/(hours*3600*quality))
def contains(x,y,z,g):
    rad=math.hypot(x,y)
    if not(g['r_mm']<=rad<=g['R_mm'] and 0<=z<=g['h_mm']):return False
    if z<=g['rim_mm'] or z>=g['h_mm']-g['rim_mm']:return True
    period=2*math.pi/g['web_count']
    angle=(math.atan2(y,x)+period/2)%period-period/2
    return abs(angle)<=period*g['web_fraction']/2
