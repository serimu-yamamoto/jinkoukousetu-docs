"""Contact kinetics and cohesive opening diagnostics, not physical validation."""
from pathlib import Path
import json, math, itertools, hashlib, re
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
M,H,T,C,K=[I[x] for x in ('machine','kinetics','time_scales','cohesive','cost')]

# Read the immutable-reviewed Claude source from the repository; do not execute it.
CA=I['claude_review']
claude_source=(P.parents[1]/CA['source_path']).read_text(encoding='utf8').replace('\r\n','\n')
claude_hash=hashlib.sha256(claude_source.encode('utf8')).hexdigest()
claude_rows=[]
for line in claude_source.splitlines():
    if re.match(r'^\| \d+ \|',line):
        cells=[x.strip() for x in line.strip('|').split('|')]
        if len(cells)==11:
            claude_rows.append(dict(rank=int(cells[0]),scores=[float(x) for x in cells[3:10]],displayed_total=float(cells[10])))
claude_first=claude_rows[0]
claude_scores=claude_first['scores']
claude_audit=dict(read_commit=CA['read_commit'],source_path=CA['source_path'],normalized_source_sha256=claude_hash,
    stated_evaluated_count=22,table_record_count=len(claude_rows),numbered_case_heading_count=len(re.findall(r'^### \d+\.',claude_source,re.M)),
    first_row_scores=claude_scores,first_row_product=math.prod(claude_scores),displayed_first_total=claude_first['displayed_total'],
    frechet_bounds_if_valid_marginals=dict(lower=max(0,sum(claude_scores)-(len(claude_scores)-1)),upper=min(claude_scores)),
    maximum_C3_all_table_rows=max(x['scores'][2] for x in claude_rows),
    maximum_C3_rows_with_positive_displayed_total=max(x['scores'][2] for x in claude_rows if x['displayed_total']>0),
    note='Counts are table records, not deduplicated inventions. The assessment scores are NOT established marginal probabilities; these bounds illustrate why their product is not a measured joint success probability. Original simulation scripts were not supplied in this source.')

normal=M['mass_kg']*M['g_m_s2']*math.cos(math.radians(M['slope_deg']))
dwell=M['reference_patch_length_m']/M['velocity_m_s']
travel=M['length_m']/M['velocity_m_s']/M['uptime_fraction']
remaining=M['closure_s']-M['overhead_s']-travel
pressure=[]
for length,fraction in itertools.product(M['patch_lengths_m'],M['normal_load_fractions']):
    p=normal*fraction/(M['width_m']*length); td=length/M['velocity_m_s']
    pressure.append(dict(patch_length_m=length,normal_load_fraction=fraction,nominal_Pa=p,dwell_s=td,pressure_exposure_Pa_s=p*td))
def state(t90,sep,eligible,td=dwell,rest=H['rest_s']):
    kh=math.log(10)/t90; ks=0 if sep is None else 1/sep
    unbonded0=eligible*math.exp(-kh*td); bonded0=eligible-unbonded0
    decay=math.exp(-(kh+ks)*rest)
    converted=unbonded0*(-math.expm1(-(kh+ks)*rest))
    bonded=bonded0+converted*kh/(kh+ks)
    lost=converted*ks/(kh+ks); unbonded=unbonded0*decay
    plateau=bonded0+unbonded0*kh/(kh+ks)
    return dict(t90_s=t90,separation_time_s=sep,eligible_fraction=eligible,dwell_s=td,rest_s=rest,
        bonded_after_roller=bonded0,unbonded_after_roller=unbonded0,bonded=bonded,unbonded=unbonded,lost=lost,
        bonded_plateau=plateau,bonded_over_eligible=bonded/eligible,kh_per_s=kh,ks_per_s=ks)
kinetics=[state(t,s,a) for t,s,a in itertools.product(H['t90_s'],H['separation_time_s'],H['eligible_fractions'])]
# Minimum contact-retention times to reach target conversion after the specified rest.
def required_retention(t90,target=.9):
    best=state(t90,None,1)['bonded']
    if best<=target:return dict(t90_s=t90,feasible_at_rest=False,best_no_loss=best,minimum_separation_time_s=None)
    low,high=1e-9,1e10
    for _ in range(100):
        middle=math.sqrt(low*high)
        if state(t90,middle,1)['bonded']<target:low=middle
        else:high=middle
    return dict(t90_s=t90,feasible_at_rest=True,best_no_loss=best,minimum_separation_time_s=high)
retention=[required_retention(t) for t in H['t90_s']]
# Independently integrate the three-state ODE for bounded dimensionless time.
def integrate(row,steps):
    kh,ks=row['kh_per_s'],row['ks_per_s']
    span=5/(kh+ks); dt=span/steps
    y=[row['unbonded_after_roller'],row['bonded_after_roller'],0.0]
    def f(y):return [-(kh+ks)*y[0],kh*y[0],ks*y[0]]
    for _ in range(steps):
        k1=f(y); k2=f([a+dt*b/2 for a,b in zip(y,k1)])
        k3=f([a+dt*b/2 for a,b in zip(y,k2)])
        k4=f([a+dt*b for a,b in zip(y,k3)])
        y=[a+dt*(b+2*c+2*d+e)/6 for a,b,c,d,e in zip(y,k1,k2,k3,k4)]
    exact=state(row['t90_s'],row['separation_time_s'],row['eligible_fraction'],rest=span)
    truth=[exact['unbonded'],exact['bonded'],exact['lost']]
    return dict(steps=steps,span_s=span,max_absolute_error=max(abs(a-b) for a,b in zip(y,truth)),sum_residual=abs(sum(y)-row['eligible_fraction']))
verification=[]
for t,s in [(10,.1),(10,600),(600,10),(600,None)]:
    r=state(t,s,.5)
    verification.append(dict(t90_s=t,separation_time_s=s,meshes=[integrate(r,n) for n in (20,80,320)]))
scales=[]
for window,extra in itertools.product(T['healing_windows_s'],T['allowed_extra_creep_over_elastic']):
    healing_tau=window/(-math.log1p(-T['healing_fraction']))
    relaxation_tau=T['use_s']/extra
    scales.append(dict(window_s=window,extra_creep_ratio=extra,maximum_healing_tau_s=healing_tau,
        minimum_bulk_relaxation_tau_s=relaxation_tau,minimum_relaxation_to_healing_ratio=relaxation_tau/healing_tau))
coverage=[]
for f,z,h in itertools.product(I['patch_coverage']['fractions'],I['patch_coverage']['coordination_numbers'],I['patch_coverage']['conditional_bond_fractions']):
    coverage.append(dict(surface_fraction=f,z=z,conditional_conversion=h,eligible_fraction=f*f,
        branching_factor=(z-1)*f*f*h,ideal_tree_supercritical=(z-1)*f*f*h>1))
cohesive=[]
for sigma,gc,r in itertools.product(C['strength_MPa'],C['Gc_J_m2'],C['pad_radius_um']):
    stress=sigma*1e6; area=math.pi*(r*1e-6)**2; df=2*gc/stress
    cohesive.append(dict(strength_MPa=sigma,Gc_J_m2=gc,pad_radius_um=r,pad_area_m2=area,
        final_opening_um=df*1e6,peak_opening_um=df*1e6*C['peak_opening_fraction'],
        peak_force_N=stress*area,work_per_contact_J=gc*area,
        peak_force_to_work_per_m=stress/gc))
def traction(x,row):
    df=row['final_opening_um']*1e-6; d0=df*C['peak_opening_fraction']; stress=row['strength_MPa']*1e6
    if x<0 or x>=df:return 0
    return stress*x/d0 if x<=d0 else stress*(df-x)/(df-d0)
quadrature=[]
for gc in C['Gc_J_m2']:
    row=next(x for x in cohesive if x['strength_MPa']==1 and x['Gc_J_m2']==gc and x['pad_radius_um']==10)
    df=row['final_opening_um']*1e-6
    # Composite midpoint quadrature, deliberately not aligned to the kink at 0.1.
    errs=[]
    for n in [103,1003,10003]:
        total=sum(traction((j+.5)*df/n,row) for j in range(n))*df/n
        errs.append(dict(cells=n,integrated_Gc_J_m2=total,relative_error=abs(total/gc-1)))
    quadrature.append(dict(Gc_J_m2=gc,meshes=errs))
base_mass=K['area_m2']*K['depth_m']*K['base_bulk_density_kg_m3']; solid_volume=base_mass/K['host_density_kg_m3']
crf=K['discount']*(1+K['discount'])**K['years']/((1+K['discount'])**K['years']-1)
def annual(mass,price):return (mass*price+K['nonmaterial_capital_JPY'])*crf+K['annual_fixed_JPY']+mass*price*K['annual_replacement_fraction']
base_annual=annual(base_mass,K['host_JPY_kg'])
cost=[]
for w,p,process in itertools.product(K['mass_fractions'],K['contact_phase_JPY_kg'],K['localization_JPY_per_finished_kg']):
    rho=1/((1-w)/K['host_density_kg_m3']+w/K['contact_phase_density_kg_m3'])
    mass=solid_volume*rho; price=(1-w)*K['host_JPY_kg']+w*p+process; year=annual(mass,price)
    cost.append(dict(w=w,contact_phase_JPY_kg=p,localization_JPY_kg=process,mixture_density_kg_m3=rho,
        mass_kg=mass,mixture_JPY_kg=price,annual_JPY=year,remaining_JPY=K['annual_budget_JPY']-year))
area_multiplier=M['length_m']*M['width_m']/K['area_m2']
selected=next(x for x in cost if x['w']==.01 and x['contact_phase_JPY_kg']==3000 and x['localization_JPY_kg']==100)
area_scaling=dict(material_area_m2=K['area_m2'],machine_area_m2=M['length_m']*M['width_m'],area_multiplier=area_multiplier,base_inventory_kg=base_mass*area_multiplier,base_initial_material_JPY=base_mass*area_multiplier*K['host_JPY_kg'],selected_inventory_kg=selected['mass_kg']*area_multiplier,selected_initial_material_JPY=selected['mass_kg']*area_multiplier*selected['mixture_JPY_kg'],note='Material-only linear scaling of the same hypothetical depth and density. The 19M annual budget and equipment/civil costs are not transferred to this area.')
checks=[]
def check(name,value):checks.append(dict(name=name,passed=bool(value)))
check('machine normal load',math.isclose(normal,33982.8368445,rel_tol=1e-10))
check('60minute conservative window positive',remaining>0)
check('pressure times dwell invariant',all(math.isclose(x['pressure_exposure_Pa_s'],normal*x['normal_load_fraction']/(M['width_m']*M['velocity_m_s'])) for x in pressure))
check('kinetic conservation',all(math.isclose(x['bonded']+x['unbonded']+x['lost'],x['eligible_fraction'],abs_tol=1e-14) for x in kinetics))
check('all states nonnegative',all(min(x['bonded'],x['unbonded'],x['lost'])>=0 for x in kinetics))
check('bonded never exceeds eligibility',all(x['bonded']<=x['eligible_fraction']+1e-14 for x in kinetics))
check('bonded below plateau',all(x['bonded']<=x['bonded_plateau']+1e-14 for x in kinetics))
check('no loss recovers ordinary kinetics',all(math.isclose(state(t,None,1)['bonded'],-math.expm1(-math.log(10)*(dwell+H['rest_s'])/t)) for t in H['t90_s']))
check('zero rest preserves roller bond count',math.isclose(state(60,10,1,rest=0)['bonded'],state(60,10,1)['bonded_after_roller']))
check('lost contact limit',state(600,1e-12,1)['bonded']-state(600,1e-12,1)['bonded_after_roller']<1e-12)
check('retention boundary solves target',all(not x['feasible_at_rest'] or math.isclose(state(x['t90_s'],x['minimum_separation_time_s'],1)['bonded'],.9,abs_tol=1e-10) for x in retention))
check('RK4 accuracy',max(v['meshes'][-1]['max_absolute_error'] for v in verification)<1e-9)
check('RK4 convergence',all(v['meshes'][0]['max_absolute_error']>v['meshes'][1]['max_absolute_error']>v['meshes'][2]['max_absolute_error'] for v in verification))
check('RK4 conservation',max(m['sum_residual'] for v in verification for m in v['meshes'])<1e-12)
check('Maxwell separation boundary',all(math.isclose(x['minimum_relaxation_to_healing_ratio'],T['use_s']*(-math.log1p(-T['healing_fraction']))/(x['extra_creep_ratio']*x['window_s'])) for x in scales))
check('coverage bound',all(0<=x['eligible_fraction']<=1 and x['branching_factor']<=x['z']-1 for x in coverage))
check('two-neighbor network not supercritical',not any(x['ideal_tree_supercritical'] for x in coverage if x['z']==2))
check('cohesive energy identity',all(math.isclose(.5*x['strength_MPa']*1e6*x['final_opening_um']*1e-6,x['Gc_J_m2']) for x in cohesive))
check('cohesive quadrature accuracy',max(v['meshes'][-1]['relative_error'] for v in quadrature)<1e-7)
check('cohesive quadrature convergence',all(v['meshes'][0]['relative_error']>v['meshes'][1]['relative_error']>v['meshes'][2]['relative_error'] for v in quadrature))
check('pad area cancels opening scale',all(math.isclose(2*x['work_per_contact_J']/x['peak_force_N'],x['final_opening_um']*1e-6) for x in cohesive))
check('base cost inherited',math.isclose(base_annual,16108182.163583575,abs_tol=.001))
check('density conserves occupied volume',all(math.isclose(x['mass_kg']/x['mixture_density_kg_m3'],solid_volume) for x in cost))
check('area scaling keeps scope separate',area_scaling['area_multiplier']==10 and area_scaling['base_inventory_kg']==1080000)
check('no success probability invention',I['evidence']['physical_tests']==0 and I['evidence']['physical_success_probability'] is None)
check('Claude source exact normalized hash',claude_hash==CA['source_sha256'])
check('Claude displayed product rounding',math.isclose(math.prod(claude_scores),claude_first['displayed_total'],rel_tol=.02))
check('conditional marginal bounds include independent product',0<=claude_audit['frechet_bounds_if_valid_marginals']['lower']<=math.prod(claude_scores)<=claude_audit['frechet_bounds_if_valid_marginals']['upper']<=1)
R=dict(claude_audit=claude_audit,evidence=I['evidence'],machine_summary=dict(normal_load_N=normal,reference_dwell_s=dwell,travel_s=travel,conservative_last_zone_rest_s=remaining,reference_material_area_m2=K['area_m2'],machine_course_area_m2=M['length_m']*M['width_m']),area_scaling=area_scaling,pressure_cases=pressure,contact_cases=kinetics,retention_boundaries=retention,ode_verification=verification,time_scale_cases=scales,coverage_cases=coverage,cohesive_cases=cohesive,quadrature=quadrature,cost_cases=cost,baseline=dict(mass_kg=base_mass,occupied_polymer_volume_m3=solid_volume,annual_JPY=base_annual,remaining_JPY=K['annual_budget_JPY']-base_annual,crf=crf))
V=dict(numerical_checks=len(checks),all_passed=all(x['passed'] for x in checks),checks=checks,not_validated=['material kinetics','50C wet creep','actual particle registration and contact retention','shear and ski friction','manufacturing and exposure safety','winter/rain recovery','commercial cost'])
for name,obj in [('results.json',R),('validation.json',V)]:
    (P/name).write_bytes((json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8'))
print(json.dumps(dict(checks=len(checks),passed=V['all_passed'],contact_cases=len(kinetics),pressure_cases=len(pressure),coverage_cases=len(coverage),cohesive_cases=len(cohesive),cost_cases=len(cost),maximum_RK_error=max(v['meshes'][-1]['max_absolute_error'] for v in verification))))
if not V['all_passed']:raise SystemExit('NUMERICAL CHECK FAILED')
