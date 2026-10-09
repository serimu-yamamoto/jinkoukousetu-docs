"""Uncalibrated heat/mass-balance counterexamples; not PBS kinetics or strength."""
import math

def ledger(initial, events):
    """Mass fractions with equal, normalized melting enthalpy; melt occurs first."""
    if not math.isfinite(initial) or not 0 <= initial <= 1:
        raise ValueError("initial fraction")
    old, new, amorphous = float(initial), 0.0, 1.0-initial
    net, melted, formed = 0.0, 0.0, 0.0
    rows = []
    for e in events:
        a, b, c = (float(e[k]) for k in ("melt_original", "melt_new", "recrystallize"))
        if not all(math.isfinite(x) and x >= 0 for x in (a,b,c)):
            raise ValueError("nonnegative finite transfers required")
        if a > old+1e-12 or b > new+1e-12 or c > amorphous+a+b+1e-12:
            raise ValueError("transfer exceeds available phase")
        old -= a; new = new-b+c; amorphous += a+b-c
        net += a+b-c; melted += a+b; formed += c
        rows.append(dict(original_crystal=old, new_crystal=new,
                         amorphous=amorphous, net_heat_normalized=net))
    return dict(original_crystal=old, new_crystal=new, amorphous=amorphous,
                final_crystal=old+new, net_heat_normalized=net,
                cumulative_melt=melted, cumulative_recrystallization=formed,
                original_fraction_retained=old/initial if initial else None,
                trajectory=rows)

def sensible_heat(cp_kj_kg_k, start_c, end_c):
    """Sensible heat only, per kg solid; latent/solvent/losses/plant excluded."""
    if not all(math.isfinite(x) for x in (cp_kj_kg_k,start_c,end_c)) or cp_kj_kg_k <= 0 or end_c < start_c:
        raise ValueError("heating assumptions")
    return cp_kj_kg_k*(end_c-start_c)/3600.0

def treatment_inventory(density_kg_m3, bed_m, fraction, increment_yen_kg):
    """Budget sensitivity, not quote or proof that only contacts need treatment."""
    if not all(math.isfinite(x) for x in (density_kg_m3,bed_m,fraction,increment_yen_kg)):
        raise ValueError("finite values")
    if density_kg_m3 <= 0 or bed_m <= 0 or not 0 <= fraction <= 1 or increment_yen_kg < 0:
        raise ValueError("inventory assumptions")
    mass = density_kg_m3*bed_m
    return dict(bed_kg_m2=mass, treated_kg_m2=mass*fraction,
                increment_yen_m2=mass*fraction*increment_yen_kg)
