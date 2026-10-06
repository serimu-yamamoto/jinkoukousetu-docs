"""Audit VT13 assumptions, not a prediction of real ski friction.

Requires NumPy. Run this file next to unmodified vt13_mu.py.
Original and changed closure assumptions use IDENTICAL random draws.
No supplier prices, measured properties, or success probabilities are generated.
"""
import sys
sys.dont_write_bytecode = True
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'vt13_mu.py'
spec = importlib.util.spec_from_file_location('vt13_reference', SOURCE)
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)
N, SEED = 200000, 20261006
LEVELS = [0, .03, .06, .10, .288, .38]

def draws(theta):
    # Operation order and draws deliberately mirror vt13_mu.py lines 4-25.
    r = np.random.default_rng(SEED)
    ts, tr = .38, .02
    mass = r.uniform(40,110,N); dyn = r.uniform(1,2.5,N); W=mass*9.81*dyn/2
    v = r.uniform(2,10,N); L=r.uniform(1,1.4,N); w=.07; A=L*w; p=W/A
    d=r.uniform(.3e-3,.6e-3,N); rough=r.uniform(.05,.3,N)*d
    fc=r.uniform(.06,.12,N); S=6*(1-ts)/d
    hav=np.minimum(theta,fc)/S+np.maximum(theta-fc,0)/(ts-fc)*d*.5
    eta=r.uniform(.7e-3,1e-3,N)
    hhd=r.uniform(.1,1,N)*np.sqrt(eta*v*L/p)
    h=np.minimum(hhd,hav); alpha=1-np.exp(-(h/rough)**1.5)
    mudry=np.exp(r.normal(np.log(.16),.3,N))
    beta=r.uniform(.3,.8,N); thw=r.uniform(.005,.03,N)
    mub=mudry*(1-beta*(1-np.exp(-theta/thw)))
    Se=np.clip((theta-tr)/(ts-tr),0,1)
    nb=np.clip((Se-.1)/.6,0,1)/d**2
    Fcap=nb*A*2*np.pi*.2*d*.072*r.uniform(.4,.9,N)
    loose=r.uniform(0,6e-3,N); crit=r.uniform(.7,.9,N)
    sink=loose*np.clip((Se-crit)/(1-crit),0,1)
    mup=.5*r.uniform(1800,2100,N)*v**2*w*sink*r.uniform(1,2,N)/W
    return dict(W=W,v=v,A=A,eta=eta,h=h,alpha=alpha,mudry=mudry,mub=mub,Fcap=Fcap,
                mup=mup,sink=sink,Se=Se)

def summarize(a, cap=None, boundary=True):
    alpha=a['alpha'] if cap is None else np.minimum(a['alpha'],cap)
    mu_b=a['mub'] if boundary else a['mudry']
    mu_v=a['eta']*a['v']/np.maximum(a['h'],1e-7)*alpha*a['A']/a['W']
    mu=(1-alpha)*mu_b*(a['W']+a['Fcap'])/a['W']+mu_v+a['mup']
    return dict(mu_p05=float(np.percentile(mu,5)),mu_median=float(np.median(mu)),
                mu_p95=float(np.percentile(mu,95)),
                fraction_below_0_1_in_assumed_distribution=float(np.mean(mu<=.1)),
                alpha_median=float(np.median(alpha)),water_film_um_median=float(np.median(a['h'])*1e6),
                capillary_over_normal_median=float(np.median(a['Fcap']/a['W'])),
                sink_mm_p95=float(np.percentile(a['sink']*1000,95)))

rows=[]; errors=[]
for theta in LEVELS:
    a=draws(theta)
    cases={
        'original': summarize(a),
        'no_assumed_boundary_lubrication':summarize(a,boundary=False),
        'fluid_load_fraction_capped_at_0_25':summarize(a,cap=.25),
        'no_fluid_load_support':summarize(a,cap=0),
        'no_boundary_lubrication_or_fluid_support':summarize(a,cap=0,boundary=False),
    }
    reference=original.run((theta,N,SEED))
    observed=np.array([cases['original']['mu_p05'],cases['original']['mu_median'],cases['original']['mu_p95']])
    errors.append(float(np.max(np.abs(observed-reference[1]))))
    assert np.allclose(observed,reference[1],rtol=0,atol=1e-12)
    rows.append(dict(theta_volume_fraction=theta,effective_saturation=float(a['Se']),
                     geometric_saturation=theta/.38,cases=cases))

calcite_rho, ice_rho, porosity = 2710., 917., .38
dry_bulk=calcite_rho*(1-porosity)
wet_bulk=dry_bulk+1000*porosity
d=.45e-3; R=d/2; gamma=.072; gravity=9.81
capillary_force=2*math.pi*R*gamma
grain_weight=calcite_rho*4*math.pi*R**3/3*gravity
geometry=dict(calcite_solid_density_kg_m3=calcite_rho,ice_solid_density_kg_m3=ice_rho,
              original_model_porosity=porosity,dry_bulk_kg_m3=dry_bulk,fully_saturated_bulk_kg_m3=wet_bulk,
              solid_density_ratio_calcite_to_ice=calcite_rho/ice_rho,
              calcite_required_porosity_for_bulk_targets={str(rho):1-rho/calcite_rho for rho in [300,350,500]},
              dry_loading_kg_m2_at_0_45m=dry_bulk*.45,saturated_loading_kg_m2_at_0_45m=wet_bulk*.45,
              representative_grain_diameter_m=d,ideal_bridge_force_N=capillary_force,
              grain_weight_N=grain_weight,ideal_bridge_to_weight_ratio=capillary_force/grain_weight,
              ideal_bridge_note='Perfect-wetting small-gap scale estimate; not total ski drag or a measured contact force.',
              acceleration_at_30deg_mu_0_16_m_s2=gravity*(math.sin(math.pi/6)-.16*math.cos(math.pi/6)),
              model_sink_depth_max_mm=6.)
assert abs(dry_bulk-1680.2)<1e-9
assert wet_bulk>dry_bulk and geometry['acceleration_at_30deg_mu_0_16_m_s2']>0
assert abs(geometry['calcite_required_porosity_for_bulk_targets']['350']-.8708487084870848)<1e-12
out=dict(date='2026-10-06',meaning='Sensitivity audit only. All variants uncalibrated; no experimental success probability.',
         source='vt13_mu.py',source_sha256_normalized_LF=hashlib.sha256(SOURCE.read_text(encoding='utf8').replace('\r\n','\n').encode()).hexdigest(),
         numpy_version=np.__version__,draw_count_per_level=N,seed=SEED,levels=LEVELS,
         original_reproduction_max_error=max(errors),variant_count_per_level=5,rows=rows,geometry=geometry,
         physical_validation=False,raw_snow_target='Measured groomed fresh-snow references required; no universal mu threshold adopted.')
(ROOT/'snow_origin_audit_results_20261006.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('VT13 original reproduced; max absolute quantile error:',max(errors))
for row in rows:
    cases=row['cases']
    print('theta={:.3f}: original={:.3f}, no_boundary={:.3f}, alpha<=.25={:.3f}, no_fluid={:.3f}, neither={:.3f}'.format(
        row['theta_volume_fraction'],*[v['mu_median'] for v in cases.values()]))
print('Geometry:',json.dumps(geometry,ensure_ascii=False))
