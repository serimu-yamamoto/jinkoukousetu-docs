"""Cycle 9: ideal component comparisons, NOT experiments or a success probability.
Run with Python >=3.10, standard library only. Writes results.json beside this file.
Reproduces the public cycle-8 clip path after a normalized-text SHA256 check.
"""
from pathlib import Path
import hashlib
import itertools
import json
import math

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
I = json.loads((HERE / "inputs.json").read_text(encoding="utf-8"))
R = json.loads((HERE / "reference_clip.json").read_text(encoding="utf-8"))
MU0 = I["mu0_H_m"]
M = I["magnetic"]
COST = I["cost"]
UM = 1e-6

def source_check():
    p = ROOT / R["source_path"]
    if not p.exists():
        return {"available": False, "checked": False, "note": "Run in the full repository to verify the cycle-8 source."}
    b = p.read_text(encoding="utf-8").replace("\r\n", "\n").encode()
    digest = hashlib.sha256(b).hexdigest()
    assert digest == R["source_sha256_utf8_LF"], "Cycle-8 source hash differs"
    original = json.loads(b)["refined_reference"]["assembly"]
    assert len(original) == len(R["points"]), "Reference path length differs"
    radius = R["curve_radius_um"]*UM
    force_scale = R["material_E_MPa"]*1e6*(R["strip_width_um"]*UM)*(R["strip_thickness_um"]*UM)**3/(12*radius**2)
    for old, copied in zip(original,R["points"]):
        assert math.isclose(copied["u_m"],(original[0]["y0"]-old["y0"])*radius,abs_tol=1e-18), "Displacement conversion differs"
        assert math.isclose(copied["F_N"],old["F"]*force_scale,abs_tol=1e-18), "Force conversion differs"
    return {"available": True, "checked": True, "sha256_utf8_LF": digest, "path_conversion_checked": True, "derived_force_scale_N": force_scale}

def moment(radius_m, polarization_T):
    return polarization_T / MU0 * 4 * math.pi * radius_m**3 / 3

def pair_force(radius_um, B, distance_m):
    return 3 * MU0 * moment(radius_um*UM, B)**2 / (2*math.pi*distance_m**4)

def pair_energy(radius_um, B, distance_m):
    return -MU0 * moment(radius_um*UM, B)**2 / (2*math.pi*distance_m**3)

def hybrid(radius_um, cover_um, width_um, thickness_um, E_MPa, B, with_path=False):
    scale = width_um/R["strip_width_um"] * (thickness_um/R["strip_thickness_um"])**3 * E_MPa/R["material_E_MPa"]
    d_final = 2*(radius_um + cover_um)*UM
    u_end = R["points"][-1]["u_m"]
    path = []
    bcrit = 0
    for p in R["points"]:
        d = d_final + u_end - p["u_m"]
        fc = p["F_N"] * scale
        fm = pair_force(radius_um, B, d)
        bcrit = max(bcrit, math.sqrt(max(fc, 0)/pair_force(radius_um, 1, d)))
        path.append({"u_um": p["u_m"]/UM, "d_um": d/UM, "clip_uN": fc/UM, "magnetic_uN": fm/UM,
                     "external_push_uN": (fc-fm)/UM})
    out = {"radius_um": radius_um, "cover_um": cover_um, "width_um": width_um,
           "thickness_um": thickness_um, "E_MPa": E_MPa, "effective_polarization_T": B,
           "max_external_push_uN": max(p["external_push_uN"] for p in path),
           "sampled_path_B_critical_T": bcrit,
           "final_magnetic_force_uN": pair_force(radius_um, B, d_final)/UM,
           "sample_count": len(path),
           "scope": "Registered two-body sliding-limit path; no dynamic capture, stability, field demagnetization or random contact geometry."}
    if with_path:
        out["path"] = path
    return out

def gamma_water(T_C):
    tau = 1 - (T_C+273.15)/647.096
    return .2358 * tau**1.256 * (1 - .625*tau)

def capillary_force(T_C, r_um, volume_ratio):
    assert 1e-6 <= volume_ratio <= .1
    return 2*math.pi*gamma_water(T_C)*r_um*UM*(1-.3823*volume_ratio**.2586)

def cost_case(radius_um, gate_width_um, fraction, magnet_price):
    c = COST
    V = c["area_m2"]*c["depth_m"]
    N = V*c["number_density_m3"]
    core_v_mm3 = 4*math.pi*(radius_um/1000)**3/3
    gate_v_mm3 = c["gate_reference_volume_mm3"]*gate_width_um/R["strip_width_um"]
    base = V*c["W2_bulk_kg_m3"]
    core_mass = N*fraction*core_v_mm3*1e-9*M["core_density_kg_m3"]
    removed = N*fraction*core_v_mm3*1e-9*c["matrix_density_kg_m3"]
    gate_mass = N*gate_v_mm3*1e-9*c["matrix_density_kg_m3"]
    matrix_mass = base - removed + gate_mass
    total_mass = matrix_mass+core_mass
    crf = c["discount"]*(1+c["discount"])**c["years"]/((1+c["discount"])**c["years"]-1)
    factor = crf+c["replacement"]
    fixed_eac = c["initial_other_JPY"]*crf+c["annual_other_JPY"]
    purchase = matrix_mass*c["assumed_price_JPY_kg"]+core_mass*magnet_price
    purchase_cap = (c["annual_budget_JPY"]-fixed_eac)/factor
    return {"radius_um": radius_um, "gate_width_um": gate_width_um, "magnetic_fraction": fraction,
            "magnet_price_assumption_JPY_kg": magnet_price, "bed_volume_m3": V,
            "core_volume_mm3": core_v_mm3, "gate_volume_mm3": gate_v_mm3,
            "base_mass_kg": base, "removed_matrix_mass_kg": removed, "gate_mass_kg": gate_mass,
            "remaining_matrix_plus_gate_kg": matrix_mass, "core_mass_kg": core_mass,
            "total_mass_kg": total_mass, "bulk_density_kg_m3": total_mass/V,
            "purchase_JPY": purchase, "annual_equivalent_JPY": fixed_eac+factor*purchase,
            "CRF": crf, "purchase_budget_JPY": purchase_cap,
            "finished_grain_price_cap_JPY_kg": purchase_cap/total_mass,
            "core_inclusive_processing_price_cap_JPY_kg": (purchase_cap-matrix_mass*c["assumed_price_JPY_kg"])/core_mass if core_mass else None,
            "remaining_one_time_processing_budget_JPY": purchase_cap-purchase,
            "ideal_random_mag_mag_contact_fraction": fraction**2,
            "scope": "Optimistic equal-volume core substitution; gates on every grain; no integrated geometry or added encapsulation volume. Prices are hypothetical, pretax."}

def calculate():
    provenance = source_check()
    default = hybrid(M["core_radius_um"], M["inner_cover_um"], M["gate_width_um"],
                     M["gate_thickness_um"], M["gate_E_MPa"], M["effective_polarization_T"], True)
    width_cases = [hybrid(M["core_radius_um"], M["inner_cover_um"], w, M["gate_thickness_um"],
                         M["gate_E_MPa"], M["effective_polarization_T"], True) for w in M["width_sweep_um"]]
    grid = [hybrid(r,c,w,M["gate_thickness_um"],M["gate_E_MPa"],b)
            for r,w,b,c in itertools.product(M["radius_sweep_um"],M["width_sweep_um"],M["polarization_sweep_T"],M["cover_sweep_um"])]
    corners = [hybrid(r,c,w,t,e,b) for r,c,w,t,e,b in itertools.product(*M["tolerance_corners"].values())]
    L = M["lean_variant"]
    lean = hybrid(L["core_radius_um"], M["inner_cover_um"], L["gate_width_um"], M["gate_thickness_um"], M["gate_E_MPa"], M["effective_polarization_T"], True)
    lean_corners = [hybrid(r,c,w,t,e,b) for r,c,w,t,e,b in itertools.product(*L["tolerance_corners"].values())]
    lean_cost = [cost_case(L["core_radius_um"],L["gate_width_um"],1,p) for p in COST["magnet_price_scenarios_JPY_kg"]]
    r, B, d = M["core_radius_um"], M["effective_polarization_T"], 2*(M["core_radius_um"]+M["inner_cover_um"])*UM
    m = moment(r*UM, B)
    distances = [{"d_um": v, "force_uN": pair_force(r,B,v*UM)/UM} for v in M["distance_sweep_um"]]
    steel = [{"centre_height_um": z, "force_uN": 3*MU0*m*m/(32*math.pi*(z*UM)**4)/UM,
              "ratio_to_seated_pair": (d/(2*z*UM))**4} for z in M["outer_core_centre_to_steel_um"]]
    torque_max = MU0*m*m/(2*math.pi*d**3)
    O = I["orientation"]
    orientation = [{"theta_deg": t, "signed_attractive_radial_force_uN": pair_force(r,B,d)*math.cos(math.radians(t))/UM,
                    "torque_magnitude_N_m": torque_max*abs(math.sin(math.radians(t)))} for t in O["angles_deg"]]
    rotation = [{"normal_N": n, "assumed_friction_torque_N_m": O["assumed_sliding_friction"]*n*O["grain_radius_m"],
                 "magnetic_to_friction_torque": torque_max/(O["assumed_sliding_friction"]*n*O["grain_radius_m"])} for n in O["contact_normal_N"]]
    C = I["capillary"]
    cap = []
    # z=4 is an illustrative contact count, NOT measured.
    bed_N = COST["area_m2"]*COST["depth_m"]*COST["number_density_m3"]
    for T, radius, v in itertools.product(C["temperature_C"], C["asperity_radius_um"], C["volume_ratio_V_R3"]):
        f = capillary_force(T,radius,v)
        cap.append({"temperature_C": T, "radius_um": radius, "V_over_R3": v,
                    "gamma_N_m": gamma_water(T), "force_uN": f/UM,
                    "force_over_10kPa_reference": f/COST["force_reference_10kPa_N"],
                    "water_mass_kg_if_4_bridges_per_grain_shared": bed_N*2*v*(radius*UM)**3*C["pure_water_density_kg_m3"]})
    prices = [cost_case(r,M["gate_width_um"],f,p) for f,p in itertools.product(COST["magnetic_grain_fraction"], COST["magnet_price_scenarios_JPY_kg"])]
    radial_costs = [cost_case(v,M["gate_width_um"],1,500) for v in M["radius_sweep_um"]]
    E = I["external_field_alternative"]
    coil = [{"field_T": b, "ideal_gap_A_turn": b*E["gap_m"]/MU0,
             "ideal_gap_stored_energy_J": b*b/(2*MU0)*E["gap_m"]*E["width_m"]*E["length_m"]} for b in E["field_T"]]
    G = I["published_grade"]
    temp_factor = 1+G["Br_reversible_coefficient_per_C"]*(G["comparison_T_C"]-G["reference_T_C"])
    return {"metadata": {"date": I["date"], "physical_test_count": 0, "physical_success_probability": None,
                          "not_success_trials": True, "source_verification": provenance},
            "nominal": default, "width_cases": width_cases, "parameter_grid": grid, "tolerance_corners": corners,
            "corner_extrema": {"lowest_B_critical": min(corners,key=lambda x:x["sampled_path_B_critical_T"]),
                               "highest_B_critical": max(corners,key=lambda x:x["sampled_path_B_critical_T"]),
                               "max_push": max(corners,key=lambda x:x["max_external_push_uN"]),
                               "min_push": min(corners,key=lambda x:x["max_external_push_uN"])},
            "lean_variant": {"nominal": lean, "corners": lean_corners, "cost": lean_cost, "max_corner_push": max(lean_corners,key=lambda x:x["max_external_push_uN"])},
            "distance_profile": distances, "steel_plane_comparator": steel, "orientation": orientation,
            "torque": {"max_N_m": torque_max,
                       "critical_normal_N_for_assumed_friction": torque_max/(O["assumed_sliding_friction"]*O["grain_radius_m"]),
                       "conditions": rotation},
            "capillary": cap, "cost": prices, "radius_cost_sweep": radial_costs, "external_field_scale": coil,
            "catalog_linear_Br50_T": {"min": G["Br23_min_T"]*temp_factor, "max": G["Br23_max_T"]*temp_factor,
                                     "not_effective_moment_measurement": True}}

def checks(out):
    done = []
    def check(name, condition):
        assert condition, name
        done.append({"name": name, "passed": True, "scope": "Numerical/internal consistency only."})
    r,B,d = 35,.25,80*UM
    h = d*1e-5
    gradient = (pair_energy(r,B,d+h)-pair_energy(r,B,d-h))/(2*h)
    check("dipole_force_energy_gradient", math.isclose(gradient,pair_force(r,B,d),rel_tol=1e-8))
    check("dipole_inverse_fourth_and_polarization_square", math.isclose(pair_force(r,B,2*d)/pair_force(r,B,d),1/16,rel_tol=1e-12) and math.isclose(pair_force(r,2*B,d)/pair_force(r,B,d),4,rel_tol=1e-12))
    check("steel_image_equals_pair_at_half_height", math.isclose(out["steel_plane_comparator"][0]["force_uN"],out["nominal"]["final_magnetic_force_uN"],rel_tol=1e-12))
    check("water_surface_tension_matches_IAPWS_50C_table", abs(gamma_water(50)*1000-67.94)<.006)
    check("capillary_below_zero_volume_limit_and_decreases_with_volume", all(0<capillary_force(50,30,v)<2*math.pi*gamma_water(50)*30*UM for v in [1e-6,.001,.1]) and capillary_force(50,30,1e-6)>capillary_force(50,30,.1))
    check("reference_and_grid_cardinality", len(R["points"])==161 and len(out["parameter_grid"])==300 and len(out["tolerance_corners"])==64 and len(out["lean_variant"]["corners"])==64)
    check("registered_path_wide_gate_barrier_narrow_gate_no_positive_samples", out["width_cases"][0]["max_external_push_uN"]>0>out["nominal"]["max_external_push_uN"])
    check("critical_field_has_zero_sampled_peak", abs(hybrid(35,5,20,5,300,out["nominal"]["sampled_path_B_critical_T"])["max_external_push_uN"])<1e-10)
    scaled = hybrid(35,5,20,10,300,.25)
    check("thickness_cube_scales_critical_field", math.isclose(scaled["sampled_path_B_critical_T"]/out["nominal"]["sampled_path_B_critical_T"],math.sqrt(8),rel_tol=1e-12))
    p = out["cost"][0]
    check("mass_balance", math.isclose(p["total_mass_kg"],p["base_mass_kg"]-p["removed_matrix_mass_kg"]+p["gate_mass_kg"]+p["core_mass_kg"],rel_tol=1e-12))
    cap = cost_case(35,20,1,p["core_inclusive_processing_price_cap_JPY_kg"])
    check("cost_budget_inversion", math.isclose(cap["annual_equivalent_JPY"],COST["annual_budget_JPY"],rel_tol=1e-12))
    check("no_physical_probability_claim", out["metadata"]["physical_success_probability"] is None and out["metadata"]["physical_test_count"]==0)
    return done

if __name__ == "__main__":
    out = calculate()
    out["checks"] = checks(out)
    (HERE/"results.json").write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    summary = {"numerical_checks": len(out["checks"]), "grid_conditions": len(out["parameter_grid"]),
               "tolerance_corners_total": len(out["tolerance_corners"])+len(out["lean_variant"]["corners"]), "nominal_peak_push_uN": out["nominal"]["max_external_push_uN"],
               "nominal_critical_B_T": out["nominal"]["sampled_path_B_critical_T"],
               "worst_corner_push_uN": out["corner_extrema"]["max_push"]["max_external_push_uN"],
               "bulk_kg_m3": out["cost"][0]["bulk_density_kg_m3"],
               "core_inclusive_processing_price_cap_JPY_kg": out["cost"][0]["core_inclusive_processing_price_cap_JPY_kg"],
               "physical_trials": 0, "physical_success_probability": None}
    print(json.dumps(summary,ensure_ascii=False,indent=2))
