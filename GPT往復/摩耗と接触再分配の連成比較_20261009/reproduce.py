"""Cycle81: implicit wear/contact evolution, hypothetical coefficients, no physical trials."""
from pathlib import Path
import sys,json,csv,math
P=Path(__file__).resolve().parent;R=P.parents[1]
if (R/'.deps').exists():sys.path.insert(0,str(R/'.deps'))
import numpy as np
from scipy.linalg import circulant,solve
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
I={'period_m':190e-6,'E_Pa':30e6,'nu':.49,'layer_depth_m':25e-6,'mean_pressure_Pa':870247.2724625465,'short_amplitude_m':.25e-6,'long_amplitude_m':.25e-6,'k_host_mm3_Nm':1e-5,'grid':128,'max_step_m':.8,'distances_m':[0,1.6,8,16,40,80,160],'uniform_tau_Pa':80000.,'tau_A_Pa':30000.,'tau_B_Pa':300000.,'coulomb_A':.03,'coulomb_B':.30,'other_mu':.02,'total_mu_screen':.10,'pressure_screen_Pa':3e6,'max_wear_fraction_layer':.1}
checks=[]
def ck(n,v,detail=None):
 checks.append({'name':n,'passed':bool(v),'detail':detail})
 if not v:print('CHECK FAILED: '+n+' '+str(detail));sys.exit(1)
def outj(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def outcsv(n,rows):
 with (P/n).open('w',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def kernel(q):
 E=I['E_Pa'];nu=I['nu'];d=I['layer_depth_m'];G=E/(2*(1+nu))
 K=np.zeros_like(q);nz=q>0;z=q[nz]*d;a=3-4*nu;ez=np.exp(-2*z)
 K[nz]=(1-nu)/(G*q[nz])*(a*(1-ez*ez)/2-2*z*ez)/(a*(1+ez*ez)/2+(2*z*z+5-12*nu+8*nu*nu)*ez)
 K[~nz]=d*(1+nu)*(1-2*nu)/(E*(1-nu))
 return K
class Surface:
 def __init__(self,n):
  self.n=n;self.x=np.arange(n)*I['period_m']/n;self.q=2*np.pi*np.fft.rfftfreq(n,I['period_m']/n);self.K=kernel(self.q)
  kh=self.K*I['mean_pressure_Pa']/1e-6;kh[0]=1.;self.C=circulant(np.fft.irfft(kh,n));self.C=(self.C+self.C.T)/2
 def pressure(self,z,extra=None,active=None):
  n=self.n;C=self.C if extra is None else self.C+np.diag(extra);hh=(z-z.mean())/1e-6
  A=np.arange(n) if active is None else np.flatnonzero(active)
  if len(A)==0:A=np.arange(n)
  for it in range(4*n):
   V=solve(C[np.ix_(A,A)],np.column_stack([hh[A],np.ones(len(A))]),assume_a='pos',check_finite=False)
   lag=(V[:,0].sum()-n)/V[:,1].sum();pa=V[:,0]-lag*V[:,1]
   if pa.min() < -1e-9:A=np.delete(A,np.argmin(pa));continue
   xx=np.zeros(n);xx[A]=np.maximum(pa,0);gg=C@xx-hh;B=np.setdiff1d(np.arange(n),A)
   if len(B) and gg[B].min() < -lag-1e-9:A=np.sort(np.append(A,B[np.argmin(gg[B])]));continue
   break
  else:raise RuntimeError('Active set limit')
  active=xx>1e-8;g=C@xx-hh;g-=g[active].mean();err=max(abs(g[active]).max(),max(0.,-g[~active].min()) if (~active).any() else 0.)
  return xx*I['mean_pressure_Pa'],active,float(err),float(abs(xx.mean()-1))
 def profile(self):return I['short_amplitude_m']*np.cos(8*np.pi*self.x/I['period_m'])+I['long_amplitude_m']*np.cos(2*np.pi*self.x/I['period_m'])
def phase_mask(S,f,shift=0):
 if f<=0:return np.zeros(S.n,dtype=bool)
 if f>=1:return np.ones(S.n,dtype=bool)
 cells=S.n//4;count=int(round(f*cells));offset=int(round(f*cells/2+shift*cells))
 return ((np.arange(S.n)%cells+offset)%cells)<count

def run(name,f,ratio,shift=0,n=None,step=None,z_initial=None,targets=None,recess_um=None,perturb_um=0.):
 S=Surface(n or I['grid']);step=step or I['max_step_m'];targets=targets or I['distances_m'];z0=S.profile() if z_initial is None else z_initial(S.x);z=z0.copy();w=np.zeros(S.n);mask=phase_mask(S,f,shift);kh=I['k_host_mm3_Nm']*1e-9;k=np.where(mask,kh/ratio,kh)
 if recess_um is not None:
  # Inverse geometry: prescribed uniform pressure on caps, positive clearance elsewhere.
  desired=np.where(mask,I['mean_pressure_Pa']/mask.mean(),0.)
  z0=np.fft.irfft(np.fft.rfft(desired)*S.K,S.n)-np.where(mask,0.,recess_um*1e-6)
  z0+=mask*perturb_um*1e-6*np.cos(8*np.pi*S.x/I['period_m']);z=z0.copy();k=np.where(mask,kh,0.)
 pp,active,err,loaderr=S.pressure(z);s=0.;records=[];profiles=[];maxerr=err;maxload=loaderr;integral=0.;maxstepwear=0.;iters=0
 def record():
  cp=pp/I['mean_pressure_Pa'];a=float(np.mean(active));aA=float(np.mean(active&mask));aB=a-aA;loadA=float(np.mean(cp*mask));delta_max=float(w.max());height=z-z.mean();physical_gap=np.fft.irfft(np.fft.rfft(pp)*S.K,S.n)-z;physical_gap-=physical_gap[active].mean()
  mu_area=(aA*I['tau_A_Pa']+aB*I['tau_B_Pa'])/I['mean_pressure_Pa'] if f else a*I['uniform_tau_Pa']/I['mean_pressure_Pa']
  mu_coul=loadA*I['coulomb_A']+(1-loadA)*I['coulomb_B'] if f else None
  rec={'case':name,'distance_m':s,'grid':S.n,'step_m':step,'fraction_A_requested':f,'fraction_A_grid':float(mask.mean()),'wear_ratio_B_over_A':ratio,'contact_fraction':a,'A_contact_area_fraction':aA,'A_load_fraction':loadA,'pmax_MPa':float(pp.max()/1e6),'mean_wear_um':float(w.mean()*1e6),'max_wear_um':delta_max*1e6,'relief_peak_to_valley_um':float(np.ptp(height)*1e6),'mu_area_law':mu_area,'mu_area_law_plus_other':mu_area+I['other_mu'],'mu_coulomb_law':mu_coul,'pressure_screen_pass':bool(pp.max()<=I['pressure_screen_Pa']),'small_wear_depth_screen':bool(delta_max/I['layer_depth_m']<=I['max_wear_fraction_layer']),'initial_height_over_layer_depth':float(np.max(np.abs(z0-z0.mean()))/I['layer_depth_m']),'recess_um':recess_um,'perturb_um':perturb_um,'B_contact_area_fraction':aB,'kkt_error_um':maxerr,'relative_load_error':maxload}
  records.append(rec)
  if s in [0,40,160]:
   for i in range(S.n):profiles.append({'case':name,'distance_m':s,'x_um':S.x[i]*1e6,'height_centered_um':height[i]*1e6,'p_MPa':pp[i]/1e6,'wear_um':w[i]*1e6,'phase_A':bool(mask[i]),'loaded_gap_um':float(physical_gap[i]*1e6)})
 record()
 for target in targets[1:]:
  while s < target-1e-10:
   ds=min(step,target-s);extra=ds*k*I['mean_pressure_Pa']/1e-6
   pn,an,en,ln=S.pressure(z,extra,active)
   dw=ds*k*pn;w+=dw;z-=dw;integral+=float(dw.mean());maxstepwear=max(maxstepwear,float(dw.max()));pp=pn;active=an;maxerr=max(maxerr,en);maxload=max(maxload,ln);s+=ds;iters+=1
  s=float(target);record()
 # Residual must satisfy the physical elastic contact after the wear update.
 pf,af,ef,lf=S.pressure(z,active=active)
 diagnostics={'case':name,'n':S.n,'step':step,'max_kkt_error_um':maxerr,'max_relative_load_error':maxload,'final_static_pressure_relative_difference':float(np.max(abs(pf-pp))/I['mean_pressure_Pa']),'integrated_volume_error_um':abs(float(w.mean())-integral)*1e6,'max_incremental_wear_um':maxstepwear*1e6,'all_nonnegative_wear':bool((w>=-1e-20).all()),'steps':iters}
 return records,profiles,diagnostics,S,z,w,pp

# Exact-limit verification: flat uniform wear, and full-contact decaying sinusoid.
flat=run('check_flat',0,1,n=64,step=.8,z_initial=lambda x:np.zeros_like(x),targets=[0,8])
ck('flat_uniform_pressure',np.max(abs(flat[6]/I['mean_pressure_Pa']-1))<1e-10)
ck('flat_exact_wear',abs(flat[5].mean()-1e-14*I['mean_pressure_Pa']*8)<1e-18)
ck('SI_conversion',math.isclose(I['k_host_mm3_Nm']*1e-9,1e-14,rel_tol=1e-12))
analytic=[]
for st in [.8,.4,.2]:
 r=run('check_sine',0,1,n=64,step=st,z_initial=lambda x:1e-9*np.cos(2*np.pi*x/I['period_m']),targets=[0,8])
 q=2*np.pi/I['period_m'];Kq=kernel(np.array([q]))[0];exact=1e-9*np.exp(-1e-14*8/Kq);amp=2*np.mean((r[4]-r[4].mean())*np.cos(q*r[3].x));analytic.append({'step_m':st,'amplitude_m':amp,'exact_amplitude_m':exact,'relative_error':abs(amp/exact-1)})
ck('analytic_error_decreases',analytic[2]['relative_error']<analytic[1]['relative_error']<analytic[0]['relative_error'])
ck('analytic_error_below_0p2percent',analytic[2]['relative_error']<.002,analytic[2]['relative_error'])
outcsv('analytic_decay_check.csv',analytic)

cases=[('uniform',0,1,0),('A12_ratio10',.125,10,0),('A12_ratio100',.125,100,0),('A50_ratio10',.5,10,0),('A87_ratio10',.875,10,0),('A50_ratio1',.5,1,0),('A50_ratio0p1',.5,.1,0),('A12_ratio10_shift',.125,10,.5)]
rows=[];profiles=[];diags=[];results={}
for name,f,r,sh in cases:
 v=run(name,f,r,sh);results[name]=v;rows+=v[0];profiles+=v[1];diags.append(v[2]);print('computed '+name,flush=True)
ck('phase_area_exact_on_grid',all(abs(r['fraction_A_grid']-r['fraction_A_requested'])<1e-12 for r in rows))
ck('all_step_contact_residual',max(x['max_kkt_error_um'] for x in diags)<1e-7)
ck('all_step_load_balance',max(x['max_relative_load_error'] for x in diags)<1e-10)
ck('implicit_contact_static_agreement',max(x['final_static_pressure_relative_difference'] for x in diags)<1e-7)
ck('nonnegative_wear',all(x['all_nonnegative_wear'] for x in diags))
ck('integrated_volume_balance',max(x['integrated_volume_error_um'] for x in diags)<1e-10)
ck('uniform_mean_wear_exact',all(abs(r['mean_wear_um']-1e-14*I['mean_pressure_Pa']*r['distance_m']*1e6)<1e-10 for r in results['uniform'][0]))
ck('uniform_peak_pressure_decreases',results['uniform'][0][-1]['pmax_MPa']<results['uniform'][0][0]['pmax_MPa'])
ck('matched_phase_wear_equals_uniform_geometry',np.max(abs(results['A50_ratio1'][5]-results['uniform'][5]))<1e-15)
ck('initial_profile_grid_agrees79',abs(results['uniform'][0][0]['pmax_MPa']-2.362593457)<.01)
# Grid/step comparison, not physical validation.
conv=[]
for name,f,r,sh in [cases[0],cases[1]]:
 for n,st in [(128,.4),(256,.4),(256,.2)]:
  v=run(name,f,r,sh,n=n,step=st);row=v[0][-1];conv.append(row);print('convergence '+name+' '+str(n)+' '+str(st),flush=True)
 for metric in ['pmax_MPa','mean_wear_um','relief_peak_to_valley_um']:
  aa=[x for x in conv if x['case']==name]
  egrid=abs(aa[0][metric]-aa[1][metric])/max(abs(aa[1][metric]),1e-12)
  estep=abs(aa[1][metric]-aa[2][metric])/max(abs(aa[2][metric]),1e-12)
  ck(name+'_grid_'+metric,egrid<.08,egrid);ck(name+'_step_'+metric,estep<.015,estep)


# Fusion of inverse pressure shaping with finite wear reserve above a recessed support.
# Stop the intended duty before the ideal clearance is consumed. Actual floor contact is audited.
recess_rows=[];recess_profiles=[];recess_diags=[];recess_final=[]
for name,f,gap,eps,end in [('P37_gap1',.375,1.,0.,40.),('P37_gap1_tol0p05',.375,1.,.05,40.),('P37_gap1_tol0p25',.375,1.,.25,40.),('P50_gap2',.5,2.,0.,80.)]:
 targets=[0.,1.6,8.,16.,40.] if end==40 else [0.,1.6,8.,16.,40.,80.]
 v=run(name,f,1,n=128,step=.4,targets=targets,recess_um=gap,perturb_um=eps)
 recess_rows+=v[0];recess_profiles+=v[1];recess_diags.append(v[2]);recess_final.append(v[0][-1])
 if eps==0:
  ck(name+'_uniform_cap_pressure',abs(v[0][-1]['pmax_MPa']-I['mean_pressure_Pa']/f/1e6)<1e-8)
  ck(name+'_no_floor_contact',all(r['B_contact_area_fraction']==0 for r in v[0]))
  ck(name+'_exact_cap_wear',abs(v[0][-1]['max_wear_um']-1e-14*I['mean_pressure_Pa']/f*end*1e6)<1e-9)
ck('recess_cases_contact_residual',max(r['max_kkt_error_um'] for r in recess_diags)<1e-7)
outcsv('recessed_support_evolution.csv',recess_rows);outcsv('recessed_support_profiles.csv',recess_profiles)
recess_design=[]
for f in [.25,.375,.5,.75]:
 for gap in [1.,2.,5.]:
  pcap=I['mean_pressure_Pa']/f
  recess_design.append({'cap_area_fraction':f,'clearance_um':gap,'uniform_cap_pressure_MPa':pcap/1e6,'distance_to_ideal_floor_contact_m':gap*1e-6/(1e-14*pcap),'local_1p6m_passes_to_ideal_floor_contact':gap*1e-6/(1e-14*pcap)/1.6,'mu_area_law_plus_other':f*30000/I['mean_pressure_Pa']+.02,'pressure_screen_pass':pcap<=3e6,'status':'exact in ideal inverse geometry only; no tolerance or finite-grain validation'})
outcsv('recess_clearance_limits.csv',recess_design)


load_rows=[];p_reference=I['mean_pressure_Pa']
for f,gap in [(.375,1.),(.5,2.)]:
 SS=Surface(128);mm=phase_mask(SS,f);pd=np.where(mm,p_reference/f,0.)
 zd=np.fft.irfft(np.fft.rfft(pd)*SS.K,SS.n)-np.where(mm,0.,gap*1e-6)
 for factor in [.5,1.,1.5,2.]:
  I['mean_pressure_Pa']=p_reference*factor;SL=Surface(128);pp,aa,ee,ll=SL.pressure(zd)
  load_rows.append({'cap_fraction':f,'nominal_loaded_clearance_um':gap,'load_factor':factor,'mean_pressure_MPa':I['mean_pressure_Pa']/1e6,'peak_pressure_MPa':float(pp.max()/1e6),'cap_contact_fraction':float(np.mean(aa&mm)),'floor_contact_fraction':float(np.mean(aa&~mm)),'pressure_screen_pass':bool(pp.max()<=3e6)})
  ck('off_design_load_balance_'+str(f)+'_'+str(factor),ll<1e-10 and ee<1e-7)
 I['mean_pressure_Pa']=p_reference
outcsv('off_design_loads.csv',load_rows)

edge_rows=[]
for n in [128,256,512]:
 SR=Surface(n);mm=phase_mask(SR,.375);pd=np.where(mm,p_reference/.375,0.)
 zz=np.fft.irfft(np.fft.rfft(pd)*SR.K,n)-np.where(mm,0.,1e-6)
 I['mean_pressure_Pa']=1.5*p_reference;SO=Surface(n);pn,an,en,ln=SO.pressure(zz)
 edge_rows.append({'grid':n,'load_factor':1.5,'cap_fraction':.375,'peak_pressure_MPa':float(pn.max()/1e6),'peak_over_E':float(pn.max()/I['E_Pa']),'interpretation':'sharp-edge model; peak is resolution dependent, not physical stress prediction'})
 ck('edge_load_balance_'+str(n),ln<1e-10 and en<1e-7)
 I['mean_pressure_Pa']=p_reference
outcsv('sharp_edge_resolution.csv',edge_rows)

cap_cost=[]
for f in [.375,.5,.875]:
 for thickness in [5.,25.]:
  area=675291.968854954*f;mass=area*thickness*1e-6*950
  cap_cost.append({'nominal_cap_coverage':f,'cap_thickness_um':thickness,'finished_cap_mass_kg':mass,'raw_cap_JPY_ex_tax_at500perkg_yield0p8':mass*500/.8,'formed_all_pad_area_m2':675291.968854954,'full_functional_depth_m':.45,'course_area_m2':2000.,'status':'no quote; support/forming/fixtures/factory/civil/tax excluded'})
outcsv('cap_material_inventory.csv',cap_cost)

# Full-contact stationary wear: k(x)*p(x) must be constant.
steady=[]
for f in [.125,.25,.5,.75,.875]:
 for ratio in [.1,1,3,10,100]:
  denom=f+(1-f)/ratio;pA=I['mean_pressure_Pa']/denom;pB=pA/ratio;loadA=f/denom;kA=1e-14/ratio
  mA=(f*I['tau_A_Pa']+(1-f)*I['tau_B_Pa'])/I['mean_pressure_Pa'];mC=loadA*.03+(1-loadA)*.30
  steady.append({'phase_A_fraction':f,'kB_over_kA':ratio,'pA_MPa':pA/1e6,'pB_MPa':pB/1e6,'A_load_fraction':loadA,'common_recession_m_per_m':kA*pA,'mu_area_law':mA,'mu_coulomb_law':mC,'peak_pressure_screen_pass':max(pA,pB)<=I['pressure_screen_Pa'],'mu_area_plus_other_screen_pass':mA+I['other_mu']<=.10})
ck('stationary_wear_equal',all(abs((1e-14/r['kB_over_kA'])*r['pA_MPa']*1e6-1e-14*r['pB_MPa']*1e6)<1e-18 for r in steady))
ck('stationary_load_balance',all(abs(r['phase_A_fraction']*r['pA_MPa']+(1-r['phase_A_fraction'])*r['pB_MPa']-I['mean_pressure_Pa']/1e6)<1e-10 for r in steady))
# Construct exact stationary profile and verify it remains stationary in shape.
S=Surface(128);mask=phase_mask(S,.125);kp=np.where(mask,1e-15,1e-14);pex=I['mean_pressure_Pa']/(kp*np.mean(1/kp));zex=np.fft.irfft(np.fft.rfft(pex)*S.K,S.n);ds=.8
pn,an,en,ln=S.pressure(zex,ds*kp*I['mean_pressure_Pa']/1e-6)
ck('stationary_profile_pressure_exact',np.max(abs(pn-pex))/I['mean_pressure_Pa']<1e-9)
ck('stationary_profile_parallel_recession',np.ptp(ds*kp*pn)<1e-18)
full_f=(I['tau_B_Pa']-(.10-.02)*I['mean_pressure_Pa'])/(I['tau_B_Pa']-I['tau_A_Pa'])
ck('all_contact_area_requirement',0<full_f<1)
# Accounting of selective finishing cost; no quote or factory design claim.
cost=[]
A=675291.968854954
for depth_um in [.1,.5,1.]:
 for speed in [5.,20.]:
  cost.append({'all_contact_area_m2':A,'removed_equivalent_thickness_um':depth_um,'captured_material_kg_if_density950':A*depth_um*1e-6*950,'hypothetical_line_width_m':1,'line_speed_m_min':speed,'availability':.7,'area_yield':.8,'processing_hours':A/(1*speed*60*.7*.8),'status':'full_depth_contact_area; no actual multiface process demonstrated'})
for n,data in [('evolution.csv',rows),('profiles.csv',profiles),('convergence.csv',conv),('stationary_phase_limits.csv',steady),('finishing_inventory.csv',cost)]:outcsv(n,data)
outj('inputs.json',I);outj('solver_diagnostics.json',diags+recess_diags);outj('checks.json',{'physical_experiments':0,'checks':checks})
summary={'cycle':81,'physical_experiments':0,'success_probability':None,'cases':len(cases),'math_numerical_checks':len(checks),'comparison_rows_excluding_profiles':len(edge_rows)+len(load_rows)+len(cap_cost)+len(recess_rows)+len(recess_design)+len(rows)+len(conv)+len(steady)+len(cost)+len(analytic),'profile_rows':len(recess_profiles)+len(profiles),'initial_uniform':rows[0],'final_cases':[results[x[0]][0][-1] for x in cases],'full_contact_phase_A_fraction_required_under_assumed_area_law':full_f,'recessed_support_final':recess_final,'constitutive_parameters_measured':False,'domain':'1D periodic bonded elastic layer; coefficients hypothetical; no thermal/water/shear-coupled/finite-grain solution','stated_goal_complete':False}
outj('summary.json',summary)
fig,axs=plt.subplots(2,2,figsize=(11,7),layout='constrained')
for name in ['uniform','A12_ratio10','A87_ratio10','A50_ratio0p1']:
 rr=results[name][0];xx=[r['distance_m'] for r in rr]
 for ax,key in zip(axs.flat,['pmax_MPa','contact_fraction','mu_area_law_plus_other','max_wear_um']):ax.plot(xx,[r[key] for r in rr],marker='o',label=name)
for ax,title,y in zip(axs.flat,['Pressure redistributes','Contact area changes','Area-law friction can rise','Wear shape is updated'],['Peak pressure [MPa]','Contact fraction','Friction + assumed other loss','Maximum wear [um]']):
 ax.set(xlabel='Accumulated local sliding distance [m]',ylabel=y,title=title);ax.grid(alpha=.2);ax.legend(fontsize=7)
axs[0,0].axhline(3,color='gray',ls='--');axs[1,0].axhline(.1,color='gray',ls='--')
fig.suptitle('Hypothetical 1D wear/contact model; no measured material performance')
fig.savefig(P/'wear_evolution.png',dpi=150);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
for name in ['uniform','A12_ratio10']:
 rr=results[name][1]
 for s in [0,160]:
  xx=[r for r in rr if r['distance_m']==s]
  axs[0].plot([r['x_um'] for r in xx],[r['height_centered_um'] for r in xx],label=f'{name} s={s}m')
  axs[1].plot([r['x_um'] for r in xx],[r['p_MPa'] for r in xx],label=f'{name} s={s}m')
for ax,title,y in zip(axs,['Centered surface height','Pressure on evolved surface'],['Height [um]','Pressure [MPa]']):
 ax.set(xlabel='Position in 190 um period [um]',ylabel=y,title=title);ax.grid(alpha=.2);ax.legend(fontsize=7)
fig.suptitle('Same effective elasticity; only wear coefficients differ between phases')
fig.savefig(P/'evolved_profiles.png',dpi=150);plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
for s in [0,40]:
 rr=[r for r in recess_profiles if r['case']=='P37_gap1' and r['distance_m']==s]
 axs[0].plot([r['x_um'] for r in rr],[r['p_MPa'] for r in rr],label=f's={s} m',ls='--' if s else '-')
 axs[1].plot([r['x_um'] for r in rr],[r['loaded_gap_um'] for r in rr],label=f's={s} m')
for ax,title,y in zip(axs,['Designed pressure on 37.5% caps','Clearance above recessed support'],['Pressure [MPa]','Loaded clearance [um]']):
 ax.set(xlabel='Position [um]',ylabel=y,title=title);ax.grid(alpha=.2);ax.legend()
fig.suptitle('Inverse-shaped ideal surface: pressure holds, but clearance is consumed')
fig.savefig(P/'recessed_support.png',dpi=150);plt.close(fig)

print(json.dumps({'checks':len(checks),'rows':summary['comparison_rows_excluding_profiles'],'profile_rows':summary['profile_rows'],'physical_experiments':0,'full_contact_min_A':full_f}))
