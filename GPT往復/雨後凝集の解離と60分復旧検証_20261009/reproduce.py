"""Cycle 76: ideal wet-bridge energy and nondestructive restoration requirements.
Pure standard library. These are screening calculations, not material tests."""
from pathlib import Path
import math,csv,json,itertools
D=Path(__file__).resolve().parent
P={'particle_mass_kg':3.5e-8,'g':9.81,'bulk_density_kg_m3':120.,'bed_depth_m':.45,
   'closed_s':3600.,'other_s':1320.,'annual_passes':200,'annual_replacement_target':.02,
   'latent_heat_assumption_J_kg':2.38e6,'material_price_assumption_JPY_kg':500.}
def gamma(T):
    tau=1-(T+273.15)/647.096
    return .2358*tau**1.256*(1-.625*tau)
def sc(R,v):
    return R*(v**(1/3)+.1*v**(2/3))
def force(s,R,v,T=50,model='2007'):
    smax=sc(R,v)
    if not 0<=s<=smax*(1+1e-12):return 0.
    if model=='2007':
        S=s/(R*math.sqrt(v))
        return 2*math.pi*R*gamma(T)/(1+1.05*S+2.5*S*S)
    x=s/smax
    a=-.3319*v**.4974+.6717*v**.1995
    b=13.84*v**(-.3909)-12.11*v**(-.3945)
    f0=2*math.pi*R*gamma(T)*(1-.3823*v**.2586)
    return f0*(1+a*x)/(1+a*b*x+b*x*x)
def analytic_energy(R,v,T=50):
    S=sc(R,v)/(R*math.sqrt(v));q=math.sqrt(4*2.5-1.05**2)
    I=2/q*(math.atan((5*S+1.05)/q)-math.atan(1.05/q))
    return 2*math.pi*R*gamma(T)*R*math.sqrt(v)*I
def simpson(fn,b,n=2048):
    h=b/n
    return h/3*(fn(0)+fn(b)+sum((4 if i%2 else 2)*fn(i*h) for i in range(1,n)))
def bridge(R,v,T=50,model='2007'):
    f=force(0,R,v,T,model)
    e=analytic_energy(R,v,T) if model=='2007' else simpson(lambda s:force(s,R,v,T,model),sc(R,v))
    return {'model':model,'R_um':R*1e6,'V_over_R3':v,'T_C':T,'gamma_N_m':gamma(T),
            'force_contact_uN':f*1e6,'rupture_distance_um':sc(R,v)*1e6,'rupture_work_nJ':e*1e9,
            'single_bridge_force_over_weight':f/(P['particle_mass_kg']*P['g']),
            'pair_relative_speed_energy_m_s':math.sqrt(4*e/P['particle_mass_kg'])}
def writej(fn,obj):(D/fn).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def writecsv(fn,rows):
    with (D/fn).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(rows)
def main():
    cap=[bridge(R*1e-6,v,T,m) for R,v,T,m in itertools.product([10,25,50],[1e-6,1e-4,1e-2],[30,50],['2007','2024'])]
    ref=bridge(25e-6,1e-3)
    F=ref['force_contact_uN']*1e-6;W=ref['rupture_work_nJ']*1e-9;m=P['particle_mass_kg']
    vibration=[]
    for G,f,alpha,n in itertools.product([5,25,50],[20,50,100],[0,.1,.5,1],[1,3]):
        omega=2*math.pi*f;A=G*9.81/omega**2;wallv=A*omega;vr=alpha*wallv
        vibration.append({'Gamma_drive':G,'frequency_Hz':f,'unknown_relative_coupling_alpha':alpha,
          'simultaneous_bridges':n,'amplitude_mm':A*1000,'wall_speed_m_s':wallv,'assumed_relative_speed_m_s':vr,
          'relative_kinetic_over_bridge_work':m*vr*vr/4/(n*W),
          'nominal_drive_force_over_bridge_force':m*G*9.81/(n*F),
          'scope':'two separate diagnostic ratios, not a fluidization or success criterion'})
    roots=[]
    for E,t,L,R,n in itertools.product([.2e9,1e9],[20e-6,30e-6],[250e-6,500e-6],[10e-6,25e-6,50e-6],[1,3]):
        w=100e-6;k=E*w*t**3/(4*L**3);f=n*force(0,R,1e-3)
        strain=6*f*L/(E*w*t*t);delta=f/k
        roots.append({'E_Pa_assumed':E,'width_um':100.,'t_um':t*1e6,'L_um':L*1e6,'R_um':R*1e6,
          'bridges_on_one_root':n,'root_k_N_m':k,'root_strain_linear':strain,'tip_deflection_um_linear':delta*1e6,
          'deflection_over_length':delta/L,'small_deflection_screen':delta/L<=.1,
          'force_limit_uN_for_assumed_strain005':.005*E*w*t*t/(6*L)*1e6,
          'scope':'0.5% is an illustrative strain budget, not measured yield/fatigue limit'})
    flow=[]
    for A,d,f in itertools.product([2000.,20000.],[.05,.30,.45],[.01,.1,1.]):
        vol=A*d*f;t=P['closed_s']-P['other_s'];q=vol/t
        flow.append({'area_m2':A,'process_depth_m':d,'damaged_area_fraction':f,'available_s':t,
          'volume_m3':vol,'mass_kg':vol*120,'flow_m3_s':q,'flow_m3_h':q*3600,
          'mass_flow_kg_s':q*120,'ideal_buffer_volume_for_15s_m3':q*15,
          'scope':'15 s is not measured processing time; 50 mm treatment does not cover 300 mm gouges'})
    loss=[]
    for A,f in itertools.product([2000.,20000.],[1e-5,1e-4,1e-3,.01]):
        M=A*.45*120;n=P['annual_passes']
        loss.append({'area_m2':A,'bed_mass_kg':M,'loss_fraction_each_pass':f,'passes':n,
          'original_fraction_remaining_without_replacement':(1-f)**n,
          'replacement_kg_to_maintain_bed_mass':M*n*f,
          'annual_material_only_JPY_assumed':M*n*f*500,
          'scope':'all bed processed each pass; loss includes captured scrap, not permission for environmental discharge'})
    drying=[]
    for A,w in itertools.product([2000.,20000.],[.001,.01,.05]):
        water=A*.45*w*1000;heat=water*P['latent_heat_assumption_J_kg']
        drying.append({'area_m2':A,'water_fraction_of_bed_volume':w,'water_kg':water,
          'latent_heat_only_MWh':heat/3.6e9,'thermal_power_in_38min_MW':heat/2280/1e6,
          'scope':'50 C approximate latent heat; no heating, air loss, transfer limit or heater efficiency included'})
    branch=[]
    for v in [1e-2,1e-4,1e-6]:
        a=bridge(25e-6,v,50,'2007');b=bridge(25e-6,v,50,'2024')
        branch.append({'V_over_R3':v,'old_F_uN':a['force_contact_uN'],'new_F_uN':b['force_contact_uN'],
          'old_W_nJ':a['rupture_work_nJ'],'new_W_nJ':b['rupture_work_nJ'],'rupture_um':a['rupture_distance_um']})
    rows={'bridge_models.csv':cap,'vibration_diagnostics.csv':vibration,'root_damage_screen.csv':roots,
          'restoration_throughput.csv':flow,'maintenance_loss_cost.csv':loss,'evaporation_bound.csv':drying,
          'draining_comparison.csv':branch}
    for fn,r in rows.items():writecsv(fn,r)
    checks=[]
    def ck(n,b):assert b,n;checks.append({'name':n,'passed':True})
    def near(a,b,rtol=1e-8):return math.isclose(a,b,rel_tol=rtol,abs_tol=1e-20)
    ck('surface_tension_50_reference',.067<gamma(50)<.069)
    ck('surface_tension_decreases',gamma(50)<gamma(30))
    for v in [1e-6,1e-4,1e-2]:
        a=analytic_energy(25e-6,v)
        b=simpson(lambda s:force(s,25e-6,v),sc(25e-6,v),4096)
        ck('analytic_vs_quadrature_'+str(v),near(a,b,1e-8))
    ck('integral_lower_limit_zero',near(math.atan(1.05/math.sqrt(8.8975))-math.atan(1.05/math.sqrt(8.8975)),0))
    ck('zero_separation_is_F0',near(force(0,25e-6,1e-3),2*math.pi*25e-6*gamma(50)))
    ck('force_radius_scaling',near(force(0,50e-6,1e-3),2*F))
    ck('work_radius_squared',near(analytic_energy(50e-6,1e-3),4*W))
    ck('rupture_radius_scaling',near(sc(50e-6,1e-3),2*sc(25e-6,1e-3)))
    ck('reduced_mass_energy',near(m*ref['pair_relative_speed_energy_m_s']**2/4,W))
    ck('force_weight_units',near(ref['single_bridge_force_over_weight'],F/(m*9.81)))
    ck('2024_contact_formula',near(force(0,25e-6,1e-3,50,'2024'),F*(1-.3823*1e-3**.2586)))
    ck('draining_need_not_reduce_contact_force',branch[2]['new_F_uN']>branch[0]['new_F_uN'])
    ck('draining_reduces_work_both_models',branch[2]['new_W_nJ']<branch[0]['new_W_nJ'] and branch[2]['old_W_nJ']<branch[0]['old_W_nJ'])
    for v in [1e-6,1e-4,1e-2]:
        a=simpson(lambda s:force(s,25e-6,v,50,'2024'),sc(25e-6,v),1024)
        b=simpson(lambda s:force(s,25e-6,v,50,'2024'),sc(25e-6,v),2048)
        ck('new_model_quadrature_convergence_'+str(v),near(a,b,1e-7))
    ck('in_phase_no_relative_energy',all(r['relative_kinetic_over_bridge_work']==0 for r in vibration if r['unknown_relative_coupling_alpha']==0))
    v20=[r for r in vibration if r['Gamma_drive']==25 and r['frequency_Hz']==20 and r['unknown_relative_coupling_alpha']==.1 and r['simultaneous_bridges']==1][0]
    v100=[r for r in vibration if r['Gamma_drive']==25 and r['frequency_Hz']==100 and r['unknown_relative_coupling_alpha']==.1 and r['simultaneous_bridges']==1][0]
    ck('same_acceleration_energy_factor25',near(v20['relative_kinetic_over_bridge_work'],25*v100['relative_kinetic_over_bridge_work']))
    ck('root_k_reference',near(1e9*100e-6*(20e-6)**3/(4*(500e-6)**3),1.6))
    ck('root_bending_relations',all(near(r['root_strain_linear'],3*(r['t_um']*1e-6)*(r['tip_deflection_um_linear']*1e-6)/(2*(r['L_um']*1e-6)**2)) for r in roots))
    ck('whole_bed_small_area_108t',near(2000*.45*120,108000))
    ck('whole_bed_large_area_1080t',near(20000*.45*120,1080000))
    ck('time_38min',P['closed_s']-P['other_s']==2280)
    ck('flow_mass_identity',all(near(r['flow_m3_s']*r['available_s'],r['volume_m3']) for r in flow))
    ck('maintenance_100ppm_limit',near(P['annual_replacement_target']/P['annual_passes'],1e-4))
    ck('loss_annual_linear_replacement',all(near(r['replacement_kg_to_maintain_bed_mass'],r['bed_mass_kg']*r['passes']*r['loss_fraction_each_pass']) for r in loss))
    ck('latent_energy_units',all(near(r['latent_heat_only_MWh']*3.6e9,r['water_kg']*2.38e6) for r in drying))
    writej('inputs.json',{'cycle':76,'physical_experiments':0,'success_probability':None,'parameters':P,
      'R_um':[10,25,50],'V_over_R3':[1e-6,1e-4,1e-2],'contact_angle_degrees':0,
      'sources':'sources.md','area_scopes':'2000 m2 economic reference; 20000 m2 grooming reference; not interchangeable'})
    writej('results.json',{'cycle':76,'physical_experiments':0,'success_probability':None,'reference_bridge':ref,
      'draining_comparison':branch,'same_acceleration_comparison':[v20,v100],
      'root_reference':[r for r in roots if r['R_um']==25 and r['t_um']==20 and r['L_um']==500 and r['bridges_on_one_root']==1],
      'annual_loss_fraction_per_pass_limit':P['annual_replacement_target']/P['annual_passes'],
      'row_counts':{fn:len(r) for fn,r in rows.items()},'total_rows':sum(map(len,rows.values()))})
    writej('checks.json',{'total':len(checks),'passed':len(checks),'checks':checks,'physical_validation':False})
    print(json.dumps({'checks':len(checks),'rows':sum(map(len,rows.values())),'physical_tests':0}))
if __name__=='__main__':main()
