"""PBS process-inventory and morphology-index diagnostics, not a production recipe.
Reuses mixture and schedule accounting from cycle128.
"""
import math
from formation_conditioning import mixture,schedule_minutes,positive

def recipe_balance(polymer_g,solvent_g,product_yield,recovery,heat_minutes,cool_minutes,
                   cp_polymer_kJ_kgK=2,cp_solvent_kJ_kgK=2,feed_C=30,heat_C=120):
    positive(polymer_g);positive(solvent_g)
    if not all(math.isfinite(x) for x in [product_yield,recovery]) or not 0<product_yield<=1 or not 0<=recovery<=1:
        raise ValueError("yield in (0,1], recovery in [0,1]")
    for x in [cp_polymer_kJ_kgK,cp_solvent_kJ_kgK]:positive(x)
    if not math.isfinite(feed_C) or not math.isfinite(heat_C) or heat_C<feed_C:raise ValueError("invalid heating temperatures")
    m=mixture(polymer_g,{'mother_solvent':solvent_g});s=solvent_g/polymer_g;y=product_yield
    heat=(cp_polymer_kJ_kgK+cp_solvent_kJ_kgK*s)*(heat_C-feed_C)/y/3600
    return dict(polymer_fraction=m['polymer_fraction'],wet_charge_kg_per_kg_product=(1+s)/y,
      polymer_feed_kg_per_kg_product=1/y,not_product_polymer_kg_per_kg_product=(1-y)/y,
      solvent_charge_kg_per_kg_product=s/y,solvent_recovered_kg_per_kg_product=s*recovery/y,
      fresh_solvent_kg_per_kg_product=s*(1-recovery)/y,
      sensible_heat_only_kWh_per_kg_product=heat,
      specified_hold_and_cool=schedule_minutes({'hold':heat_minutes,'cool':cool_minutes}),
      total_batch_time_h=None,final_residual_solvent_ppm=None)

def recovery_budget(solvent_per_polymer,solvent_to_polymer_price,budget_fraction):
    positive(solvent_per_polymer);positive(solvent_to_polymer_price)
    if not math.isfinite(budget_fraction) or budget_fraction<0:raise ValueError("invalid cost budget")
    return max(0.,1-budget_fraction/(solvent_per_polymer*solvent_to_polymer_price))

def solid_oblate(equatorial_um,faceon_index,view_angle_deg):
    positive(equatorial_um)
    if not math.isfinite(faceon_index) or faceon_index<1 or not math.isfinite(view_angle_deg) or not 0<=view_angle_deg<=90:
        raise ValueError("oblate shape and angle required")
    D=equatorial_um;H=D/faceon_index**3;theta=math.radians(view_angle_deg)
    minor=math.sqrt(D*D*math.cos(theta)**2+H*H*math.sin(theta)**2)
    area=math.pi*D*minor/4;C=math.sqrt(4*area/math.pi)
    volume=math.pi*D*D*H/6;B=(6*volume/math.pi)**(1/3)
    return dict(equatorial_um=D,thickness_um=H,volume_um3=volume,projected_area_um2=area,
      image_equivalent_diameter_um=C,volume_equivalent_diameter_um=B,diameter_index=C/B,
      true_internal_void_fraction=0,incorrect_spherical_void_estimate=1-(B/C)**3)

def integrate_oblate_volume(D,H,n=100):
    """Independent Simpson integration of ellipsoid cross sections."""
    if n<2 or n%2:raise ValueError("even positive subdivision")
    a=D/2;c=H/2;dz=2*c/n
    total=0.
    for i in range(n+1):
        z=-c+i*dz;area=math.pi*a*a*max(0.,1-(z/c)**2)
        total+=(1 if i in [0,n] else 4 if i%2 else 2)*area
    return total*dz/3
