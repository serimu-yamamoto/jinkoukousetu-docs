"""Audit of the received v2.2 summary; no measured properties or physical success claims."""
import math
from capillo_v21_system_audit import drainage_height, recycling_balance

def volume_partition(mass_g,solid_volume_cm3,water_g,water_density_g_cm3,particle_density_kg_m3,bed_density_kg_m3):
    vals=[mass_g,solid_volume_cm3,water_g,water_density_g_cm3,particle_density_kg_m3,bed_density_kg_m3]
    if min(vals)<=0 or water_g>=mass_g:raise ValueError("positive physical inputs required")
    vw=water_g/water_density_g_cm3
    vp=mass_g/(particle_density_kg_m3/1000)
    vb=mass_g/(bed_density_kg_m3/1000)
    if not solid_volume_cm3+vw<=vp<=vb:raise ValueError("impossible phase or packing volumes")
    va=vp-solid_volume_cm3-vw
    return dict(water_cm3=vw,wet_no_gas_cm3=solid_volume_cm3+vw,wet_no_gas_density_kg_m3=mass_g/(solid_volume_cm3+vw)*1000,
                particle_envelope_cm3=vp,bed_cm3=vb,particle_air_cm3=va,
                particle_gas_fraction=va/vp,particle_water_fraction=vw/vp,particle_solid_fraction=solid_volume_cm3/vp,
                particle_pore_fraction_if_all_water_is_pore_water=1-solid_volume_cm3/vp,
                water_saturation_if_all_water_is_pore_water=vw/(vp-solid_volume_cm3),
                packing_fraction=vp/vb,interparticle_fraction=1-vp/vb,
                bed_solid_fraction=solid_volume_cm3/vb,bed_water_fraction=vw/vb,
                bed_air_fraction=(vb-solid_volume_cm3-vw)/vb)

def accepted_output(rate_kg_h,hours_day,days,uptime,product_yield):
    if min(rate_kg_h,hours_day,days)<0 or not all(0<=x<=1 for x in [uptime,product_yield]):raise ValueError("invalid input")
    return rate_kg_h*hours_day*days*uptime*product_yield

def carrier_water_budget(dry_g,solids_fraction,total_water_target_g):
    if dry_g<0 or total_water_target_g<0 or not 0<solids_fraction<=1:raise ValueError("invalid mass or solids fraction")
    product=dry_g/solids_fraction
    carrier=product-dry_g
    return dict(product_g=product,carrier_water_g=carrier,additional_water_g=total_water_target_g-carrier)

def audit():
    v=volume_partition(100,21.3025,52,1.,1180.40,487.)
    old=recycling_balance(2191500.)
    required=old["target_recycled_kg"]
    capacity=750*8*220
    cells=[]
    for uptime in [1.,.85,.8]:
      for quality in [1.,.95,.8]:
        q=accepted_output(750,8,220,uptime,quality)
        cells.append(dict(uptime=uptime,qualified_yield=quality,good_kg_year=q,margin_kg=q-required,arithmetic_capacity_meets=q>=required))
    area=.060*.060;vol=area*.020
    mass=vol*487*1000
    r={
      "date":"2026-10-23","input_scope":"v2.2 summary plus re-submitted v2.1 full text; v2.2 formula, process and cost breakdown still not provided",
      "physical_trials":0,"physical_success_probability":None,
      "density":{"inputs":{"mass_g":100,"solid_volume_cm3_supplied_not_rederived":21.3025,"water_g":52,"water_density_g_cm3_assumed":1,"particle_density_target":1180.40,"bed_density_target":487},**v,
                 "note":"additive solid+water volume assumption; hydration/bound water/closed pores and actual envelope remain unmeasured"},
      "regeneration":{"required_good_kg_from_v21_basis":required,"gross_nameplate_kg_year":capacity,
                      "minimum_uptime_if750_is_good_output":required/capacity,
                      "minimum_good_yield_at85pct_uptime_if750_is_input_or_unqualified_output":required/(capacity*.85),
                      "cases":cells,
                      "previous_wear_kg":old["wear_kg"],"previous_recycled_fraction_of_whole_bed":required/2191500,
                      "if_1051920_is_new_wear_and80pct_recovered_recycle_kg":required*.8,
                      "if_1051920_is_new_wear_and80pct_recovered_makeup_with3pct_storm_kg":required*.2+2191500*.03},
      "drainage":{"convention":"rain per slope surface area as in original formula, angle30deg, steady uniform layer",
                   "cases":[{"rain_mm_h":i,"k_m_s":k,"h_m":drainage_height(i,10,k)} for k in [.0025,.001] for i in [100,150]],
                   "k_min_below450mm_rain100":.1/3600*10/(.45*.5),
                   "k_min_below450mm_rain150":.15/3600*10/(.45*.5),
                   "222_2mm_claim_depends_on_100mm_h_k0025":True},
      "cost":{"new_capex_yen_supplied":1057000000,"previous_capex_yen":1020025000,
              "capex_increase_yen":1057000000-1020025000,
              "new_opex_yen_supplied":246700000,"previous_opex_yen":241700000,
              "opex_increase_yen":246700000-241700000,
              "new_total_costs_verified":False},
      "feed_water_example":{"basis":"illustration only: v2.1 CNF dry4.5g, assumed dispersion2wt%; not an identified v2.2 ingredient grade",**carrier_water_budget(4.5,.02,52)},
      "sample_budget":{"illustration_only_not_standard_qualified":True,"box_dimensions_m":[.060,.060,.020],
                        "box_volume_cm3":vol*1e6,"mass_g_at487":mass,
                        "three_normal_loads_one_condition_mass_g":mass*3,
                        "three_batches_three_histories_three_loads_mass_g":mass*27,
                        "normal_stress_kPa":[25,50,80],"normal_force_N":[s*1000*area for s in [25,50,80]],
                        "notes":"fresh specimen for each destructive test; 100g batch cannot supply three illustrated shear specimens, before other measurements"},
      "dimensional_check":{"Sf50_kPa_given_c_phi":42+50*math.tan(math.radians(36)),
                           "triangular_work_J_m2_if_delta10um":.5*(42+50*math.tan(math.radians(36)))*1000*10e-6}}
    checks={
      "particle_phase_volumes_close":math.isclose(v["particle_envelope_cm3"],21.3025+v["water_cm3"]+v["particle_air_cm3"]),
      "particle_phase_fractions_close":math.isclose(v["particle_solid_fraction"]+v["particle_water_fraction"]+v["particle_gas_fraction"],1),
      "bed_phase_fractions_close":math.isclose(v["bed_solid_fraction"]+v["bed_water_fraction"]+v["bed_air_fraction"],1),
      "two_independent_packing_formulas":math.isclose(v["packing_fraction"],487/1180.4),
      "dispersion_mass_balance":math.isclose(carrier_water_budget(4.5,.02,52)["carrier_water_g"]+4.5,carrier_water_budget(4.5,.02,52)["product_g"]),
      "dry_feed_adds_no_carrier_water":carrier_water_budget(4.5,1,52)["carrier_water_g"]==0,
      "zero_yield_gives_zero_output":accepted_output(750,8,220,.85,0)==0,
      "capacity_threshold_closes":math.isclose(accepted_output(750,8,220,required/capacity,1),required),
      "rain_doubles_height":math.isclose(drainage_height(200,10,.0025),2*drainage_height(100,10,.0025)),
      "specified_moisture_is_not_measured":r["physical_trials"]==0 and r["physical_success_probability"] is None}
    assert all(checks.values())
    r["arithmetic_checks"]=checks
    return r
