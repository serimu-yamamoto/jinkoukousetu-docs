"""H47 necessary-condition calculations. No physical test or success estimate."""
from pathlib import Path
import json, math, sys
ROOT=Path(__file__).resolve().parent
if (ROOT.parents[1]/'.deps').exists(): sys.path.insert(0,str(ROOT.parents[1]/'.deps'))
I=json.loads((ROOT/'inputs.json').read_text(encoding='utf-8'))
R=I['retention']; P=I['impact']; C=I['cost']; F=I['finite_motion']
def save(name,data):
 (ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
rim=[]
for D in R['plate_diameters_m']:
 for p in R['contact_pressures_Pa']:
  for tau in R['anchor_shear_strength_Pa']:
   area=math.pi*D*D/4
   force=R['mu']*p*area
   e=force/(tau*math.pi*D)
   rim.append(dict(D_m=D,p_Pa=p,tau_Pa=tau,friction_force_N=force,minimum_engaged_edge_depth_m=e,e_over_D=e/D))
back=[]
for p in R['contact_pressures_Pa']:
 for beta in R['back_bonded_area_fraction']:
  back.append(dict(p_Pa=p,bonded_fraction=beta,required_uniform_shear_Pa=R['mu']*p/beta))
def beam(radius,length,E,sigma,rho,arms):
 inertia=math.pi*radius**4/4
 stiffness=3*E*inertia/length**3
 limit_force=sigma*inertia/(length*radius)
 delta=limit_force/stiffness
 elastic_energy=limit_force*delta/2
 mass=arms*rho*math.pi*radius**2*length
 return dict(inertia_m4=inertia,stiffness_N_m=stiffness,force_N=limit_force,delta_m=delta,elastic_energy_J=elastic_energy,grain_mass_kg=mass)
impact=[]
for sig in P['elastic_limit_Pa']:
 b=beam(P['branch_radius_m'],P['branch_length_m'],P['E_Pa'],sig,P['density_kg_m3'],P['branch_count'])
 for alpha in P['collision_speed_fraction']:
  speed=alpha*P['mixer_tip_speed_m_s']
  for eta in P['energy_coupling_fraction']:
   coupled=.5*b['grain_mass_kg']*speed**2*eta
   capacity=b['elastic_energy_J']*P['simultaneous_supports']
   impact.append(dict(sigma_Pa=sig,collision_speed_fraction=alpha,collision_speed_m_s=speed,coupling=eta,coupled_energy_J=coupled,elastic_budget_J=capacity,budget_ratio=coupled/capacity,meaning='single ideal impact budget only, not fracture outcome'))
finite=[]
for stroke in F['available_stroke_m']:
 for speed in F['speeds_m_s']:
  travel=speed*F['loaded_time_s']
  finite.append(dict(stroke_m=stroke,speed_m_s=speed,loaded_travel_m=travel,one_stroke_time_s=stroke/speed,optimistic_zero_friction_distance_fraction=min(1,stroke/travel)))
mass=C['bed_area_m2']*C['bed_depth_m']*C['bulk_density_kg_m3']
area=2*mass/(C['skeleton_density_kg_m3']*C['skeleton_radius_m'])
r=C['discount_rate'];n=C['years'];crf=r*(1+r)**n/((1+r)**n-1)
cost=[]
for parts in C['patent_LL_parts_per_100_base']:
 deposit=mass*parts/100
 initial=deposit*C['LL_price_JPY_kg']/C['yield_fraction']
 cost.append(dict(LL_parts_per_100_base=parts,LL_fraction_of_total=parts/(100+parts),deposit_kg=deposit,purchase_kg=deposit/C['yield_fraction'],initial_JPY=initial,annualized_JPY=initial*crf,equivalent_full_skeleton_thickness_m=deposit/(C['LL_density_kg_m3']*area),ratio_to_previous_target=deposit/C['target_LL_deposit_kg']))
binder=[]
for h in C['holding_layer_eq_thickness_m']:
 for price in C['holding_layer_price_JPY_kg']:
  deposit=area*C['patch_area_fraction']*C['bonded_back_fraction']*h*C['holding_layer_density_kg_m3']
  initial=deposit/C['yield_fraction']*price
  binder.append(dict(h_m=h,price_JPY_kg=price,deposit_kg=deposit,purchase_kg=deposit/C['yield_fraction'],initial_JPY=initial,annualized_JPY=initial*crf))
bref=beam(30e-6,150e-6,1e9,10e6,1200,6)
G=P['E_Pa']/(2*(1+P['poisson_ratio']))
delta_shear=bref['force_N']*P['branch_length_m']/(P['shear_correction_factor']*G*math.pi*P['branch_radius_m']**2)
shear_factor=1+delta_shear/bref['delta_m']
source_speed=I['source_kinematics']['D_reported_m']*I['source_kinematics']['omega_rad_s']
checks=[]
def check(name,passed):
 checks.append(dict(name=name,passed=bool(passed)))
 if not passed: raise AssertionError(name)
def near(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-14)
check('bed mass 108t',near(mass,108000))
check('branch lateral area 6million m2',near(area,6000000))
rr=next(x for x in rim if x['D_m']==20e-6 and x['p_Pa']==2e6 and x['tau_Pa']==1e6)
check('rim depth 1um representative',near(rr['minimum_engaged_edge_depth_m'],1e-6))
check('rim shear capacity equals applied tangential force',near(math.pi*rr['D_m']*rr['minimum_engaged_edge_depth_m']*rr['tau_Pa'],rr['friction_force_N']))
check('rim dimensionless depth independent diameter',near(rim[0]['e_over_D'],rim[9]['e_over_D']))
check('backside half area needs 0.4MPa at 2MPa',near(next(x['required_uniform_shear_Pa'] for x in back if x['p_Pa']==2e6 and x['bonded_fraction']==.5),.4e6))
check('backside full area halves required stress',near(back[1]['required_uniform_shear_Pa']/back[2]['required_uniform_shear_Pa'],2))
check('beam delta stress relation',near(bref['delta_m'],10e6*(150e-6)**2/(3*1e9*30e-6)))
check('beam energy independent formula',near(bref['elastic_energy_J'],(10e6)**2*math.pi*(30e-6)**2*150e-6/(24*1e9)))
check('reference delta 2.5um',near(bref['delta_m'],2.5e-6))
check('grain mass six branches',near(bref['grain_mass_kg'],6*1200*math.pi*(30e-6)**2*150e-6))
ref=next(x for x in impact if x['sigma_Pa']==10e6 and x['collision_speed_fraction']==.1 and x['coupling']==.1)
check('impact ratio 1.3824',near(ref['budget_ratio'],1.3824))
check('impact ratio alternate analytical cancellation',near(ref['budget_ratio'],12*6*1200*1e9*4**2*.1/(10e6)**2))
b2=beam(60e-6,150e-6,1e9,10e6,1200,6)
check('thickening changes mass and energy together',near(b2['grain_mass_kg']/bref['grain_mass_kg'],b2['elastic_energy_J']/bref['elastic_energy_J']))
check('doubling limit stress quadruples elastic budget',near(beam(30e-6,150e-6,1e9,20e6,1200,6)['elastic_energy_J']/bref['elastic_energy_J'],4))
check('100um stroke at5m/s lasts20us',near(100e-6/5,20e-6))
check('100um stroke accounts for .02percent of .5m travel',near(100e-6/(5*.1),.0002))
check('5 parts per100 gives 5400kg',near(cost[1]['deposit_kg'],5400))
check('5 parts is4.7619 percent total not5percent',near(cost[1]['LL_fraction_of_total'],1/21))
check('5parts price is67.5million JPY',near(cost[1]['initial_JPY'],67500000))
check('5parts uses7.5times720kg',near(cost[1]['ratio_to_previous_target'],7.5))
br=next(x for x in binder if x['h_m']==.2e-6 and x['price_JPY_kg']==1000)
check('holding phase144kg and180000JPY',near(br['deposit_kg'],144) and near(br['initial_JPY'],180000))
check('source speed equation gives63mm/s',near(source_speed,.063))
check('shear correction increases displacement by8.6667percent',near(shear_factor,1+13/150))
check('shear energy correction lowers impact budget ratio',ref['budget_ratio']/shear_factor<ref['budget_ratio'])
check('physical probability not estimated',I['physical_tests']==0 and I['physical_success_probability'] is None)
results=dict(cycle=47,physical_tests=0,physical_success_probability=None,rim_conditions=rim,back_conditions=back,impact_conditions=impact,beam_reference=bref,impact_reference=ref,shear_sensitivity=dict(extra_deflection_m=delta_shear,capacity_factor=shear_factor,corrected_reference_ratio=ref['budget_ratio']/shear_factor,note='Timoshenko shear compliance added at same bending-stress limit; still not impact/fracture simulation'),finite_motion=finite,coating_cost=cost,holding_phase_cost=binder,capital_recovery_factor=crf,source_speed_diagnostic=dict(literal_equation_m_s=source_speed,half_stroke_m_s=source_speed/2,stated_max_m_s=.03,interpretation='documented ambiguity, not a measured correction'),counts=dict(rim=len(rim),back=len(back),impact=len(impact),finite=len(finite),coating_cost=len(cost),holding_cost=len(binder)),numerical_checks=len(checks))
save('results.json',results);save('numerical-validation.json',dict(status='passed',checks=checks,scope='Equations and implementation only. No material validation.'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyArrowPatch
plt.rcParams.update({'font.size':10,'svg.fonttype':'none'})
fig,axs=plt.subplots(1,2,figsize=(12,4.5))
for tau in R['anchor_shear_strength_Pa']:
 ds=[.2+i*.2 for i in range(100)]
 axs[0].plot(ds,[.1*2e6*d/(4*tau) for d in ds],label=f'Rim strength {tau/1e6:g} MPa')
axs[0].set(xlabel='Plate diameter (um)',ylabel='Required rim engagement depth (um)',title='A. Rim-only retention; assumed mu=0.1, p=2 MPa');axs[0].legend();axs[0].grid(alpha=.25)
vs=[.1+i*.1 for i in range(100)]
for eta in P['energy_coupling_fraction']:
 ratios=[.5*bref['grain_mass_kg']*v*v*eta/bref['elastic_energy_J'] for v in vs]
 axs[1].plot(vs,ratios,label=f'Energy coupling {eta:g}')
axs[1].axhline(1,color='black',ls='--',label='Single-branch elastic budget')
axs[1].set(xlabel='Assumed actual collision speed (m/s)',ylabel='Coupled energy / elastic budget',title='B. Mixing can consume branch elastic margin',yscale='log');axs[1].legend();axs[1].grid(alpha=.25)
fig.suptitle('H47 necessary conditions — no measured adhesion or fracture prediction')
fig.tight_layout();fig.savefig(ROOT/'constraints.svg');fig.savefig(ROOT/'constraints.png',dpi=150);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(12,4.5))
for ax in axs:ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
for ax,mode in zip(axs,['rim','back']):
 ax.add_patch(Rectangle((.12,.72),.76,.07,facecolor='#c9dbe8'));ax.text(.5,.85,'Ski base / tangential sliding',ha='center')
 ax.add_patch(Rectangle((.24,.6),.52,.09,facecolor='#e5b655',edgecolor='#876521'))
 ax.add_patch(Rectangle((.12,.34),.76,.13,facecolor='#a7ccb8',edgecolor='#37644b'))
 ax.add_patch(FancyArrowPatch((.3,.75),(.7,.75),arrowstyle='->',mutation_scale=15))
 if mode=='rim':
  for x in [.2,.74]:ax.add_patch(Rectangle((x,.46),.06,.19,facecolor='#c796aa'))
  ax.text(.5,.22,'Rim-only: load carried at thin edges',ha='center');ax.text(.5,.12,'Plate bending and peel are not included',ha='center',fontsize=9)
 else:
  ax.add_patch(Rectangle((.26,.47),.48,.13,facecolor='#c796aa'))
  ax.text(.5,.22,'Back support: keep the sliding face exposed',ha='center');ax.text(.5,.12,'Bond chemistry and 50 C durability unverified',ha='center',fontsize=9)
fig.suptitle('H47 concept: underside anchoring + low-impact coating before node separation',fontsize=12)
fig.text(.5,.02,'Not to scale. Purple = unspecified holding phase; green = open-branch precursor.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.05,1,.95));fig.savefig(ROOT/'concept.svg');fig.savefig(ROOT/'concept.png',dpi=150);plt.close(fig)
for name in ['concept.svg','constraints.svg']:
 p=ROOT/name;p.write_text('\n'.join(s.rstrip() for s in p.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'counts':results['counts'],'checks':len(checks),'reference_beam':bref,'reference_impact':ref,'cost5parts':cost[1],'binder_example':br},ensure_ascii=False))
