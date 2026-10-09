"""H65: coupling thickness, initial stiffness, fracture work and parallel load paths.
All material parameters are assumptions; no fitted snow or protein properties.
"""
import csv,json,math
from pathlib import Path
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
g=I['geometry'];r=I['reference'];s=I['sweep'];p=I['cost']
V=g['area_m2']*g['depth_m'];D=g['grain_D_m'];F=g['assumed_network_strength_Pa']*math.pi*D*D/(g['phi']*g['z']*g['q'])
N=6*g['phi']*V/(math.pi*D**3);Nb=g['z']*N/2
sig=r['joint_strength_Pa'];E=r['joint_modulus_Pa'];ell=r['length_m'];Gc=r['Gc_J_m2'];A=F/sig
checks=[]
def check(n,b):
    checks.append({'name':n,'passed':bool(b)})
    if not b: raise AssertionError(n)
def close(a,b,tol=1e-10):return math.isclose(a,b,rel_tol=tol,abs_tol=1e-16)
def one(sig,E,ell,G,A):
    d0=sig*ell/E;df=2*G/sig;k=E*A/ell;fp=sig*A
    return {'sigma_Pa':sig,'E_Pa':E,'length_m':ell,'Gc_J_m2':G,'area_m2':A,'Fpeak_N':fp,'d0_um':d0*1e6,'df_um':df*1e6,'minimum_G_J_m2':sig*sig*ell/(2*E),'bridge_K_N_m':k,'energy_J':A*G,'positive_softening_interval':df>d0,'linear_strain_diagnostic_ok':sig/E<=s['small_strain_diagnostic_limit'],'initial_strain':sig/E,'softening_slope_magnitude_N_m':fp/(df-d0) if df>d0 else None}
ref=one(sig,E,ell,Gc,A)
rows=[one(ss,ee,ll,gg,F/ss) for ss in s['strength_Pa'] for ee in s['modulus_Pa'] for ll in s['length_m'] for gg in s['Gc_J_m2']]
def force_chem(x,c):
    d0=c['d0_um']*1e-6;df=c['df_um']*1e-6
    if x<0:return 0.
    if x<=d0:return c['bridge_K_N_m']*x
    if x<df:return c['Fpeak_N']*(df-x)/(df-d0)
    return 0.
def trap(fn,a,b,n=100007):
    h=(b-a)/n
    return h*(0.5*fn(a)+sum(fn(a+i*h) for i in range(1,n))+0.5*fn(b))
check('Rumpf_force_matches_cycle64',close(F,0.004759988869075444))
check('reference_peak_opening_1um',close(ref['d0_um'],1))
check('reference_final_opening_20um',close(ref['df_um'],20))
check('reference_minimum_G_0_5',close(ref['minimum_G_J_m2'],.5))
check('reference_work_numeric',close(trap(lambda x:force_chem(x,ref),0,ref['df_um']*1e-6),ref['energy_J'],1e-8))
check('inconsistent_combo_detected',not one(1e6,1e6,10e-6,1,A)['positive_softening_interval'])
check('threshold_zero_interval_rejected',not one(1e6,10e6,10e-6,.5,A)['positive_softening_interval'])
check('force_zero_after_complete_release',force_chem(30e-6,ref)==0)
check('peak_force_matches',close(force_chem(1e-6,ref),F))
thickness=[]
for ll in s['length_m']:
    c=one(sig,E,ll,Gc,A);mass=Nb*A*ll*g['connector_density_kg_m3'];beta=c['bridge_K_N_m']/(c['bridge_K_N_m']+r['mechanical_K_N_m'])
    thickness.append({'length_um':ll*1e6,'mass_kg':mass,'bridge_K_N_m':c['bridge_K_N_m'],'fraction_if_parallel_100N_m':beta,'peak_opening_um':c['d0_um'],'final_opening_um':c['df_um'],'initial_material_JPY':mass/p['downstream_yield']*p['price_JPY_kg']})
check('thin_layer_same_final_opening',len(set(x['final_opening_um'] for x in thickness))==1)
check('thinning_increases_stiffness_10fold',close(thickness[0]['bridge_K_N_m']/thickness[1]['bridge_K_N_m'],10))
check('thinning_mass_10fold',close(thickness[1]['mass_kg']/thickness[0]['mass_kg'],10))
beta=r['target_chemical_load_fraction'];small=one(sig,E,ell,Gc,beta*A);d0=small['d0_um']*1e-6;df=small['df_um']*1e-6
Km_needed=(1-beta)*F/d0
Km_wrong=r['mechanical_K_N_m'];beta_actual=small['bridge_K_N_m']/(small['bridge_K_N_m']+Km_wrong)
width=r['mechanical_release_width_m']
def force_mech(x,release):
    if x<=d0:return Km_needed*x
    if not release:return Km_needed*x
    if x<d0+width:return Km_needed*d0*(d0+width-x)/width
    return 0.
def total(x,release):return force_chem(x,small)+force_mech(x,release)
curve=[]
for n in range(801):
    x=n*25e-6/800
    curve.append({'opening_um':x*1e6,'chemical_N':force_chem(x,small),'mechanical_stays_N':force_mech(x,False),'mechanical_releases_N':force_mech(x,True),'total_stays_N':total(x,False),'total_releases_N':total(x,True)})
Wmech=.5*Km_needed*d0*d0+.5*Km_needed*d0*width
Wtotal=small['energy_J']+Wmech
check('target_load_sum_at_peak',close(total(d0,True),F))
check('target_fraction_at_peak',close(force_chem(d0,small)/total(d0,True),beta))
check('small_patch_not_10percent_with_soft_parallel',beta_actual>beta)
check('mechanical_residual_at_df',close(force_mech(df,False)/F,18))
check('ideal_bypass_zero_final_force',total(df,True)==0)
check('mechanical_release_work_integral',close(trap(lambda x:force_mech(x,True),0,df),Wmech,1e-7))
check('total_release_work_integral',close(trap(lambda x:total(x,True),0,df),Wtotal,1e-7))
fixture=[]
ksoft=ref['softening_slope_magnitude_N_m']
for K in s['fixture_K_N_m']:
    fixture.append({'fixture_K_N_m':K,'softening_slope_N_m':ksoft,'du_d_delta':1-ksoft/K,'quasistatic_displacement_branch_stable':K>ksoft,'peak_crosshead_um':ref['d0_um']+F/K*1e6,'final_crosshead_um':ref['df_um']})
check('fixture_soft_snapback',not fixture[0]['quasistatic_displacement_branch_stable'])
check('fixture_stiff_traceable',fixture[-1]['quasistatic_displacement_branch_stable'])
check('fixture_compliance_unit',close(fixture[0]['peak_crosshead_um'],1+F/50*1e6))
check('grid96',len(rows)==96)
check('physical_test_status',I['evidence']['physical_tests']==0 and I['evidence']['success_probability'] is None)
summary={'evidence':I['evidence'],'force_reference_N':F,'reference':ref,'thickness':thickness,'load_split':{'target_beta':beta,'reduced_area_m2':beta*A,'actual_beta_if_Km100':beta_actual,'total_peak_N_if_Km100':small['Fpeak_N']+Km_wrong*d0,'required_Km_N_m':Km_needed,'unchanged_mechanical_force_at_20um_N':force_mech(df,False),'ideal_release_total_work_J':Wtotal,'ideal_release_chemical_work_J':small['energy_J'],'ideal_release_mechanical_work_J':Wmech,'mechanical_stored_energy_at_peak_J':.5*Km_needed*d0*d0,'ideal_remaining_chemical_force_fraction_at_mechanical_release':force_chem(d0+width,small)/F,'ideal_chemical_mass_kg':Nb*beta*A*ell*g['connector_density_kg_m3'],'ideal_initial_material_JPY':Nb*beta*A*ell*g['connector_density_kg_m3']/p['downstream_yield']*p['price_JPY_kg'],'warning':'load paths, coordinated release, networks, damping, material parameters and manufacture unproven'},'fixture':fixture,'grid_rows':len(rows),'valid_form_and_strain_rows':sum(x['positive_softening_interval'] and x['linear_strain_diagnostic_ok'] for x in rows),'valid_rows_are_not_success_probability':True}
def csvwrite(name,rs):
    with (P/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
csvwrite('bridge_screen.csv',rows);csvwrite('thickness_screen.csv',thickness);csvwrite('force_paths.csv',curve);csvwrite('fixture_screen.csv',fixture)
(P/'results.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
(P/'numerical_checks.json').write_text(json.dumps({'passed':all(c['passed'] for c in checks),'checks':checks,'physical_tests':0},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':len(checks),'grid':len(rows),'reference':ref,'load_split':summary['load_split']},ensure_ascii=False))
