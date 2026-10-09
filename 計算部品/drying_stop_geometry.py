"""Geometric diagnostics only; no drying mechanics or ski performance prediction."""
import math
def positive(*values):
    if not all(math.isfinite(v) and v>0 for v in values):
        raise ValueError("finite positive values required")
def shape_ratios(initial,final):
    if len(initial)!=3 or len(final)!=3:raise ValueError("three dimensions required")
    positive(*initial,*final)
    ratios=[b/a for a,b in zip(initial,final)]
    return dict(axis_ratios=ratios,xy_projected_area_ratio=ratios[0]*ratios[1],
                ellipsoid_envelope_volume_ratio=math.prod(ratios),
                note="same ellipsoid shape factor; not solid volume or measured packing")
def stop_geometry(width_m,length_m,plate_thickness_m,gap_m,post_radius_m,post_height_m,posts_per_face):
    positive(width_m,length_m,plate_thickness_m,gap_m,post_radius_m,post_height_m)
    if type(posts_per_face) is not int or posts_per_face<1:raise ValueError("integer post count required")
    if 2*post_height_m>=gap_m:raise ValueError("initial clearance required")
    if 2*post_radius_m>=min(width_m,length_m):raise ValueError("post wider than patch")
    patch=width_m*length_m
    area=posts_per_face*math.pi*post_radius_m**2
    if area>=patch:raise ValueError("post area exceeds patch")
    base=2*patch*plate_thickness_m
    added=2*area*post_height_m
    return dict(remaining_gap_at_first_contact_m=2*post_height_m,
      closure_before_first_contact_m=gap_m-2*post_height_m,
      ideal_remaining_gap_fraction=2*post_height_m/gap_m,
      contact_area_m2=area,reference_patch_area_m2=patch,
      nominal_stop_stress_multiplier=patch/area,
      added_solid_volume_m3=added,reference_plate_volume_m3=base,
      local_added_solid_fraction=added/base,
      assumptions="aligned circular rigid posts; all share load; same density; no deformation, holes, flow, adhesion or process waste")
def mass_increment(base_kg,local_base_mass_fraction,local_added_fraction):
    positive(base_kg)
    if not math.isfinite(local_base_mass_fraction) or not 0<=local_base_mass_fraction<=1:raise ValueError("invalid local fraction")
    if not math.isfinite(local_added_fraction) or local_added_fraction<0:raise ValueError("invalid increment")
    add=base_kg*local_base_mass_fraction*local_added_fraction
    return dict(added_kg=add,total_kg=base_kg+add,per_yen_per_kg_increment_yen=add)
