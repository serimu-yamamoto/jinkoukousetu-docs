"""Conditional audit of formulation claims. No physical-performance or success prediction."""
from math import isfinite, radians, tan, prod
def positive(x):
    if not isfinite(x) or x <= 0:
        raise ValueError("finite positive value required")
    return x
def ideal_freezing_depression(solutes, water_kg, kf=1.86):
    """solutes: iterable of (mass_g, molecular_mass_g_per_mol); all dissolved, i=1."""
    n = sum(positive(g) / positive(mw) for g, mw in solutes)
    return positive(kf) * n / positive(water_kg)
def retained_water(water_mass_fraction, total_mass_loss_fraction):
    if not 0 < water_mass_fraction <= 1 or not 0 <= total_mass_loss_fraction <= water_mass_fraction:
        raise ValueError("loss must be entirely assignable to water")
    return 1 - total_mass_loss_fraction / water_mass_fraction
def shear_bound_kpa(cohesion_kpa, normal_stress_kpa, phi_degrees):
    if not 0 <= phi_degrees < 90:
        raise ValueError("friction angle out of range")
    return positive(cohesion_kpa) + positive(normal_stress_kpa) * tan(radians(phi_degrees))
def layer_mass_kg(area_m2, thickness_m, density_kg_m3):
    return positive(area_m2) * positive(thickness_m) * positive(density_kg_m3)
def replacement_cost_yen(daily_kg, operating_days, yen_per_kg):
    return positive(daily_kg) * positive(operating_days) * positive(yen_per_kg)
def closure_minutes(recovery_h, other_minutes=0):
    if other_minutes < 0:
        raise ValueError("nonnegative additional work")
    return positive(recovery_h) * 60 + other_minutes
def skin_friction_coefficient(wall_shear_pa, air_density_kg_m3, speed_m_s):
    return positive(wall_shear_pa) / (0.5 * positive(air_density_kg_m3) * positive(speed_m_s)**2)
def audit():
    # Supplier values: trehalose dihydrate 378.33 g/mol; betaine 117.1 g/mol.
    solutes=[(7,378.33),(2,117.1)]
    dt=ideal_freezing_depression(solutes,0.058)
    hydration_water_kg=(7/378.33)*2*18.01528/1000
    dt_hyd=ideal_freezing_depression(solutes,0.058+hydration_water_kg)
    shear={name:{"c_kpa":c,"reported_Sf_kpa":sf,
        "max_under_stated_sigma_phi_kpa":shear_bound_kpa(c,80,38),
        "compatible_if_same_linear_test":sf <= shear_bound_kpa(c,80,38)}
        for name,c,sf in [("I",46,145),("II",49.5,158),("III",39.2,122)]}
    result={
      "date":"2026-10-22",
      "status":"conditional arithmetic audit; not a validated material model",
      "physical_trials":0,"physical_success_probability":None,
      "grid_count_only":prod([3,5,4,4,6]),
      "freezing":{"assumptions":"all nominal trehalose and betaine dissolved, ideal i=1, no other solutes; no measured activity or extract dilution",
        "basis_g":100,"trehalose_dihydrate_g":7,"betaine_g":2,"nominal_water_g":58,
        "molecular_weights_g_mol":[378.33,117.1],"kf_K_kg_mol":1.86,
        "nominal_water_only_K":dt,"including_dihydrate_water_K":dt_hyd,
        "effective_fraction_limit_for_0_0004_K_same_water":0.0004/dt_hyd,
        "effective_fraction_limit_for_0_01_K_same_water":0.01/dt_hyd},
      "water_denominator":{"water_mass_fraction":0.58,"limiting_total_mass_loss_fraction":0.12,
        "retention_at_boundary_if_only_water_lost":retained_water(.58,.12),
        "note":"12% is a strict total-mass-loss threshold; retention approaches this boundary from above, not a 91.8% guarantee"},
      "shear":shear,
      "closure":{"user_limit_min":60,"recovery_min_without_other_work":[closure_minutes(1.5),closure_minutes(4)]},
      "wind":{"rho_assumed_kg_m3":1.2,"U_claim_m_s":80,"tau_claim_Pa":12,
        "Cf_required":skin_friction_coefficient(12,1.2,80),
        "note":"not a validated conversion; requires roughness, wind profile and terrain"},
      "inventory":{"assumed_area_m2":10000,"density_claim_kg_m3":488,
        "mass_kg_250mm":layer_mass_kg(10000,.25,488),
        "mass_kg_450mm":layer_mass_kg(10000,.45,488),
        "mass_kg_at_3pct_runoff_250mm":.03*layer_mass_kg(10000,.25,488),
        "replacement_sensitivity":{"daily_kg_claim_limit":1000,"operating_days_assumed":120,
        "assumed_yen_per_kg":[100,300,1000],
        "annual_material_yen":[replacement_cost_yen(1000,120,p) for p in [100,300,1000]],
        "note":"hypothetical wet-material prices, not quotes; excludes recovery, energy, labor and disposal"}}}
    checks={
      "zero_mass_loss_retains_all_water":retained_water(.58,0)==1,
      "all_water_loss_retains_none":retained_water(.58,.58)==0,
      "shear_zero_angle_equals_cohesion":shear_bound_kpa(46,80,0)==46,
      "dilution_halves_ideal_depression":abs(ideal_freezing_depression(solutes,.116)*2-dt)<1e-12,
      "hydration_water_reduces_depression":dt_hyd<dt,
      "grid_arithmetic":result["grid_count_only"]==1440,
      "all_reported_shear_above_stated_bound":all(not x["compatible_if_same_linear_test"] for x in shear.values()),
      "shortest_recovery_exceeds_closure":result["closure"]["recovery_min_without_other_work"][0]>60,
      "doubling_thickness_doubles_mass":layer_mass_kg(10000,.5,488)==2*result["inventory"]["mass_kg_250mm"]}
    assert all(checks.values()),checks
    result["arithmetic_boundary_checks"]=checks
    return result
if __name__=="__main__":
    import json
    print(json.dumps(audit(),ensure_ascii=False,indent=2))
