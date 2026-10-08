"""Cycle 44: humidity and ideal pressure-fed hydration contact sizing."""
from pathlib import Path
import json,csv,math,sys
D=Path(__file__).resolve().parent
if (D.parents[1]/'.deps').exists():sys.path.insert(0,str(D.parents[1]/'.deps'))
p=json.loads((D/'inputs.json').read_text(encoding='utf-8'))
v=p['vapor'];ch=p['channel'];bed=p['bed'];cost=p['cost'];ld=p['load']
def write(name,data):
 with (D/name).open('w',encoding='utf-8',newline='\n') as f:json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def tab(name,rows):
 with (D/name).open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(rows)
checks=[]
def ck(name,ok):
 checks.append({'name':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
def eq(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-24)
def sat(TC):
 T=TC+273.15
 if not(v['valid_K'][0]<=T<=v['valid_K'][1]):raise ValueError('NIST fit outside range')
 return 1e5*10**(v['NIST_A']-v['NIST_B']/(T+v['NIST_C']))
def surface_tension(TC):
 x=p['surface_tension'];t=1-(TC+273.15)/x['Tc_K'];return x['B_N_m']*t**x['mu']*(1+x['b']*t)
hum=[]
for ta in v['air_C']:
 for ts in v['surface_C']:
  for rh in v['air_RH']:
   local=rh*sat(ta)/sat(ts)
   hum.append({'air_C':ta,'surface_C':ts,'ambient_RH':rh,'vapor_pressure_Pa':rh*sat(ta),'local_RH_without_added_water':local,'ambient_RH_needed_for_local_55pct':.55*sat(ts)/sat(ta),'ambient_RH_needed_for_local_75pct':.75*sat(ts)/sat(ta)})
ck('same-temperature RH preserved',all(eq(x['local_RH_without_added_water'],x['ambient_RH']) for x in hum if x['air_C']==x['surface_C']))
ck('warming decreases RH at fixed vapor pressure',all(x['local_RH_without_added_water']<=x['ambient_RH']+1e-12 for x in hum))
ck('vapor pressure conservation',all(eq(x['local_RH_without_added_water']*sat(x['surface_C']),x['vapor_pressure_Pa']) for x in hum))
# Independently tabulated NIST Bridgeman-Aldrich coefficients, compared inside shared range.
ck('NIST two fits consistent within2percent',all(abs(sat(t)/(1e5*10**(5.20389-1733.926/(t+273.15-39.485)))-1)<.02 for t in [35,40,50,55]))
ck('IAPWS surface tension50C magnitude',.067<surface_tension(50)<.069)
T=ch['surface_C']+273.15;rho=ch['water_density_kg_m3'];eta=ch['viscosity_Pa_s'];gamma=surface_tension(ch['surface_C'])
pv=ch['air_RH']*sat(ch['air_C']);ps=sat(ch['surface_C']);drho=(ps-pv)/(v['R_water_J_kg_K']*T)
# Film volume is a demand example, not a prediction of hydrodynamic film formation.
Vfilm=math.pi*(ch['contact_patch_radius_um']*1e-6)**2*ch['target_water_film_nm']*1e-9
Rgas=8.314462618;Mw=.01801528
thermal=math.sqrt(8*Rgas*T/(math.pi*Mw))
def throat(rum,Lum,MPa,pocket_um=None,theta=None):
 if pocket_um is None:pocket_um=ch["water_pocket_radius_um"]
 if theta is None:theta=ch["nonwetting_contact_angle_deg"]
 a=rum*1e-6;L=Lum*1e-6;Vr=4*math.pi*(pocket_um*1e-6)**3/3
 Dk=2*a/3*thermal;Db=1/(1/ch['vapor_diffusivity_m2_s']+1/Dk)
 # Diffusive loss along a DRY nonwetting throat. If liquid reaches mouth this formula is invalid.
 J=Db*math.pi*a*a*drho/L
 Pentry=max(0,-2*gamma*math.cos(math.radians(theta))/a)
 dP=max(0,MPa*1e6-Pentry)
 Q=math.pi*a**4*dP/(8*eta*L)
 Vprime=math.pi*a*a*L
 tneed=(Vprime+Vfilm)/Q if Q>0 else None
 # Steady Q over full dwell deliberately includes possible overdelivery; all neck water is counted lost.
 pulse=Q*ch['contact_duration_s']
 Q_after_open=math.pi*a**4*(MPa*1e6)/(8*eta*L) if dP>0 else 0
 evaporation=J*ch['closed_interval_h']*3600
 pulseloss=pulse*rho*bed['local_passes']
 total=evaporation+pulseloss
 return {'throat_radius_um':rum,'throat_length_um':Lum,'liquid_pressure_MPa':MPa,'pocket_radius_um':pocket_um,'contact_angle_deg':theta,'entry_pressure_MPa':Pentry/1e6,'Knudsen_D_m2_s':Dk,'effective_D_m2_s':Db,'evaporation_kg_s':J,'pocket_water_kg':rho*Vr,'steady_evaporation_inventory_hours':rho*Vr/J/3600,'liquid_flow_m3_s':Q,'liquid_Re':2*rho*Q/(math.pi*a*eta),'channel_length_over_diameter':L/(2*a),'priming_m3':Vprime,'film_demand_m3':Vfilm,'conservative_priming_plus_film_s':tneed,'pulse_water_kg':pulse*rho,'four_hour_evaporation_kg':evaporation,'hundred_pulses_water_kg':pulseloss,'four_hour_total_loss_fraction':total/(rho*Vr),'flow_if_capillary_hold_vanishes_m3_s':Q_after_open,'loss_fraction_if_capillary_hold_vanishes':(evaporation+Q_after_open*ch['contact_duration_s']*rho*bed['local_passes'])/(rho*Vr),'supply_within_dwell':tneed is not None and tneed<=ch['contact_duration_s'],'water_inventory_covers_retained_capillary_head':total<=rho*Vr,'water_inventory_covers_zero_postopening_head':(evaporation+Q_after_open*ch['contact_duration_s']*rho*bed['local_passes'])<=rho*Vr}
pores=[]
for a in ch['radii_um']:
 for L in ch['lengths_um']:
  for pr in ch['liquid_pressure_MPa']:pores.append(throat(a,L,pr))
ck('closed gate no liquid flow',all(x['liquid_flow_m3_s']==0 for x in pores if x['liquid_pressure_MPa']<=x['entry_pressure_MPa']))
ck('equivalent diffusion less than both limits',all(x['effective_D_m2_s']<min(ch['vapor_diffusivity_m2_s'],x['Knudsen_D_m2_s']) for x in pores))
ck('entry pressure inverse radius',eq(throat(.1,100,2)['entry_pressure_MPa']/throat(.3,100,2)['entry_pressure_MPa'],3))
ck('Poiseuille flow inverse length',eq(throat(.1,10,2)['liquid_flow_m3_s']/throat(.1,100,2)['liquid_flow_m3_s'],10))
ck('dry-throat evaporation inverse length',eq(throat(.1,10,2)['evaporation_kg_s']/throat(.1,100,2)['evaporation_kg_s'],10))
ck('pocket capacity cubed radius',eq(throat(.1,100,2,20)['pocket_water_kg']/throat(.1,100,2,10)['pocket_water_kg'],8))
ck('post-opening zero capillary head increases water requirement',all(x['loss_fraction_if_capillary_hold_vanishes']>=x['four_hour_total_loss_fraction'] for x in pores))
ck('water accounting',all(eq(x['four_hour_evaporation_kg']+x['hundred_pulses_water_kg'],x['four_hour_total_loss_fraction']*x['pocket_water_kg']) for x in pores))
# Independent integration of ideal fully developed axisymmetric liquid velocity profile.
def midpoint_flow(a,L,dp,n):
 dr=a/n;return sum((dp/(4*eta*L))*(a*a-((i+.5)*dr)**2)*2*math.pi*((i+.5)*dr)*dr for i in range(n))
bas=throat(.1,100,2)
a=.1e-6;L=100e-6;dp=(2-bas['entry_pressure_MPa'])*1e6
q1=midpoint_flow(a,L,dp,100);q2=midpoint_flow(a,L,dp,200)
ck('velocity profile integral convergence',abs(q2/bas['liquid_flow_m3_s']-1)<abs(q1/bas['liquid_flow_m3_s']-1) and abs(q2/bas['liquid_flow_m3_s']-1)<2e-5)
ck('no pressure gives no flow',throat(.1,100,0)['liquid_flow_m3_s']==0)
# Neck radius sensitivity, larger reservoir, and wettability sensitivity do NOT share a probability distribution.
sensitivity=[]
for a in [.08,.09,.1,.11,.12]:
 for Rp in [15,20]:sensitivity.append(throat(a,100,2,Rp))
for angle in [95,105,135]:sensitivity.append(throat(.1,100,2,15,angle))
M=bed['area_m2']*bed['depth_m']*bed['bulk_density_kg_m3']
reservoir=[]
for d in bed['active_depths_m']:
 mass=bed['area_m2']*d*bed['bulk_density_kg_m3'];w=mass*bed['water_mass_per_dry_mass']
 for flux in bed['open_surface_flux_kg_m2_h']:
  for h in bed['film_nm']:
   film=rho*bed['area_m2']*h*1e-9*bed['local_passes']*bed['lost_film_fraction']
   evap=bed['area_m2']*flux*bed['operating_interval_h']
   reservoir.append({'active_depth_m':d,'available_water_kg':w,'open_surface_flux_kg_m2_h':flux,'film_nm':h,'evaporation_kg':evap,'film_replacement_kg':film,'total_required_water_kg':film+evap,'required_water_per_active_dry_mass':(film+evap)/mass,'water_deficit_kg':max(0,film+evap-w)})
ck('bed material mass',eq(M,108000))
ck('film water unit conversion100nm',eq(rho*bed['area_m2']*100e-9*100,20))
ck('macro water mass conservation',all(eq(x['evaporation_kg']+x['film_replacement_kg'],x['total_required_water_kg']) for x in reservoir))
share=[]
for mu in ld['dry_mu']:
 lam=(mu-ld['target_mu'])/(mu-ld['wet_mu'])
 for area in ld['patch_area_fraction']:
  share.append({'dry_mu':mu,'wet_mu':ld['wet_mu'],'target_mu':ld['target_mu'],'required_wet_load_fraction':lam,'wet_area_fraction':area,'wet_to_dry_mean_pressure_ratio':lam*(1-area)/(area*(1-lam))})
ck('load weighted friction reconstruction',all(eq(x['required_wet_load_fraction']*x['wet_mu']+(1-x['required_wet_load_fraction'])*x['dry_mu'],x['target_mu']) for x in share))
ck('area-weighted pressures give desired loads',all(eq(x['wet_to_dry_mean_pressure_ratio']*x['wet_area_fraction']/(x['wet_to_dry_mean_pressure_ratio']*x['wet_area_fraction']+1-x['wet_area_fraction']),x['required_wet_load_fraction']) for x in share))
# Thin cylindrical-skeleton layer estimate excludes nodes/ends and requires measured real accessible area.
SperM=2/(cost['solid_density_kg_m3']*cost['branch_radius_um']*1e-6)
r=cost['discount_rate'];n=cost['capital_life_years'];crf=r*(1+r)**n/((1+r)**n-1)
coats=[]
for f in cost['patch_fraction']:
 layer=M*SperM*f*cost['dry_layer_thickness_nm']*1e-9*cost['dry_layer_density_kg_m3']
 for price in cost['added_material_price_JPY_kg']:
  initial=layer/cost['manufacturing_yield']*price;annual=initial*(crf+cost['annual_material_replacement'])
  coats.append({'patch_area_fraction':f,'retained_layer_kg':layer,'purchased_layer_equivalent_kg':layer/cost['manufacturing_yield'],'assumed_price_JPY_kg':price,'initial_material_only_JPY':initial,'annualized_material_and_replacement_JPY':annual,'annual_remaining_for_processing_JPY':cost['annual_cost_budget_JPY']-annual})
ck('thin cylinder surface-volume dimensional check',eq(SperM,2/(1200*30e-6)))
ck('retained and purchased mass yield',all(eq(x['retained_layer_kg'],x['purchased_layer_equivalent_kg']*cost['manufacturing_yield']) for x in coats))
ck('annual cost bookkeeping',all(eq(x['annualized_material_and_replacement_JPY']+x['annual_remaining_for_processing_JPY'],cost['annual_cost_budget_JPY']) for x in coats))
# The thin-layer estimate is compared with an exact straight-cylinder shell.
t=cost['dry_layer_thickness_nm']*1e-9;rad=cost['branch_radius_um']*1e-6
ck('thin layer geometric approximation error',abs(((rad+t)**2-rad**2)/(2*rad*t)-1)<.002)
ck('reference microchannel creeping flow',0<bas['liquid_Re']<.1)
summary={'physical_tests':0,'physical_success_probability':None,'status':'hypothetical diagnostic only','counts':{'humidity':len(hum),'pores':len(pores),'pore_sensitivity':len(sensitivity),'macro_water':len(reservoir),'load_share':len(share),'coating_cost':len(coats),'numeric_checks':len(checks)},'sat30_Pa':sat(30),'sat50_Pa':sat(50),'surface50_RH_for_air30_RH60':.6*sat(30)/sat(50),'surface50_RH_for_saturated_air30':sat(30)/sat(50),'surface_tension50_N_m':gamma,'base_pore':bas,'larger_pocket_20um':throat(.1,100,2,20),'macro_50mm_100nm_flux005':next(x for x in reservoir if x['active_depth_m']==.05 and x['film_nm']==100 and x['open_surface_flux_kg_m2_h']==.05),'coating_area_per_kg_m2':SperM,'coating_costs':coats,'load_shares':share,'conditional_pocket_count_for_120kg_water':120/bas['pocket_water_kg'],'limitations':['no achieved water film/friction prediction','dry nonwetting throat must return after load','actual liquid pressure is not nominal ski pressure','gas/liquid transition, elasticity, clogging and 50C wear not solved','safety and winter anchoring unverified']}
for name,rows in [('humidity.csv',hum),('pores.csv',pores),('pore_sensitivity.csv',sensitivity),('macro_water.csv',reservoir),('load_share.csv',share),('coating_cost.csv',coats)]:tab(name,rows)
write('results.json',summary);write('checks.json',checks)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy,platform
plt.rcParams.update({'font.size':10,'svg.hashsalt':'cycle44-fixed'})
fig,ax=plt.subplots(1,2,figsize=(11.6,4.4),layout='constrained')
xs=list(range(30,66))
for rh in [.4,.6,.8,1]:ax[0].plot(xs,[100*rh*sat(30)/sat(t) for t in xs],label='Air30C RH'+str(round(rh*100))+'%')
ax[0].axhspan(55,75,alpha=.16,color='orange',label='Room-T study transition (NOT50C limit)')
ax[0].set(xlabel='Surface temperature (C)',ylabel='Local RH without added water (%)',title='Fixed ambient vapor pressure');ax[0].legend(fontsize=7);ax[0].grid(alpha=.2)
for pr in ch['liquid_pressure_MPa']:
 z=[x for x in pores if x['throat_length_um']==100 and x['liquid_pressure_MPa']==pr and x['conservative_priming_plus_film_s'] is not None]
 ax[1].loglog([x['throat_radius_um'] for x in z],[x['conservative_priming_plus_film_s'] for x in z],marker='o',label='Liquid pressure '+str(pr)+'MPa')
ax[1].axhline(.1,color='black',ls='--',label='0.1s load diagnostic');ax[1].set(xlabel='Nonwetting throat radius (um)',ylabel='Priming + 50nm film demand / Q (s)',title='Ideal liquid transport; closed cases omitted');ax[1].legend(fontsize=8);ax[1].grid(alpha=.2)
fig.savefig(D/'humidity_and_delivery.png',dpi=180);fig.savefig(D/'humidity_and_delivery.svg',metadata={'Date':None});plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(11.6,4.4),layout='constrained')
for Rp in [15,20]:
 z=[x for x in sensitivity if x['pocket_radius_um']==Rp and x['contact_angle_deg']==120]
 ax[0].plot([x['throat_radius_um'] for x in z],[x['four_hour_total_loss_fraction'] for x in z],marker='o',label=str(Rp)+'um pocket: capillary head retained')
 ax[0].plot([x['throat_radius_um'] for x in z],[x['loss_fraction_if_capillary_hold_vanishes'] for x in z],ls='--',marker='x',label=str(Rp)+'um pocket: capillary head vanishes')
ax[0].axhline(1,color='black',ls='--',label='Full initial inventory');ax[0].set(xlabel='Throat radius (um)',ylabel='4h diffusion + 100 liquid pulses / inventory',title='100um neck; 2MPa; each pulse0.1s');ax[0].legend(fontsize=8);ax[0].grid(alpha=.2)
xs=[x['patch_area_fraction'] for x in coats if x['assumed_price_JPY_kg']==20000]
z=[x for x in coats if x['assumed_price_JPY_kg']==20000]
ax[1].bar([str(round(f*100)) for f in xs],[x['annualized_material_and_replacement_JPY']/1e6 for x in z],color='#287d7d')
ax[1].axhline(1,color='black',ls='--',label='1M JPY/year hypothetical budget');ax[1].set(xlabel='Coated fraction of total branch area (%)',ylabel='Added material annualized cost (M JPY/year)',title='20,000JPY/kg; 100nm layer; processing excluded');ax[1].legend(fontsize=8)
fig.savefig(D/'inventory_and_cost.png',dpi=180);fig.savefig(D/'inventory_and_cost.svg',metadata={'Date':None});plt.close(fig)
for f in D.glob('*.svg'):f.write_text('\n'.join(x.rstrip() for x in f.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
write('environment.json',{'python':platform.python_version(),'matplotlib':matplotlib.__version__,'numpy':numpy.__version__})
print(json.dumps(summary,ensure_ascii=False,allow_nan=False))
