"""Independent deterministic checks. Hypotheses are not measured properties.
Python 3 standard library only; no Monte Carlo success probabilities.
Run from the repository root. Writes one JSON result beside this script.
"""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
G = 9.81
BETA = math.radians(30)
SIGMA = 5.670374419e-8


def dry_temperature(albedo, h, air_c=35.0, solar=1000.0, sky_emissivity=0.9):
    # Flat local energy balance with irradiance on the actual slope surface.
    # No evaporative or ground heat sink; this is a conditional sensitivity case.
    def residual(t):
        return (solar * (1 - albedo)
                + sky_emissivity * SIGMA * (air_c + 273.15) ** 4
                - 0.95 * SIGMA * (t + 273.15) ** 4 - h * (t - air_c))
    lo, hi = air_c - 30, air_c + 100
    assert residual(lo) > 0 > residual(hi)
    for _ in range(80):
        mid = (lo + hi) / 2
        if residual(mid) > 0:
            lo = mid
        else:
            hi = mid
    t = (lo + hi) / 2
    assert abs(residual(t)) < 1e-7
    return {"albedo_assumed": albedo, "h_W_m2K_assumed": h,
            "air_C_assumed": air_c, "surface_C": t,
            "heat_to_remove_at_50C_W_m2": max(0.0, residual(50)),
            "evap_at_50C_kg_m2_h": max(0.0, residual(50)) * 3600 / 2.45e6}


def slope_cohesion(rho_d=1674.0, rho_s=2710.0, phi_deg=35.0,
                   thickness_normal=0.45, factor=1.5):
    # Infinite slope with saturated parallel seepage. Thickness is NORMAL to slope.
    por = 1 - rho_d / rho_s
    gamma = (rho_d + por * 1000) * G
    phi = math.radians(phi_deg)
    shear = gamma * thickness_normal * math.sin(BETA)
    effective_normal = (gamma - 1000 * G) * thickness_normal * math.cos(BETA)
    required = max(0.0, factor * shear - effective_normal * math.tan(phi))
    return {"phi_deg_assumed": phi_deg, "porosity": por,
            "cohesion_required_kPa_normal_450mm": required / 1000,
            "cohesion_kPa_if_450mm_is_vertical": required * math.cos(BETA) / 1000}


def vt3_replica(evaporation_factor=1.0, dt=10.0):
    """North-facing, 3 vol-% target every 5 min; mirrors vt3.py assumptions.
    Scale the UNMEASURED evaporative availability without tuning to a target.
    """
    lat, dec = math.radians(36), math.radians(21)
    dz, por, c_dry, h = 0.005, 0.382, 1674 * 840 * 0.005, 13.3
    t, next_pulse, surface, below, theta = 21600.0, 30600.0, 25.0, 25.0, 0.0
    water_mm, observations = 0.0, []
    es = lambda temp: 0.6108 * math.exp(17.27 * temp / (temp + 237.3))
    while t < 61200:
        hr = t / 3600
        ha = math.radians(15 * (hr - 12))
        se = math.sin(lat) * math.sin(dec) + math.cos(lat) * math.cos(dec) * math.cos(ha)
        elevation = math.asin(max(se, 0))
        az = math.pi + math.atan2(math.sin(ha), math.cos(ha)*math.sin(lat)-math.tan(dec)*math.cos(lat))
        ci = math.sin(elevation)*math.cos(BETA)+math.cos(elevation)*math.sin(BETA)*math.cos(az)
        gh = 1000 * math.sin(elevation) ** 1.15 if elevation > 0 else 0
        solar = (0.8*gh/math.sin(elevation)*max(ci,0)+0.2*gh*(1+math.cos(BETA))/2) if elevation > 0 else 0
        air = 26.5 + 4.5 * math.sin(math.pi * (hr - 8) / 12)
        rh = min(0.9, max(0.4, 0.75 - 0.25*math.sin(math.pi*(hr-8)/12)))
        if t >= next_pulse:
            add = max(0.03 - theta, 0) * dz * 1000
            theta += add / 1000 / dz
            water_mm += add
            next_pulse += 300
        if theta > 0.06:
            theta = 0.06 + (theta - 0.06) * math.exp(-dt/600)
        demand = max(h/1005*0.622/101.3*(es(surface)-rh*es(air)), 0)
        availability = min(1, max(0, (theta-0.005)/0.02)) * evaporation_factor
        evap = demand * availability
        albedo = 0.35 if theta > 0.02 else 0.55
        # Use exactly the original rounded Stefan-Boltzmann constant here.
        q = solar*(1-albedo)+0.85*5.67e-8*(air+273.15)**4-0.95*5.67e-8*(surface+273.15)**4-h*(surface-air)-evap*2.45e6-16*(surface-below)
        surface += q*dt/(c_dry+theta*dz*4.18e6)
        below += 16*(surface-below)*dt/(1674*840*0.05)
        theta = max(theta - evap*dt/1000/dz, 0)
        if hr >= 9:
            observations.append(surface)
        t += dt
    return {"evaporation_factor_assumed": evaporation_factor, "dt_s": dt,
            "surface_max_C": max(observations),
            "water_t_day_at_70pct_efficiency": water_mm*2000/1000/0.7}


def vt5_vt6_checks():
    """Audit specified VT5/VT6 assumptions; no physical success probabilities."""
    area, depth, rho_d, por = 2000.0, 0.005, 1674.0, 0.382
    layer_mass = area * depth * rho_d
    deposit = layer_mass * 0.001
    lime = deposit * 74.09 / 100.09
    co2 = deposit * 44.01 / 100.09
    # 1.6 g/L = 1.6 kg/m3, with perfect retention and conversion assumed.
    water_m3 = lime / 1.6
    data = {
        "VT5_mean_pressure_N_mm2_assumed": 1400 / 0.168 / 1e6,
        "VT5_distance_m_per_season_assumed": 30000 * 100,
        "VT5_allowed_specific_wear_mm3_Nm": {},
        "VT6_porosity_assumed": por,
        "VT6_extra_Rumpf_factor": 1 / por,
        "VT6_corrected_tensile_estimate_from_report_kPa_not_cohesion": [x * por for x in (68, 101)],
        "VT6_surface_layer_mass_kg": layer_mass,
        "VT6_CaCO3_deposit_kg_per_day_assumed": deposit,
        "VT6_CaOH2_required_kg": lime,
        "VT6_CO2_required_kg": co2,
        "VT6_limewater_m3_min_at_perfect_retention": water_m3,
        "VT6_limewater_L_m2": water_m3 * 1000 / area,
        "VT6_surface_pore_capacity_L_m2": depth * por * 1000,
        "VT6_dose_over_pore_volume": water_m3 / (area * depth * por),
        "VT6_CaCO3_added_kg_after_100days_no_export": deposit * 100,
        "VT6_added_fraction_of_surface_layer_after_100days": deposit * 100 / layer_mass,
        "VT6_ideal_freezing_depression_K_of_unreacted_feed": 1.86 * 3 * 1.6 / 74.09,
        "VT6_ideal_gas_supply_hours_NOT_reaction_completion": [],
    }
    for target_um in (100, 500):
        data["VT5_allowed_specific_wear_mm3_Nm"][str(target_um)] = target_um / (
            data["VT5_mean_pressure_N_mm2_assumed"] * 30000 * 100 * 1000)
    for hm in (0.003, 0.01):
        for deff in (1e-6, 3e-6):
            co2_air_g_m3 = 0.75
            flux_g_m2_s = 1 / (1 / (hm * co2_air_g_m3)
                                + 0.0025 / (deff * co2_air_g_m3))
            data["VT6_ideal_gas_supply_hours_NOT_reaction_completion"].append({
                "hm_m_s_assumed": hm, "Deff_m2_s_assumed": deff,
                "hours": co2 * 1000 / area / flux_g_m2_s / 3600})
    return data


def storm_recovery_checks():
    """Screen transport and recovery budgets, not a calibrated erosion model."""
    area, depth = 2000.0, 0.45
    volume = area * depth
    data = {
        "rain_horizontal_mm_h_assumed": 100,
        "rain_on_slope_m3_h_no_external_catchment": 0.1 * area * math.cos(BETA),
        "VT7_rain30mm_on_slope_m3": 0.03 * area * math.cos(BETA),
        "VT7_CaCO3_kg_if_50mg_L_is_assumed": 0.03 * area * math.cos(BETA) * 0.05,
        "surface_water_shear_cases": [],
        "noncohesive_calcite_reference_Pa_NOT_bonded_grain_threshold": [
            theta * (2710 - 1000) * G * 0.001 for theta in (0.03, 0.06)],
        "transport_cases": [],
        "recovery_mass_cases": [],
        "uphill_push_cases": [],
    }
    for h_mm in (1, 3, 10):
        tau = 1000 * G * h_mm / 1000 * math.sin(BETA)
        data["surface_water_shear_cases"].append({"flow_depth_normal_mm_assumed": h_mm,
            "steady_uniform_water_shear_Pa": tau, "screening_threshold_Pa_at_factor1p5": 1.5 * tau})
    # Effective delivery includes fill/spill/bulking; not a manufacturer's rating.
    # Distance is an assumed MEAN one-way uphill delivery distance.
    cycle_s = 50 / 0.8 + 50 / 1.2 + 60
    data["transport_assumptions"] = {"mean_distance_m": 50, "uphill_m_s": 0.8,
        "downhill_m_s": 1.2, "load_dump_turn_s": 60, "utilization": 0.6,
        "cycle_seconds": cycle_s, "bed_volume_m3": volume}
    for q in (0.5, 1.5, 3.0):
        for displaced_fraction in (0.01, 0.05, 0.10, 0.30):
            moved = volume * displaced_fraction
            trips = math.ceil(moved / q)
            hours = trips * cycle_s / 0.6 / 3600
            data["transport_cases"].append({"effective_delivery_m3_per_trip_assumed": q,
                "displaced_fraction_assumed": displaced_fraction, "volume_m3": moved,
                "trips": trips, "transport_only_hours": hours})
    rate = 1.5 * 3600 * 0.6 / cycle_s
    data["maximum_displaced_fraction_for_2h_transport_budget_at_q1p5"] = rate * 2 / volume
    long_cycle = 500 / 0.8 + 500 / 1.2 + 60
    data["one_km_course_sensitivity_NOT_field_prediction"] = []
    for bed_depth in (0.30, 0.45):
        for displaced_fraction in (0.01, 0.10):
            moved = 1000 * 40 * bed_depth * displaced_fraction
            trips = math.ceil(moved / 1.5)
            data["one_km_course_sensitivity_NOT_field_prediction"].append({
                "depth_m_assumed": bed_depth, "displaced_fraction_assumed": displaced_fraction,
                "volume_m3": moved, "mean_return_distance_m_assumed": 500,
                "trips": trips, "transport_only_hours": trips * long_cycle / 0.6 / 3600})
    for rho in (300, 1674):
        displaced_kg = volume * rho * 0.1
        for captured, reusable in ((0.99, 0.95), (0.90, 0.80)):
            recovered = displaced_kg * captured * reusable
            rejected = displaced_kg * captured * (1 - reusable)
            escaped = displaced_kg * (1 - captured)
            assert math.isclose(displaced_kg, recovered + rejected + escaped)
            data["recovery_mass_cases"].append({"dry_density_kg_m3_assumed": rho,
                "displaced_kg": displaced_kg, "capture_fraction_assumed": captured,
                "reusable_fraction_of_capture_assumed": reusable,
                "reusable_kg": recovered, "captured_reject_kg": rejected,
                "uncaptured_kg": escaped, "new_material_required_kg": rejected + escaped})
        vehicle_mass, q, rolling, push_mu, winch = 13490.0, 1.5, 0.05, 0.5, 45000.0
        normal = vehicle_mass * G * math.cos(BETA)
        vehicle_grade = vehicle_mass * G * math.sin(BETA)
        material_push = q * rho * G * (math.sin(BETA) + push_mu * math.cos(BETA))
        force = vehicle_grade + rolling * normal + material_push
        data["uphill_push_cases"].append({"dry_density_kg_m3_assumed": rho,
            "pushed_volume_m3_assumed": q, "material_mass_kg": q * rho,
            "vehicle_mass_kg_example": vehicle_mass,
            "vehicle_grade_force_kN": vehicle_grade / 1000,
            "rolling_coefficient_assumed": rolling, "material_slide_coefficient_assumed": push_mu,
            "material_push_kN_simple_model": material_push / 1000,
            "total_tractive_force_kN_excluding_cutting_tiller": force / 1000,
            "winch_force_kN_ideal_along_slope": winch / 1000,
            "track_traction_ratio_required_no_safety_factor": (force - winch) / normal})
    return data


def design_checks():
    af = (1 - 1.08 ** -10) / 0.08
    financial_numerator = (19e6 - 4e6) * af - 20e6
    data = {
        "status": "calculations only; all new material properties below are assumptions",
        "baseline_git_revision": "06c70ed",
        "additional_VT5_VT6_git_revision": "b8458e2",
        "additional_VT7_git_revision": "0bdff45",
        "additional_VT8_git_revision": "71b8210",
        "source_hash_basis": "UTF-8 text normalized to LF line endings",
        "units": "SI except explicitly labelled fields",
        "source_code_sha256": {},
        "slope": [slope_cohesion(phi_deg=p) for p in (30, 35, 40)],
        "dry_heat_sensitivity": [dry_temperature(a, h)
                                 for a in (0.35, 0.55, 0.85, 0.95)
                                 for h in (5.7, 13.3)],
        "annualized_material_budget": [],
        "thermal_storage": [],
        "mechanical_power": [],
        "mossner_geometry_example": [],
        "wind": [],
        "hierarchical_grain_modulus_sensitivity": [],
        "VT3_assumption_sensitivity": [vt3_replica(f) for f in (1.0, 0.3, 0.1)],
        "VT3_time_step_check": vt3_replica(1.0, 5.0),
        "neck_stress_sensitivity": [],
        "VT5_VT6_audit": vt5_vt6_checks(),
        "storm_recovery_audit": storm_recovery_checks(),
        "winter_interface_example": {
            "snow_density_kg_m3_assumed": 300,
            "snow_depth_NORMAL_m_assumed": 1,
            "downslope_shear_kPa": 300 * G * math.sin(BETA) / 1000,
            "normal_stress_kPa": 300 * G * math.cos(BETA) / 1000,
            "required_total_interface_resistance_kPa_at_FS1p5": 1.5 * 300 * G * math.sin(BETA) / 1000,
        },
    }
    for name in ("vt1.py", "vt2a.py", "vt2bcd.py", "vt3.py", "vt4.py", "vt5.py", "vt6.py", "vt7.py", "vt8.py"):
        source_path = ROOT / "バーチャル試験" / name
        data["source_code_sha256"][name] = (hashlib.sha256(source_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
                                                if source_path.exists() else "source unavailable")
    for rho in (200, 300, 500, 1674):
        mass = rho * 2000 * 0.45
        pmax = financial_numerator / (mass * (1 + 0.1 * af))
        data["annualized_material_budget"].append({
            "dry_bulk_density_assumed_kg_m3": rho, "mass_kg": mass,
            "pmax_yen_kg_at_old_B_I_O_lambda": pmax,
            "max_initial_material_yen_m2": pmax * mass / 2000,
        })
    for label, rho, cp in (("HBG5_dry_assumed", 1674, 840),
                           ("porous_candidate_assumed", 300, 1500)):
        for delta in (10, 30):
            q = rho * 0.45 * cp * delta
            data["thermal_storage"].append({"case": label, "cooling_delta_K": delta,
                "stored_sensible_MJ_m2": q / 1e6,
                "melt_equivalent_kg_m2_if_all_heat_enters_snow": q / 334000})
    normal = 80 * G * math.cos(BETA)
    for mu in (0.05, 0.10):
        for speed in (2, 10, 20):
            data["mechanical_power"].append({"mu_assumed": mu, "speed_m_s": speed,
                "normal_force_N": normal, "interface_dissipation_W": mu * normal * speed})
    # Derive geometry from F=HV*V, not from elastic modulus.
    for hv in (0.04, 0.16):
        force, length, width = 490.5, 200.0, 62.0  # N, mm, mm
        e_flat = force / (hv * length * width)
        e_45 = math.sqrt(2 * force / (hv * length))
        assert e_45 < width * math.sin(math.pi / 4)
        data["mossner_geometry_example"].append({"HV_N_mm3_assumed": hv,
            "force_N": force, "flat_penetration_mm": e_flat,
            "edged_45deg_penetration_mm": e_45})
    # Weight only is an UPPER bound on available whole-bed lift resistance.
    # A bed's whole weight is not automatically mobilized by surface-grain suction.
    wind_q = 0.5 * 1.2 * 80 ** 2
    for rho in (200, 300, 500, 1674):
        weight_n = rho * 0.45 * G * math.cos(BETA)
        data["wind"].append({"rho_d_assumed_kg_m3": rho,
            "normal_weight_Pa": weight_n, "dynamic_pressure_at_80m_s_Pa": wind_q,
            "lift_margin_Pa_at_Cp1_no_factor": weight_n - wind_q})
    # Cellular-solid scaling describes an INDIVIDUAL porous grain, not a grain bed.
    for solid_e in (0.5e9, 2e9):
        for relative_density in (0.15, 0.3):
            for c_shape in (0.1, 1.0):
                data["hierarchical_grain_modulus_sensitivity"].append({
                    "solid_E_GPa_assumed": solid_e / 1e9,
                    "relative_density_assumed": relative_density,
                    "geometry_factor_assumed": c_shape,
                    "grain_E_MPa_screening_only": c_shape * solid_e * relative_density ** 2 / 1e6})
    data["water_storage"] = {"surface_depth_m": 0.005, "volumetric_water": 0.03,
        "water_kg_m2": 1000 * 0.005 * 0.03,
        "minutes_until_all_water_evaporates_at_0p6kg_m2h": 60 * 1000 * 0.005 * 0.03 / 0.6,
        "VT3_full_evap_assumption_water_fraction": 0.025}
    data["pva_replenishment"] = {
        "bed_area_m2": 2000, "coating_loss_um_day_assumed": 0.5,
        "exposed_surface_area_ratio_assumed": [2, 4],
        "kg_per_day": [2000 * 0.5e-6 * 1270 * a for a in (2, 4)],
        "kg_for_100days": [100 * 2000 * 0.5e-6 * 1270 * a for a in (2, 4)],
    }
    for ratio in (0.03, 0.06, 0.10):
        # Isotropic central-bond stress estimate: sigma=phi*Z*sigma_b*(a/d)^2.
        # This is NOT Mohr-Coulomb cohesion, snow Sf, or an achieved strength.
        data["neck_stress_sensitivity"].append({"neck_radius_over_grain_d_assumed": ratio,
            "packing_assumed": 0.6, "contacts_assumed": 6, "neck_material_strength_MPa_assumed": 1,
            "network_stress_kPa_estimate": 0.6 * 6 * 1e6 * ratio**2 / 1000})
    return data


if __name__ == "__main__":
    result = design_checks()
    output = Path(__file__).with_suffix(".json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Independent deterministic audit completed; no physical validation claimed.")
    print("Saturated slope c[kPa], NORMAL thickness 450mm:",
          [round(x["cohesion_required_kPa_normal_450mm"], 3) for x in result["slope"]])
    print("Dry surface C (albedo,h):", [(r["albedo_assumed"], r["h_W_m2K_assumed"],
          round(r["surface_C"], 2)) for r in result["dry_heat_sensitivity"]])
    print("Pmax yen/kg (density):", [(r["dry_bulk_density_assumed_kg_m3"],
          round(r["pmax_yen_kg_at_old_B_I_O_lambda"], 2))
          for r in result["annualized_material_budget"]])
    print("Snow geometry:", result["mossner_geometry_example"])
    print("VT5/VT6 audit:", result["VT5_VT6_audit"])
    print("JSON saved:", output.name)
