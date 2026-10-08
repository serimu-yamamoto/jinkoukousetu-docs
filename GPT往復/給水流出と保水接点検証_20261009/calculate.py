"""Cycle 45: diagnostic ideal models, not material-performance validation."""
import json, math, sys, platform
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]/'.deps'))
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
w=I['water']; p=I['pore']; c=I['contact']; H=I['hydrostatic']; R=I['retention']; C=I['cost']
pi=math.pi
checks=[]
def check(name,ok):
    checks.append({'name':name,'passed':bool(ok)})
    if not ok: raise AssertionError(name)
def eq(a,b,rtol=1e-10,atol=1e-25): return math.isclose(a,b,rel_tol=rtol,abs_tol=atol)
def entry(r): return max(0.,-2*w['surface_tension_N_m']*math.cos(math.radians(p['contact_angle_deg']))/r)
def tube_resistance(r): return 8*w['viscosity_Pa_s']*p['length_m']/(pi*r**4)
def freeflow(r,ps,hold=True):
    if ps<=entry(r): return 0.
    return (ps-entry(r) if hold else ps)/tube_resistance(r)
def volume(r): return 4*pi*r**3/3
q0=freeflow(p['radius_m'],p['source_pressure_Pa'])
transport=[]
for a in c['radii_m']:
 for h in c['film_m']:
  for U in c['speeds_m_s']:
   q=U*a*h # integrated outward Couette contribution on downstream half of circle
   dwell=c['effective_loaded_length_m']/U
   vf=pi*a*a*h
   shear=w['viscosity_Pa_s']*U/h
   transport.append(dict(patch_radius_m=a,film_m=h,speed_m_s=U,loaded_s=dwell,
      free_pore_flow_m3_s=q0,outward_Couette_m3_s=q,
      fluid_volume_m3=vf,film_turnover_s=vf/q,
      flow_ratio=q/q0,parallel_pores_for_rate=math.ceil(q/q0),
      minimum_reuse_if_pore_only=max(0.,1-q0/q),
      outward_volume_per_load_m3=q*dwell,
      piston_stroke_if_full_supply_m=q*dwell/(pi*a*a),
      shear_Pa=shear,fluid_shear_mu_at_2MPa=shear/2e6,
      reservoir20_load_equivalents=q*dwell/volume(20e-6),
      warnings='Couette component only, not total Reynolds solution; upstream reuse/rain/inlet supply can reduce new-water demand. Film assumed, not proven.'))
base=next(x for x in transport if eq(x['patch_radius_m'],10e-6) and eq(x['film_m'],50e-9) and x['speed_m_s']==5)
pressure=[]
for nom in c['nominal_pressure_Pa']:
 for phi in c['real_area_fraction']:
  for beta in c['liquid_force_fraction']:
   for alpha in c['actuator_to_contact_area_ratio']:
    ps=beta*nom/(alpha*phi)
    pressure.append(dict(nominal_Pa=nom,real_area_fraction=phi,liquid_force_fraction=beta,
      actuator_to_contact_area_ratio=alpha,ideal_source_Pa=ps,
      entry_exceeded=ps>entry(p['radius_m']),
      unloaded_outlet_flow_m3_s=freeflow(p['radius_m'],ps),
      warnings='Force-area balance only: actual beta, cavity compliance, fatigue and edge loads unknown.'))
def hydrostatic(r,h,ps,hold=True):
 a=H['patch_radius_m']; lg=math.log(a/r)
 rt=tube_resistance(r); rg=6*w['viscosity_Pa_s']*lg/(pi*h**3)
 available=max(0.,ps-entry(r)) if hold else (ps if ps>entry(r) else 0.)
 q=available/(rt+rg); pb=q*rg
 load=pi*pb*(a*a-r*r)/(2*lg)
 return dict(pore_radius_m=r,gap_m=h,source_Pa=ps,capillary_head_retained=hold,
    pipe_R_Pa_s_m3=rt,gap_R_Pa_s_m3=rg,flow_m3_s=q,feed_pressure_Pa=pb,
    supported_N=load,mean_patch_pressure_Pa=load/(pi*a*a),
    warning='Parallel rigid faces, central feed, ambient edge, no sliding or wedge. Not total ski load support.')
hydro=[hydrostatic(r,h,ps,hold) for r in H['pore_radii_m'] for h in H['gap_m'] for ps in H['source_Pa'] for hold in [True,False]]
hbase=hydrostatic(p['radius_m'],50e-9,2e6)
# A one-mode diagnostic: s decays under load and refills toward 1 when unloaded.
# The latter needs available water. It is NOT guaranteed in open dry air.
def retained(tau,tc,tr):
 a=math.exp(-tc/tau); b=math.exp(-tr/tau)
 pre=-math.expm1(-tr/tau)/(-math.expm1(-(tc+tr)/tau))
 return a,pre,a*pre,-math.expm1(-tr/tau)
retention=[]
for ell in R['path_m']:
 for D in R['diffusivity_m2_s']:
  tau=ell*ell/D
  for tc in R['loaded_s']:
   for tr in R['rest_s']:
    a,pre,end,refill=retained(tau,tc,tr)
    retention.append(dict(path_m=ell,D_m2_s=D,tau_s=tau,loaded_s=tc,rest_s=tr,
      single_load_retention=a,rest_refill_of_deficit=refill,
      steady_preload_capacity=pre,steady_endload_capacity=end,
      warning='Single-mode hypothesis, geometry factor=1. No friction prediction; refill assumes an available internal/external water source.'))
rbase=next(x for x in retention if eq(x['path_m'],50e-6) and eq(x['D_m2_s'],1.22e-9) and x['loaded_s']==0.1 and x['rest_s']==10)
band_ratio=math.log(1/(1-R['refill_fraction']))/(-math.log(R['hold_fraction']))
rate=C['discount_rate']; n=C['years']; crf=rate*(1+rate)**n/((1+rate)**n-1)
M=C['bed_area_m2']*C['bed_depth_m']*C['bulk_density_kg_m3']
area=M*2/(C['skeleton_density_kg_m3']*C['skeleton_radius_m'])
cost=[]
for f in C['patch_area_fraction']:
 for h in C['hydrated_thickness_m']:
  wet=area*f*h*C['hydrated_density_kg_m3']; dry=wet*C['dry_mass_fraction']; water=wet-dry
  initial=dry/C['yield_fraction']*C['dry_price_JPY_kg']
  shell_factor=1+h/(2*C['skeleton_radius_m'])
  cost.append(dict(area_fraction=f,hydrated_thickness_m=h,wet_phase_kg=wet,dry_phase_kg=dry,
      water_inventory_kg=water,cylindrical_shell_volume_factor=shell_factor,
      cylindrical_shell_wet_kg=wet*shell_factor,cylindrical_shell_water_kg=water*shell_factor,
      cylindrical_shell_initial_JPY=initial*shell_factor,
      cylindrical_shell_annual_JPY=initial*shell_factor*(crf+C['annual_replacement_fraction']),
      initial_material_only_JPY=initial,
      annual_material_and_replacement_JPY=initial*(crf+C['annual_replacement_fraction']),
      one_full_water_refill_cost_JPY=water/1000*C['water_JPY_m3'],
      warning='Planar thin-layer approximation, excludes forming/washing/refill/recovery/equipment; no commercial quote.'))
# Independent numerical integrations and balance checks.
check('cylindrical shell exact volume correction',eq((pi*((30e-6+5e-6)**2-(30e-6)**2))/(2*pi*30e-6*5e-6),1+5e-6/(2*30e-6)))
check('44 baseline pore flow reproduced',eq(q0,9.428783066939748e-16))
check('Poiseuille radius resistance ratio',eq(tube_resistance(1e-7)/tube_resistance(2e-7),16))
check('channel closes below entry',freeflow(1e-7,entry(1e-7)*0.99)==0)
check('film volume = rate x turnover',eq(base['fluid_volume_m3'],base['outward_Couette_m3_s']*base['film_turnover_s']))
# Two-dimensional numerical integration of circular boundary normal flux.
def circle_flux(N):
 a=1e-5; h=5e-8; U=5
 dth=2*pi/N
 return sum(max(0.,math.cos((j+0.5)*dth))*U*h*a/2*dth for j in range(N))
e200=abs(circle_flux(200)-base['outward_Couette_m3_s']);e400=abs(circle_flux(400)-base['outward_Couette_m3_s'])
check('circular Couette quadrature converges',e400<e200/3.8)
check('circular Couette quadrature matches',eq(circle_flux(2000),base['outward_Couette_m3_s'],rtol=2e-6))
check('faster travel same integrated water over fixed loaded length',eq(transport[0]['outward_volume_per_load_m3'],transport[2]['outward_volume_per_load_m3']))
check('reuse plus source balances transport',eq(base['outward_Couette_m3_s']*(1-base['minimum_reuse_if_pore_only']),q0,rtol=1e-12))
check('piston volume conserved',eq(base['piston_stroke_if_full_supply_m']*pi*1e-10,base['outward_volume_per_load_m3']))
check('hydrostatic series resistance',eq(hbase['flow_m3_s']*(hbase['pipe_R_Pa_s_m3']+hbase['gap_R_Pa_s_m3']),2e6-entry(1e-7)))
check('hydrostatic load-flow identity',eq(hbase['supported_N']/hbase['flow_m3_s'],3*w['viscosity_Pa_s']*(1e-10-1e-14)/(5e-8)**3))
def integrated_load(N):
 a=1e-5;b=1e-7;pb=hbase['feed_pressure_Pa'];lg=math.log(a/b); dr=a/N
 return sum(2*pi*((j+.5)*dr)*dr*(pb if (j+.5)*dr<=b else pb*math.log(a/((j+.5)*dr))/lg) for j in range(N))
check('radial pressure integration matches analytic load',eq(integrated_load(20000),hbase['supported_N'],rtol=1e-7))
check('removing capillary hold increases hydrostatic flow',hydrostatic(1e-7,5e-8,2e6,False)['flow_m3_s']>hbase['flow_m3_s'])
check('pressure force-area reconstruction',all(eq(x['ideal_source_Pa']*x['actuator_to_contact_area_ratio']*x['real_area_fraction'],x['liquid_force_fraction']*x['nominal_Pa']) for x in pressure))
check('Sakai dimensional scale K*M',eq(R['source_K_m4_N_s']*R['source_M_Pa'],1.22e-9))
check('diffusion path doubling quadruples tau',eq((2*50e-6)**2/1.22e-9,4*(50e-6)**2/1.22e-9))
check('hold-window lower bound',eq(math.exp(-0.1/(0.1/-math.log(.9))),.9))
check('refill-window upper bound',eq(1-math.exp(-10/(10/math.log(20))),.95))
check('single-path time-window threshold',eq((band_ratio*.1)/math.log(20),.1/-math.log(.9)))
a,pre,end,bcomp=retained(rbase['tau_s'],.1,10)
s=1.
for _ in range(10000): s=1-(1-s*a)*math.exp(-10/rbase['tau_s'])
check('cycle recurrence matches steady solution',eq(s,pre))
check('all retained capacities physical',all(0<=x['steady_endload_capacity']<=x['steady_preload_capacity']<=1 for x in retention))
check('no rest cannot restore capacity',retained(1,.1,0)[1]==0)
check('bed mass remains108t',eq(M,108000))
check('cost dry plus water balances mass',all(eq(x['dry_phase_kg']+x['water_inventory_kg'],x['wet_phase_kg']) for x in cost))
check('cost replacement counted once',all(eq(x['annual_material_and_replacement_JPY'],x['initial_material_only_JPY']*crf+x['initial_material_only_JPY']*.1) for x in cost))
check('physical evidence not numerical acceptance',I['physical_tests']==0 and I['physical_success_probability'] is None)
parallel_life={str(r):volume(r)*w['density_kg_m3']/(base['parallel_pores_for_rate']*p['previous_evaporation_kg_s']) for r in p['pocket_radii_m']}
results=dict(physical_tests=0,physical_success_probability=None,status='diagnostic hypotheses; no achieved ski friction or snow feel',
 counts=dict(transport=len(transport),pressure=len(pressure),hydrostatic=len(hydro),retention=len(retention),cost=len(cost),numeric_checks=len(checks)),
 baseline_transport=base,baseline_hydrostatic=hbase,baseline_retention=rbase,
 minimum_rest_over_loaded_for_single_mode=band_ratio,
 ideal_parallel_pore_evaporation_inventory_seconds=parallel_life,
 baseline_cost=next(x for x in cost if x['area_fraction']==.05 and eq(x['hydrated_thickness_m'],5e-6)),
 paired_diffusion_window_at_ell50um_tc01_tr10=dict(tau_min_s=.1/-math.log(.9),tau_max_s=10/math.log(20),D_min_m2_s=(50e-6)**2/(10/math.log(20)),D_max_m2_s=(50e-6)**2/(.1/-math.log(.9))),
 conclusion='H44 single-throat film replenishment cannot be inferred from one-fill time; prioritize low-leakage contact phase plus dry supporting phase, conditional on 50C real-sole evidence.')
for name,obj in [('transport',transport),('pressure',pressure),('hydrostatic',hydro),('retention',retention),('cost',cost),('results',results),('checks',checks)]:
 (P/(name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':10,'svg.hashsalt':'cycle45'})
fig,axs=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
for h in c['film_m']:
 rows=[x for x in transport if eq(x['patch_radius_m'],1e-5) and eq(x['film_m'],h)]
 axs[0].plot([x['speed_m_s'] for x in rows],[x['flow_ratio'] for x in rows],'o-',label=f'{h*1e9:g} nm gap')
axs[0].set(xlabel='Sliding speed [m/s]',ylabel='Outward Couette rate / one-pore supply',yscale='log',title='Assumed free film: transport burden')
axs[0].legend();axs[0].grid(True,alpha=.25)
for ps in H['source_Pa']:
 rows=[x for x in hydro if eq(x['pore_radius_m'],1e-7) and x['source_Pa']==ps and x['capillary_head_retained']]
 axs[1].plot([x['gap_m']*1e9 for x in rows],[x['mean_patch_pressure_Pa']/1000 for x in rows],'o-',label=f'{ps/1e6:g} MPa source')
axs[1].set(xlabel='Parallel gap [nm]',ylabel='Hydrostatic-only mean pressure [kPa]',title='Feed + outlet resistances coupled')
axs[1].legend();axs[1].grid(True,alpha=.25)
fig.suptitle('Cycle 45 | Ideal sensitivity only: no physical ski-performance data',fontsize=12)
for ext in ['png','svg']:fig.savefig(P/('flow_and_support.'+ext),dpi=160)
plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
for tr in [.1,1,10]:
 rows=[x for x in retention if eq(x['D_m2_s'],1.22e-9) and x['loaded_s']==.1 and x['rest_s']==tr]
 axs[0].plot([x['path_m']*1e6 for x in rows],[x['steady_endload_capacity'] for x in rows],'o-',label=f'{tr:g} s rest')
axs[0].set(xlabel='Effective drainage path [um]',ylabel='End-load normalized capacity',ylim=(0,1.03),title='Repeated 0.1 s loads | refill assumed')
axs[0].axhline(.9,ls=':',c='gray');axs[0].legend();axs[0].grid(True,alpha=.25)
for f in C['patch_area_fraction']:
 rows=[x for x in cost if x['area_fraction']==f]
 axs[1].plot([x['hydrated_thickness_m']*1e6 for x in rows],[x['cylindrical_shell_annual_JPY']/1e6 for x in rows],'o-',label=f'{f*100:g}% surface fraction')
axs[1].set(xlabel='Hydrated phase thickness [um]',ylabel='Material annualized + replacement [M JPY/y]',title='Cylindrical shell | processing excluded')
axs[1].legend();axs[1].grid(True,alpha=.25)
fig.suptitle('Cycle 45 | Retention model and cost bounds are not material qualification',fontsize=12)
for ext in ['png','svg']:fig.savefig(P/('retention_and_cost.'+ext),dpi=160)
plt.close(fig)
for f in P.glob('*.svg'):f.write_text('\n'.join(x.rstrip() for x in f.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
(P/'environment.json').write_text(json.dumps({'python':platform.python_version(),'matplotlib':matplotlib.__version__},indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'counts':results['counts'],'flow_ratio':base['flow_ratio'],'reuse':base['minimum_reuse_if_pore_only'],'support_kPa':hbase['mean_patch_pressure_Pa']/1000,'retained':rbase['steady_endload_capacity'],'all_numeric_checks_passed':all(x['passed'] for x in checks)},ensure_ascii=False))
