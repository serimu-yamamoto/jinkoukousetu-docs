"""Conditional factory inventory; lab enzyme charge is not catalytic capacity."""
import math
def inventory(target_kg, concentration_mM, phosphate_mM, mw_guanine, mw_guanosine,
              isolation_yield, placement_yield, enzyme_units_per_mL):
    values=[target_kg,concentration_mM,phosphate_mM,mw_guanine,mw_guanosine,enzyme_units_per_mL]
    if not all(math.isfinite(v) and v>0 for v in values):
        raise ValueError("Positive finite inputs required")
    if not all(math.isfinite(v) and 0<v<=1 for v in [isolation_yield,placement_yield]):
        raise ValueError("Yields must be in (0,1]")
    if phosphate_mM<concentration_mM:
        raise ValueError("Insufficient phosphate for assumed complete conversion")
    volume=target_kg/(concentration_mM*mw_guanine/1000*isolation_yield*placement_yield)
    converted_mol=volume*concentration_mM
    phosphate_mol=volume*phosphate_mM
    return dict(target_retained_kg=target_kg,isolation_yield_assumed=isolation_yield,
        placement_yield_assumed=placement_yield,batch_equivalent_liquid_m3=volume,
        guanosine_input_kg=converted_mol*mw_guanosine/1000,
        guanine_generated_kg=converted_mol*mw_guanine/1000,
        isolated_crystal_kg=target_kg/placement_yield,
        isolation_loss_kg=converted_mol*mw_guanine/1000-target_kg/placement_yield,
        placement_loss_kg=target_kg/placement_yield-target_kg,
        phosphate_input_mol=phosphate_mol,phosphate_consumed_mol=converted_mol,
        inorganic_phosphate_remaining_mol=phosphate_mol-converted_mol,
        ribose1phosphate_generated_mol=converted_mol,
        enzyme_charge_units_if_lab_loading_preserved=volume*1e6*enzyme_units_per_mL,
        note="Complete substrate conversion assumed; yields and lab-to-factory scaling unverified. No credit for recycling, no morphology transfer.")
def reactor_inventory(feed_m3,batch_hours,production_days,uptime_fraction):
    if not all(math.isfinite(v) and v>0 for v in [feed_m3,batch_hours,production_days,uptime_fraction]) or uptime_fraction>1:
        raise ValueError("Invalid production schedule")
    return feed_m3*batch_hours/(24*production_days*uptime_fraction)
