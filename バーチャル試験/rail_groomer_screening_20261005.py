"""Rail-guided artificial-snow groomer: conditional engineering screening.
All geometry, friction, speed, price and material inputs are assumptions.
Not a structural design, equipment rating, DEM, quote or physical validation.
Python standard library only. Writes a sibling JSON result.
"""
import json
import math
from pathlib import Path

G = 9.81
BETA = math.radians(30)


def annuity(years, rate):
    return (1 - (1 + rate) ** (-years)) / rate


def traction(width, wet_density, sliding_mu):
    # Triangular carried wedge: 0.5 m high, 2 m long; not a blade rating.
    volume = 0.5 * width * 0.5 * 2
    mass = volume * wet_density
    frame_mass = 250 * width  # kg/m of width, assumed for this sensitivity only
    rolling_coefficient = 0.02
    tool_drag = 1000 * width  # N, excludes a jam or severe excavation
    material = mass * G * (math.sin(BETA) + sliding_mu * math.cos(BETA))
    frame = frame_mass * G * (math.sin(BETA) + rolling_coefficient * math.cos(BETA))
    total = material + frame + tool_drag
    return dict(width_m=width, wet_density_kg_m3_assumed=wet_density,
                sliding_mu_assumed=sliding_mu, material_volume_m3=volume,
                material_mass_t=mass / 1000, frame_mass_t_assumed=frame_mass / 1000,
                tool_drag_kN_assumed=tool_drag / 1000, force_kN=total / 1000,
                force_kN_with_illustrative_1p5_multiplier=total * 1.5 / 1000,
                traction_power_kW_at_0p1m_s_eff0p75=total * 0.1 / 0.75 / 1000)


def calculate():
    data = dict(
        evidence="conditional arithmetic; no field validation or supplier quote",
        repository_context_revision="61b4c57",
        traction=[traction(b, rho, mu) for b in (10, 20, 40)
                  for rho in (500, 1800) for mu in (0.3, 0.5)],
        pass_time=[], beam_stiffness=[], roller_reaction=[],
        jack_cycle=[], capital_budget=[], rail_installation_sensitivity=[],
    )
    for length in (100, 1000):
        for speed in (0.05, 0.1, 0.2):
            working_h = length / speed / 0.6 / 3600
            return_h = length / 0.3 / 3600
            data["pass_time"].append(dict(length_m=length, working_speed_m_s_assumed=speed,
                work_utilization_assumed=0.6, working_h=working_h,
                return_h_at_0p3m_s=return_h, setup_h_assumed=0.5,
                total_h_single_material_sufficient_pass=working_h + return_h + 0.5))
    for width in (10, 20, 40):
        # Simply supported equivalent beam, UDL 2 kN/m, E=200 GPa, delta=10mm.
        # Same UDL across widths isolates span sensitivity; no hinge/torsion design.
        inertia = 5 * 2000 * width**4 / (384 * 200e9 * 0.01)
        data["beam_stiffness"].append(dict(span_m=width, udl_N_m_assumed=2000,
            deflection_limit_m_assumed=0.01, equivalent_I_m4_required=inertia))
    frame_normal = 5000 * G * math.cos(BETA)
    for pressure_kPa in (20, 50, 100):
        roller = pressure_kPa * 1000 * 20 * 0.10
        data["roller_reaction"].append(dict(pressure_kPa_assumed=pressure_kPa,
            total_contact_area_m2_assumed=2, normal_frame_weight_kN=frame_normal / 1000,
            roller_reaction_kN=roller / 1000,
            total_rail_hold_down_kN_before_factors=max(0, roller-frame_normal) / 1000))
    for cycle_s in (30, 60, 120):
        speed_m_h = 0.5 / cycle_s * 3600
        data["jack_cycle"].append(dict(stroke_m_assumed=0.5, complete_cycle_s_assumed=cycle_s,
            mean_speed_m_h=speed_m_h, hours_for_1km_without_other_stops=1000/speed_m_h))
    for years, rate in ((10, 0.08), (15, 0.04)):
        for annual_saving in (1e6, 3e6, 5e6, 10e6):
            data["capital_budget"].append(dict(years=years, discount_rate=rate,
                NET_annual_saving_yen_assumed=annual_saving,
                allowed_ADDITIONAL_initial_cost_yen=annuity(years, rate)*annual_saving))
    for length in (100, 1000):
        for unit_cost in (10000, 30000, 60000):
            data["rail_installation_sensitivity"].append(dict(course_length_m=length,
                installed_cost_per_single_rail_m_yen_assumed=unit_cost,
                two_rails_cost_yen=2 * length * unit_cost))
    data["installed_rail_only_annual_saving_needed_10y8pct_at_60million"] = 60e6/annuity(10, .08)
    data["feed_example"] = dict(final_fill_depth_m_assumed=0.01,
        final_over_loose_density_assumed=1.25, width_m_assumed=20, speed_m_s_assumed=0.1,
        loose_feed_m3_h=20*0.1*0.01*1.25*3600,
        loose_depth_m_required_for_0p04m_final=0.04*1.25)
    # A conservation ledger, not a particle-flow simulation.
    inventory, filled, deficit = 10.0, 0.0, 0.0
    for _ in range(100):
        need = 20 * 10 * 0.005
        delivered = min(inventory, need)
        inventory -= delivered
        filled += delivered
        deficit += need - delivered
    assert math.isclose(10, filled + inventory)
    assert math.isclose(100, filled + deficit)
    data["one_pass_inventory_example"] = dict(course_length_m=1000, width_m=20,
        uniform_deficit_m=0.005, initial_pile_m3=10, refill_along_course_m3=0,
        filled_m3=filled, remaining_deficit_m3=deficit,
        replenishment_loads_at_least=math.ceil((filled+deficit)/10))
    data["long_rail_and_rope"] = dict(steel_expansion_coefficient_assumed_per_K=12e-6,
        rail_expansion_1km_delta60K_m=12e-6*1000*60,
        rail_expansion_50m_delta60K_m=12e-6*50*60,
        rope_EA_N_assumed=20e6, tension_difference_N_assumed=20000,
        differential_stretch_at_1km_m=20000*1000/20e6)
    return data


if __name__ == "__main__":
    result = calculate()
    out = Path(__file__).with_suffix(".json")
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    central = next(x for x in result["traction"] if x["width_m"]==20
                   and x["wet_density_kg_m3_assumed"]==1800 and x["sliding_mu_assumed"]==0.3)
    print("Conditional rail-groomer screening complete; no physical validation.")
    print("20m heavy-grain example traction kN:", round(central["force_kN"], 2))
    print("10-year 8% annuity factor:", round(annuity(10, .08), 6))
    print("JSON:", out.name)
