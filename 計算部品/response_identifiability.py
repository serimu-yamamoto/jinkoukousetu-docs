"""Identifiability and linear geometry audit; no calibrated ski-friction model."""
import math
from viscoelastic_glide import complex_stiffness
def positive(x):
 if not math.isfinite(x) or x<=0:raise ValueError('positive finite value required')
 return x
def sls_family(E_storage_MPa,E_loss_MPa,frequency_Hz,x):
 ep=positive(E_storage_MPa);el=positive(E_loss_MPa);f=positive(frequency_Hz);x=positive(x)
 e0=ep-el*x
 if e0<=0:raise ValueError('x must preserve positive equilibrium modulus')
 return dict(E0_MPa=e0,deltaE_MPa=el*(1+x*x)/x,tau_s=x/(2*math.pi*f),
             E_infinity_MPa=ep+el/x,x_at_anchor=x,anchor_frequency_Hz=f)
def response(frequency_Hz,family):
 # Same standard-linear-solid algebra as the shared112 component; numbers here are MPa.
 return complex_stiffness(frequency_Hz,family['E0_MPa'],family['deltaE_MPa'],family['tau_s'])
def geometry_compensations(E_reference,E_hot,loss_reference,loss_hot):
 er=positive(E_reference);eh=positive(E_hot);lr=positive(loss_reference);lh=positive(loss_hot)
 radius=(er/eh)**.25
 return dict(storage_ratio_hot_to_reference=eh/er,loss_tangent_reference=lr/er,
     loss_tangent_hot=lh/eh,matched_storage_loss_ratio=(lh/eh)/(lr/er),
     circular_radius_ratio=radius,circular_active_material_ratio=radius**2,
     active_span_length_ratio=(eh/er)**(1/3),
     effective_parallel_member_ratio=er/eh,
     assumptions='Same uniform linear bending material, boundary condition and frequency; no whole-grain guarantee.')
def interval_ratio(n,spread_n,d,spread_d):
 positive(n);positive(d)
 if spread_n<0 or spread_d<0 or n-spread_n<=0 or d-spread_d<=0:raise ValueError('positive interval endpoints required')
 return dict(low=(n-spread_n)/(d+spread_d),central=n/d,high=(n+spread_n)/(d-spread_d),
             interpretation='Arithmetic corners of reported spreads; NOT confidence interval or independent sampling model.')
def partial_mass_cost(core_kg,active_fraction,active_material_ratio,price_jpy_kg):
 positive(core_kg);positive(active_material_ratio)
 if not 0<=active_fraction<=1 or price_jpy_kg<0:raise ValueError('invalid fraction or price')
 added=core_kg*active_fraction*(active_material_ratio-1)
 return dict(core_kg=core_kg,active_mass_fraction_assumed=active_fraction,added_kg=added,
             assumed_jpy_per_kg=price_jpy_kg,added_material_only_jpy=added*price_jpy_kg)
