#!/usr/bin/env python3
"""Cycle 80: accounting and screening only. No physical performance validation."""
from pathlib import Path
import math,json,csv,sys,argparse
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
if (REPO/'.deps').exists():sys.path.insert(0,str(REPO/'.deps'))
p=argparse.ArgumentParser();p.add_argument('--no-plots',action='store_true');args=p.parse_args()
checks=[]
def check(name,ok):
    if not ok:
        print("CHECK FAILED: "+name);sys.exit(1)
    checks.append({'check':name,'passed':True})
def close(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12)
def writej(n,x):(HERE/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def writecsv(n,rows):
    with (HERE/n).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
# Inputs are scenarios, not measured properties or operating forecasts.
I={'course_area_m2':2000.,'course_length_m':100.,'course_width_m':20.,'functional_depth_m':.45,'skier_normal_load_N':800.,'two_ski_total_width_m':.2,'ski_length_m':1.6,'p_pad_Pa':.870247272462546e6,'grains':3117691453623.979,'pads_per_grain':6,'pad_pitch_m':190e-6,'rho_UH_kg_m3':950.,'rho_TPU_kg_m3':1200.,'raw_price_JPY_kg':500.,'material_yield':.8,'interface_mu_budget':.08,'other_mu_assumed':.02,'real_contact_fraction79':.7421875,'tau_matrix_Pa':300000.,'tau_UH_Pa':30000.,'film_utilizable_fraction':.5,'p_peak79_Pa':2362593.4572750307}
A=I['grains']*I['pads_per_grain']*I['pad_pitch_m']**2
p_nom=I['skier_normal_load_N']/(I['two_ski_total_width_m']*I['ski_length_m'])
footprint_active=p_nom/I['p_pad_Pa']
tau_allow=I['interface_mu_budget']*I['p_pad_Pa']/I['real_contact_fraction79']
phi_need=(I['tau_matrix_Pa']-tau_allow)/(I['tau_matrix_Pa']-I['tau_UH_Pa'])
w_need=(phi_need*I['rho_UH_kg_m3'])/(phi_need*I['rho_UH_kg_m3']+(1-phi_need)*I['rho_TPU_kg_m3'])
check('area_identity',close(I['course_length_m']*I['course_width_m'],I['course_area_m2']))
check('SI_wear_conversion',close(1e-5*1e-9,1e-14))
check('nominal_pressure',close(p_nom,2500.))
check('load_recovery',close(footprint_active*I['p_pad_Pa'],p_nom))
check('phase_threshold_bounds',0<phi_need<1 and 0<w_need<1)
# A fixed contact patch model: no rotation, no redistribution, uniform wear inside active area.
# kw in mm^3/(N m), hence SI = kw * 1e-9 m^2/N.
wear=[]
for N in [1000,10000,100000]:
 for lane in [20.,5.,2.]:
  for kw in [1e-7,1e-6,1e-5,1e-4]:
   local_passes=N*I['two_ski_total_width_m']/lane
   distance=local_passes*I['ski_length_m']
   delta=kw*1e-9*I['p_pad_Pa']*distance
   global_V=kw*1e-9*I['skier_normal_load_N']*I['course_length_m']*N
   active_area=lane*I['course_length_m']*footprint_active
   check(f'global_local_volume_{N}_{lane}_{kw}',close(active_area*delta,global_V))
   wear.append({'total_course_runs':N,'traffic_band_m':lane,'kw_mm3_Nm_ASSUMED':kw,'mean_local_passes':local_passes,'sliding_distance_per_fixed_patch_m':distance,'wear_depth_um':delta*1e6,'nominal_thickness_um_from_patch_mean_at_half_utilization':delta*1e6/I['film_utilizable_fraction'],'total_material_loss_g':global_V*I['rho_UH_kg_m3']*1000,'fixed_active_course_area_m2':active_area,'model_status':'sensitivity_not_life_prediction'})
writecsv('wear_budget.csv',wear)
localization=[]
for r in wear:
 if r['kw_mm3_Nm_ASSUMED']==1e-5 and r['total_course_runs']==10000:
  peak=r['wear_depth_um']*I['p_peak79_Pa']/I['p_pad_Pa']
  localization.append({'traffic_band_m':r['traffic_band_m'],'mean_over_pad_um':r['wear_depth_um'],'mean_over_real_contact_um':r['wear_depth_um']/I['real_contact_fraction79'],'frozen_profile_peak_wear_um':peak,'nominal_thickness_um_from_peak_at_half_utilization':peak/.5,'local_passes_to_0p05um_peak_wear':.05/(1e-5*1e-9*I['p_peak79_Pa']*I['ski_length_m']*1e6),'status':'frozen_profile_diagnostic; shape changes require coupled wear-contact model'})
writecsv('within_pad_wear.csv',localization)
check('peak_above_contact_mean',all(r['frozen_profile_peak_wear_um']>r['mean_over_real_contact_um']>r['mean_over_pad_um'] for r in localization))
check('traffic_concentration_x10',close(wear[8]['wear_depth_um']/wear[0]['wear_depth_um'],10.))
# Layer life inverse; this is acceptance criterion for kw measured on the candidate.
requirements=[]
for N in [10000,100000]:
 for lane in [20.,2.]:
  for t in [1.,5.,25.,50.]:
   s=N*I['two_ski_total_width_m']/lane*I['ski_length_m']
   kmax=t*1e-6*I['film_utilizable_fraction']/(I['p_pad_Pa']*s)/1e-9
   requirements.append({'course_runs':N,'traffic_band_m':lane,'nominal_cap_um':t,'usable_fraction':I['film_utilizable_fraction'],'kw_max_mm3_Nm':kmax,'status':'required_value_not_measured'})
writecsv('wear_requirements.csv',requirements)
# Same nominal pressure pbar and contact fraction as cycle 79; no new coupled contact solution.
blend=[]
for w in [0.,.05,.10,.20,.40,.60,.80,1.]:
 phi=(w/I['rho_UH_kg_m3'])/(w/I['rho_UH_kg_m3']+(1-w)/I['rho_TPU_kg_m3'])
 tau=(1-phi)*I['tau_matrix_Pa']+phi*I['tau_UH_Pa']
 mu=tau*I['real_contact_fraction79']/I['p_pad_Pa']
 blend.append({'UH_weight_fraction':w,'UH_volume_fraction':phi,'exposed_area_fraction_assumed_equal_to_volume':phi,'tau_uniform_mix_Pa':tau,'mu_interface_screen':mu,'mu_with_other_assumed':mu+I['other_mu_assumed'],'meets_assumed_interface_budget':mu<=I['interface_mu_budget'],'status':'uniform_shear_hypothesis_not_composite_prediction'})
check('end_members',close(blend[0]['UH_volume_fraction'],0) and close(blend[-1]['UH_volume_fraction'],1))
check('weight_to_volume_inverse',close((w_need/I['rho_UH_kg_m3'])/(w_need/I['rho_UH_kg_m3']+(1-w_need)/I['rho_TPU_kg_m3']),phi_need))
check('shear_threshold',close(((1-phi_need)*I['tau_matrix_Pa']+phi_need*I['tau_UH_Pa'])*I['real_contact_fraction79']/I['p_pad_Pa'],.08))
writecsv('phase_exposure.csv',blend)
# Load-bearing area reduction amplifies local wear; total wear unchanged for constant kw.
contact=[]
for f in [1.,.75,.5,.25,.1]:
 contact.append({'load_bearing_area_fraction_relative':f,'local_pressure_multiplier':1/f,'local_wear_depth_multiplier':1/f,'total_wear_volume_multiplier':f/f,'assumptions':'same_total_load_distance_kw; no change of friction law or contact mechanics'})
writecsv('contact_localization.csv',contact)
# Full-depth inventory: every grain and six faces. Not only the visible course surface.
inventory=[]
for area_factor in [1.,10.]:
 for t in [1.,5.,25.,50.]:
  mass=A*area_factor*t*1e-6*I['rho_UH_kg_m3']
  cost=mass/I['material_yield']*I['raw_price_JPY_kg']
  inventory.append({'course_area_m2':I['course_area_m2']*area_factor,'functional_depth_m':.45,'all_pad_area_m2':A*area_factor,'cap_thickness_um':t,'finished_cap_mass_kg':mass,'raw_cap_material_JPY_ex_tax':cost,'assumed_price_JPY_kg':I['raw_price_JPY_kg'],'assumed_yield':I['material_yield'],'excludes':'support skeleton; bonding; shaping; rejects beyond stated yield; factory; shipping; civil; maintenance; tax'})
writecsv('full_depth_cap_inventory.csv',inventory)
check('inventory_x10',close(inventory[4]['finished_cap_mass_kg']/inventory[0]['finished_cap_mass_kg'],10))
check('thickness_x25',close(inventory[2]['raw_cap_material_JPY_ex_tax']/inventory[0]['raw_cap_material_JPY_ex_tax'],25))
# Plate correction only for continuous films; thick and segmented caps explicitly out of scope.
skin=[]
E=30e6;nu=.49;d=10e-6;G=E/(2*(1+nu));q=2*math.pi/47.5e-6
x=q*d;K=(1-nu)/(G*q)*((3-4*nu)*math.sinh(2*x)-2*x)/((3-4*nu)*math.cosh(2*x)+2*x*x+5-12*nu+8*nu*nu)
for t_um in [1.,2.,5.,25.,50.]:
 t=t_um*1e-6;thin=t/(47.5e-6)<=.05;B=1e9*t**3/(12*(1-.35**2))
 skin.append({'thickness_um':t_um,'thickness_wavelength_ratio':t/(47.5e-6),'thin_plate_screen_in_scope':thin,'compliance_retention_if_in_scope':1/(1+B*q**4*K) if thin else None,'status':'continuous_film_only; no segmented-cap extrapolation'})
writecsv('film_model_scope.csv',skin)
check('thick_caps_excluded',skin[-1]['compliance_retention_if_in_scope'] is None)
check('1um_film_compliance_reproduced',abs(skin[0]['compliance_retention_if_in_scope']-.995674050522591)<1e-12)
# Accounting of course travel versus patch exposure and pin-on-disk path.
residence=[]
for speed in [.1,.45,1.,5.,10.]:
 residence.append({'speed_m_s':speed,'fixed_ground_patch_contact_time_s':I['ski_length_m']/speed,'moving_ski_point_time_over_190um_patch_s':190e-6/speed,'ratio_fixed_to_moving':I['ski_length_m']/190e-6,'interpretation':'kinematic time only; not a flash-temperature solution'})
writecsv('body_role_contact_time.csv',residence)
check('contact_time_ratio',close(residence[-1]['ratio_fixed_to_moving'],residence[0]['ratio_fixed_to_moving']))
check('course_not_pin_path',not close(100.,1.6))
check('pressure_source_arithmetic_discrepancy',abs(15/7.07-1.4)>.7)
summary={'cycle':80,'physical_tests_performed':0,'success_probability':None,'external_material_properties_validated_for_ski':False,'input_status':'assumptions except inherited accounting quantities','all_pad_area_m2':A,'nominal_ski_pressure_Pa':p_nom,'fixed_active_area_fraction':footprint_active,'tau_allow_Pa':tau_allow,'required_UH_exposed_area_fraction_under_uniform_shear_hypothesis':phi_need,'equivalent_UH_mass_fraction':w_need,'representative_wear':[r for r in wear if r['total_course_runs']==10000 and r['kw_mm3_Nm_ASSUMED']==1e-5],'math_accounting_checks':len(checks),'comparison_rows':len(localization)+len(wear)+len(requirements)+len(blend)+len(contact)+len(inventory)+len(skin)+len(residence),'no_lifetime_or_success_claim':True}
writej('inputs.json',I);writej('summary.json',summary);writej('verification.json',{'physical_experiments':0,'checks':checks})
if not args.no_plots:
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.patches import Rectangle
 fig,axs=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
 for lane in [20,2]:
  rr=[r for r in wear if r['total_course_runs']==10000 and r['traffic_band_m']==lane]
  axs[0].loglog([r['kw_mm3_Nm_ASSUMED'] for r in rr],[r['wear_depth_um'] for r in rr],marker='o',label=f'Traffic band {lane} m')
 axs[0].axhline(.5,color='gray',ls='--',label='Half of 1 um film')
 axs[0].set(xlabel='Assumed specific wear rate [mm3/(N m)]',ylabel='Local wear depth [um]',title='10,000 runs: fixed patches, no mixing')
 axs[0].legend(fontsize=8);axs[0].grid(True,which='both',alpha=.2)
 axs[1].plot([r['UH_volume_fraction']*100 for r in blend],[r['mu_with_other_assumed'] for r in blend],'o-',label='Uniform shear mixture hypothesis')
 axs[1].axhline(.10,color='gray',ls='--',label='Provisional total friction budget')
 axs[1].axvline(phi_need*100,color='orange',ls=':',label=f'Required area fraction {phi_need:.1%}')
 axs[1].set(xlabel='Low-shear phase exposed area [%]',ylabel='Friction coefficient (assumed model)',title='Small filler fractions do not ensure full coverage')
 axs[1].legend(fontsize=8);axs[1].grid(alpha=.2)
 fig.suptitle('Screening only: no candidate wear rate or shear stress measured',fontsize=12)
 fig.savefig(HERE/'wear_and_phase.png',dpi=150);plt.close(fig)
 fig,axs=plt.subplots(1,3,figsize=(12,4),layout='constrained')
 for ax in axs:ax.set(xlim=(0,10),ylim=(0,6));ax.set_aspect('equal');ax.axis('off')
 axs[0].add_patch(Rectangle((1,1),8,2.5,color='#b9d8dc'));axs[0].add_patch(Rectangle((1,3.5),8,.12,color='#315e8b'))
 axs[0].text(5,5,'H79: thin continuous film',ha='center');axs[0].text(5,.2,'Wear-through exposes support',ha='center',fontsize=9)
 axs[1].add_patch(Rectangle((1,1),8,2.5,color='#b9d8dc'))
 for j in range(8):
  for z in [1.2,2.2,3.2]:axs[1].add_patch(Rectangle((1.2+j,z),.35,.3,color='#315e8b'))
 axs[1].text(5,5,'H80-B: dispersed bulk phase',ha='center');axs[1].text(5,.2,'Exposure / pullout must be measured',ha='center',fontsize=9)
 axs[2].add_patch(Rectangle((1,1),8,1.5,color='#b9d8dc'))
 for x in [1.1,3.2,5.3,7.4]:axs[2].add_patch(Rectangle((x,2.5),1.5,1.1,color='#315e8b'))
 axs[2].text(5,5,'H80-R: thick divided contact regions',ha='center',fontsize=10);axs[2].text(5,.2,'Gap / peak pressure / retention unresolved',ha='center',fontsize=8)
 fig.suptitle('Local cross-section of an open grain; conceptual, not to scale',fontsize=12)
 fig.savefig(HERE/'contact_concepts.png',dpi=150);plt.close(fig)
print(json.dumps(summary,ensure_ascii=False))
