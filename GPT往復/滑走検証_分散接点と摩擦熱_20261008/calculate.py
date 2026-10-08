"""Independent analytical screening, Python 3 standard library only.
Not experimental evidence. All inputs in inputs.json; no random pass fraction.
Run: python calculate.py (writes results.json and validation.json here).
"""
from pathlib import Path
import json, math, itertools
P = Path(__file__).resolve().parent
I = json.loads((P/'inputs.json').read_text(encoding='utf-8-sig'))
C, T, L, B, O = (I[k] for k in ('contact','thermal','layout','budget','operation'))
pi = math.pi

def resistance(a, k, cvol, v):
    # Area-average circular uniform-flux source. n=2 asymptotic blend.
    # Muzychka & Yovanovich 2001, Eqs 15,24,36, circular b=a.
    rs = 8/(3*pi*pi*k*a)
    if v == 0:
        return rs
    pe = v*a*cvol/k
    rm_fast = 1/(pi*k*a*math.sqrt(pe))
    return 1/math.sqrt(1/rs**2 + 1/rm_fast**2)

def single(F, R_um, v, mu, kg=None):
    kg = T['grain_k_W_mK'] if kg is None else kg
    E, R = C['equivalent_E_MPa']*1e6, R_um*1e-6
    a = (3*F*R/(4*E))**(1/3)
    area = pi*a*a
    rs = resistance(a, kg, 1, 0)  # stationary resistance independent of Cvol
    rm = resistance(a, T['base_k_W_mK'], T['base_Cvol_J_m3K'], v)
    power = mu*F*v
    dt = power/(1/rs+1/rm)
    qs, qm = dt/rs, dt/rm
    tc = 2*a/v
    return dict(force_N=F,radius_um=R_um,a_um=a*1e6,area_um2=area*1e12,
                a_over_R=a/R,geometry_diagnostic_ok=a/R<=C['hertz_geometry_diagnostic_limit_a_over_R'],
                pmax_MPa=1.5*F/area/1e6,indentation_um=a*a/R*1e6,
                speed_m_s=v,mu=mu,grain_k_W_mK=kg,
                Pe=v*a*T['base_Cvol_J_m3K']/T['base_k_W_mK'],
                base_pulse_us=tc*1e6,grain_loaded_s=T['ski_length_m']/v,
                Rs_K_W=rs,Rm_K_W=rm,power_W=power,heat_to_grain_W=qs,heat_to_base_W=qm,
                grain_heat_fraction=qs/power,delta_average_K=dt,
                interface_average_C=T['initial_C']+dt,
                no_grain_heat_intake_average_C=T['initial_C']+power*rm)

def case(R,phi,n,v,mu,kg=None):
    ft=C['nominal_pressure_Pa']*(C['pitch_um']*1e-6)**2/phi
    row=single(ft/n,R,v,mu,kg)
    row.update(support_fraction=phi,contacts=n,total_force_N=ft,
               total_area_um2=n*row['area_um2'])
    return row

def pulse_peak(row, count, spacing_um):
    # 1-D halfspace superposition at downstream contact centreline, all heat
    # to the base. q applies on each centre chord for 2a/v. Laterally separated
    # tracks and full circular averages are NOT represented by this function.
    a=row['a_um']*1e-6
    v=row['speed_m_s']
    tc=2*a/v
    period=spacing_um*1e-6/v
    assert count==1 or period>=tc
    alpha=T['base_k_W_mK']/T['base_Cvol_J_m3K']
    q=row['power_W']/(pi*a*a)
    terms=[math.sqrt(j*period+tc)-math.sqrt(j*period) for j in range(count)]
    peak=2*q*math.sqrt(alpha)/(T['base_k_W_mK']*math.sqrt(pi))*sum(terms)
    return dict(inline_contacts=count,spacing_um=spacing_um,speed_m_s=v,
                pulse_peak_rise_K=peak,pulse_peak_C=T['initial_C']+peak,
                wake_multiplier=sum(terms)/math.sqrt(tc))

ref=(C['reference_support_fraction'],C['reference_speed_m_s'],C['reference_mu'])
phi,v,mu=ref
cases=[case(r,f,n,s,m) for r,f,n,s,m in itertools.product(
    C['radii_um'],C['support_fractions'],C['equal_contact_counts'],C['speeds_m_s'],C['friction_coefficients'])]
representatives=[case(50,phi,1,v,mu),case(150,phi,1,v,mu),case(300,phi,1,v,mu),
                 case(150,phi,4,v,mu),case(150,phi,1,v,mu,2)]
conductivity=[case(r,phi,1,v,m,k) for r,m,k in itertools.product(
    C['radii_um'],C['friction_coefficients'],T['grain_k_sensitivity'])]
load_cases=[]
ft=case(150,phi,1,v,mu)['total_force_N']
for weights,speed in itertools.product(I['load_shares'],C['speeds_m_s']):
    active=[single(ft*w,150,speed,mu) for w in weights if w>0]
    load_cases.append(dict(shares=weights,speed_m_s=speed,
        max_isolated_average_C=max(x['interface_average_C'] for x in active),
        total_area_um2=sum(x['area_um2'] for x in active),
        peak_pressure_MPa=max(x['pmax_MPa'] for x in active),
        max_contact_load_fraction=max(weights)))
wakes=[]
for speed,n,d in itertools.product(C['speeds_m_s'],L['inline_counts'],L['centre_spacing_um']):
    wakes.append(pulse_peak(case(150,phi,4,speed,mu),n,d))
small=case(150,phi,4,v,mu)
large=case(300,phi,1,v,mu)
layout=dict(small_four=small,large_one=large,
    small_isolated=pulse_peak(small,1,80),square_aligned_two=pulse_peak(small,2,80),
    row_aligned_four=pulse_peak(small,4,80),large_isolated=pulse_peak(large,1,80),
    cap_aperture_radius_um=L['land_radius_um'],
    spherical_cap_height_um=150-math.sqrt(150**2-L['land_radius_um']**2),
    cap_centre_distance_um=80,land_edge_gap_um=80-2*L['land_radius_um'],
    nominal_uniform_base_rise_K=2*mu*C['nominal_pressure_Pa']*v*
       math.sqrt(T['base_k_W_mK']/T['base_Cvol_J_m3K']*T['ski_length_m']/v)/
       (T['base_k_W_mK']*math.sqrt(pi)))
# Economics: materials only under inherited fixed inventory; no vendor prices.
mass=O['area_m2']*O['depth_m']*O['bulk_density_kg_m3']
i,n=B['discount'],B['years']
crf=i*(1+i)**n/((1+i)**n-1)
def annual(premium,replacement):
    return (B['nonmaterial_capital_JPY']+mass*(B['material_JPY_kg']+premium))*crf + \
        B['annual_fixed_JPY']+mass*(B['material_JPY_kg']+premium)*replacement
base=annual(0,B['annual_material_replacement_fraction'])
margin=B['annual_budget_JPY']-base
cost_rows=[]
for premium,replacement in itertools.product(I['cost']['finished_material_premiums_JPY_kg'],
                                              I['cost']['annual_replacement_fractions']):
    total=annual(premium,replacement)
    cost_rows.append(dict(premium_JPY_kg=premium,replacement_fraction=replacement,
        annual_total_JPY=total,remaining_annual_JPY=B['annual_budget_JPY']-total))
reform=[]
for premium,fraction in itertools.product(I['cost']['finished_material_premiums_JPY_kg'],O['reform_fractions']):
    remain=B['annual_budget_JPY']-annual(premium,B['annual_material_replacement_fraction'])
    throughput=mass*fraction*O['closures_per_year']
    reform.append(dict(premium_JPY_kg=premium,reform_fraction_per_closure=fraction,
        annual_reform_kg=throughput,remaining_annual_JPY=remain,
        process_budget_JPY_kg=remain/throughput if remain>=0 else None))
cost=dict(mass_kg=mass,CRF=crf,annual_baseline_JPY=base,remaining_annual_JPY=margin,
    maximum_finished_premium_JPY_kg=margin/(mass*(crf+B['annual_material_replacement_fraction'])),
    scenarios=cost_rows,reform_budget=reform)
# Meaningful independent invariants and asymptotes; no material pass counts.
checks=[]
def check(name,ok,detail=None):
    checks.append(dict(name=name,ok=bool(ok),detail=detail))
def near(a,b,rel=1e-9,absolute=1e-12):
    return math.isclose(a,b,rel_tol=rel,abs_tol=absolute)
check('Hertz force reconstructed from radius',all(near(4/3*C['equivalent_E_MPa']*1e6*
      (x['a_um']*1e-6)**3/(x['radius_um']*1e-6),x['force_N']) for x in cases))
check('Heat conservation into two surfaces',all(near(x['heat_to_grain_W']+x['heat_to_base_W'],x['power_W']) for x in cases))
check('Interface equality from both thermal paths',all(near(x['heat_to_grain_W']*x['Rs_K_W'],x['heat_to_base_W']*x['Rm_K_W']) for x in cases))
check('Finite grain endmember increases interface temperature',all(x['no_grain_heat_intake_average_C']>=x['interface_average_C'] for x in cases))
check('Equal total area for four R150 versus one R300',near(small['total_area_um2'],large['total_area_um2']))
check('Equal peak pressure for matched-area pair',near(small['pmax_MPa'],large['pmax_MPa']))
check('Matched-area centreline pulse scales with sqrt(contact length)',near(layout['large_isolated']['pulse_peak_rise_K']/layout['small_isolated']['pulse_peak_rise_K'],math.sqrt(2)))
check('Four in-line contacts can erase split-contact heat benefit',layout['row_aligned_four']['pulse_peak_C']>layout['large_isolated']['pulse_peak_C'])
check('Two aligned square contacts retain benefit in this pulse model',layout['square_aligned_two']['pulse_peak_C']<layout['large_isolated']['pulse_peak_C'])
check('One pulse wake factor equals one',near(pulse_peak(small,1,80)['wake_multiplier'],1))
check('Large gap pulse returns to isolated limit',abs(pulse_peak(small,2,1e14)['wake_multiplier']-1)<1e-5)
check('Zero speed thermal resistance is stationary',near(resistance(1e-5,.4,1.86e6,0),8/(3*pi*pi*.4*1e-5)))
check('High speed resistance approaches moving asymptote',near(resistance(1e-5,.4,1.86e6,1e10),1/(pi*.4*1e-5*math.sqrt(1e10*1e-5*1.86e6/.4)),rel=1e-8))
check('Load share vectors conserve total force',all(near(sum(w),1) for w in I['load_shares']))
check('Costs preserve inventory',near(mass,108000))
check('Budget premium boundary closes annual budget',near(annual(cost['maximum_finished_premium_JPY_kg'],.02),B['annual_budget_JPY']))
check('One-contact Hertz geometric diagnostic intentionally fails R50 reference',not representatives[0]['geometry_diagnostic_ok'])
check('Illustrative four contact footprint fits apertures',small['a_um']<L['land_radius_um'] and layout['land_edge_gap_um']>0)
result=dict(evidence=I['evidence'],representatives=representatives,thermal_cases=cases,
            conductivity_cases=conductivity,unequal_load_cases=load_cases,wake_cases=wakes,layout=layout,cost=cost)
validation=dict(physical_tests=0,physical_success_probability=None,check_count=len(checks),all_checks_ok=all(x['ok'] for x in checks),
    checks=checks,counts=dict(contact_thermal=len(cases),conductivity=len(conductivity),unequal_load=len(load_cases),wake=len(wakes),cost=len(cost_rows)),
    scope='Arithmetic, conservation, limiting behaviour and constructed counterexamples only; no experimental validation.')
for fn,obj in [('results.json',result),('validation.json',validation)]:
    (P/fn).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
assert validation['all_checks_ok'],[x for x in checks if not x['ok']]
print(json.dumps(dict(counts=validation['counts'],checks=len(checks),checks_ok=True,physical_tests=0,
                     premium_limit_JPY_kg=cost['maximum_finished_premium_JPY_kg']),ensure_ascii=False))
