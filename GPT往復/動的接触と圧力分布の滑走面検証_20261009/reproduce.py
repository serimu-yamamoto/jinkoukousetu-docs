"""Cycle 71. Mechanism bounds; NOT a material simulation or physical trial.
Run: python reproduce.py (matplotlib is needed only for PNG plots).
"""
from pathlib import Path
import csv,json,math,sys
D=Path(__file__).resolve().parent
I=json.loads((D/'inputs.json').read_text(encoding='utf-8'))
checks=[]
def ck(name,yes):
    checks.append({'name':name,'passed':bool(yes)})
    assert yes,name
def near(a,b,rtol=1e-8,atol=1e-12):return abs(a-b)<=atol+rtol*abs(b)
def writej(name,obj):
    (D/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def writecsv(name,rows):
    with (D/(name+'.csv')).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def average(q,n=16384):
    # Periodic midpoint integration; q = maximum transverse speed / forward speed.
    sq=[math.sqrt(1+(q*math.cos(2*math.pi*(j+.5)/n))**2) for j in range(n)]
    return math.fsum(1/x for x in sq)/n,math.fsum(sq)/n
def inverse_g(g):
    lo,hi=0.,128.
    for _ in range(55):
        mid=(lo+hi)/2
        if average(mid,4096)[0]>g:lo=mid
        else:hi=mid
    return (lo+hi)/2
p=I['peak_pressure_Pa'];b=I['pressure_friction_slope_b'];mu0=I['baseline_mu_interface'];beta0=I['reference_shape_factor'];target=I['illustrative_target_mu']
tau0=(mu0-b)*beta0*p
ck('reference intercept from given friction',near(tau0,233333.3333333333))
ck('normal force by Hertz pressure integral',near(2*math.pi*p*I['contact_peak_radius_m']**2/3,beta0*p*math.pi*I['contact_peak_radius_m']**2))
duty=[]
for bb in [0.,.02,.03,.05]:
    for d in [10**(-j/5) for j in range(16)]:
        ratio=d**(1/3)
        duty.append({'b':bb,'active_fraction':d,'mu_interface':bb+(mu0-bb)*ratio,'peak_pressure_Pa':p/ratio,'adhesive_ratio':ratio,'pressure_multiplier':1/ratio,'coulomb_mu_constant':mu0})
solve=[]
for bb in [0.,.02,.03,.04,.05]:
    if target>bb:
        rr=(target-bb)/(mu0-bb); dd=rr**3
        solve.append({'b':bb,'finite_solution':True,'active_fraction':dd,'peak_multiplier':1/rr,'peak_pressure_Pa':p/rr})
    else:solve.append({'b':bb,'finite_solution':False,'active_fraction':None,'peak_multiplier':None,'peak_pressure_Pa':None})
ck('pure NSS duty 0.064',near(solve[0]['active_fraction'],.064))
ck('b 0.03 requires duty 1 over 343',near(solve[2]['active_fraction'],1/343))
ck('b 0.03 requires sevenfold peak pressure',near(solve[2]['peak_multiplier'],7))
ck('target equal slope has no finite duty',not solve[3]['finite_solution'])
ck('duty friction pressure reciprocal',all(near(x['adhesive_ratio']*x['pressure_multiplier'],1) for x in duty))
ck('constant Coulomb coefficient not reduced by redistribution',all(x['coulomb_mu_constant']==mu0 for x in duty))
# A reduced pressure ceiling compared with 5 MPa is not imposed here: no safe value is known.
profiles=[('parabolic',.5,2),('Hertz',2/3,None),('power8',.8,8),('power16',8/9,16),('ideal_uniform',1.,None)]
profile_rows=[]
W=I['normal_force_N']
for label,be,m in profiles:
    area=W/(be*p)
    profile_rows.append({'profile':label,'beta_mean_over_peak':be,'area_m2':area,'mu_interface':b+tau0/(be*p),'ratio_to_Hertz_adhesion':beta0/be,'tau0_max_for_target_Pa':(target-b)*be*p,'new_tau_over_reference':(target-b)*be*p/tau0})
    if m is not None:
        num=math.fsum(2*((j+.5)/100000)*(1-((j+.5)/100000)**m) for j in range(100000))/100000
        ck('profile integral '+label,near(num,be,rtol=1e-8))
ck('ideal uniform only removes one third of Hertz area',near(profile_rows[-1]['ratio_to_Hertz_adhesion'],2/3))
ck('shape power8 does not meet target with old interface',profile_rows[2]['mu_interface']>target)
ck('power8 target needs intercept 40000 Pa',near(profile_rows[2]['tau0_max_for_target_Pa'],40000))
ck('power8 target removes 82.857 percent intercept',near(1-profile_rows[2]['new_tau_over_reference'],29/35))
budgets=[]
for pp in [1e6,5e6,10e6]:
 for bb in [0.,.01,.03,.05]:
  for be in [2/3,.8,1.]:
   for mech in [0.,.01]:
    room=target-bb-mech
    budgets.append({'peak_pressure_Pa':pp,'b':bb,'beta':be,'mu_other':mech,'target_total_mu':target,'positive_intercept_possible':room>1e-12,'tau0_upper_Pa':max(0.,room)*be*pp,'strictly_feasible_with_positive_tau':room>1e-12})
ck('mechanical resistance consumes interface budget',not next(x for x in budgets if x['peak_pressure_Pa']==5e6 and x['b']==.03 and x['beta']==.8 and x['mu_other']==.01)['positive_intercept_possible'])
# y(t) = A sin(2 pi f t), x_tip = 0. An externally imposed motion diagnostic.
vib=[]
for q in [0.,.25,.5,1.,2.,4.,8.,16.]:
 g,h=average(q)
 vib.append({'q':q,'forward_force_ratio':g,'total_dissipation_ratio':h,'required_lateral_work_ratio':h-g})
ck('zero oscillation baseline',near(vib[0]['forward_force_ratio'],1) and near(vib[0]['required_lateral_work_ratio'],0))
ck('lateral work positive',all(x['required_lateral_work_ratio']>=0 for x in vib))
ck('oscillation dissipation at least baseline',all(x['total_dissipation_ratio']>=1 for x in vib))
ck('force reduction monotonic in q',all(vib[i]['forward_force_ratio']>vib[i+1]['forward_force_ratio'] for i in range(len(vib)-1)))
freq=[];inverse=[]
for gg in [.5,.4]:
 q=inverse_g(gg);g,h=average(q)
 ck('inverse vibration ratio '+str(gg),near(g,gg,rtol=1e-9))
 g2,h2=average(q,8192)
 ck('quadrature convergence '+str(gg),near(g2,g,rtol=1e-10) and near(h2,h,rtol=1e-10))
 inverse.append({'target_forward_ratio':gg,'q':q,'dissipation_ratio':h,'lateral_work_ratio':h-g})
 for V in [2.,5.,10.]:
  for Aum in [50.,100.,200.]:
   A=Aum*1e-6;f=q*V/(2*math.pi*A)
   freq.append({'target_forward_ratio':gg,'amplitude_um':Aum,'speed_m_s':V,'frequency_Hz':f,'lateral_peak_speed_m_s':q*V,'peak_acceleration_m_s2':q*q*V*V/A,'cycles_under_1_5m_board':f*I['ski_contact_length_m']/V,'cycles_per_100_passes':100*f*I['ski_contact_length_m']/V})
# Independent energy identity sampled at q = 2.
q=2.;g,h=average(q)
lateral=math.fsum((q*math.cos(2*math.pi*(j+.5)/16384))**2/math.sqrt(1+(q*math.cos(2*math.pi*(j+.5)/16384))**2) for j in range(16384))/16384
ck('vector friction energy balance',near(g+lateral,h,rtol=1e-10))
stroke_fraction=I['max_follow_stroke_m']/I['ski_contact_length_m']
ck('single following stroke fraction',near(stroke_fraction,1/15000))
ck('same waveform cycles independent of forward speed',near(freq[1]['cycles_under_1_5m_board'],freq[4]['cycles_under_1_5m_board']))
# Audit the printed coordinate identity; independent of any reproduction of source dynamics.
x,y,z=1.,0.,2.;vx,vy=0.,1.
true_rate=(x*vy-y*vx)/(x*x+y*y)
printed_rate=(x*vy-y*vx)/(x*x+y*y+z*z)
eps=1e-7;finite_diff=(math.atan2(y+eps*vy,x+eps*vx)-math.atan2(y-eps*vy,x-eps*vx))/(2*eps)
ck('atan2 identity matches independent finite difference',near(true_rate,finite_diff))
ck('printed r squared is not s squared in counterexample',near(printed_rate,.2) and not near(printed_rate,true_rate))
# Conservative incremental cap skin: same functionality on every grain through the full bed.
cap=[]
for dum in I['cap_diameters_um']:
 totalA=I['grain_count']*I['caps_per_grain']*math.pi*(dum*1e-6/2)**2
 mass=totalA*I['cap_thickness_m']*I['cap_density_kg_m3']
 for raw in I['assumed_material_JPY_kg']:
  for form in I['assumed_forming_JPY_m2']:
   cap.append({'cap_diameter_um':dum,'cap_surface_area_m2':totalA,'cap_skin_mass_kg':mass,'assumed_JPY_kg':raw,'assumed_JPY_m2':form,'raw_cost_JPY':mass*raw,'forming_cost_JPY':totalA*form,'partial_initial_cost_JPY':mass*raw+totalA*form,'annual_10pct_replacement_JPY':.1*(mass*raw+totalA*form),'annual_50pct_replacement_JPY':.5*(mass*raw+totalA*form)})
ck('cap mass equals area thickness density',all(near(x['cap_skin_mass_kg'],x['cap_surface_area_m2']*1e-5*950) for x in cap))
ck('double cap diameter quadruples area and mass',near(cap[4]['cap_skin_mass_kg']/cap[0]['cap_skin_mass_kg'],4))
ck('costs omit tooling and handling explicitly',I['cap_layer_is_additional_conservative'])
ck('physical evidence not fabricated',I['physical_tests']==0 and I['success_probability'] is None and not I['material_selected'])
rows={'duty_cases':duty,'pressure_profiles':profile_rows,'material_budgets':budgets,'vibration_cases':vib,'frequency_requirements':freq,'cap_costs':cap}
for stem,rr in rows.items():writecsv(stem,rr)
result={'cycle':71,'physical_tests':0,'success_probability':None,'material_selected':False,'assumptions':I['assumption_note'],'tau0_reference_Pa':tau0,'target_duty_solutions':solve,'shape_profile_results':profile_rows,'vibration_inverse':inverse,'single_stroke_fraction':stroke_fraction,'coordinate_identity':{'true_dtheta':true_rate,'printed_r_squared_dtheta':printed_rate,'finite_difference':finite_diff,'author_code_checked':False,'source_dynamics_reproduced':False},'rows':{k:len(v) for k,v in rows.items()},'total_calculated_rows':sum(len(x) for x in rows.values()),'check_count':len(checks),'all_math_checks_passed':all(x['passed'] for x in checks),'new_design':'H71-P: pressure-distribution control plus measured low-shear interface; not a validated grain'}
writej('results.json',result);writej('checks.json',{'count':len(checks),'checks':checks,'physical_tests':0})
# Figures are original plots of this script, not reproductions of published figures.
if '--no-plots' not in sys.argv:
 if (D.parents[1]/'.deps').exists():sys.path.insert(0,str(D.parents[1]/'.deps'))
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})
 fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
 for bb in [0.,.02,.03,.05]:
  rr=[x for x in duty if x['b']==bb]
  ax[0].plot([x['pressure_multiplier'] for x in rr],[x['mu_interface'] for x in rr],label=f'b = {bb:.2f}')
 ax[0].axhline(target,color='black',linestyle='--',label='Illustrative target 0.04')
 ax[0].set(xlabel='Peak-pressure multiplier at constant total load',ylabel='Interface friction coefficient',title='Fewer active contacts: pressure cost');ax[0].legend(fontsize=8)
 xx=[r['profile'] for r in profile_rows[1:]]
 ax[1].bar(xx,[r['mu_interface'] for r in profile_rows[1:]],color=['#9ca3af','#0284c7','#0891b2','#22c55e'])
 ax[1].axhline(target,color='black',linestyle='--');ax[1].set(ylabel='Interface friction coefficient',title='Redistributing pressure at the same 5 MPa peak',ylim=(0,.12));ax[1].tick_params(axis='x',rotation=15)
 fig.suptitle('Cycle 71 | Uncalibrated mechanism bounds, not snow or material test results',fontsize=12)
 fig.savefig(D/'figure1_pressure.png');plt.close(fig)
 fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
 qs=[i*.05 for i in range(161)];vals=[average(q,1024) for q in qs]
 ax[0].plot(qs,[v[0] for v in vals],label='Forward drag / baseline')
 ax[0].plot(qs,[v[1] for v in vals],label='Total dissipation / baseline')
 ax[0].plot(qs,[v[1]-v[0] for v in vals],label='Required lateral work / baseline')
 ax[0].set(xlabel='q = peak transverse speed / forward speed',ylabel='Ratio',title='Prescribed transverse motion needs work');ax[0].legend(fontsize=8)
 for gg in [.5,.4]:
  rr=[r for r in freq if r['target_forward_ratio']==gg and r['speed_m_s']==10]
  ax[1].plot([r['amplitude_um'] for r in rr],[r['frequency_Hz']/1000 for r in rr],'o-',label=f'Forward force ratio {gg}')
 ax[1].set(xlabel='Transverse amplitude (micrometres)',ylabel='Required frequency (kHz)',title='10 m/s, sinusoidal motion diagnostic');ax[1].legend(fontsize=8)
 fig.suptitle('External-motion diagnostic: does not reproduce passive bristle dynamics',fontsize=12)
 fig.savefig(D/'figure2_vibration.png');plt.close(fig)
print(json.dumps({'checks':len(checks),'rows':result['total_calculated_rows'],'physical_tests':0,'success_probability':None,'duty_b003':solve[2],'vibration':inverse},ensure_ascii=False))
