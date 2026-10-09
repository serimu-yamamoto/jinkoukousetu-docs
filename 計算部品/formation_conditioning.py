"""Process-stage, residual inventory and particle-size matching audit.
Facts and assumptions remain separate. No safety/performance or factory yield model.
"""
import math
def positive(x):
    if not math.isfinite(x) or x<=0:raise ValueError("positive finite required")
def size_match(d_m,d_s,base_additive_mass,base_carrier_mass):
    for x in (d_m,d_s,base_additive_mass,base_carrier_mass):positive(x)
    r=d_m/d_s
    area_mass=base_additive_mass/r
    count_mass=base_additive_mass/r**3
    return dict(diameter_ratio_M_over_S=r,number_ratio_S_over_M_same_mass=r**3,
                area_ratio_S_over_M_same_mass=r,
                S_mass_same_area=area_mass,S_mass_same_number=count_mass,
                source_mass_fraction=base_additive_mass/(base_additive_mass+base_carrier_mass),
                same_area_mass_fraction=area_mass/(area_mass+base_carrier_mass),
                same_number_mass_fraction=count_mass/(count_mass+base_carrier_mass))
def sphere_totals(mass,density,diameter):
    for x in (mass,density,diameter):positive(x)
    count=mass/(density*math.pi*diameter**3/6)
    return dict(number=count,area=count*math.pi*diameter**2)
def mixture(polymer,others):
    positive(polymer)
    if not others or any(not math.isfinite(x) or x<0 for x in others.values()):raise ValueError("invalid feed")
    total=polymer+sum(others.values())
    return dict(total=total,polymer_fraction=polymer/total,
                total_per_polymer=total/polymer,
                auxiliaries_per_polymer={k:v/polymer for k,v in others.items()})
def schedule_minutes(stages):
    if not stages or any(not math.isfinite(x) or x<0 for x in stages.values()):raise ValueError("invalid times")
    return dict(minutes=sum(stages.values()),hours=sum(stages.values())/60)
def residual_inventory(product_mass,ppm):
    if not math.isfinite(product_mass) or product_mass<0 or not math.isfinite(ppm) or not 0<=ppm<=1e6:raise ValueError("invalid mass or ppm")
    return product_mass*ppm/1e6
