"""Mass/volume conversion and inclusion scales, not a tribology predictor."""
import math
def mixture(w,rho_matrix,rho_additive):
    if not math.isfinite(w) or not 0<=w<=1 or not all(math.isfinite(x) and x>0 for x in [rho_matrix,rho_additive]):raise ValueError("Invalid composition")
    v0=(1-w)/rho_matrix;v1=w/rho_additive
    return dict(additive_mass_fraction=w,additive_volume_fraction=v1/(v0+v1),ideal_density_kg_m3=1/(v0+v1))
def replacement_inventory(reference_mass,reference_density,compound_volume_fraction,compound_density,additive_mass_fraction,throughput):
    if not all(math.isfinite(x) and x>0 for x in [reference_mass,reference_density,compound_density,throughput]):raise ValueError("Invalid mass density or throughput")
    if not 0<=compound_volume_fraction<=1 or not 0<=additive_mass_fraction<=1:raise ValueError("Invalid fraction")
    v=reference_mass/reference_density;mc=v*compound_volume_fraction*compound_density;mr=reference_mass*(1-compound_volume_fraction)
    return dict(retained_reference_kg=mr,removed_reference_kg=reference_mass*compound_volume_fraction,compound_kg=mc,
        total_kg=mr+mc,additive_kg=mc*additive_mass_fraction,additive_whole_grain_mass_fraction=mc*additive_mass_fraction/(mr+mc),
        lab_throughput_equivalent_h=mc/throughput)
def source_comparison(before,after):
    if not all(math.isfinite(x) and x>0 for x in [before,after]):raise ValueError("Positive measured numbers required")
    return dict(after_over_before=after/before,reduction_fraction=1-after/before)
def inclusion_scale(thickness_um,diameter_um):
    if not all(math.isfinite(x) and x>0 for x in [thickness_um,diameter_um]):raise ValueError("Positive dimensions required")
    return dict(thickness_um=thickness_um,diameter_um=diameter_um,diameters_across=thickness_um/diameter_um,
        centered_cover_each_side_um=max(0,(thickness_um-diameter_um)/2),fits_single_sphere=diameter_um<=thickness_um)
