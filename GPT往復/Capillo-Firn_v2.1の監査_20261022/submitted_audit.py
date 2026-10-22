import math
import json

def audit_master_v2_1():
    # 1. 最終3候補 (Alpha-v2.1, Alpha-Talc, Beta-Soft) の体積・密度収支
    candidates = {
        "Alpha_v2_1": {
            "solids": [(30.0, 2.830), (6.0, 2.600), (4.5, 1.500), (2.5, 1.500), (3.5, 1.550), (1.5, 1.500)],
            "water_g": 52.0, "Sw": 0.820, "phi_pack": 0.410
        },
        "Alpha_Talc": {
            "solids": [(30.0, 2.830), (3.0, 2.600), (3.0, 2.750), (4.5, 1.500), (2.5, 1.500), (3.5, 1.550), (1.5, 1.500)],
            "water_g": 52.0, "Sw": 0.820, "phi_pack": 0.410
        },
        "Beta_Soft": {
            "solids": [(32.0, 2.830), (6.0, 2.800), (6.5, 1.420), (4.0, 1.550), (1.5, 1.600)],
            "water_g": 50.0, "Sw": 0.840, "phi_pack": 0.400
        }
    }
    comp_out = {}
    for name, c in candidates.items():
        m_sol = sum(m for m, _ in c["solids"])
        v_sol = sum(m / rho for m, rho in c["solids"])
        v_wat = c["water_g"]
        v_pore = v_wat / c["Sw"]
        v_air = v_pore - v_wat
        v_env = v_sol + v_pore
        rho_sol = (m_sol / v_sol) * 1000.0
        rho_mat = ((m_sol + v_wat) / (v_sol + v_wat)) * 1000.0
        rho_env = ((m_sol + v_wat) / v_env) * 1000.0
        rho_bulk = rho_env * c["phi_pack"]
        comp_out[name] = {
            "V_solid_cm3": round(v_sol, 4),
            "V_air_cm3": round(v_air, 4),
            "rho_solid_kg_m3": round(rho_sol, 1),
            "rho_mat_kg_m3": round(rho_mat, 1),
            "rho_env_kg_m3": round(rho_env, 2),
            "rho_bulk_kg_m3": round(rho_bulk, 2)
        }

    # 2. 毛管圧ゲート・吐出時間・再吸水時間・無散水滑走時間
    gamma = 0.0712
    P_cap_kPa = (2.0 * gamma * math.cos(math.radians(20.0)) / 0.40e-6) / 1000.0
    P_cap_paper_kPa = (2.0 * gamma * math.cos(math.radians(20.0)) / 5.0e-6) / 1000.0
    dP_extract_paper_kPa = (10.0 / 0.25) + P_cap_paper_kPa

    eta_w = 8.0e-4
    L_diff = 15.0e-6
    tau_Darcy_s = (eta_w * L_diff**2) / (1.0e-18 * 3.0e5)
    dP_squeeze_Pa = ((20.0 / 0.030) - P_cap_kPa) * 1000.0
    t_fill_K17_ms = ((eta_w * L_diff * 0.85e-6) / (1.0e-17 * dP_squeeze_Pa)) * (0.92 / 0.45) * 1000.0
    mu_ski = 0.08 * 0.42 + (0.030 * 0.92 * eta_w * 10.0) / (20000.0 * 0.85e-6)

    w0_active_kg_m2 = 0.030 * 487.0 * 0.52
    dw_allow_kg_m2 = w0_active_kg_m2 * ((0.82 - 0.70) / 0.82)
    t_limit_no_watering_h = dw_allow_kg_m2 / 0.250

    # 3. 6次元滑走感覚 (カービング横G支持・脆性ネック破壊エネルギー)
    g = 9.81
    v_turn = 15.0
    R_turn = 12.0
    bank_rad = math.atan(v_turn**2 / (g * R_turn))
    g_force = 1.0 / math.cos(bank_rad)
    F_total_N = 75.0 * g * g_force
    sigma_edge_req_kPa = (0.80 * F_total_N / (1.10 * 0.018)) / 1000.0
    Kp = math.tan(math.radians(45.0 + 36.0 / 2.0))**2
    sigma_p0_kPa = 2.0 * 42.0 * math.sqrt(Kp)
    edge_safety_factor = sigma_p0_kPa / sigma_edge_req_kPa

    Sf_50_Pa = (42.0 + 50.0 * math.tan(math.radians(36.0))) * 1000.0
    Gf_ductile_80um = 0.5 * Sf_50_Pa * 80.0e-6
    Gf_brittle_10um = 0.5 * Sf_50_Pa * 10.0e-6

    # 4. 台風豪雨 (100mm/h) 浸透流と25m間隔横断暗渠水位
    q_max_m2_s = 1.0e-2 * 0.465 * math.sin(math.radians(30.0))
    I_100_m_s = (100.0 / 1000.0) / 3600.0
    L_crit_no_drain_m = q_max_m2_s / I_100_m_s
    h_sat_25m_100mmh_mm = (I_100_m_s * 25.0 / (1.0e-2 * 0.50)) * 1000.0
    h_sat_25m_150mmh_mm = h_sat_25m_100mmh_mm * 1.5

    # 5. 非冬季220日稼働・商業採算モデル (標準450mm厚, 2,191.5t)
    M_bed_t = 10000.0 * 0.45 * 487.0 / 1000.0
    capex_total_man = 16800.0 + 8500.0 + (M_bed_t * 1000.0 * 350.0) / 10000.0
    opex_replenish_man = (M_bed_t * 0.15 * 1000.0 * 350.0) / 10000.0
    opex_total_man = opex_replenish_man + 12664.625

    scenarios = {}
    for label, visitors_day, camp_man in [("Conservative_250", 250, 2200.0), ("Standard_350", 350, 3500.0), ("High_450", 450, 4400.0)]:
        rev_man = (visitors_day * 220 * 8500.0) / 10000.0 + camp_man
        ebitda_man = rev_man - opex_total_man
        payback_yr = capex_total_man / ebitda_man
        scenarios[label] = {
            "revenue_man_yen": round(rev_man, 1),
            "ebitda_man_yen": round(ebitda_man, 1),
            "payback_years": round(payback_yr, 2)
        }

    return {
        "compositions": comp_out,
        "mechanics_and_water": {
            "P_cap_kPa": round(P_cap_kPa, 2),
            "dP_extract_paper_kPa": round(dP_extract_paper_kPa, 2),
            "tau_Darcy_s": round(tau_Darcy_s, 3),
            "t_fill_K17_ms": round(t_fill_K17_ms, 2),
            "mu_ski": round(mu_ski, 5),
            "t_limit_no_watering_h": round(t_limit_no_watering_h, 3)
        },
        "ski_feel_6D": {
            "turn_g_force": round(g_force, 3),
            "sigma_edge_req_kPa": round(sigma_edge_req_kPa, 2),
            "sigma_p0_kPa": round(sigma_p0_kPa, 2),
            "edge_safety_factor": round(edge_safety_factor, 2),
            "Gf_ductile_80um_J_m2": round(Gf_ductile_80um, 4),
            "Gf_brittle_10um_J_m2": round(Gf_brittle_10um, 4)
        },
        "typhoon_drainage": {
            "L_crit_no_drain_m": round(L_crit_no_drain_m, 2),
            "h_sat_25m_100mmh_mm": round(h_sat_25m_100mmh_mm, 2),
            "h_sat_25m_150mmh_mm": round(h_sat_25m_150mmh_mm, 2)
        },
        "business_220days_standard": {
            "M_bed_t": round(M_bed_t, 2),
            "CAPEX_total_man_yen": round(capex_total_man, 1),
            "OPEX_total_man_yen": round(opex_total_man, 1),
            "scenarios": scenarios
        }
    }

if __name__ == "__main__":
    print(json.dumps(audit_master_v2_1(), indent=2))
