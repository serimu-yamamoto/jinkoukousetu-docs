"""Dimensionless beam/material screening; no calibrated 50 C material law."""
import math
def positive(*xs):
    if not all(math.isfinite(x) and x>0 for x in xs):raise ValueError("finite positive values required")
def same_bending(e_ratio,rho_ratio,price_ratio=1):
    positive(e_ratio,rho_ratio,price_ratio)
    t=e_ratio**(-1/3)
    return dict(thickness_ratio=t,stiffness_ratio=e_ratio*t**3,
        mass_ratio=rho_ratio*t,stress_ratio=1/t**2,strain_ratio=1/(t*t*e_ratio),
        raw_cost_ratio=rho_ratio*t*price_ratio,
        minimum_life_ratio_for_raw_replacement_parity=rho_ratio*t*price_ratio,
        price_ratio_for_initial_raw_parity=1/(rho_ratio*t))
def local_replacement(volume_fraction,rho_ratio,price_ratio=1):
    positive(rho_ratio,price_ratio)
    if not math.isfinite(volume_fraction) or not 0<=volume_fraction<=1:raise ValueError("fraction outside [0,1]")
    return dict(volume_fraction=volume_fraction,mass_ratio=1-volume_fraction+volume_fraction*rho_ratio,
        raw_cost_ratio=1-volume_fraction+volume_fraction*rho_ratio*price_ratio)
def annual_raw_ratio(initial_raw_ratio,life_ratio):
    positive(initial_raw_ratio,life_ratio)
    return initial_raw_ratio/life_ratio
def mass_budget(area_m2,depth_m,bulk_density_kg_m3,reference_price_yen_kg):
    positive(area_m2,depth_m,bulk_density_kg_m3,reference_price_yen_kg)
    m=area_m2*depth_m*bulk_density_kg_m3
    return dict(reference_mass_kg=m,reference_raw_yen=m*reference_price_yen_kg)
