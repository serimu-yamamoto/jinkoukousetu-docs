"""Cycle 51: source transcription and conditional design calculations.
No measurements of the proposed ski material; no success probability model.
Run: python -X utf8 model.py. Standard library only.
"""
from pathlib import Path
import csv
import json
import math

OUT = Path(__file__).resolve().parent
checks = []

def check(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append(name)

def close(a, b, tol=1e-10):
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)

def save_csv(name, rows):
    with (OUT / name).open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)

# S1 Table 2, visually checked on original PDF page 6. SD, not SE.
# Mechanical n=10 per group; crystallinity averages 11 measurements/type.
# SI test temperature/rate not obtained; these are NOT wet 50 C values.
raw = [
    ('crystallinity', 'percent', 29.6, 2.4, 45.4, 4.0),
    ('Young_modulus', 'GPa', 1.5, .3, 1.2, .2),
    ('yield_strength', 'MPa', 201, 22, 80, 6),
    ('engineering_tensile_strength', 'MPa', 344, 25, 192, 6),
    ('engineering_break_strain', 'percent', 71, 6, 162, 6),
    ('DSC_melting_temperature', 'degC', 149.1, .2, 160.7, .1),
]
evidence = [dict(property=p, unit=u, PP_mean=a, PP_SD=sa,
    PP_ER_1p5wtpct_mean=b, PP_ER_SD=sb, difference=b-a,
    ratio=None if u == 'degC' else b/a,
    source='10.1021/acsnano.4c00114 Table 2') for p,u,a,sa,b,sb in raw]
save_csv('source_table.csv', evidence)
check('Table 2 modulus ratio 0.8', close(evidence[1]['ratio'], .8))
check('Crystallinity up but yield down', evidence[0]['ratio'] > 1 > evidence[2]['ratio'])
check('Temperature difference not Celsius ratio', evidence[-1]['ratio'] is None and close(evidence[-1]['difference'], 11.6))

def changed_skin(q, eta):
    """Same OUTER radius: outer annulus converted to modulus eta*E."""
    return (1-q)**4 + eta * (1-(1-q)**4)

def added_skin(q, eta):
    """Same CORE radius: added perfectly bonded shell; core unchanged."""
    return 1 + eta*((1+q)**4 - 1)

def softened_zone(f, eta, placement):
    """Uniform circular cantilever, full cross-section softened in zone."""
    weight = f**3 if placement == 'tip' else 1-(1-f)**3
    return 1/(1+(1/eta-1)*weight)

skin = [dict(thickness_radius_ratio=q, modulus_ratio=eta,
    changed_same_outer_EI_ratio=changed_skin(q,eta),
    added_same_core_EI_ratio=added_skin(q,eta))
    for q in [0,.05,.1,.2] for eta in [.1,.3,.8,1]]
save_csv('skin.csv', skin)
zone = [dict(length_fraction=f, modulus_ratio=eta, placement=p,
    stiffness_ratio=softened_zone(f,eta,p))
    for f in [.1,.2,.5] for eta in [.1,.3,.8] for p in ['root','tip']]
save_csv('placement.csv', zone)
check('No shell change at zero thickness', close(changed_skin(0,.1),1) and close(added_skin(0,.1),1))
check('Matched modulus replacement unchanged', close(changed_skin(.2,1),1))
check('Added shell increases EI if core retained', all(x['added_same_core_EI_ratio']>=1 for x in skin))
check('Modified skin never exceeds parent for eta<=1', all(x['changed_same_outer_EI_ratio']<=1 for x in skin))
check('End zone is less costly than root zone', all(softened_zone(f,e,'tip')>softened_zone(f,e,'root') for f in [.1,.2,.5] for e in [.1,.3,.8]))
check('Full length softening equals eta', close(softened_zone(1,.3,'tip'),.3))
# Independent midpoint compliance integration, not a second copy of cubic formula.
n=20000
for p in ['root','tip']:
    integ=sum((1-(i+.5)/n)**2 / (.1 if ((i+.5)/n < .2 if p=='root' else (i+.5)/n > .8) else 1) for i in range(n))/n
    check('Compliance integral '+p, close((1/3)/integ,softened_zone(.2,.1,p),1e-7))

# S3 abstract: 10^-9...10^-11 cm2/s across tested temperatures, NOT all at 50 C.
diffusion=[dict(D_m2_s=d, elapsed_h=h, characteristic_rms_um=math.sqrt(2*d*h*3600)*1e6)
    for d in [1e-15,1e-14,1e-13] for h in [8,15*24,100*24]]
save_csv('diffusion_scale.csv',diffusion)
check('cm2 to m2 conversion', close(1e-9*1e-4/1e-13,1))
check('Diffusion length at 8 h lower scenario', close(diffusion[0]['characteristic_rms_um'],7.5894663844))
check('100x D gives 10x length', close(diffusion[6]['characteristic_rms_um']/diffusion[0]['characteristic_rms_um'],10))

# Independent design assumptions, not PP, ER or LL measured coefficients.
mu_base=.25
mu_crystal=.05
mu_target=.10
lam=(mu_base-mu_target)/(mu_base-mu_crystal)
mean_pressure_MPa=2
allow_pressure_MPa=5  # illustrative; no selected material validated
surface_m2=6e6  # whole bed geometry assumption carried from Cycle 47
rho_kg_m3=1200
t0_um=.5
price_JPY_kg=10000
yield_fraction=.8
stock_full_kg=surface_m2*t0_um*1e-6*rho_kg_m3

patch=[]
for a in [.2,.3,.5,.75]:
    # phi=a is a deliberately restrictive comparison, not a random-grain identity.
    phi=a
    for wear_ratio in [.5,1,2]:
        # Wear volume/distance ratio versus full reference = lam*wear_ratio.
        lifetime_ratio=phi/(lam*wear_ratio)
        equal_life_thickness_um=t0_um/lifetime_ratio
        initial_stock_kg=stock_full_kg*phi
        equal_life_stock_kg=initial_stock_kg/lifetime_ratio
        patch.append(dict(projected_area_fraction=a, whole_surface_coated_fraction=phi,
            crystal_load_fraction=lam, specific_wear_ratio=wear_ratio,
            crystal_pressure_MPa=mean_pressure_MPa*lam/a,
            initial_thickness_um=t0_um, initial_stock_kg=initial_stock_kg,
            initial_purchase_JPY=initial_stock_kg/yield_fraction*price_JPY_kg,
            same_thickness_lifetime_ratio=lifetime_ratio,
            equal_life_thickness_um=equal_life_thickness_um,
            equal_life_stock_kg=equal_life_stock_kg,
            equal_life_purchase_JPY=equal_life_stock_kg/yield_fraction*price_JPY_kg,
            illustrative_pressure_screen=mean_pressure_MPa*lam/a<=allow_pressure_MPa+1e-12))
save_csv('patch_cost.csv',patch)
check('Load share 0.75', close(lam,.75))
check('Friction force balance', close(mu_crystal*lam+mu_base*(1-lam),mu_target))
check('20pct area uniform pressure fails target', mu_crystal*.2+mu_base*.8>mu_target)
check('Area/load pressure balance', all(close(x['crystal_pressure_MPa']*x['projected_area_fraction'],mean_pressure_MPa*lam) for x in patch))
p20=next(x for x in patch if x['projected_area_fraction']==.2 and x['specific_wear_ratio']==1)
p50=next(x for x in patch if x['projected_area_fraction']==.5 and x['specific_wear_ratio']==1)
check('20pct area pressure 7.5 MPa', close(p20['crystal_pressure_MPa'],7.5))
check('20pct area equal life needs 1.875 um', close(p20['equal_life_thickness_um'],1.875))
check('50pct area equal life needs .75 um', close(p50['equal_life_thickness_um'],.75))
check('Equal life material cancels area under stated assumptions', close(p20['equal_life_stock_kg'],p50['equal_life_stock_kg']))
check('20pct initial cost versus equal life cost', close(p20['initial_purchase_JPY'],9000000) and close(p20['equal_life_purchase_JPY'],33750000))
check('More area lowers pressure', p50['crystal_pressure_MPa']<p20['crystal_pressure_MPa'])

rate=.08
years=10
crf=rate/(1-(1+rate)**(-years))
budget=5000000  # coating-only illustrative annual budget, NOT whole business budget
capital_year=p50['equal_life_purchase_JPY']*crf
cost=dict(full_coat_reference_stock_kg=stock_full_kg,
    full_coat_reference_purchase_JPY=stock_full_kg/yield_fraction*price_JPY_kg,
    equal_life_patch_stock_kg=p50['equal_life_stock_kg'],
    equal_life_patch_purchase_JPY=p50['equal_life_purchase_JPY'],
    capital_recovery_factor=crf, annualized_initial_JPY=capital_year,
    coating_only_budget_JPY_y=budget, budget_before_replacement_JPY_y=budget-capital_year,
    price_ceiling_without_replacement_JPY_kg=budget/(p50['equal_life_stock_kg']/yield_fraction*crf))
annual=[dict(annual_replacement_fraction=r, coating_price_JPY_kg=p,
    annualized_capital_and_replacement_JPY=p50['equal_life_stock_kg']/yield_fraction*p*(crf+r),
    price_ceiling_JPY_kg=budget/(p50['equal_life_stock_kg']/yield_fraction*(crf+r)))
    for r in [0,.01,.05,.1] for p in [5000,10000]]
save_csv('annual_cost.csv',annual)
check('Annualization positive and finite', 0<crf<1)
check('No free recurring cost after capitalization', cost['budget_before_replacement_JPY_y']<0)
check('Cost proportional to wear coefficient scenario', close(next(x for x in patch if x['projected_area_fraction']==.5 and x['specific_wear_ratio']==2)['equal_life_stock_kg'],2*p50['equal_life_stock_kg']))
check('10pct replacement at 5000 fits coating-only budget before other costs', annual[-2]['annualized_capital_and_replacement_JPY']<budget)
result=dict(physical_tests=0, physical_success_probability=None,
    source_scope='Other materials/systems; not measurements of H51',
    hypothesis='H51: broad load seats; protected unmodified roots; localized retained crystals',
    checks_passed=len(checks), checks=checks,
    row_counts=dict(evidence=len(evidence),skin=len(skin),placement=len(zone),diffusion=len(diffusion),patch=len(patch),annual=len(annual)),
    illustrative=dict(lambda_required=lam, min_projected_fraction=lam*mean_pressure_MPa/allow_pressure_MPa,
        root20pct_eta01_k_ratio=softened_zone(.2,.1,'root'),
        tip20pct_eta01_k_ratio=softened_zone(.2,.1,'tip')),
    cost=cost,
    limitations=['No validated wet-50C material constants', 'No calibrated wear coefficient or lifetime',
        'No mapping from total geometric coverage to load share in random grain bed',
        'Diffusion RMS is a scale, not a front or ER-specific 50C prediction',
        'No additive adoption or permission exception', 'No claim of safety or winter acceptance'])
(OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(checks_passed=len(checks),rows=result['row_counts'],cost=cost),ensure_ascii=False))
