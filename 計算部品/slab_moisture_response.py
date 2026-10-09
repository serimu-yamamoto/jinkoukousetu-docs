"""Constant-D, two-sided slab sorption. Geometry diagnostic, not a material qualification.
h is full thickness; D and time must use consistent units.
No swelling, degradation, freezing, external film or friction model.
"""
import math

def uptake(fo):
    if not math.isfinite(fo) or fo < 0:
        raise ValueError("finite nonnegative Fourier number required")
    if fo == 0:
        return 0.0
    total = 0.0
    for n in range(100000):
        j = 2*n+1
        term = math.exp(-math.pi**2*j*j*fo)/(j*j)
        total += term
        if term < 1e-16:
            return max(0.0, min(1.0, 1-8*total/math.pi**2))
    raise ValueError("Fourier number too small for this series")

def time_to_fraction(fraction, thickness_mm, D_mm2_h):
    if not (0 < fraction < 1) or not all(math.isfinite(x) and x>0 for x in [thickness_mm,D_mm2_h]):
        raise ValueError("positive dimensions and 0<fraction<1")
    lo, hi = 0.0, 1.0
    while uptake(hi) < fraction:
        hi *= 2
    for _ in range(80):
        mid = (lo+hi)/2
        if uptake(mid) < fraction:
            lo = mid
        else:
            hi = mid
    fo = (lo+hi)/2
    return {"Fo":fo,"hours":fo*thickness_mm**2/D_mm2_h}

def pulse_remaining(wet_h, dry_h, thickness_mm, D_mm2_h):
    if not all(math.isfinite(x) and x>=0 for x in [wet_h,dry_h]) or not all(math.isfinite(x) and x>0 for x in [thickness_mm,D_mm2_h]):
        raise ValueError("invalid duration or material dimensions")
    scale = D_mm2_h/thickness_mm**2
    loaded = uptake(wet_h*scale)
    remaining = uptake((wet_h+dry_h)*scale)-uptake(dry_h*scale)
    return {"before_dry_fraction_of_equilibrium":loaded,
            "after_dry_fraction_of_equilibrium":remaining,
            "remaining_fraction_of_loaded":None if loaded==0 else remaining/loaded}

def finite_volume(fo, cells):
    """Independent cell-centered diffusion operator with two Dirichlet faces.
    Analytical matrix exponential via real symmetric eigendecomposition.
    """
    import numpy as np
    from scipy.linalg import eigh_tridiagonal
    if fo<0 or not math.isfinite(fo) or not isinstance(cells,int) or cells<2:
        raise ValueError("invalid mesh or time")
    d=np.full(cells,-2.0*cells*cells);d[0]=d[-1]=-3.0*cells*cells
    e=np.full(cells-1,float(cells*cells))
    vals,vecs=eigh_tridiagonal(d,e)
    weights=vecs.sum(axis=0)**2/cells
    return float(1-(weights*np.exp(vals*fo)).sum())
