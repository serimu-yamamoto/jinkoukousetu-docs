"""Incremental audit of received Capillo-Firn v2.2 response. No empirical data."""
import math
from capillo_v22_summary_audit import volume_partition, accepted_output
from capillo_v21_system_audit import drainage_height

FORMULA = [
 ("calcite",30.,2.71),("kaolinite",6.,2.60),("CNF_core",4.5,1.50),
 ("MCC_shell",2.5,1.50),("CMC_Ca",3.5,1.55),("gellan_Ca",1.5,1.50)]
def recovery_time_limit(target_kpa,plateau_kpa,initial_kpa=0.,deadline_s=1800.):
    """Illustrative exponential kinetics only; not fitted to any material."""
    if target_kpa>=plateau_kpa:return None
    if target_kpa<=initial_kpa:return math.inf
    return deadline_s/(-math.log((plateau_kpa-target_kpa)/(plateau_kpa-initial_kpa)))

def audit():
    vs=sum(m/rho for _,m,rho in FORMULA)
    part=volume_partition(100.,vs,52.,1.,1180.40,487.)
    target=42+50*math.tan(math.radians(36))
    drains=[]
    for angle in [30.,20.,math.degrees(math.asin(.25))]:
        for rain in [50.,100.,150.]:
            h=drainage_height(rain,10.,.0025,angle)
            drains.append(dict(angle_deg=angle,rain_mm_h=rain,
                height_if_rain_per_slope_area_mm=h*1000,
                height_if_vertical_rain_per_horizontal_area_mm=h*math.cos(math.radians(angle))*1000,
                spacing_limit_for_450mm_if_rain_per_slope_area_m=10*.45/h))
    mass=10000*.45*487
    recycled=mass*.6*.8
    capacity=accepted_output(750,8,220,.85,1)
    revenue=350*220*8500+35000000
    capex=1.057e9;opex=2.467e8
    pit=350.;area=10000.
    result=dict(physical_trials=0,physical_success_probability=None,
        input_kind="reported formula with assumed densities; model hypotheses",
        composition=FORMULA,solid_mass_g=sum(x[1] for x in FORMULA),
        solid_volume_cm3=vs,water_per_dry_solid=52/48,water_per_polymer_g_g=52/12,
        solid_fraction_of_no_gas_volume=vs/(vs+52),phase_partition=part,
        drainage=drains,
        recycling=dict(bed_kg=mass,wear_kg=mass*.6,required_good_product_kg=recycled,
            good_product_hours=recycled/750,planned_hours=8*220,
            minimum_uptime_if_good_product_output=recycled/(750*8*220),
            good_output_at_85pct_uptime_kg=capacity,
            good_output_at_85pct_uptime_80pct_yield_kg=accepted_output(750,8,220,.85,.8),
            required_yield_at_85pct_uptime=recycled/capacity),
        finance=dict(revenue_yen=revenue,capex_yen=capex,opex_yen=opex,ebitda_yen=revenue-opex,
            simple_payback_years=capex/(revenue-opex),costs_itemized=False),
        recovery=dict(target_kpa=target,triangular_fracture_work_j_m2=.5*target*1000*10e-6,
            illustrative_exponential_time_limits_s={str(p):recovery_time_limit(target,p) for p in [60.,80.,100.]},
            not_measured=True),
        pit=dict(nominal_m3=pit,water_only_rain_100mm_h_m3_h=area*.1,
            water_only_no_outflow_fill_minutes=pit/(area*.1)*60,
            assumed_3pct_lost_bulk_volume_m3=10000*.45*.03,
            remaining_volume_if_bulk_and_water_additive_m3=pit-10000*.45*.03,
            water_after_that_minutes=(pit-10000*.45*.03)/(area*.1)*60,
            illustrative_no_outflow_only=True))
    assert abs(sum(x[1] for x in FORMULA)+52-100)<1e-12
    assert abs(vs-21.3025)<.0001
    assert abs(part['particle_gas_fraction']+part['particle_water_fraction']+part['particle_solid_fraction']-1)<1e-12
    assert abs(drainage_height(50,10,.0025,math.degrees(math.asin(.25)))-drainage_height(100,10,.0025,30))<1e-12
    assert drainage_height(150,10,.0025,20)>.45
    assert result['recycling']['good_output_at_85pct_uptime_80pct_yield_kg']<recycled
    assert abs(revenue-opex-442800000)<.1
    assert recovery_time_limit(target,60) is None
    result['arithmetic_checks']=8
    return result
