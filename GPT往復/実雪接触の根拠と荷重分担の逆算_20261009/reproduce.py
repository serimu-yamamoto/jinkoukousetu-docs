"""Cycle 87: hypothetical height-distributed contact recruitment; no physical trials."""
from pathlib import Path
import json, math, hashlib
P=Path(__file__).resolve().parent
R=P.parents[1]
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
checks=[]
def ck(name,condition):
    if not condition: raise AssertionError(name)
    checks.append(dict(name=name,passed=True))
def close(a,b,rtol=1e-10,atol=1e-13):
    return math.isclose(a,b,rel_tol=rtol,abs_tol=atol)
def out(name,data):
    (P/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def solve(p,n,k,h):
    # h is the full uniform distribution width of support gaps (not Ra).
    if min(p,n,k)<=0 or h<0: raise ValueError('positive p,n,k and nonnegative h required')
    if h==0:
        d=p/(n*k); f=1.
    elif p<n*k*h/2:
        d=math.sqrt(2*p*h/(n*k)); f=d/h
    else:
        d=p/(n*k)+h/2; f=1.
    meanF=p/(n*f)
    mean_delta=d if h==0 else (d*d/(2*h) if d<h else d-h/2)
    return dict(approach_m=d,active_fraction=f,active_density_m2=n*f,mean_force_N=meanF,
                max_force_N=k*d,tangent_stiffness_Pa_per_m=n*k*f,
                reconstructed_pressure_Pa=n*k*mean_delta)
def pressure(d,n,k,h):
    return n*k*(max(d,0) if h==0 else (max(d,0)**2/(2*h) if d<h else d-h/2))
for q in I['provenance']:
    text=(R/q['path']).read_text(encoding='utf-8').replace('\r\n','\n').rstrip()+'\n'
    ck('source_hash_'+Path(q['path']).stem,hashlib.sha256(text.encode()).hexdigest()==q['sha256_lf'])
geo={x['id']:x for x in I['geometries']}
branches=[]
for b in I['mechanical_reference']:
    g=geo[b['geometry']]
    k=b['arm_tip_load_N']/(b['total_deflection_um']*1e-6)
    n=1/(g['tile_area_mm2']*1e-6)
    branches.append(dict(b,stiffness_N_m=k,potential_density_m2=n))
ck('12_branch_inputs',len(branches)==12)
ck('positive_branch_stiffness',all(x['stiffness_N_m']>0 for x in branches))
rows=[]
for b in branches:
    g=geo[b['geometry']]
    for h_um in I['height_spread_um_assumed']:
        for p in I['pressure_Pa_assumed']:
            s=solve(p,b['potential_density_m2'],b['stiffness_N_m'],h_um*1e-6)
            ratio=s['max_force_N']/b['arm_tip_load_N']
            strain=b['outer_fibre_strain_estimate']*ratio
            dl=s['approach_m']/(g['arm_free_length_mm']*1e-3)
            flags=[]
            if g['thickness_over_free_length']>.3: flags.append('short_thick_arm_requires_3D_analysis')
            if dl>.1: flags.append('large_deflection_requires_nonlinear_analysis')
            if p==150000: flags.append('hard_snow_load_bridge_not_fresh_snow_target')
            rows.append(dict(geometry=b['geometry'],solid_modulus_MPa_assumed=b['solid_modulus_MPa_assumed'],
                        pressure_Pa_assumed=p,height_spread_um_assumed=h_um,
                        stiffness_N_m=b['stiffness_N_m'],potential_density_m2=b['potential_density_m2'],
                        **s,max_root_strain_linear_diagnostic=strain,approach_over_arm_length=dl,
                        review_flags=flags,actual_50C_modulus=None,actual_allowable_strain=None,
                        snowlike_performance=None))
ck('144_hypothetical_rows',len(rows)==144)
ck('pressure_balance',all(close(x['reconstructed_pressure_Pa'],x['pressure_Pa_assumed']) for x in rows))
ck('fraction_bounds_and_force_order',all(0<x['active_fraction']<=1 and x['max_force_N']>=x['mean_force_N']*(1-1e-12) for x in rows))
ck('zero_spread_reproduces_cycle86',all(close(x['max_force_N'],x['pressure_Pa_assumed']/x['potential_density_m2']) and x['active_fraction']==1 for x in rows if x['height_spread_um_assumed']==0))
ck('partial_max_twice_mean',all(close(x['max_force_N'],2*x['mean_force_N']) for x in rows if x['active_fraction']<1))
b0=next(x for x in branches if x['geometry']=='planar_only_s3' and x['solid_modulus_MPa_assumed']==500)
n,k=b0['potential_density_m2'],b0['stiffness_N_m']
h=50e-6; pt=n*k*h/2
eps=1e-7
ck('continuous_at_full_recruitment',abs(solve(pt*(1-eps),n,k,h)['approach_m']/h-1)<eps and close(solve(pt,n,k,h)['approach_m'],h))
ck('tangent_matches_finite_difference',all(close((pressure(d+1e-11,n,k,h)-pressure(d-1e-11,n,k,h))/2e-11,n*k*min(d/h,1),1e-6) for d in [h*.2,h*.7,h*1.5]))
# Independent discrete quadrature and bisection (nodes are not specimens).
quad=[]
cases=[('planar_only_s1',500,2000,50),('planar_only_s3',500,2000,50),
       ('planar_only_s4',500,2000,50),('planar_only_s3',100,2000,200),
       ('planar_only_s3',500,20000,50),('planar_only_s3',1000,150000,10),
       ('planar_only_s2',500,2000,0),('planar_only_s4',1000,2000,200)]
N=8192
for gid,E,p,h_um in cases:
    b=next(x for x in branches if x['geometry']==gid and x['solid_modulus_MPa_assumed']==E)
    nn,kk,hh=b['potential_density_m2'],b['stiffness_N_m'],h_um*1e-6
    gaps=[(i+.5)*hh/N for i in range(N)]
    lo,hi=0.,hh+p/(nn*kk)+1e-6
    for _ in range(60):
        mid=(lo+hi)/2
        pq=nn*kk*math.fsum(max(mid-z,0) for z in gaps)/N
        if pq<p: lo=mid
        else: hi=mid
    numeric=(lo+hi)/2
    ana=solve(p,nn,kk,hh)
    err=abs(numeric/ana['approach_m']-1)
    quad.append(dict(geometry=gid,modulus_MPa=E,pressure_Pa=p,height_spread_um=h_um,nodes=N,
                     analytic_approach_m=ana['approach_m'],quadrature_approach_m=numeric,relative_error=err))
ck('independent_quadrature_8_cases',len(quad)==8 and max(x['relative_error'] for x in quad)<1e-5)
# n doubles and k halves: same P(d), different force per contact.
pairs=[]
for p in [1000,2000,5000,20000,50000,150000]:
    a=solve(p,n,k,h); b=solve(p,2*n,k/2,h)
    pairs.append(dict(pressure_Pa=p,A=a,B=b,interpretation='Same normal curve; twice contacts; half per-contact force. No friction prediction.'))
ck('nonidentifiable_bulk_curve',all(close(x['A']['approach_m'],x['B']['approach_m']) and close(x['A']['tangent_stiffness_Pa_per_m'],x['B']['tangent_stiffness_Pa_per_m']) for x in pairs))
ck('different_contact_force',all(close(x['B']['active_density_m2'],2*x['A']['active_density_m2']) and close(x['B']['mean_force_N'],x['A']['mean_force_N']/2) for x in pairs))
# Both dry compliance and fixed-base capillary compliance scale as 1/E at fixed geometry.
inv=I['inverse'];fmin=inv['active_fraction_min_assumed'];ymax=inv['closure_fraction_max_assumed']
lammax=ymax*(1-ymax);windows=[]
for gid in ['planar_only_s3','planar_only_s4']:
    b=next(x for x in branches if x['geometry']==gid and x['solid_modulus_MPa_assumed']==500)
    for hu in inv['height_spread_um']:
        Emax=500*(2*inv['pressure_Pa']/(b['potential_density_m2']*b['stiffness_N_m']*hu*1e-6*fmin*fmin))
        for gu in inv['gap_um']:
            w=next(x for x in I['wet_reference'] if x['geometry']==gid and x['gap_um_assumed']==gu)
            Emin=500*w['lambda_total']/lammax
            windows.append(dict(geometry=gid,height_spread_um_assumed=hu,initial_water_gap_um_assumed=gu,
                                minimum_E_MPa_for_closure_limit=Emin,maximum_E_MPa_for_contact_fraction=Emax,
                                necessary_intersection_exists=Emin<=Emax,actual_joint_wet_contact_solution=None,
                                provisional_fraction_min=fmin,provisional_closure_max=ymax))
ck('18_inverse_windows',len(windows)==18)
ck('dry_inverse_boundary',all(close(solve(inv['pressure_Pa'],
 next(b['potential_density_m2'] for b in branches if b['geometry']==x['geometry']),
 next(b['stiffness_N_m'] for b in branches if b['geometry']==x['geometry'] and b['solid_modulus_MPa_assumed']==500)*x['maximum_E_MPa_for_contact_fraction']/500,
 x['height_spread_um_assumed']*1e-6)['active_fraction'],fmin) for x in windows))
ck('wet_inverse_boundary',all(close(500*next(w['lambda_total'] for w in I['wet_reference'] if w['geometry']==x['geometry'] and w['gap_um_assumed']==x['initial_water_gap_um_assumed'])/x['minimum_E_MPa_for_closure_limit'],lammax) for x in windows))
w20=next(x for x in windows if x['geometry']=='planar_only_s3' and x['height_spread_um_assumed']==50 and x['initial_water_gap_um_assumed']==20)
w50=next(x for x in windows if x['geometry']=='planar_only_s3' and x['height_spread_um_assumed']==50 and x['initial_water_gap_um_assumed']==50)
ck('20um_conflict_and_50um_necessary_window',not w20['necessary_intersection_exists'] and w50['necessary_intersection_exists'])
Etest=200
st=solve(2000,n,k*Etest/500,50e-6)
lam=500/Etest*next(w['lambda_total'] for w in I['wet_reference'] if w['geometry']=='planar_only_s3' and w['gap_um_assumed']==50)
y=2*lam/(1+math.sqrt(1-4*lam))
minimum_gap=20*math.sqrt(w20['minimum_E_MPa_for_closure_limit']/w20['maximum_E_MPa_for_contact_fraction'])
witness=dict(geometry='planar_only_s3',assumed_E_MPa=Etest,height_spread_um_assumed=50,water_gap_um_assumed=50,
            **st,independent_fixed_base_closure_fraction=y,
            max_root_strain_linear_diagnostic=b0['outer_fibre_strain_estimate']*500/Etest*st['max_force_N']/b0['arm_tip_load_N'],
            minimum_gap_um_at_dry_bound=minimum_gap,manufactured=False,validated=False)
overload=solve(20000,n,k*Etest/500,50e-6)
witness['20kPa_diagnostic']=dict(**overload,approach_over_arm_length=overload['approach_m']/(geo['planar_only_s3']['arm_free_length_mm']*1e-3),linear_model_invalid_for_design=True)
ck('20kPa_witness_requires_nonlinear_review',witness['20kPa_diagnostic']['approach_over_arm_length']>.1)
ck('witness_passes_only_two_necessary_screens',st['active_fraction']>=fmin and y<=ymax)
refs=json.loads((P/'reference_scope.json').read_text(encoding='utf-8'))
ck('reference_speed_mask',all(q['accepted_as_observation_at_10']==(10<=q['published_vmax_m_s']) and q['accepted_as_observation_at_15']==(15<=q['published_vmax_m_s']) for q in refs))
ck('no_physical_probability',I['physical_experiments']==0 and I['success_probability'] is None)
out('contact_recruitment.json',rows);out('quadrature_check.json',quad)
out('nonidentifiability.json',pairs);out('inverse_windows.json',windows);out('design_witness.json',witness)
out('checks.json',checks)
summary=dict(cycle=87,numeric_checks=len(checks),calculation_rows=len(rows)+len(quad)+len(pairs)+len(windows)+1,
             row_breakdown=dict(contact=len(rows),quadrature=len(quad),nonidentifiability=len(pairs),inverse=len(windows),witness=1),
             physical_experiments=0,success_probability=None,provider_contacts_sent=0,orders_placed=0,
             equipment_secured=False,actual_50C_material_moduli=None,actual_total_manufacturing_cost_yen=None,
             actual_snow_contact_fraction_target=None)
out('summary.json',summary)
print(json.dumps(summary))
