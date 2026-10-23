"""Independent arithmetic audit; all material performance remains unmeasured.
Run python3 -B 計算部品/capillo_theory_critique_audit.py.
Uses the author's req_screen.py without alteration. No optimization or fitted success values.
"""
import math
import json
from req_screen import granule_density, capillary_tensile, penman_open

def audit():
    density = []
    # Published critique's rounded, gas-free densities. Uniform diagnostic grid, not a recipe.
    for name, rho in [("S1",1364.0),("S3",1566.0),("S4",1668.0)]:
        density.append({
            "name":name,"gas_free_rho":rho,"bulk_at_pack058":rho*.58,
            "diagnostic_air_grid":[
                {"air_volume_fraction":a,
                 "gas_retained_bulk":rho*(1-a)*.58,
                 "same_pores_water_filled_bulk":(rho*(1-a)+1000*a)*.58}
                 for a in [0,.2,.4,.6]]
        })
    cap=[]
    for d in [.0008,.0001]:
        for n in [.42,.58]:
            cap.append({"diameter_m":d,"interparticle_void_fraction":n,
                        "surface_tension_N_m":.072,
                        "Rumpf_tensile_kPa":capillary_tensile(d,n)/1000})
    bridge_force=math.pi*.0008*.072
    network_tensile=6*.58*bridge_force/(math.pi*.0008**2)
    evap=[]
    # Rs=25 is a declared reconstruction scenario, not a recovered original input.
    for alb in [.8,.5]:
        E=penman_open(25,alb,T=28,RH=.6,u2=2,Ln_MJ=5)
        evap.append({"albedo":alb,"Rs_MJ_m2_day":25,"T_C":28,"RH":.6,"u2_m_s":2,
                     "Ln_MJ_m2_day":5,"open_water_mm_day":E,"tonnes_per_ha_day":10*E})
    energywater=[]
    for M in [19.,43.]:
        energywater.append({"scenario_tonnes_day":M,"latent_heat_GJ_day":M*1000*2.45/1000,
             "supply_L_s_over_8h":M*1000/(8*3600),
             "restore_whole_day_L_s_over_25min":M*1000/(25*60),
             "half_day_restore_L_s_over_25min":M*500/(25*60),
             "annual_makeup_m3_220days":M*220,
             "fraction_of_30mm_layer_initial_water":M/(.03*10000*487*.52/1000)})
    wetbed_t=10000*.45*487/1000
    wetunrecovered_t=wetbed_t*.60*(1-.80)
    dryloss_t=wetunrecovered_t*.48
    dryorg_t=dryloss_t*(12/48)
    runoff=[]
    for water_m3 in [15000,25000]:
        ss=dryloss_t*.10*1e6/water_m3
        organic=ss*.25
        runoff.append({"annual_water_m3":water_m3,"assumed_runoff_fraction_of_dryloss":.1,
          "all_suspended_equivalent_mg_L":ss,"organic_mass_mg_L":organic,
          "cellulose_only_theoretical_oxygen_equivalent_mg_L":organic*192/162,
          "treatment_sensitivity":[{"assumed_mass_removal":e,"residual_SS_equivalent_mg_L":ss*(1-e)}
                                    for e in [.9,.99,.999]]})
    eta,v,p,h,f=.0008,10.,20000.,.85e-6,.03*.92
    film_viscous=eta*v/(p*h)
    friction={"assumed_eta_Pa_s":eta,"assumed_v_m_s":v,"nominal_pressure_Pa":p,
       "assumed_film_h_m":h,"full_area_Couette_mu_component":film_viscous,
       "assumed_film_area_fraction":f,"restricted_area_mu_component":f*film_viscous,
       "old_assumed_solid_load_mu_component":.08*.42,
       "old_conditional_mu_sum":.08*.42+f*film_viscous,
       "full_area_film_water_g_m2":h*1000*1000,
       "is_prediction_of_actual_mu":False}
    # Pore closure sensitivity only: no fitted bulk modulus.
    invariant_tests = [
        math.isclose(density[0]["bulk_at_pack058"],791.12),
        math.isclose(density[-1]["bulk_at_pack058"],967.44),
        all(math.isclose(x["diagnostic_air_grid"][0]["gas_retained_bulk"],x["bulk_at_pack058"]) for x in density),
        all(x["same_pores_water_filled_bulk"]>=x["gas_retained_bulk"] for r in density for x in r["diagnostic_air_grid"]),
        cap[2]["Rumpf_tensile_kPa"]>cap[0]["Rumpf_tensile_kPa"],
        math.isclose(cap[2]["Rumpf_tensile_kPa"]/cap[0]["Rumpf_tensile_kPa"],8),
        math.isclose(wetbed_t,2191.5), math.isclose(wetunrecovered_t,262.98),
        math.isclose(dryloss_t,126.2304), math.isclose(dryorg_t,31.5576),
        math.isclose(runoff[0]["all_suspended_equivalent_mg_L"],841.536),
        math.isclose(runoff[1]["all_suspended_equivalent_mg_L"],504.9216),
        math.isclose(friction["old_conditional_mu_sum"],.046588235294117645),
        math.isclose(friction["full_area_film_water_g_m2"],.85),
        all(r["treatment_sensitivity"][2]["residual_SS_equivalent_mg_L"]<
            r["treatment_sensitivity"][0]["residual_SS_equivalent_mg_L"] for r in runoff),
        math.isclose(energywater[0]["annual_makeup_m3_220days"],4180)]
    assert all(invariant_tests)
    return {"status":{"physical_tests":0,"fitted_inputs":False,"success_probability":None},
      "density":density,"capillary":cap,"coordination6_network_tensile_kPa":network_tensile/1000,
      "capillary_bridge_force_mN":bridge_force*1000,
      "open_water_scenarios":evap,"water_operating_scenarios":energywater,
      "loss":{"wet_unrecovered_t_yr":wetunrecovered_t,"dry_unrecovered_t_yr":dryloss_t,
              "dry_organic_t_yr":dryorg_t,"water_route_t_yr":dryloss_t*.1,
              "other_routes_or_inventory_t_yr":dryloss_t*.9},
      "runoff":runoff,"friction":friction,"arithmetic_checks":len(invariant_tests),
      "caveats":["None of the assumed pore volumes, recoveries, removal efficiencies or friction shares is a measured material property.",
                 "Organic mass and theoretical oxygen demand are not BOD5 or CODMn measurements.",
                 "Annual average load / annual water volume is not an event peak or effluent compliance result.",
                 "req_screen.py returns an approximate tensile strength, not a measured Mohr-Coulomb cohesion."]}

if __name__=="__main__":
    print(json.dumps(audit(),ensure_ascii=False,indent=2))
