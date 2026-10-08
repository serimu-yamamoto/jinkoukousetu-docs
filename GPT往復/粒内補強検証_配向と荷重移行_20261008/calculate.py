"""Finite-matrix axial spring model. Not a fitted material or snow model."""
from pathlib import Path
import json,math,itertools,sys
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]/'.deps'))
import numpy as np
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
C,K,B,Q=[I[x] for x in ('composite','budget','bed','reference')]
mass0=B['area_m2']*B['depth_m']*B['reference_bulk_density_kg_m3']
solid_volume=mass0/B['reference_host_density_kg_m3']
crf=K['discount']*(1+K['discount'])**K['years']/((1+K['discount'])**K['years']-1)
factor=crf+K['annual_replacement_fraction']
base=(mass0*K['material_JPY_kg']+K['nonmaterial_capital_JPY'])*crf+K['annual_fixed_JPY']+mass0*K['material_JPY_kg']*K['annual_replacement_fraction']
margin=K['annual_budget_JPY']-base
def density(w):
    return 1/(w/C['fiber_density_kg_m3']+(1-w)/C['host_density_kg_m3'])
def model(w=Q['fiber_mass_fraction'],skin=Q['skin_um'],em=Q['host_E_MPa'],ef=Q['fiber_E_MPa'],d=1,length=Q['length_um'],chi=1,orientation=1):
    rho=density(w); vf=w*rho/C['fiber_density_kg_m3']
    core=(1-skin/C['branch_radius_um'])**2
    v=vf/core
    if not 0<v<1: raise ValueError('Fibrils do not fit inside fiber-free skin')
    r=d*1e-6/2; L=length*1e-6
    Af=math.pi*r*r; Acell=Af/v; Am=Acell-Af
    Km=Am*em*1e6; Kf=Af*ef*1e6; total=Km+Kf
    gm=em*1e6/(2*(1+C['host_nu']))
    spring=chi*2*math.pi*gm/math.log(1/math.sqrt(v))
    beta=math.sqrt(spring*(1/Km+1/Kf))
    b=beta*L/2
    tb=1 if b==0 else math.tanh(b)/b
    effective_EA=total/(1+(Kf/Km)*tb)
    Ecore=effective_EA/Acell/1e6
    core_matrix=em*(1-v)
    Eproxy=(1-core)*em+core*(core_matrix+orientation*(Ecore-core_matrix))
    voigt=em*(1-vf)+ef*vf
    return dict(w=w,skin_um=skin,Em_MPa=em,Ef_MPa=ef,diameter_um=d,length_um=length,
        transfer_factor=chi,orientation_factor=orientation,density_kg_m3=rho,
        fiber_volume_fraction=vf,core_area_fraction=core,core_local_fiber_volume_fraction=v,
        beta_per_m=beta,b=b,Ecore_parallel_MPa=Ecore,E_direction_proxy_MPa=Eproxy,
        stiffness_ratio_proxy=Eproxy/em,perfect_long_aligned_MPa=voigt,
        matrix_only_area_MPa=em*(1-vf),
        cell=dict(Af_m2=Af,Am_m2=Am,Acell_m2=Acell,Kf_N=Kf,Km_N=Km,spring_N_m2=spring,L_m=L,effective_EA_N=effective_EA))
geometry=[model(d=d,length=l,chi=c,orientation=o) for d,l,c,o in itertools.product(C['fiber_diameter_um'],C['fiber_length_um'],C['transfer_factors'],C['orientation_factors'])]
properties=[model(em=em,ef=ef,chi=c) for em,ef,c in itertools.product(C['host_E_MPa'],C['fiber_E_MPa'],C['transfer_factors'])]
skins=[model(w=w,skin=s,orientation=o) for w,s,o in itertools.product(C['fiber_mass_fractions'],C['skin_thickness_um'],C['orientation_factors'])]
refs=[model(d=d,chi=c) for d,c in itertools.product(Q['diameter_um'],Q['transfer_factors'])]
cost=[]
for w,pf,forming in itertools.product(C['fiber_mass_fractions'],K['fiber_JPY_kg'],K['forming_JPY_kg']):
    rho=density(w); mass=solid_volume*rho; price=(1-w)*K['host_JPY_kg']+w*pf+forming
    annual=(mass*price+K['nonmaterial_capital_JPY'])*crf+K['annual_fixed_JPY']+mass*price*K['annual_replacement_fraction']
    cost.append(dict(w=w,fiber_JPY_kg=pf,forming_JPY_kg=forming,density_kg_m3=rho,
        fixed_shape_material_mass_kg=mass,mixture_JPY_kg=price,annual_total_JPY=annual,
        annual_remaining_JPY=K['annual_budget_JPY']-annual,
        minimum_modulus_ratio_for_ideal_same_bending_material_cost=(rho/B['reference_host_density_kg_m3']*price/K['material_JPY_kg'])**2))
resize=[]
for r,pf in itertools.product(refs,K['fiber_JPY_kg']):
    price=(1-r['w'])*K['host_JPY_kg']+r['w']*pf
    ratio=r['stiffness_ratio_proxy']
    radius_ratio=ratio**(-.25); volume_ratio=ratio**(-.5)
    material_ratio=r['density_kg_m3']/B['reference_host_density_kg_m3']*volume_ratio
    resize.append(dict(diameter_um=r['diameter_um'],transfer_factor=r['transfer_factor'],fiber_JPY_kg=pf,
        proxy_modulus_ratio=ratio,ideal_radius_ratio=radius_ratio,ideal_mass_ratio=material_ratio,
        ideal_raw_material_cost_ratio=material_ratio*price/K['material_JPY_kg'],
        note='Conditional circular-beam scaling only if this proxy were the measured bending modulus. Does not preserve snow contact, openings, skin depth, torsion or buckling.'))
production=[]
for w,rate in itertools.product(C['fiber_mass_fractions'],I['throughput']['reference_laboratory_kg_h']):
    m=solid_volume*density(w); need=m/(I['throughput']['campaign_hours']*I['throughput']['yield_fraction'])
    production.append(dict(w=w,finished_mass_kg=m,assumed_yield=I['throughput']['yield_fraction'],gross_needed_kg_h=need,
        laboratory_reference_kg_h=rate,equivalent_lines=math.ceil(need/rate),annual_purchase_kg=m*K['annual_replacement_fraction']))
reg=I['regeneration']
loss=dict(source=reg['source'],retained_modulus_fraction=reg['modulus_after_GPa']/reg['modulus_before_GPa'],
    same_geometry_deflection_multiplier=reg['modulus_before_GPa']/reg['modulus_after_GPa'],
    hypothetical_radius_multiplier=(reg['modulus_before_GPa']/reg['modulus_after_GPa'])**.25,
    hypothetical_mass_multiplier=(reg['modulus_before_GPa']/reg['modulus_after_GPa'])**.5)
# Independent minimum-energy discretization: matrix ends prescribed, fiber ends free.
def fe(cell,n):
    h=cell['L_m']/n; size=2*(n+1)
    A=np.zeros((size,size))
    for j in range(n):
        for phase,key in [(0,'Kf_N'),(1,'Km_N')]:
            a=2*j+phase; b=a+2; k=cell[key]/h
            A[a,a]+=k; A[b,b]+=k; A[a,b]-=k; A[b,a]-=k
        ids=[2*j,2*j+1,2*j+2,2*j+3]
        D=np.array([[1,-1,0,0],[0,0,1,-1]],float)
        H=cell['spring_N_m2']*h/6*(D.T@np.array([[2,1],[1,2]])@D)
        A[np.ix_(ids,ids)]+=H
    fixed=[1,size-1]; free=[j for j in range(size) if j not in fixed]
    u=np.zeros(size); u[-1]=cell['L_m']*.001
    u[free]=np.linalg.solve(A[np.ix_(free,free)],-A[np.ix_(free,fixed)]@u[fixed])
    reaction=A@u; force=reaction[-1]; ea=force*cell['L_m']/u[-1]
    work=.5*force*u[-1]; energy=.5*u@(A@u)
    return dict(elements=n,EA_N=ea,relative_error=abs(ea/cell['effective_EA_N']-1),
        relative_energy_residual=abs(energy/work-1),
        free_equilibrium_residual_relative=float(np.max(np.abs(reaction[free]))/abs(force)))
verification=[]
for d,c in [(1,.01),(1,1),(10,.01),(10,1)]:
    r=model(d=d,chi=c)
    verification.append(dict(diameter_um=d,transfer_factor=c,analytical_EA_N=r['cell']['effective_EA_N'],meshes=[fe(r['cell'],n) for n in I['numerics']['fe_elements']]))
checks=[]
def check(name,test):checks.append(dict(name=name,passed=bool(test)))
all_rows=geometry+properties+skins
check('108t reference',mass0==108000)
check('inherited baseline',math.isclose(base,16108182.1636,abs_tol=.01))
check('mass-volume conversion',all(math.isclose(r['fiber_volume_fraction']*C['fiber_density_kg_m3']/r['density_kg_m3'],r['w'],rel_tol=1e-12) for r in all_rows))
check('skin preserves global fiber volume',all(math.isclose(r['core_local_fiber_volume_fraction']*r['core_area_fraction'],r['fiber_volume_fraction']) for r in all_rows))
check('core fiber volume fraction below unity',all(0<r['core_local_fiber_volume_fraction']<1 for r in all_rows))
check('positive all stiffness',all(r['E_direction_proxy_MPa']>0 for r in all_rows))
check('upper aligned Voigt bound',all(r['E_direction_proxy_MPa']<=r['perfect_long_aligned_MPa']*(1+1e-12) for r in all_rows))
check('matrix area lower bound',all(r['E_direction_proxy_MPa']>=r['matrix_only_area_MPa'] for r in all_rows))
check('zero transfer uncouples fiber',math.isclose(model(chi=0)['E_direction_proxy_MPa'],model(chi=0)['matrix_only_area_MPa'],rel_tol=1e-12))
check('long-fiber limit',math.isclose(model(length=1e10)['E_direction_proxy_MPa'],model(length=1e10)['perfect_long_aligned_MPa'],rel_tol=1e-7))
check('monotonic transfer',model(chi=.01)['E_direction_proxy_MPa']<model(chi=.1)['E_direction_proxy_MPa']<model(chi=1)['E_direction_proxy_MPa'])
check('monotonic fiber length',model(length=20)['E_direction_proxy_MPa']<model(length=50)['E_direction_proxy_MPa']<model(length=150)['E_direction_proxy_MPa'])
check('orientation proxies ordered',model(orientation=.2)['E_direction_proxy_MPa']<model(orientation=.375)['E_direction_proxy_MPa']<model(orientation=1)['E_direction_proxy_MPa'])
check('same aspect scaling',math.isclose(model(d=1,length=50)['E_direction_proxy_MPa'],model(d=3,length=150)['E_direction_proxy_MPa'],rel_tol=1e-12))
check('geometric stiffness scaling invariant',all(math.isclose(r['proxy_modulus_ratio']*r['ideal_radius_ratio']**4,1,rel_tol=1e-12) for r in resize))
check('price threshold algebra',all(math.isclose(r['minimum_modulus_ratio_for_ideal_same_bending_material_cost']**.5,r['density_kg_m3']/B['reference_host_density_kg_m3']*r['mixture_JPY_kg']/K['material_JPY_kg']) for r in cost))
check('fixed shape volume conserved',all(math.isclose(r['fixed_shape_material_mass_kg']/r['density_kg_m3'],solid_volume) for r in cost))
check('source modulus retention',loss['retained_modulus_fraction']==.375)
check('source stiffness resize arithmetic',math.isclose(loss['hypothetical_radius_multiplier']**4,8/3))
check('FE final stiffness accuracy',all(x['meshes'][-1]['relative_error']<I['numerics']['fe_relative_error_limit'] for x in verification))
check('FE convergence',all(x['meshes'][0]['relative_error']>x['meshes'][1]['relative_error']>x['meshes'][2]['relative_error'] for x in verification))
check('FE energy balance',all(x['relative_energy_residual']<1e-8 for v in verification for x in v['meshes']))
check('FE free-node equilibrium',all(x['free_equilibrium_residual_relative']<1e-8 for v in verification for x in v['meshes']))
check('no probability invention',I['evidence']['physical_success_probability'] is None and I['evidence']['physical_tests']==0)
result=dict(evidence=I['evidence'],common=dict(reference_mass_kg=mass0,reference_polymer_volume_m3=solid_volume,crf=crf,base_annual_JPY=base,margin_JPY=margin),
    geometry_cases=geometry,property_cases=properties,skin_cases=skins,reference_cases=refs,
    same_shape_cost_cases=cost,ideal_resize_diagnostics=resize,production_diagnostics=production,regeneration_reference=loss,fe_verification=verification)
validation=dict(numerical_checks=len(checks),all_passed=all(x['passed'] for x in checks),checks=checks,numpy_version=np.__version__,not_validated=['50C creep','actual modulus or adhesion','3D branch mechanics','skin closure and exposed fiber abrasion','snowlike morphology and friction','rain/winter/weather safety','commercial costs'])
for name,data in [('results.json',result),('validation.json',validation)]:
 (P/name).write_bytes((json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
print(json.dumps(dict(checks=len(checks),passed=validation['all_passed'],counts={x:len(result[x]) for x in ['geometry_cases','property_cases','skin_cases','same_shape_cost_cases','ideal_resize_diagnostics']},FE_max_final_error=max(x['meshes'][-1]['relative_error'] for x in verification),numpy=np.__version__)))
if not validation['all_passed']:raise SystemExit('NUMERICAL VALIDATION FAILED')
