"""Independent balances, numerical quadrature, scaling and boundary checks."""
import json
import math
from pathlib import Path
from process_model import calculate,cooling,hydration

ROOT=Path(__file__).resolve().parent
p=json.loads((ROOT/'inputs.json').read_text(encoding='utf-8'))
r=calculate(p)
checks=[]
def check(label,condition,detail=None):
    checks.append(dict(label=label,passed=bool(condition),detail=detail))
    if not condition: raise AssertionError((label,detail))
def close(x,y):return math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-10)

def simpson(fun,x0,x1,n):
    dx=(x1-x0)/n
    return dx/3*(fun(x0)+fun(x1)+4*sum(fun(x0+i*dx) for i in range(1,n,2))+
                 2*sum(fun(x0+i*dx) for i in range(2,n,2)))

t=p['thermal']; a=p['aqueous'];b=p['bed'];g=p['bridge']
for row in r['cooling']:
    d=row['diameter_um']*1e-6
    mass=t['rho_kg_m3']*math.pi*d**3/6
    area=math.pi*d*d
    h=row['Nu']*t['k_air_W_mK']/d
    integrand=lambda temp:mass*t['cp_J_kgK']/(area*h*(temp-row['ambient_C']))
    errors=[]
    for n in [128,512]:
        numeric=simpson(integrand,t['T_cryst_C'],t['T_feed_C'],n)
        numeric+=mass*t['latent_J_kg']/(area*h*(t['T_cryst_C']-row['ambient_C']))
        numeric+=simpson(integrand,row['exit_C'],t['T_cryst_C'],n)
        errors.append(abs(numeric-row['total_s']))
    check('cooling quadrature',errors[1]<1e-8*row['total_s'],errors)
    other=cooling(d*2,row['ambient_C'],row['Nu'],t)
    check('diameter square scaling',close(other['total_s'],4*row['total_s']))
    check('lumped validity flag',row['lumped_screen']==(row['Nu']<8))

for row in r['reforming']:
    mass=row['area_m2']*row['depth_m']*b['bulk_density_kg_m3']*row['fraction']
    check('material throughput closes',close(row['rate_kg_h']*b['process_minutes']/60,mass))
    energy_air=row['air_mass_kg']*t['air_cp_J_kgK']*t['air_rise_K']
    check('air energy closes',close(energy_air,row['reject_kWh']*3.6e6))
    check('heat input-output sensible difference',close(row['ideal_heat_kWh']-row['reject_kWh'],
        mass*t['cp_J_kgK']*(t['T_exit_C']-t['T_start_C'])/3.6e6))

for row in r['bridges']:
    check('hydration mass closes',close(row['hemi_kg']+row['feed_water_kg'],row['product_kg']+row['free_water_kg']))
    check('bound water equals stoichiometric difference',close(row['bound_water_kg']/row['product_kg'],
        (a['gypsum_M_g_mol']-a['hemihydrate_M_g_mol'])/a['gypsum_M_g_mol']))
    check('annual renewal closes',close(row['annual_product_kg'],row['product_kg']*g['rebuilds_per_day']*g['days_per_year']))
try:hydration(1,.99,a)
except ValueError:check('insufficient reaction water rejected',True)
else:check('insufficient reaction water rejected',False)

for row in r['rain']:
    check('dissolution cannot exceed inventory',0<=row['capped_loss_kg']<=row['inventory_kg'])
    equivalent=row['capacity_equiv_rain_mm']*.001*row['area_m2']*row['effective_saturation']*a['gypsum_C_kg_m3']
    check('rain inventory equivalence',close(equivalent,row['inventory_kg']))

for row in r['beds']:
    c=p['baseline_cost']; rate=c['discount']; years=c['years']
    discounted=sum(1/(1+rate)**year for year in range(1,years+1))
    annual=(row['material_initial_JPY']+c['initial_other_JPY'])/discounted
    annual+=c['annual_other_JPY']+row['material_initial_JPY']*c['replacement_fraction_year']
    check('EAC against discounted cash-flow sum',close(annual,row['EAC_JPY']))
check('no fabricated physical probability',r['scope']['physical_success_probability'] is None)
check('no fabricated experiment count',r['scope']['physical_tests']==0)
out={'checks':len(checks),'passed':sum(x['passed'] for x in checks),'details':checks,
     'scope':'Numerical and accounting checks only. Not experiments or statistical success trials.'}
(ROOT/'verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:out[k] for k in ['checks','passed']}))
