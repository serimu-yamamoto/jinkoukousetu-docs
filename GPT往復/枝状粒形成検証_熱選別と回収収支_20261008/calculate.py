from pathlib import Path
import json, math, itertools
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf8'))
T,W,F=[I[x] for x in ('thermal','wet','factory')]
checks=[]
def check(name,condition): checks.append(dict(name=name,passed=bool(condition)))
def heat(radius_um,h,gas):
    r=radius_um*1e-6
    tau=T['rho_kg_m3']*T['cp_J_kgK']*r/(2*h)
    sensible=tau*math.log((gas-T['T0_C'])/(gas-T['Tm_C']))
    phase=T['rho_kg_m3']*r*T['latent_J_kg']/(2*h*(gas-T['Tm_C']))
    return dict(onset_s=sensible,full_melt_s=sensible+phase,latent_s=phase,tau_s=tau,Bi=h*r/(2*T['k_W_mK']))
def process(rf,rs,h,gas,eta,mults=(1,1)):
    a=heat(rf,h*mults[0],gas);b=heat(rs,h*mults[1],gas)
    shape=T['shape_time_coefficient']*eta*rf*1e-6/T['melt_surface_tension_N_m']
    j=T['residence_fraction_uncertainty']
    lower=(a['full_melt_s']+shape)/(1-j);upper=b['onset_s']/(1+j)
    available=b['onset_s']*(1-j)/(1+j)-a['full_melt_s']
    eta_limit=max(0,available)*T['melt_surface_tension_N_m']/(T['shape_time_coefficient']*rf*1e-6)
    return dict(fine_radius_um=rf,support_radius_um=rs,h=h,gas_C=gas,eta_Pa_s=eta,h_fine_factor=mults[0],h_support_factor=mults[1],fine=a,support=b,shape_scale_s=shape,nominal_lower_s=lower,nominal_upper_s=upper,conditional_window=lower<upper,available_shape_s=available,eta_limit_Pa_s=eta_limit)
thermal=[process(*x) for x in itertools.product(T['fine_radii_um'],T['support_radii_um'],T['h_W_m2K'],T['gas_C'],T['viscosity_Pa_s'],T['h_multipliers'])]
# Independent midpoint quadrature of dt/dH, with a separate exact constant-temperature latent segment.
quadrature=[]
for r,h,g in [(0.5,500,150),(3,100,180),(20,2000,150)]:
    exact=heat(r,h,g); rho_r=T['rho_kg_m3']*r*1e-6; Hs=T['cp_J_kgK']*(T['Tm_C']-T['T0_C'])
    meshes=[]
    for n in [100,1000,10000]:
        dH=Hs/n
        qs=sum(rho_r/(2*h*(g-T['T0_C']-(k+.5)*dH/T['cp_J_kgK']))*dH for k in range(n))
        ql=rho_r*T['latent_J_kg']/(2*h*(g-T['Tm_C']))
        val=qs+ql
        meshes.append(dict(n=n,full_melt_s=val,relative_error=abs(val-exact['full_melt_s'])/exact['full_melt_s']))
    quadrature.append(dict(radius_um=r,h=h,gas_C=g,analytic=exact['full_melt_s'],meshes=meshes))
wet=[]
for ru,lu,Em,b in itertools.product(W['radii_um'],W['lengths_um'],W['moduli_MPa'],W['force_factors']):
    r=ru*1e-6;L=lu*1e-6;E=Em*1e6;J=math.pi*r**4/4
    force=2*math.pi*r*W['gamma_N_m']*b
    delta=force*L**3/(3*E*J)
    gap=W['gap_um']*1e-6
    wet.append(dict(radius_um=ru,length_um=lu,E_MPa=Em,force_factor=b,force_N=force,delta_um=delta*1e6,delta_over_L=delta/L,pair_closure_over_gap=2*delta/gap,slenderness=L/r,within_linear_slender_domain=L/r>=W['min_slenderness'] and delta/L<=W['max_linear_deflection_ratio'],linear_contact_span_um=(3*E*r**3*gap/(16*W['gamma_N_m']*b))**(1/3)*1e6,max_span_for_linear_deflection_um=math.sqrt(3*E*r**3*W['max_linear_deflection_ratio']/(8*W['gamma_N_m']*b))*1e6))
# Factory inventory is not the field operational layer's instantaneous replacement.
factory=[]
for c,y,rec,hr in itertools.product(F['polymer_mass_fractions'],F['good_yields'],F['solvent_recovery'],F['heat_recovery']):
    solvent=(1-c)/c
    pump=(1/c)*F['pressure_Pa']/(F['solution_density_kg_m3']*F['pump_efficiency']*3.6e6)
    energy=solvent*F['solvent_specific_heat_kWh_kg']*(1-hr)+F['polymer_process_energy_kWh_kg']+pump
    makeup=solvent*(1-rec)
    perfeed=F['resin_JPY_kg']+makeup*F['solvent_JPY_kg']+energy*F['electric_JPY_kWh']+F['base_processing_JPY_per_feed_kg']
    price=perfeed/y
    factory.append(dict(c=c,yield_good=y,recovery=rec,heat_recovery=hr,solution_kg_per_feed_kg=1/c,solvent_kg_per_feed_kg=solvent,pump_kWh_per_feed_kg=pump,energy_kWh_per_feed_kg=energy,makeup_kg_per_feed_kg=makeup,cost_JPY_per_feed_kg=perfeed,cost_JPY_per_good_kg=price,remaining_to_comparator_JPY_per_good_kg=F['finished_price_comparator_JPY_kg']-price,minimum_yield_for_comparator=perfeed/F['finished_price_comparator_JPY_kg']))
reference=next(x for x in factory if x['c']==.12 and x['yield_good']==.8 and x['recovery']==.999 and x['heat_recovery']==.7)
inventory=[]
for area in F['areas_m2']:
    good=area*F['depth_m']*F['bulk_density_kg_m3'];feed=good/reference['yield_good']
    inventory.append(dict(area_m2=area,good_kg=good,feed_kg=feed,reject_kg=feed-good,solution_kg=feed/reference['c'],solvent_circulation_kg=feed*reference['solvent_kg_per_feed_kg'],makeup_kg=feed*reference['makeup_kg_per_feed_kg'],energy_kWh=feed*reference['energy_kWh_per_feed_kg'],initial_hypothetical_material_JPY=good*reference['cost_JPY_per_good_kg'],hours_at_100_good_kg_h=good/F['good_production_kg_h'],required_good_kg_h_for_build=good/(F['initial_build_days']*F['hours_per_day']),required_solvent_kg_h_for_build=feed*reference['solvent_kg_per_feed_kg']/(F['initial_build_days']*F['hours_per_day'])))
liquid_cases=[]
for c,beta in itertools.product([.03,.05],F['antisolvent_to_solution_mass_ratios']):
    liquid_cases.append(dict(c=c,antisolvent_to_solution_ratio=beta,solution_kg_per_polymer_kg=1/c,solvent_kg_per_polymer_kg=(1-c)/c,antisolvent_kg_per_polymer_kg=beta/c,combined_liquid_kg_per_polymer_kg=(1-c+beta)/c,final_polymer_mass_fraction=c/(1+beta),note='Antisolvent ratios are assumed; no washing included. No automatic industrial scale-up from rotor rpm.'))
# Report the distinction between radius, modulus type, and model scope explicitly.
check('all thermal phase intervals positive',all(x['fine']['full_melt_s']>x['fine']['onset_s']>0 for x in thermal))
check('phase time balances latent enthalpy',all(math.isclose(2*x['h']*x['h_fine_factor']*(x['gas_C']-T['Tm_C'])*x['fine']['latent_s']/(T['rho_kg_m3']*x['fine_radius_um']*1e-6),T['latent_J_kg']) for x in thermal))
check('temperature at onset',all(math.isclose(x['gas_C']-(x['gas_C']-T['T0_C'])*math.exp(-x['fine']['onset_s']/x['fine']['tau_s']),T['Tm_C']) for x in thermal))
check('quadrature convergence',all(q['meshes'][0]['relative_error']>q['meshes'][1]['relative_error']>q['meshes'][2]['relative_error'] for q in quadrature))
check('quadrature accuracy',max(q['meshes'][-1]['relative_error'] for q in quadrature)<1e-8)
check('lumped Bi does not exceed nominal 0.1',max(x['support']['Bi'] for x in thermal)<=.1+1e-12)
check('radius scaling at equal h',math.isclose(heat(10,500,150)['onset_s']/heat(.5,500,150)['onset_s'],20))
check('same-size fine and support cannot finish melting before onset',not process(5,5,500,150,100)['conditional_window'])
check('viscosity boundary agrees with interval',all(x['conditional_window']==(x['eta_Pa_s']<x['eta_limit_Pa_s']) for x in thermal))
check('wet force and beam form identity',all(math.isclose(x['delta_over_L'],8*W['gamma_N_m']*x['force_factor']*(x['length_um']*1e-6)**2/(3*x['E_MPa']*1e6*(x['radius_um']*1e-6)**3)) for x in wet))
check('unsupported length changes displacement cubically',math.isclose(next(x['delta_um'] for x in wet if x['radius_um']==1 and x['length_um']==50 and x['E_MPa']==300 and x['force_factor']==1)/next(x['delta_um'] for x in wet if x['radius_um']==1 and x['length_um']==10 and x['E_MPa']==300 and x['force_factor']==1),125))
check('wet cutoff has explicit two flags',all(x['within_linear_slender_domain']==(x['slenderness']>=10 and x['delta_over_L']<=.1) for x in wet))
check('solution mass conservation',all(math.isclose(x['solvent_kg_per_feed_kg']+1,x['solution_kg_per_feed_kg']) for x in factory))
check('good feed reject conservation',all(math.isclose(x['feed_kg'],x['good_kg']+x['reject_kg']) for x in inventory))
check('recovery does not erase circulating solvent',all(x['makeup_kg_per_feed_kg']<x['solvent_kg_per_feed_kg'] and x['solvent_kg_per_feed_kg']>0 for x in factory))
check('yield scales all production cost',all(math.isclose(x['cost_JPY_per_good_kg']*x['yield_good'],x['cost_JPY_per_feed_kg']) for x in factory))
check('heat recovery preserves pumping energy',all(x['energy_kWh_per_feed_kg']>=x['pump_kWh_per_feed_kg']+F['polymer_process_energy_kWh_kg'] for x in factory))
check('area inventories separate',inventory[1]['good_kg']==10*inventory[0]['good_kg'])
check('antisolvent dilution mass conservation',all(math.isclose(x['final_polymer_mass_fraction']*(1+x['combined_liquid_kg_per_polymer_kg']),1) for x in liquid_cases))
check('physical success remains unmeasured',I['evidence']['physical_tests']==0 and I['evidence']['physical_success_probability'] is None)
R=dict(evidence=I['evidence'],thermal_cases=thermal,thermal_reference=[process(.5,10,500,150,v) for v in [100,1000,10000]],quadrature=quadrature,wet_cases=wet,factory_cases=factory,factory_reference=reference,inventory=inventory,liquid_precipitation=liquid_cases)
V=dict(numerical_checks=len(checks),all_passed=all(x['passed'] for x in checks),checks=checks,not_validated=['actual branched-grain production','viscosity and local convection','rounding without beads or welding','wet bridge geometry','50C creep and grain-bed response','snowlike friction and edge release','health environment winter and rain','manufacturing yield and prices'])
for name,data in [('results.json',R),('validation.json',V)]: (P/name).write_bytes((json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8'))
print(json.dumps(dict(checks=len(checks),passed=V['all_passed'],thermal_cases=len(thermal),wet_cases=len(wet),factory_cases=len(factory),quadrature_max_relative_error=max(q['meshes'][-1]['relative_error'] for q in quadrature))))
if not V['all_passed']:raise SystemExit('check failed')
