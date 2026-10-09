"""Conditional constant-volume washing models; no measured material properties."""
import math

def _nonneg(v):
    if not math.isfinite(v) or v < 0:
        raise ValueError("finite nonnegative input required")
    return v

def _rate(v):
    if not math.isfinite(v) or not 0 <= v <= 1:
        raise ValueError("transmission must lie in [0,1]")
    return v

def batch_fraction(hold, wash_each, stages):
    if _nonneg(hold) == 0 or _nonneg(wash_each) < 0 or isinstance(stages, bool) or not isinstance(stages, int) or stages < 0:
        raise ValueError("positive hold and nonnegative integer stages required")
    return (hold / (hold + wash_each)) ** stages

def concentration_fraction(D, solute_transmission, inlet_ratio=0.0):
    """c=C/C0; dc/dD=b-s*c. H held constant; inlet has b*C0 impurity."""
    D=_nonneg(D); s=_rate(solute_transmission); b=_nonneg(inlet_ratio)
    if s == 0:
        return 1 + b * D
    # Stable even for small s*D. Equivalent to b/s+(1-b/s)*exp(-s*D).
    return math.exp(-s*D) + b * (-math.expm1(-s*D)) / s

def product_yield(D, product_transmission):
    return math.exp(-_rate(product_transmission)*_nonneg(D))

def impurity_per_product_ratio(D, solute_transmission, product_transmission, inlet_ratio=0.0):
    """(impurity mass / product mass)_D relative to the initial mass ratio."""
    return concentration_fraction(D, solute_transmission, inlet_ratio) / product_yield(D, product_transmission)

def minimum_ratio(solute_transmission, product_transmission, inlet_ratio=0.0, max_D=30.0):
    """Minimum of q=c/y on [0,max_D], with stationary point if present."""
    s=_rate(solute_transmission); p=_rate(product_transmission); b=_nonneg(inlet_ratio); limit=_nonneg(max_D)
    points=[0.0,limit]
    if s > p > 0 and 0 < b < s-p:
        a=b/s
        d=math.log((s-p)*(1-a)/(p*a))/s
        if 0 < d < limit:
            points.append(d)
    d=min(points,key=lambda x:impurity_per_product_ratio(x,s,p,b))
    return {"D":d,"ratio":impurity_per_product_ratio(d,s,p,b),"max_D":limit}

def first_target(solute_transmission, product_transmission, inlet_ratio, target=0.001, max_D=30.0):
    if not math.isfinite(target) or not 0 < target < 1:
        raise ValueError("target must lie in (0,1)")
    m=minimum_ratio(solute_transmission,product_transmission,inlet_ratio,max_D)
    if m["ratio"] > target:
        return {"D":None,"reason":"target_not_reached_within_stated_D_range","minimum":m}
    lo=0.0; hi=m["D"]
    for _ in range(80):
        mid=(lo+hi)/2
        if impurity_per_product_ratio(mid,solute_transmission,product_transmission,inlet_ratio)>target:
            lo=mid
        else:
            hi=mid
    return {"D":hi,"reason":None,"minimum":m}

def clean_water_selectivity_limit(target, minimum_yield):
    """p/s upper bound for q<=target AND y>=minimum_yield, clean inlet."""
    if not 0 < target < 1 or not 0 < minimum_yield < 1:
        raise ValueError("fractions must lie in (0,1)")
    a=-math.log(minimum_yield); l=-math.log(target)
    return a/(l+a)

def delivered_inventory(delivered_kg, hold_L_per_initial_kg, D, product_transmission, input_jpy_per_kg):
    if _nonneg(delivered_kg)==0:
        raise ValueError("positive delivered mass required")
    h=_nonneg(hold_L_per_initial_kg); price=_nonneg(input_jpy_per_kg)
    y=product_yield(D,product_transmission)
    feed=delivered_kg/y
    return {"delivered_kg":delivered_kg,"yield_fraction":y,"input_kg":feed,
            "loss_kg":feed-delivered_kg,"hold_L":h*feed,"wash_m3":D*h*feed/1000,
            "replacement_only_jpy":(feed-delivered_kg)*price}
