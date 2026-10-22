"""Capillo-Firn v2.1: conditional conservation, capacity and cost audit.
No calibrated performance model, measured material properties, or probability.
All mass flows use the submitted wet-product reference basis unless labelled dry.
"""
import math
from formulation_claim_audit import layer_mass_kg
from capillo_physics_audit import capillary_pressure, film_supply_time

def recycling_balance(mass_kg, wear=.60, target=.80, output_kg_h=200.,
                      hours_day=8., days=220., uptime=1., storm_loss=.03):
    if mass_kg<=0 or hours_day<=0 or days<=0 or output_kg_h<0:
        raise ValueError("positive mass/time and nonnegative capacity required")
    if not all(0<=x<=1 for x in [wear,target,uptime,storm_loss]):
        raise ValueError("fractions must be between zero and one")
    fines=mass_kg*wear
    goal=fines*target
    capacity=output_kg_h*hours_day*days*uptime
    recovered=min(goal,capacity)
    return dict(wear_kg=fines,target_recycled_kg=goal,capacity_kg=capacity,
                recycled_kg=recovered,replacement_kg=fines-recovered+mass_kg*storm_loss,
                required_output_kg_h=goal/(hours_day*days*uptime) if uptime else None,
                achieved_recovery_fraction=recovered/fines if fines else None)

def cash_scenarios(capex_yen, fixed_opex_yen, replacement_kg, price_yen_kg):
    opex=fixed_opex_yen+replacement_kg*price_yen_kg
    rows=[]
    for n,camp in [(250,22000000),(350,35000000),(450,44000000)]:
        revenue=n*220*8500+camp
        margin=revenue-opex
        rows.append(dict(visitors_day=n,revenue_yen=revenue,opex_yen=opex,
                        pretax_simple_operating_surplus_yen=margin,
                        simple_capex_over_surplus_years=capex_yen/margin if margin>0 else None))
    return rows

def drainage_height(rain_mm_h,spacing_m,k_m_s,angle_deg=30.):
    if min(rain_mm_h,spacing_m,k_m_s)<=0:raise ValueError("positive inputs")
    return rain_mm_h/1000/3600*spacing_m/(k_m_s*math.sin(math.radians(angle_deg)))

def audit():
    mass=layer_mass_kg(10000,.45,487)
    nominal=recycling_balance(mass)
    design=recycling_balance(mass,uptime=.85)
    dry_rated=recycling_balance(mass,output_kg_h=200/.48)
    optmass=layer_mass_kg(10000,.30,487)
    opt=recycling_balance(optmass)
    pcap=capillary_pressure(.0712,20,.4e-6)
    sigma_req=.8*75*math.hypot(9.81,15**2/12)/(.018*1.10)/1000
    kp=math.tan(math.radians(63))**2
    s0=84*math.sqrt(kp)
    vs_orig=sum(m/rho for m,rho in [(30,2.83),(6,2.6),(7,1.5),(3.5,1.55),(1.5,1.5)])
    vs_ref=vs_orig-30/2.83+30/2.930
    w=.03*487*.52
    dw=w*(.82-.70)/.82
    r={
      "date":"2026-10-22","physical_trials":0,"physical_success_probability":None,
      "interpretation":"conditional arithmetic only; no supplier quotations or field validation",
      "basis":{"area_m2":10000,"depth_m":.45,"bulk_density_kg_m3":487,"wet_reference_mass_kg":mass,
               "operating_days":220,"wear_fraction_assumed":.6,"target_recovery_fraction_assumed":.8},
      "recycling":{"wet_output_200kg_h":nominal,"output_85pct_availability":design,
                   "if_rating_is_200kg_DRY_product_h":dry_rated,
                   "required_wet_feed_kg_h_if_yield_80pct":nominal["required_output_kg_h"]/.8,
                   "hours_day_required_at_200wet_output":nominal["target_recycled_kg"]/(200*220),
                   "max_wear_fraction_for_80pct_recovery":352000/(mass*.8),
                   "capacity_even_365days_kg":200*8*365,
                   "additional_makeup_cost_yen_at350":(nominal["replacement_kg"]-mass*.15)*350},
      "financial":{
        "fixed_other_opex_yen_assumed":126646250,
        "standard_capex_yen":168000000+85000000+mass*350,
        "original_assumed_15pct_loss":cash_scenarios(1020025000,126646250,mass*.15,350),
        "capacity_limited_200wet_output":cash_scenarios(1020025000,126646250,nominal["replacement_kg"],350),
        "if_200dry_output":cash_scenarios(1020025000,126646250,dry_rated["replacement_kg"],350),
        "optimized_300mm_safety_not_validated":cash_scenarios(515200000,108170000,opt["replacement_kg"],200),
        "equipment_plus_civil_yen":168000000+85000000,
        "over_200million_before_tax_scope":168000000+85000000-200000000,
        "raw_100kg_yen":30*120+6*100+7*2000+3.5*1500+1.5*4500,
        "CNF_MCC_plus_gellan_only_yen_per_kg_wet":.07*2000+.015*4500,
        "summer_days_for_350_weighted_from_550_250":220*(350-250)/(550-250),
        "weighted_if_60days_at550":(60*550+160*250)/220,
        "loss_fraction_is_not_lifetime_years":True},
      "hydraulic":{
        "height_m":[{"k_m_s":k,"rain_mm_h":i,"h_m":drainage_height(i,25,k)}
                    for k in [.01,.0025,.001] for i in [100,150]],
        "k_min_for_450mm_100mm_h":.1/3600*25/(.45*.5),
        "k_min_for_450mm_150mm_h":.15/3600*25/(.45*.5),
        "max_spacing_m_k0025_rain100_h450":.0025*.45*.5/(.1/3600),
        "rain_m3_h_slope_area_convention_100":1000,
        "rain_m3_h_horizontal_rain_on_30deg_100":1000*math.cos(math.radians(30)),
        "transmissivity_single_layer_replacement_requires_measurement":True},
      "pit_and_storm":{
        "pit_capacity_kg_at487":150*487,"claimed_capacity_kg":180000,
        "density_implied_by_claim_kg_m3":180000/150,
        "recovered_3pct_kg":mass*.03,"volume_3pct_at487_m3":mass*.03/487,
        "4ton_blade_payload_volume_m3_at487":4000/487,
        "binder_added_kg_m2_if_1kg_L":.005*2,
        "binder_added_wt_pct_of20mm_bed":.005*2/(.02*487)*100,
        "storm_spray_water_total_L":2*10000,
        "wind_dynamic_pressure_Pa_if_air1_2":.5*1.2*80**2,
        "dry_downslope_load_5m_by25m_rib_N_zero_interface_friction":.45*487*9.81*.5*5*25},
      "maintenance":{
        "minimum_7passes_2machines_longest_path_min":4*400/(10000/60),
        "initial_two_tanks_L":3000,"daytime_makeup_L_assumed":10000,
        "minimum_additional_refill_L":7000,
        "average_makeup_two_machines_L_min_25min":10000/25,
        "central_per_machine_during_movement_L_min":(6000/4)/(400/(10000/60)),
        "one_machine_mill_mass_kg_s_150mm":3.6*(10000/3600)*.15*487,
        "both_machine_150mm_total_mass_kg":10000*.15*487,
        "one_machine_mill_mass_kg_s_30mm":3.6*(10000/3600)*.03*487,
        "central_mist_hydraulic_power_kW_at_1MPa_ideal":625/60000*1e6/1000,
        "central_mist_hydraulic_power_kW_at_10MPa_ideal":625/60000*10e6/1000,
        "last_completion_min_required_for_30min_recovery":30,
        "release_time_min_if_recovery_45min":30+45},
      "mechanical_identifiability":{
        "pcap_kPa":pcap/1000,"sigma_req_kPa":sigma_req,
        "rankine_zero_depth_kPa":s0,"rankine_15mm_selfweight_term_kPa":487*9.81*.015*kp/1000,
        "rankine_ratio_not_design_safety_factor":s0/sigma_req,
        "film_fill_ms_assumptions_unchanged":film_supply_time(.0008,15e-6,.85e-6,1e-17,20e3/.03-pcap,.92/.45)*1000,
        "shearband_frequency_Hz_if_given_spacing":[15/.035,15/.018],
        "mini_slope_volume_m3":15*3*.45,"mini_slope_mass_kg":15*3*.45*487,
        "15m_from_rest_gravity_only_max_speed_m_s_30deg":math.sqrt(2*9.81*15*.5),
        "30min_Sf_gate_kPa":40,"Sf_used_for_Gf_kPa":42+50*math.tan(math.radians(36)),
        "mcc_length_is_not_measured_failure_displacement":True},
      "material_and_water":{
        "alpha_bulk_original_kg_m3":100/(vs_orig+52/.82)*1000*.41,
        "alpha_bulk_if_aragonite2_930_kg_m3":100/(vs_ref+52/.82)*1000*.41,
        "active_allowed_loss_kg_m2":dw,
        "no_watering_hours":[{"J_kg_m2_h":j,"h":dw/j} for j in [.125,.25,.5]],
        "daily_evap_kg_7h_at025_all_area":.25*7*10000,
        "additional_afternoon_kg_3h_at025":.25*3*10000,
        "absorbed_shortwave_W_m2_if_albedo078_800":(1-.78)*800,
        "latent_flux_W_m2_if_Lv2_38MJ_kg":.25*2.38e6/3600,
        "residual_for_other_heat_flux_W_m2":(1-.78)*800-.25*2.38e6/3600,
        "15percent_replaced_yearly_original_fraction_after_6_6667years":.85**(1/.15)}
    }
    checks={
      "recycling_mass_conservation":math.isclose(nominal["wear_kg"]+mass*.03,nominal["recycled_kg"]+nominal["replacement_kg"]),
      "capacity_enforced":nominal["recycled_kg"]<=nominal["capacity_kg"],
      "zero_capacity_all_wear_replaced":math.isclose(recycling_balance(mass,output_kg_h=0)["replacement_kg"],mass*.63),
      "unlimited_capacity_recovers_target":math.isclose(recycling_balance(mass,output_kg_h=1e6)["replacement_kg"],mass*.15),
      "less_uptime_no_more_recovery":design["recycled_kg"]<=nominal["recycled_kg"],
      "wet_and_dry_reference_conversion":math.isclose(dry_rated["capacity_kg"]*.48,nominal["capacity_kg"]),
      "rain_double_height_double":math.isclose(drainage_height(200,25,.01),2*drainage_height(100,25,.01)),
      "shorter_spacing_less_height":drainage_height(100,12.5,.01)<drainage_height(100,25,.01),
      "independent_pit_volume_mass_balance":math.isclose(r["pit_and_storm"]["volume_3pct_at487_m3"]*487,mass*.03),
      "cash_delta_equals_material_delta":math.isclose(r["financial"]["original_assumed_15pct_loss"][1]["pretax_simple_operating_surplus_yen"]-r["financial"]["capacity_limited_200wet_output"][1]["pretax_simple_operating_surplus_yen"],r["recycling"]["additional_makeup_cost_yen_at350"])
    }
    assert all(checks.values()),checks
    r["arithmetic_boundary_checks"]=checks
    return r
