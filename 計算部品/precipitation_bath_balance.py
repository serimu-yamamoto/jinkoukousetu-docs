"""Ideal precipitation bath balances; no particle-shape or drying prediction."""
import math
def finite_positive(*xs):
    if not all(math.isfinite(x) and x>0 for x in xs):raise ValueError("Finite positive values required")
def feed_inventory(dry_polymer_kg,polymer_mass_fraction):
    finite_positive(dry_polymer_kg)
    if not math.isfinite(polymer_mass_fraction) or not 0<polymer_mass_fraction<1:raise ValueError("Invalid feed fraction")
    feed=dry_polymer_kg/polymer_mass_fraction
    return dict(polymer_kg=dry_polymer_kg,solution_kg=feed,solvent_kg=feed-dry_polymer_kg)
def growing_bath(initial_bath_kg,solvent_added_kg):
    finite_positive(initial_bath_kg)
    if not math.isfinite(solvent_added_kg) or solvent_added_kg<0:raise ValueError("Invalid solvent mass")
    total=initial_bath_kg+solvent_added_kg
    return dict(bath_mass_kg=total,solvent_mass_fraction=solvent_added_kg/total)
def product_at_bath_fraction(initial_bath_kg,target_fraction,polymer_feed_fraction):
    finite_positive(initial_bath_kg)
    if not 0<target_fraction<1:raise ValueError("Invalid target")
    perkg=feed_inventory(1,polymer_feed_fraction)['solvent_kg']
    return initial_bath_kg*target_fraction/(1-target_fraction)/perkg
def steady_balance(solvent_load_kg,recovered_load_fraction,target_fraction):
    finite_positive(solvent_load_kg)
    if not math.isfinite(recovered_load_fraction) or not 0<=recovered_load_fraction<=1 or not 0<target_fraction<1:raise ValueError("Invalid recovery or target")
    recovered=solvent_load_kg*recovered_load_fraction;residual=solvent_load_kg-recovered
    purge=residual/target_fraction;makeup=purge-residual
    return dict(gross_solvent_load_kg=solvent_load_kg,recovered_solvent_kg=recovered,residual_load_kg=residual,
        purge_solution_kg=purge,fresh_carrier_makeup_kg=makeup,purge_solvent_fraction=target_fraction,
        meaning="recovery fraction of incoming solvent load; not per-pass separator efficiency or emissions")
