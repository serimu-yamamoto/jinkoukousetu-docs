"""Geometric screening, not contact mechanics or material success."""
import math
def geometry(length_nm,thickness_nm,angle_deg,recess_nm,rim_rise_nm=0,continuous_cover=False):
    if not all(math.isfinite(v) for v in [length_nm,thickness_nm,angle_deg,recess_nm,rim_rise_nm]):
        raise ValueError("Finite geometry required")
    if length_nm<=0 or thickness_nm<=0 or not 0<=angle_deg<=90 or recess_nm<0:
        raise ValueError("Invalid geometry")
    a=math.radians(angle_deg);span=length_nm*math.sin(a)+thickness_nm*math.cos(a)
    h=span-recess_nm-rim_rise_nm
    return dict(length_nm=length_nm,thickness_nm=thickness_nm,angle_deg=angle_deg,recess_nm=recess_nm,
       rim_rise_nm=rim_rise_nm,continuous_cover=continuous_cover,vertical_extent_nm=span,
       protrusion_above_rim_nm=h,projected_broad_face_area_ratio=math.cos(a),
       geometrically_exposed=h>0 and not continuous_cover)
def robust_height_window(limit_nm,uncertainty_nm):
    if not all(math.isfinite(x) for x in [limit_nm,uncertainty_nm]) or limit_nm<=0 or uncertainty_nm<0:
        raise ValueError("Invalid tolerance")
    return dict(limit_nm_assumed=limit_nm,uncertainty_nm_assumed=uncertainty_nm,
      nominal_height_lower_exclusive_nm=uncertainty_nm,
      nominal_height_upper_inclusive_nm=limit_nm-uncertainty_nm,
      interval_nonempty=2*uncertainty_nm<limit_nm)
def rework_inventory(retained_target_kg,accepted_fraction,rework_recovery_fraction):
    if not math.isfinite(retained_target_kg) or retained_target_kg<=0 or not 0<accepted_fraction<=1 or not 0<=rework_recovery_fraction<=1:
        raise ValueError("Invalid yields")
    feed=retained_target_kg/accepted_fraction;reject=feed-retained_target_kg
    return dict(target_kg=retained_target_kg,accepted_fraction_assumed=accepted_fraction,
      recovery_fraction_assumed=rework_recovery_fraction,total_application_throughput_kg=feed,
      rejected_throughput_kg=reject,recovered_for_rework_kg=reject*rework_recovery_fraction,
      steady_state_fresh_input_kg=feed-reject*rework_recovery_fraction,
      final_unrecovered_loss_kg=reject*(1-rework_recovery_fraction),
      scope="Steady-state balance only; no reuse degradation. First-batch inventory and startup feed may be higher.")
