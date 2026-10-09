"""Cycle 67: geometric diagnostics and conditional cost limits. No empirical prediction."""
from pathlib import Path
import csv, json, math, sys
import numpy as np
HERE=Path(__file__).resolve().parent
DEP=HERE.parents[1]/'.deps'
if DEP.exists(): sys.path.insert(0,str(DEP))
P=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
checks=[]
def check(name,condition):
    if not bool(condition): raise AssertionError(name)
    checks.append(name)
def close(a,b,rtol=1e-9,atol=1e-12): return math.isclose(float(a),float(b),rel_tol=rtol,abs_tol=atol)
def phi(w):
    return (w/P['densities_kg_m3']['UHMWPE'])/(w/P['densities_kg_m3']['UHMWPE']+(1-w)/P['densities_kg_m3']['PEEK'])
def density(w): return 1/(w/P['densities_kg_m3']['UHMWPE']+(1-w)/P['densities_kg_m3']['PEEK'])
def volume_ball(r):return 4*math.pi*r**3/3
def excluded(a,r):return 2*math.pi*a*a*r+math.pi**2*a*r*r+volume_ball(r)
def intensity(v,r):return -math.log1p(-v)/volume_ball(r)
def hit(v,a,r):return -math.expm1(-intensity(v,r)*excluded(a,r))
def simpson(y,x):
    h=(x[-1]-x[0])/(len(x)-1)
    return h/3*(y[0]+y[-1]+4*y[1:-1:2].sum()+2*y[2:-1:2].sum())
def variance(v,a,r,n=10001):
    d=np.linspace(0,min(2*a,2*r),n)
    overlap_sphere=math.pi*(4*r+d)*(2*r-d)**2/12
    disk=2*a*a*np.arccos(np.clip(d/(2*a),0,1))-0.5*d*np.sqrt(np.maximum(4*a*a-d*d,0))
    lam=intensity(v,r)
    cov=np.exp(-lam*(2*volume_ball(r)-overlap_sphere))-math.exp(-2*lam*volume_ball(r))
    return float(simpson(cov*disk*2*math.pi*d,d)/(math.pi*a*a)**2)
def csvout(name,rows):
    with (HERE/name).open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
ref=P['reference']; v=phi(ref['mass_fraction']); a=ref['contact_radius_um']
rows=[]
for w in P['mass_fractions']:
 for aa in P['contact_radii_um']:
  for d in P['domain_diameters_um']:
   vv=phi(w); s2=variance(vv,aa,d/2)
   rows.append(dict(w_mass=w,phi_volume=vv,a_um=aa,domain_d_um=d,contact_presence=hit(vv,aa,d/2),expected_area_fraction=vv,area_fraction_sd=math.sqrt(max(0,s2))))
csvout('contact_presence.csv',rows)
# Numerical integral via z=r sin(theta), independent of polynomial closed form.
x=np.linspace(-math.pi/2,math.pi/2,10001); rr=5.0
numeric=simpson(math.pi*(a+rr*np.cos(x))**2*rr*np.cos(x),x)
check('excluded volume agrees with independent cross-section integration',close(numeric,excluded(a,rr),rtol=1e-11))
check('point-contact limit equals phase fraction',close(hit(v,0,rr),v))
check('scale invariance of presence',close(hit(v,a,rr),hit(v,1000*a,1000*rr)))
check('mass-volume conversion round trip',close((v*934)/(v*934+(1-v)*1300),0.02))
check('mixture density conserves mass and component volumes',close(density(0.02),v*934+(1-v)*1300))
check('zero phase gives zero presence',close(hit(0,a,rr),0))
check('contact presence bounded for all cases',all(0<=r['contact_presence']<=1 for r in rows))
check('stationary expected area equals phase volume fraction',all(close(r['expected_area_fraction'],r['phi_volume']) for r in rows))
check('area variance bounded by Bernoulli point variance',all(r['area_fraction_sd']**2<=r['phi_volume']*(1-r['phi_volume'])+1e-12 for r in rows))
check('area-variance integral converges',close(variance(v,10,5,10001),variance(v,10,5,20001),rtol=2e-7))
check('larger contact radius increases presence',all(hit(v,5,d/2)<hit(v,50,d/2) for d in P['domain_diameters_um']))
check('finer domains increase presence at fixed phase fraction',hit(v,a,0.5)>hit(v,a,15))
# Solve the requested geometry target analytically: D/V = 1 + (3pi/4)x + 1.5x^2, x=a/r.
target=ref['geometry_contact_presence_target']; ratio=-math.log1p(-target)/(-math.log1p(-v)); b=3*math.pi/4
xx=(-b+math.sqrt(b*b+6*(ratio-1)))/3; dlimit=2*a/xx
check('analytical domain limit reproduces geometric target',close(hit(v,a,dlimit/2),target))
clusters=[]
for q in P['cluster_regions_fraction']:
    local=v/q; pr=q*hit(local,a,1)
    clusters.append(dict(region_area_fraction=q,local_phase_fraction=local,global_phase_fraction=q*local,contact_presence=pr,uncovered_fraction=1-pr))
csvout('cluster_counterexamples.csv',clusters)
check('cluster construction preserves global composition',all(close(r['global_phase_fraction'],v) for r in clusters))
check('cluster construction cannot cover unoccupied macroregions',all(r['contact_presence']<=r['region_area_fraction'] for r in clusters))
polys=[]
for f in P['coarse_intensity_volume_shares']:
    eta=-math.log1p(-v)
    lf=(1-f)*eta/volume_ball(1); lc=f*eta/volume_ball(10)
    ph=-math.expm1(-lf*volume_ball(1)-lc*volume_ball(10))
    polys.append(dict(coarse_share_of_intensity_times_volume=f,global_phase_fraction=ph,contact_presence=-math.expm1(-lf*excluded(a,1)-lc*excluded(a,10))))
csvout('mixed_domain_sizes.csv',polys)
check('two-size Boolean model preserves phase fraction',all(close(r['global_phase_fraction'],v) for r in polys))
check('two-size limits recover monodisperse cases',close(polys[0]['contact_presence'],hit(v,a,1)) and close(polys[-1]['contact_presence'],hit(v,a,10)))
C=P['cost']; crf=C['discount_rate']/(1-(1+C['discount_rate'])**(-C['years'])); mass=C['contact_volume_m3']*density(.02)
base=mass*C['processed_reference_price_JPY_kg']*(crf+C['reference_annual_replacement'])
cost=[]
for g in C['lifetime_multipliers']:
 for qa in C['additional_annual_QA_JPY']:
  repl=C['reference_annual_replacement']/g
  ceiling=(base-qa)/(mass*(crf+repl))
  cost.append(dict(lifetime_factor_assumed=g,annual_replacement_fraction=repl,added_annual_QA_JPY=qa,total_processed_price_ceiling_JPY_kg=ceiling,price_premium_ceiling_JPY_kg=ceiling-C['processed_reference_price_JPY_kg']))
csvout('conditional_process_cost.csv',cost)
check('no measured lifetime gain permits no price premium',close(cost[0]['price_premium_ceiling_JPY_kg'],0,atol=1e-8))
check('cost ceilings recover common annual budget',all(close(mass*r['total_processed_price_ceiling_JPY_kg']*(crf+r['annual_replacement_fraction'])+r['added_annual_QA_JPY'],base) for r in cost))
yields=[]
for y in C['process_yield']:
 yields.append(dict(usable_mass_kg=mass,yield_fraction=y,gross_input_kg=mass/y,reject_kg=mass*(1/y-1)))
csvout('manufacturing_yield.csv',yields)
check('yield mass balance',all(close(r['gross_input_kg'],r['usable_mass_kg']+r['reject_kg']) for r in yields))
materials=['M0_UHMWPE','M1_unfilled_PEI','M2_unfilled_PEEK','M3_PEEK98_PE2_as_prepared','M4_PEEK98_PE2_fine_target','M5_PEEK97_PE3_fine_target','M6_unfilled_POM_C']
plan=[]
for mat in materials:
 for lot in range(1,4):
  for temp in [30,50]:
   for state in ['dry','water_thin_film','drained_wet','redried']:
    plan.append(dict(test_id='T67-%03d'%(len(plan)+1),material=mat,stage='A' if mat in materials[:4] else 'B_conditional',candidate_lot=lot,surface_C=temp,ambient_C=30,water_state=state,sole='real_unwaxed_UHMWPE_same_specification_record_lot',nominal_pressure_MPa=.5,nominal_contact_diameter_mm=8,load_N=.5*math.pi*4**2,sliding_speed_m_s=.5,sliding_time_min=30,stop_hold_min=5,setup_time_min_assumed=10,status='NOT_EXECUTED',observed_friction='',observed_wear=''))
csvout('planned_coupon_tests.csv',plan)
check('all experiment rows explicitly unperformed',all(r['status']=='NOT_EXECUTED' and r['observed_friction']=='' and r['observed_wear']=='' for r in plan))
check('experimental IDs unique',len({r['test_id'] for r in plan})==len(plan))
check('new plan includes every material-state-temperature-lot combination',len(plan)==7*3*2*4)
summary=dict(cycle=67,physical_tests=0,success_probability=None,checks_passed=len(checks),checks=checks,reference_phi=v,mixture_density_kg_m3=density(.02),geometry_95pct_domain_limit_um=dlimit,reference_rows=[r for r in rows if close(r['w_mass'],.02) and r['a_um']==10],cluster_counterexamples=clusters,two_size_cases=polys,cost=dict(contact_mass_kg=mass,capital_recovery_factor=crf,initial_contact_material_JPY=mass*6000,annual_reference_JPY=base,ceilings=cost),planned=dict(stage_A_cells=96,stage_B_conditional_cells=72,stage_A_nominal_rig_hours=96*.75,stage_B_nominal_rig_hours=72*.75,excluded='conditioning, microscopy, load/speed validation, aging, grain-bed trials, setup commissioning'),interpretation='presence is geometric contact with at least one phase domain, not low friction, load share, snow likeness or success probability')
(HERE/'results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
# Original figures, no publisher artwork redistributed.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':10,'figure.dpi':150})
fig,axs=plt.subplots(1,2,figsize=(11,4.4),constrained_layout=True)
for aa in [5,10,25,50]:
 ds=np.geomspace(.5,40,200); axs[0].plot(ds,[hit(v,aa,d/2)*100 for d in ds],label=f'contact radius {aa} um')
axs[0].set(xscale='log',xlabel='Final phase-domain diameter (um), assumed',ylabel='Contacts touching phase (%)',ylim=(0,103),title='Geometry only: 2 wt% UHMWPE in PEEK'); axs[0].legend(fontsize=8); axs[0].grid(alpha=.25)
sel=summary['reference_rows']; ds=[r['domain_d_um'] for r in sel]
axs[1].plot(ds,[100*r['contact_presence'] for r in sel],'-o',label='At least one domain touched')
axs[1].axhline(v*100,color='tab:red',label='Mean phase area = 2.76%')
axs[1].set(xscale='log',xlabel='Final domain diameter (um)',ylabel='Fraction (%)',ylim=(0,103),title='Presence does not mean full lubrication'); axs[1].legend(fontsize=8);axs[1].grid(alpha=.25)
fig.savefig(HERE/'phase_presence.png');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(11,4.4),constrained_layout=True)
axs[0].bar([str(r['region_area_fraction']) for r in clusters],[100*r['contact_presence'] for r in clusters],color='tab:blue')
axs[0].set(xlabel='Fraction of large regions containing domains',ylabel='Contacts touching phase (%)',ylim=(0,103),title='Same global 2 wt%, fine 2 um domains')
for qa in C['additional_annual_QA_JPY']:
 xx=[r for r in cost if r['added_annual_QA_JPY']==qa];axs[1].plot([r['lifetime_factor_assumed'] for r in xx],[r['price_premium_ceiling_JPY_kg'] for r in xx],'-o',label=f'Extra QA: {qa/1e6:g} MJPY/year')
axs[1].axhline(0,color='black',linewidth=.8);axs[1].set(xlabel='Lifetime multiplier (unmeasured assumption)',ylabel='Allowed processed-price premium (JPY/kg)',title='Conditional economics; 6,000 JPY/kg baseline');axs[1].legend(fontsize=8);axs[1].grid(alpha=.25)
fig.savefig(HERE/'clustering_and_cost.png');plt.close(fig)
print(json.dumps({'checks':len(checks),'phi':v,'d95_um':dlimit,'reference':summary['reference_rows'],'cost':summary['cost'],'planned':summary['planned']},ensure_ascii=False))
