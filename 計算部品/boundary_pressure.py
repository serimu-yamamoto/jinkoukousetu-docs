"""Identifiability counterexamples for nominal versus local pressure."""
import math
def nominal_response(pressure_pa,internal_mu,intrinsic_c_pa,wall_pressure_gain,wall_pressure_offset_pa):
    x=[pressure_pa,internal_mu,intrinsic_c_pa,wall_pressure_gain,wall_pressure_offset_pa]
    if not all(math.isfinite(v) for v in x) or min(x)<0:raise ValueError("Nonnegative finite diagnostic inputs required")
    local=pressure_pa*(1+wall_pressure_gain)+wall_pressure_offset_pa
    return dict(nominal_pressure_pa=pressure_pa,local_pressure_pa_assumed=local,
       shear_stress_pa=internal_mu*local+intrinsic_c_pa,
       apparent_slope=internal_mu*(1+wall_pressure_gain),
       apparent_intercept_pa=intrinsic_c_pa+internal_mu*wall_pressure_offset_pa)
def cylindrical_wall_pressure(diameter_m,engaged_height_m,wall_shear_pa):
    if not all(math.isfinite(v) for v in [diameter_m,engaged_height_m,wall_shear_pa]) or diameter_m<=0 or min(engaged_height_m,wall_shear_pa)<0:
        raise ValueError("Invalid cylinder inputs")
    force=math.pi*diameter_m*engaged_height_m*wall_shear_pa
    area=math.pi*diameter_m**2/4
    return dict(diameter_m=diameter_m,engaged_height_m_assumed=engaged_height_m,wall_shear_pa_assumed=wall_shear_pa,
      wall_force_N=force,cross_section_area_m2=area,pressure_offset_pa=force/area)
def gravity_pressure(bulk_density_kg_m3,normal_depth_m,slope_deg,g=9.8):
    if not all(math.isfinite(v) for v in [bulk_density_kg_m3,normal_depth_m,slope_deg,g]) or bulk_density_kg_m3<=0 or normal_depth_m<0 or not 0<=slope_deg<90 or g<=0:raise ValueError("Invalid slope inputs")
    return bulk_density_kg_m3*g*normal_depth_m*math.cos(math.radians(slope_deg))
