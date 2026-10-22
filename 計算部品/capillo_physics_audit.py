"""Capillo-Firn conditional audit; no synthesis, safety, or performance predictions."""
import math
from formulation_claim_audit import positive, layer_mass_kg, shear_bound_kpa, retained_water
def capillary_pressure(gamma,theta_deg,radius_m):
    if not 0<=theta_deg<90:raise ValueError("wetting-angle example required")
    return 2*positive(gamma)*math.cos(math.radians(theta_deg))/positive(radius_m)
def hydraulic_time(eta,length,permeability,delta_p):
    return positive(eta)*positive(length)**2/(positive(permeability)*positive(delta_p))
def film_supply_time(eta,length,film_thickness,permeability,delta_p,film_outlet_area_ratio):
    return positive(eta)*positive(length)*positive(film_thickness)*positive(film_outlet_area_ratio)/(positive(permeability)*positive(delta_p))
def parallel_defect_reduction(intact_reduction,defect_fraction):
    if not 0<=defect_fraction<=1:raise ValueError("fraction")
    return 1/(defect_fraction+(1-defect_fraction)/positive(intact_reduction))
def audit():
    gamma=.0712;theta=20;radius=.4e-6;eta=.8e-3;L=15e-6;K=1e-18;dp=300e3
    pc=capillary_pressure(gamma,theta,radius);tip=20e3/.03
    solids=[(30,2.83),(6,2.6),(7,1.5),(3.5,1.55),(1.5,1.50)]
    vs=sum(m/rho for m,rho in solids);vw=52.;vpore=vw/.82;va=vpore-vw
    rho=100/(vs+vpore)*1000;bulk=rho*.410
    mu=.08*.42+(1-.08)*eta*10*.03/(20e3*.85e-6)
    tau=hydraulic_time(eta,L,K,dp)
    barrier=1+80**2*.4**2/(4*(1-.4))
    mass=layer_mass_kg(10000,.45,487)
    flow_dp=tip-pc # highly optimistic: assumes all tip stress becomes liquid pressure
    r={
      "date":"2026-10-22","physical_trials":0,"physical_success_probability":None,
      "classification":"conditional arithmetic and model-identifiability audit",
      "given_inputs":{"gamma_N_m":gamma,"theta_deg":theta,"pore_radius_m":radius,"eta_Pa_s":eta,"L_m":L,"K_m2":K,"dp_Pa":dp},
      "arithmetic":{"Pcap_kPa":pc/1000,"tip_stress_kPa":tip/1000,"paper_stress_kPa":10/.25,
        "friction_formula_only":mu,"barrier_formula_only":barrier,"water_retention_if_loss_5_8g":retained_water(.52,.058),
        "solid_volume_cm3":vs,"air_volume_cm3":va,"envelope_density_kg_m3":rho,"bulk_density_kg_m3":bulk,
        "chi_if_pack_fractions_given":1-.410/.5,"Mohr_Coulomb_kPa":[shear_bound_kpa(42,s,36) for s in [25,50,80]],
        "Bingham_capillary_number":2500*30e-6/.055},
      "ICSS_time":{"recomputed_s":tau,"claimed_s":600,"claimed_over_recomputed":600/tau,
        "K_needed_for_600s_m2":eta*L**2/(600*dp),"L_needed_for_600s_m":math.sqrt(600*K*dp/eta),
        "interpretation":"water-transport scaling time, not measured contact-strength recovery time"},
      "water_inventory":{"bed_mass_kg":mass,"initial_water_kg":.52*mass,"daily_evap_kg_if_5pct_whole_bed":.05*mass,
        "daily_evap_kg_if_5_8pct_whole_bed":.058*mass,
        "active_depth_m_for_11t_at_5pct":11000/(10000*487*.05),
        "active_depth_m_for_11t_at_5_8pct":11000/(10000*487*.058),
        "note":"not actual evaporation prediction; effective drying depth, replenishment and heat balance required"},
      "film_flow":{"assumptions":"same brush K used in outflow; full stress-to-liquid conversion; steady Darcy; no counterpressure; all unverified",
        "available_dp_Pa":flow_dp,
        "time_equal_film_outlet_area_s":film_supply_time(eta,L,.85e-6,K,flow_dp,1),
        "time_film_0_92_nominal_outlet_0_03_nominal_s":film_supply_time(eta,L,.85e-6,K,flow_dp,.92/.03),
        "K_needed_for_0_05s_equal_area_m2":eta*L*.85e-6/(flow_dp*.05),
        "K_needed_for_0_05s_large_area_m2":eta*L*.85e-6*(.92/.03)/(flow_dp*.05)},
      "suction":{"15nm_equivalent_radius_Pcap_Pa":capillary_pressure(gamma,theta,15e-9),
        "ratio_to_0_4um_pore":radius/15e-9,
        "gas_absolute_Pa_if_minus_300kPa_gauge":101325-300e3,
        "note":"15nm is an equivalent-radius illustration; actual gap meniscus geometry not specified; liquid tension is not gas negative absolute pressure"},
      "coating_defects":[{"fraction":d,"relative_reduction":parallel_defect_reduction(barrier,d)} for d in [0,.001,.01,.05,1]],
      "freeze_volume":{"saturation":.82,"expansion_assumed":.09,"ice_fraction_of_pore":.82*1.09,
        "air_fraction_after_freeze_no_water_movement":1-.82*1.09,"critical_global_saturation_no_air_compression":1/1.09,
        "note":"global volume margin only; does not exclude local ice pressure, cryosuction, gas compression or water influx"},
      "solubility_screen":{"total_osmoles_2mmol_per_kg_K":1.86*.002,
        "citrate_salt_2mmol_if_five_ideal_ions_K":1.86*.002*5,
        "supplier_solubility_example_g_L":1,"molar_mass_tetrahydrate_g_mol":570.49,
        "ideal_5particle_example_K":1.86*5/570.49,
        "note":"1L approximated 1kg water; supplier solubility temperature not specified; ion pairing, pH, activity and mixed-solid equilibria unmeasured"},
      "rain":{"intensity_mm_h":100,"area_m2":10000,"rainwater_m3_h":100/1000*10000,
        "hydraulic_conductivity_target_m_s":.01,"rain_flux_m_s":.1/3600,
        "note":"vertical rain flux alone does not validate slopewise discharge, filter clogging or stability"},
      "cost_sensitivity":{"not_market_quotes":True,"wet_material_yen_per_kg_assumed":[100,300,1000],
        "initial_material_yen":[mass*p for p in [100,300,1000]],
        "equipment_budget_yen":200000000,
        "note":"material and maintenance costs are separate from the equipment budget; mixing, transport, water processing and disposal excluded"}}
    checks={
      "mass_alpha_100g":sum(m for m,_ in solids)+52==100,
      "time_si_units":math.isclose(tau,.6,rel_tol=1e-12),
      "time_scales_quadratically":math.isclose(hydraulic_time(eta,2*L,K,dp),4*tau),
      "time_inverse_permeability":math.isclose(hydraulic_time(eta,L,2*K,dp),tau/2),
      "darcy_equals_inventory_flux":math.isclose(r["film_flow"]["time_equal_film_outlet_area_s"],.85e-6/(K*flow_dp/(eta*L))),
      "defect_endpoints":math.isclose(parallel_defect_reduction(barrier,0),barrier) and parallel_defect_reduction(barrier,1)==1,
      "defect_monotonic":all(r["coating_defects"][i]["relative_reduction"]>r["coating_defects"][i+1]["relative_reduction"] for i in range(4)),
      "five_percent_inventory":math.isclose(r["water_inventory"]["daily_evap_kg_if_5pct_whole_bed"],109575),
      "grain_volume_balance":math.isclose(vs+vw+va,vs+vpore),
      "freeze_air_positive_global_only":r["freeze_volume"]["air_fraction_after_freeze_no_water_movement"]>0,
      "shear_50_kPa":math.isclose(r["arithmetic"]["Mohr_Coulomb_kPa"][1],78.32712640026805,rel_tol=1e-10),
      "rain_volume_units":r["rain"]["rainwater_m3_h"]==1000}
    assert all(checks.values()),checks
    r["arithmetic_checks"]=checks
    return r
if __name__=="__main__":
    import json
    print(json.dumps(audit(),ensure_ascii=False,indent=2))
