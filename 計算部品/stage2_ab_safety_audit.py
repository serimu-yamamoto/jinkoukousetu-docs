"""Stage 2 A/B audit arithmetic. No empirical results or safety certification.
Run: python3 -B 計算部品/stage2_ab_safety_audit.py
All formula inputs transcribed from the cited Gemini plan; prices/density are assumptions.
"""
import json
import math
from formulation_claim_audit import layer_mass_kg

def audit():
    # [calcite, kaolinite, CNF, MCC, binder I, binder II, total water], g
    a1_core = [21.5, 4.5, 4.5, 0, 2.8, 1.0, 45.2]
    a1_shell = [7.0, 1.5, 0, 2.3, .7, .5, 6.8]
    dust = [.8, 0, 0, .2, 0, 0, 0]
    s1_shell = [7.2, 1.5, 0, 2.3, .7, .5, 6.8]
    s5b_shell = [5.2, 1.2, 0, .3, .7, .3, 6.3]
    a1_total = sum(a1_core + a1_shell + dust)
    def shell_stats(x):
        dry = sum(x[:-1])
        return {"wet_g":sum(x), "dry_g":dry, "water_over_dry_percent":100*x[-1]/dry,
                "MCC_dry_percent":100*x[3]/dry}
    area, rho = 10000.0, 487.0
    m450 = layer_mass_kg(area, .45, rho)
    m500 = layer_mass_kg(area, .50, rho)
    dm = m500-m450
    specimen_g = math.pi*(.06/2)**2*.02*rho*1000
    out = {
        "status":{"physical_tests":0,"safety_pass":None,"source_date":"2026-10-23"},
        "A1":{"core_g":sum(a1_core),"shell_g":sum(a1_shell),"dust_g":sum(dust),
              "total_g":a1_total,"missing_to_100g":100-a1_total,
              "three_batches_g":3*a1_total,"four_conditions_g":900+3*a1_total,
              "core_W_over_S_percent":100*a1_core[-1]/sum(a1_core[:-1]),
              "shell_W_over_S_percent":100*a1_shell[-1]/sum(a1_shell[:-1])},
        "shell":{"S1":shell_stats(s1_shell),"S5_B":shell_stats(s5b_shell),
                 "mechanical_brittleness":"unmeasured"},
        "bed":{"area_m2":area,"assumed_density_kg_m3":rho,
               "mass450_t":m450/1000,"mass500_t":m500/1000,
               "increase_t":dm/1000,"increase_percent":100*dm/m450,
               "increase_volume_m3":area*(.5-.45),
               "price_scenarios":[{"assumed_yen_per_kg":p,"added_yen":dm*p,"total500_yen":m500*p}
                                  for p in [200,350]],
               "wear60_recovery80_scenario":{
                   "wear500_t":m500*.6/1000,"recovery500_t":m500*.6*.8/1000,
                   "unrecovered500_t":m500*.6*.2/1000}},
        "freezing":{"project_target_K":.01,"water_Kf_K_kg_per_osmol":1.86,
                    "equivalent_mOsm_per_kg_water":.01/1.86*1000,
                    "legal_safety_limit":False},
        "B_part4":{"nominal30g_times36_g":30*36,
                   "geometry60mm20mm_at487kg_m3_g":specimen_g,
                   "geometry_times36_g":specimen_g*36,
                   "friction_specimen_mass_included":False},
        "notes":["No data-backed harmlessness or success probability is inferred.",
                 "Na, citrate and Ca individual acceptance concentrations remain unconfirmed.",
                 "500 mm and unit prices are scenarios, not an approved design or quote."]}
    expected=[(sum(a1_core),79.5),(sum(a1_shell),18.8),(a1_total,99.3),
              (100-a1_total,.7),(3*a1_total,297.9),(900+3*a1_total,1197.9),
              (sum(s1_shell),19),(sum(s5b_shell),14),
              (m450/1000,2191.5),(m500/1000,2435),(dm/1000,243.5),
              (dm*200,48700000),(dm*350,85225000)]
    for actual,target in expected:
        assert math.isclose(actual,target,rel_tol=1e-10,abs_tol=1e-9),(actual,target)
    out["arithmetic_checks"]={"passed":len(expected),"physical_validation":False}
    return out

if __name__ == "__main__":
    print(json.dumps(audit(),ensure_ascii=False,indent=2))
