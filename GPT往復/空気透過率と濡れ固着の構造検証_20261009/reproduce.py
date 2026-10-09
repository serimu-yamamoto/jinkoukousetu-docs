"""Cycle75: pore geometry, capillary instability and local/global compliance.
Screening only. No experiments, calibrated ski prediction, or success probability.
Standard library. Reuses cycle74 air operator with its limitations.
"""
from pathlib import Path
from math import pi,exp,sqrt,cos,isfinite
import json,csv,importlib.util,hashlib
D=Path(__file__).resolve().parent;R=D.parents[1]
BASE='f2f920434683c60d55a035d3c0f12b92d070cc09'
PRIOR=R/'GPT往復/粒間空気支持と排水の両立検証_20261009/reproduce.py'
spec=importlib.util.spec_from_file_location('cycle74_air',PRIOR)
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
P={'gamma_water_N_m':.072,'rho_water':1000.,'mu_water':.001,'g':9.81,
   'E_local_Pa':1e9,'plate_t_m':10e-6,'plate_span_m':100e-6,'gap_m':40e-6,
   'wetting_cosine':1.,'local_phi_for_channel_comparison':.8,'target_air_k_m2':3e-12,
   'functional_area_m2':330565.0,'solid_density_kg_m3':1200.,
   'price_JPY_kg_assumption':[500.,2000.],'yield_assumption':.8,
   'whole_bed_kg':108000.,'bulk_phi_reference':.9,
   'root_width_m':100e-6,'root_t_m':20e-6,'root_L_m':500e-6,
   'head_area_m2':1e-8,'representative_particle_mass_kg':3.5e-8,'normal_test_force_N':20e-6}
SNOW=[
('Fr','PP',3.58,3.77,3.69,55.30,120.49),
('P04','DF',6.14,6.38,4.62,25.36,157.54),
('P11','RG',.46,.45,.40,20.76,413.75),
('H02','MF',1.22,1.22,1.27,6.18,471.70),
('E2b','FC',5.71,4.87,5.62,15.43,239.70),
('Grad3','DH',.65,.63,1.06,21.84,369.18)]
def wj(fn,obj):
    (D/fn).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def wc(fn,rows):
    with (D/fn).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def root_y(lam):
    if lam<0:raise ValueError('negative wetting attraction excluded')
    return 2*lam/(1+sqrt(1-4*lam)) if lam<=.25 else None
def capillary(E,t,l,s,gamma=.072,ct=1.):
    lam=6*gamma*ct*l**4/(E*t**3*s**2)
    y=root_y(lam)
    pc=2*gamma*ct/(s*(1-y)) if y is not None else None
    return dict(E_Pa=E,t_um=t*1e6,span_um=l*1e6,gap_um=s*1e6,cos_contact_angle=ct,
                Lambda=lam,lumped_equilibrium_exists=y is not None,
                gap_closure_fraction=y,gap_remaining_um=s*(1-y)*1e6 if y is not None else None,
                meniscus_pressure_Pa=pc,
                max_root_bending_stress_Pa=3*pc*l*l/t**2 if pc is not None else None,
                each_tip_deflection_over_span=s*y/(2*l) if y is not None else None,
                critical_span_um=(E*t**3*s*s/(24*gamma*ct))**.25*1e6 if ct>0 else None)
def bridge(k,A,s,gamma=.072):
    lam=4*gamma*A/(k*s*s);y=root_y(lam)
    return dict(root_k_N_m=k,overlap_area_m2=A,gap_um=s*1e6,Lambda=lam,
                lumped_equilibrium_exists=y is not None,closure_fraction=y,
                overlap_area_limit_m2=k*s*s/(16*gamma))
def main():
    inp={'cycle':75,'basis_commit':BASE,'physical_experiments':0,'success_probability':None,
         'parameters':P,'source':{'snow_table':'Calonne et al. 2012 Supplement Table2, six grey-row examples; CT-derived computations',
         'prior_air_operator':PRIOR.relative_to(R).as_posix(),
         'prior_code_sha256_lf':hashlib.sha256(PRIOR.read_text(encoding='utf-8').replace('\r\n','\n').encode()).hexdigest()}}
    wj('inputs.json',inp)
    snow=[];air=[]
    for name,typ,kx,ky,kz,ssa,rho in SNOW:
        mean=(kx+ky+kz)/3*1e-9;re=3/(ssa*917.)
        snow.append(dict(sample=name,type=typ,kx_m2=kx*1e-9,ky_m2=ky*1e-9,kz_m2=kz*1e-9,
                         SSA_m2_kg=ssa,rho_kg_m3=rho,mean_k_m2=mean,vertical_horizontal_ratio=kz/((kx+ky)/2),
                         k_over_cycle74_assumption=mean/3e-12,
                         re_equivalent_um=re*1e6,K_calonne_final_m2=3*re**2*exp(-.013*rho)))
        aa=prior.solve(ky=(kx+ky)/2*1e-9,kz=kz*1e-9,Ed=50000.)
        air.append({'source_sample':name,'interpretation':'only k imported; Ed/phi/temperature artificial hypothetical bed, NOT snow skiing',
                    'k_horizontal_m2':aa['ky'],'k_vertical_m2':aa['kz'],'hypothetical_Ed_Pa':50000.,
                    'air_fraction':aa['air_load_fraction'],'diagnostic_mu':aa['mu_diagnostic'],
                    'delta_mm':aa['delta_mm'],'small_strain_pressure_screen':aa['within_small_strain_and_pressure_screen']})
    channels=[]
    for geometry in ['parallel_slit','circular_tube']:
        for dim in [10e-6,20e-6,40e-6,100e-6,300e-6]:
            for tau in [1.,10.,100.]:
                # dim=full slit gap or tube radius; tortuosity resistance factor (path ratio squared)
                denom=12 if geometry=='parallel_slit' else 8
                kk=.8*dim**2/(denom*tau)
                channels.append(dict(geometry=geometry,dimension_um=dim*1e6,resistance_factor=tau,
                        path_ratio_if_ideal_tube=sqrt(tau),local_void_fraction=.8,k_m2=kk,
                        target_k_ratio=kk/3e-12,
                        resistance_factor_needed_for_target=.8*dim**2/(denom*3e-12),
                        complete_wetting_capillary_head_m=2*.072/(1000*9.81*dim),
                        intrinsic_Darcy_mm_h_at_gradient1=kk*1000*9.81/.001*3.6e6))
    plates=[capillary(e,t,l,s) for e in [.2e9,1e9,2e9] for t in [5e-6,10e-6,20e-6]
            for l in [50e-6,100e-6,200e-6] for s in [10e-6,40e-6,100e-6]]
    # 3^4 = 81 plate cases
    tolerances=[{'pressure_multiplier':fac,**capillary(e,t,l,s,gamma=.072*fac)}
            for l in [50e-6,100e-6] for e in [.2e9,1e9] for t in [8e-6,12e-6]
            for s in [30e-6,40e-6] for fac in [1.,2.]]
    heads=[{'fraction_of_100um_square':f,**bridge(k,1e-8*f,40e-6)}
           for k in [.2,.8,1.6,5.,10.] for f in [.001,.01,.05,.1,.2,.5,1.]]
    mobility=[]
    for s in [10e-6,40e-6]:
        for f in [.0001,.001,.01,.05,.1,.5,1.]:
            area=1e-8*f;fp=2*.072*area/s;line=2*.072*sqrt(pi*area);weight=P['representative_particle_mass_kg']*9.81
            mobility.append(dict(gap_um=s*1e6,area_fraction=f,area_m2=area,
                    pressure_component_N=fp,contact_line_scale_N=line,
                    illustrative_sum_N=fp+line,particle_weight_N=weight,
                    pressure_over_weight=fp/weight,sum_over_weight=(fp+line)/weight,
                    scope='two contributions are geometric scales, not measured pull-off or universal upper bound'))
    roots=[]
    for L in [250e-6,500e-6,1e-3]:
        for t in [10e-6,20e-6,30e-6]:
            k=1e9*100e-6*t**3/(4*L**3);de=20e-6/k
            roots.append(dict(L_um=L*1e6,t_um=t*1e6,width_um=100.,E_Pa=1e9,
                     k_N_m=k,deflection_at_20uN_um=de*1e6,deflection_over_L=de/L,
                     small_deflection_screen=de/L<=.1,
                     interparticle_bridge_Lambda_full_square=bridge(k,1e-8,40e-6)['Lambda']))
    costs=[]
    A=P['functional_area_m2']
    for pitch in [50e-6,100e-6,200e-6]:
        for height in [10e-6,40e-6,100e-6]:
            d=10e-6;fraction=2*d/pitch-(d/pitch)**2;volume=A*height*fraction
            for price in P['price_JPY_kg_assumption']:
                costs.append(dict(pitch_um=pitch*1e6,rib_width_um=10.,rib_height_um=height*1e6,
                    square_grid_area_fraction=fraction,open_projected_fraction=1-fraction,
                    functional_area_m2=A,added_volume_m3=volume,added_mass_kg=volume*1200,
                    added_fraction_of_108t=volume*1200/108000,
                    price_JPY_kg=price,yield_fraction=.8,
                    raw_only_JPY_ex_tax=volume*1200*price/.8))
    datasets={'snow_source_subset.csv':snow,'snow_k_transfer.csv':air,
              'channel_geometries.csv':channels,'capillary_plates.csv':plates,'capillary_tolerance.csv':tolerances,
              'interparticle_bridge.csv':heads,'particle_mobility.csv':mobility,'root_compliance.csv':roots,'rib_cost.csv':costs}
    for n,rows in datasets.items():wc(n,rows)
    checks=[]
    def ck(name,ok,detail=''):
        checks.append(dict(name=name,passed=bool(ok),detail=detail))
    reference=capillary(1e9,10e-6,100e-6,40e-6)
    ck('lambda_reference',abs(reference['Lambda']-.027)<1e-12,reference)
    ck('lambda_length_fourth',abs(capillary(1e9,10e-6,200e-6,40e-6)['Lambda']/reference['Lambda']-16)<1e-12)
    ck('lambda_thickness_inverse_cube',abs(capillary(1e9,20e-6,100e-6,40e-6)['Lambda']/reference['Lambda']-1/8)<1e-12)
    ck('lambda_gap_inverse_square',abs(capillary(1e9,10e-6,100e-6,80e-6)['Lambda']/reference['Lambda']-.25)<1e-12)
    ck('lambda_E_inverse',abs(capillary(2e9,10e-6,100e-6,40e-6)['Lambda']/reference['Lambda']-.5)<1e-12)
    ck('threshold_root',abs(root_y(.25)-.5)<1e-14)
    ck('above_lumped_threshold',root_y(.25001) is None,'not a proof of collapse in a real structure')
    ck('nonwetting_attraction_zero',capillary(1e9,10e-6,100e-6,40e-6,ct=0)['gap_closure_fraction']==0,'no claim actual contact angle is 90 degrees')
    valid=[r for r in plates if r['lumped_equilibrium_exists']]
    ck('lumped_equilibrium_residual',all(abs(r['gap_closure_fraction']*(1-r['gap_closure_fraction'])-r['Lambda'])<1e-12 for r in valid))
    ck('beam_force_deflection_closure',all(abs(3*r['meniscus_pressure_Pa']*(r['span_um']*1e-6)**4/(r['E_Pa']*(r['t_um']*1e-6)**3)/(r['gap_um']*1e-6)-r['gap_closure_fraction'])<1e-12 for r in valid))
    ck('critical_length_lambda',abs(capillary(1e9,10e-6,reference['critical_span_um']*1e-6,40e-6)['Lambda']-.25)<1e-12)
    ck('pore_model_units',abs(next(r for r in channels if r['geometry']=='parallel_slit' and r['dimension_um']==40 and r['resistance_factor']==1)['k_m2']-1.0666666666666667e-10)<1e-22)
    ck('tortuosity_scaling',all(abs(r['k_m2']/3e-12-r['resistance_factor_needed_for_target']/r['resistance_factor'])<1e-9 for r in channels),'all 30 ideal channel rows')
    ck('capillary_head_gap40',abs(next(r for r in channels if r['geometry']=='parallel_slit' and r['dimension_um']==40)['complete_wetting_capillary_head_m']-.36697247706422015)<1e-12)
    kr=1e9*100e-6*(20e-6)**3/(4*(500e-6)**3)
    ck('root_stiffness',abs(kr-1.6)<1e-12)
    hh=bridge(kr,1e-8,40e-6);small=bridge(kr,1e-9,40e-6)
    ck('interparticle_full_overlap_counterexample',abs(hh['Lambda']-1.125)<1e-12 and hh['closure_fraction'] is None)
    ck('interparticle_reduced_overlap',small['Lambda']<.25 and small['closure_fraction'] is not None)
    ck('overlap_limit_units',abs(hh['overlap_area_limit_m2']/(1e-12)-2222.222222222222)<1e-8)
    ck('rib_area_inclusion_exclusion',abs((2*.1-.1**2)-.19)<1e-12)
    ck('cost_mass_identity',all(abs(r['added_mass_kg']-r['added_volume_m3']*1200)<1e-9 for r in costs))
    ck('cost_yield_identity',all(abs(r['raw_only_JPY_ex_tax']*.8-r['added_mass_kg']*r['price_JPY_kg'])<1e-6 for r in costs))
    ck('source_six_types',len({r['type'] for r in snow})==6)
    ck('source_tensor_average',all(abs(r['mean_k_m2']-(r['kx_m2']+r['ky_m2']+r['kz_m2'])/3)<1e-22 for r in snow))
    ck('prior_air_same_parameters',all(r['hypothetical_Ed_Pa']==50000 and r['small_strain_pressure_screen'] for r in air))
    ck('source_K_not_actual_ski_experiment',all('NOT snow skiing' in r['interpretation'] for r in air))
    ck('finite_numbers',all(isfinite(v) for rs in datasets.values() for r in rs for v in r.values() if isinstance(v,(int,float))))
    short=[r for r in tolerances if r['span_um']==50.]
    long=[r for r in tolerances if r['span_um']==100.]
    ck('tolerance_worst_lambda',abs(max(r['Lambda'] for r in short)-.05859375)<1e-12)
    ck('tolerance_counterexample_retained',max(r['Lambda'] for r in long)>.25 and all(r['Lambda']<.25 for r in short),'parameter box only, not a success probability')
    ck('particle_weight_units',abs(P['representative_particle_mass_kg']*9.81-3.4335e-7)<1e-18)
    ck('line_force_area_scaling',abs((2*.072*sqrt(pi*1e-10))/(2*.072*sqrt(pi*1e-8))-.1)<1e-12,'pressure-area reduction alone does not scale the line contribution equally')
    counts={k:len(v) for k,v in datasets.items()}
    result={'cycle':75,'physical_experiments':0,'success_probability':None,'reference_plate':reference,
            'long_plate':capillary(1e9,10e-6,200e-6,40e-6),'root_reference_k_N_m':kr,
            'interparticle_full_overlap':hh,'interparticle_10percent_overlap':small,
            'source_k_ratio_range':[min(r['k_over_cycle74_assumption'] for r in snow),max(r['k_over_cycle74_assumption'] for r in snow)],
            'artificial_reference_same_Ed50':prior.solve(Ed=50000.),'transferred_air_fraction_range':[min(r['air_fraction'] for r in air),max(r['air_fraction'] for r in air)],
            'rib_reference':[r for r in costs if abs(r['pitch_um']-100)<1e-8 and abs(r['rib_height_um']-40)<1e-8],
            'tolerance_short_worst_Lambda':max(r['Lambda'] for r in short),'tolerance_long_worst_Lambda':max(r['Lambda'] for r in long),'row_counts':counts,'total_rows':sum(counts.values())}
    wj('results.json',result);wj('checks.json',{'checks':checks,'passed':sum(x['passed'] for x in checks),'total':len(checks),'physical_validation':False})
    assert all(x['passed'] for x in checks),[x for x in checks if not x['passed']]
    print(json.dumps({'checks':len(checks),'rows':result['total_rows'],'reference':reference,'air_share_range':result['transferred_air_fraction_range'],'rib_reference':result['rib_reference']}))
if __name__=='__main__':main()
