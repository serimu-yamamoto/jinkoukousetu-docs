"""Cycle 79: normal contact of a periodic bonded layer. No physical trials."""
from pathlib import Path
import sys, json, csv, math, itertools
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
if (ROOT/'.deps').exists(): sys.path.insert(0,str(ROOT/'.deps'))
import numpy as np
import scipy
from scipy.linalg import circulant, solve
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
I=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
checks=[]
def check(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail))
 if not ok: raise AssertionError(name+': '+str(detail))
def dump(name,rows):
 with (HERE/name).open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n"); w.writeheader(); w.writerows(rows)
def kernel(q,E,nu,d,kind='layer'):
 q=np.asarray(q,dtype=float); out=np.zeros_like(q); G=E/(2*(1+nu)); nz=q>0
 # Zero mode is constrained uniaxial compression, not a free uniaxial spring.
 k0=d*(1+nu)*(1-2*nu)/(E*(1-nu))
 if kind=='winkler': return np.full_like(q,k0)
 out[nz]=(1-nu)/(G*q[nz]); out[~nz]=k0
 if kind=='halfspace': return out
 z=q[nz]*d; a=3-4*nu; ez=np.exp(-2*z)
 # Divide numerator and denominator by exp(2z) to avoid overflow.
 ratio=(a*(1-ez*ez)/2-2*z*ez)/(a*(1+ez*ez)/2+(2*z*z+5-12*nu+8*nu*nu)*ez)
 out[nz]*=ratio
 return out

def simplex(v,total):
 u=np.sort(v)[::-1]; css=np.cumsum(u)-total
 r=np.nonzero(u-css/(np.arange(len(v))+1)>0)[0][-1]
 return np.maximum(v-css[r]/(r+1),0)

def contact(E,nu,d,kind,n=256,profile_override=None):
 L=I['period_um']*1e-6; x=np.arange(n)*L/n
 z=(I['short_amplitude_um']*np.cos(2*np.pi*x/(I['ripple_wavelength_um']*1e-6))+I['long_amplitude_um']*np.cos(2*np.pi*x/L))*1e-6
 if profile_override is not None: z=np.asarray(profile_override,dtype=float)
 q=2*np.pi*np.fft.rfftfreq(n,L/n); K=kernel(q,E,nu,d,kind)
 pbar=I['mean_pressure_Pa']; hs=1e-6
 kh=K*pbar/hs; kh[0]=1.0 # fixed mean pressure makes zero mode irrelevant to contact distribution
 C=circulant(np.fft.irfft(kh,n)); C=(C+C.T)/2
 hh=z/hs
 # FISTA with projection onto nonnegative pressures of prescribed total load.
 xx=np.ones(n); yy=xx.copy(); tt=1.; lip=max(kh)
 for it in range(15000):
  grad=np.fft.irfft(np.fft.rfft(yy)*kh,n)-hh
  xn=simplex(yy-grad/lip,n); tn=(1+np.sqrt(1+4*tt*tt))/2
  yy=xn+(tt-1)/tn*(xn-xx); xx=xn; tt=tn
  if it%100==99:
   gg=C@xx-hh; A=xx>1e-8; lam=np.mean(gg[A]); res=max(np.max(np.abs(gg[A]-lam)),max(0,float(np.max(lam-gg[~A]))) if np.any(~A) else 0)
   if res<1e-9: break
 # Polish the contact active set, keeping unilateral/equality constraints.
 A=np.flatnonzero(xx>1e-7)
 for polish in range(n*2):
  ca=C[np.ix_(A,A)]; uv=solve(ca,np.column_stack([hh[A],np.ones(len(A))]),assume_a='pos')
  lag=(uv[:,0].sum()-n)/uv[:,1].sum(); pa=uv[:,0]-lag*uv[:,1]
  if pa.min() < -1e-8:
   A=np.delete(A,np.argmin(pa)); continue
  xx=np.zeros(n); xx[A]=np.maximum(pa,0); gg=C@xx-hh; B=np.setdiff1d(np.arange(n),A)
  if len(B) and gg[B].min() < -lag-1e-9:
   A=np.sort(np.append(A,B[np.argmin(gg[B])])); continue
  break
 else: raise RuntimeError('Active set did not converge')
 gg=C@xx-hh; A=xx>1e-8; lam=np.mean(gg[A]); gap=gg-lam
 err=max(np.max(np.abs(gap[A])),max(0,float(-gap[~A].min())) if np.any(~A) else 0)
 pp=xx*pbar; phi=float(np.count_nonzero(A)/n)
 physical_u=np.fft.irfft(np.fft.rfft(pp)*K,n)
 mean_u=float(K[0]*pbar) if kind!='halfspace' else None
 row=dict(model=kind,E_MPa=E/1e6,nu=nu,d_um=d*1e6,grid=n,contact_fraction_1D=phi,pmax_MPa=float(pp.max()/1e6),mean_pressure_MPa=pbar/1e6,normal_gap_min_um=float(gap.min()),normal_gap_max_um=float(gap.max()),kkt_error_um=float(err),relative_load_error=float(abs(xx.sum()/n-1)),mean_compression_um=mean_u*1e6 if mean_u is not None else '',mean_compression_over_thickness=mean_u/d if mean_u is not None else '',surface_displacement_range_over_d=float(np.ptp(physical_u)/d),max_profile_slope=float(np.max(np.abs(np.gradient(z,L/n)))))
 # These are screening diagnostics, not strain-field or small-strain proof.
 row['peak_pressure_over_E']=float(pp.max()/E)
 row['profile_amplitude_over_d']=float(np.max(np.abs(z))/d)
 row['small_deformation_diagnostic']=bool(row['surface_displacement_range_over_d']<=.1 and row['peak_pressure_over_E']<=.1 and row['profile_amplitude_over_d']<=.1 and (mean_u is None or mean_u/d<=.1))
 row['tau_max_kPa_for_mu0p1_other0p02']=float((.1-.02)*pbar/phi/1000)
 return row,dict(x=x,z=z,p=pp,gap=gap,K=K)

# Independent limit/units checks of the linear response.
E=30e6; nu=.49; d=10e-6
for nnu in [.3,.49,.5]:
 q=np.array([1e2,1e5,1e8]); kk=kernel(q,E,nnu,d)
 check('kernel_positive_nu_'+str(nnu),np.all(kk>0))
 check('thick_limit_nu_'+str(nnu),abs(kk[-1]/kernel(q,E,nnu,d,'halfspace')[-1]-1)<1e-12)
 if nnu<.5:
  k0=d*(1+nnu)*(1-2*nnu)/(E*(1-nnu))
  check('thin_compressible_limit_'+str(nnu),abs(kk[0]/k0-1)<1e-4)
 else:
  asym=d**3*q[0]**2/(3*(E/3))
  check('thin_incompressible_limit',abs(kk[0]/asym-1)<1e-4)
check('modulus_inverse_scaling',np.allclose(kernel(np.array([1e5]),2*E,nu,d)*2,kernel(np.array([1e5]),E,nu,d),rtol=1e-12,atol=0))
check('zero_mode_constrained_compression',abs(kernel(np.array([0.]),E,nu,d)[0]-d/(E*(1-nu)/((1+nu)*(1-2*nu))))<1e-25)

Ltest=I['period_um']*1e-6; xtest=np.arange(128)*Ltest/128
rr,pr=contact(30e6,.49,10e-6,'layer',128,1e-9*np.cos(2*np.pi*xtest/Ltest))
panalytic=I['mean_pressure_Pa']+1e-9/kernel(np.array([2*np.pi/Ltest]),30e6,.49,10e-6)[0]*np.cos(2*np.pi*xtest/Ltest)
check('full_contact_sinusoid_vs_exact_pressure',np.max(np.abs(pr['p']-panalytic))/I['mean_pressure_Pa']<1e-9)
rr,pr=contact(30e6,.49,10e-6,'layer',128,np.zeros(128))
check('flat_full_contact_uniform',np.max(np.abs(pr['p']/I['mean_pressure_Pa']-1))<1e-10)
check('uniform_displacement_matches_constrained_modulus',abs(rr['mean_compression_um']-kernel(np.array([0.]),30e6,.49,10e-6)[0]*I['mean_pressure_Pa']*1e6)<1e-12)

modes=[]
for lam,dum,nnu,Empa in itertools.product([47.5,190],[2,5,10,25,50],[.3,.49,.5],[10,30,100]):
 q=2*np.pi/(lam*1e-6); kval=kernel(np.array([q]),Empa*1e6,nnu,dum*1e-6)[0]; half=kernel(np.array([q]),Empa*1e6,nnu,dum*1e-6,'halfspace')[0]
 amp=.25e-6; pp=amp/kval
 modes.append(dict(wavelength_um=lam,d_um=dum,nu=nnu,E_MPa=Empa,compliance_m_Pa=kval,ratio_to_halfspace=kval/half,pressure_amplitude_MPa=pp/1e6,single_mode_full_contact=pp<=I['mean_pressure_Pa'],Emax_MPa_for_single_mode_full_contact=Empa*I['mean_pressure_Pa']/pp))
dump('mode_response.csv',modes)
rows=[]; profiles={}
for kind,Empa,dum in itertools.product(['layer','winkler'],I['E_MPa'],I['thickness_um']):
 row,prof=contact(Empa*1e6,I['nu'],dum*1e-6,kind,I['grid']); rows.append(row)
 if kind=='layer' and Empa==30 and dum in [2,10,25,50]: profiles[str(dum)]=prof
for Empa in I['E_MPa']:
 row,prof=contact(Empa*1e6,I['nu'],50e-6,'halfspace',I['grid']);rows.append(row)
 if Empa==30:profiles['halfspace']=prof
check('all_contacts_KKT',max(r['kkt_error_um'] for r in rows)<1e-7)
check('all_contacts_load',max(r['relative_load_error'] for r in rows)<1e-10)
check('contact_fractions_range',all(0<r['contact_fraction_1D']<=1 for r in rows))
check('peak_above_mean',all(r['pmax_MPa']>=r['mean_pressure_MPa']-1e-9 for r in rows))
check('area_pressure_lower_bound',all(r['pmax_MPa']*r['contact_fraction_1D']>=r['mean_pressure_MPa']-1e-9 for r in rows))
dump('contact_results.csv',rows)
conv=[]
for dum in [2,10,25]:
 for n in [128,256,512]:
  row,pr=contact(30e6,I['nu'],dum*1e-6,'layer',n);conv.append(row)
for dum in [2,10,25]:
 a=[r for r in conv if abs(r['d_um']-dum)<1e-8 and r['grid']==256][0];b=[r for r in conv if abs(r['d_um']-dum)<1e-8 and r['grid']==512][0]
 check('grid_peak_256_512_d'+str(dum),abs(a['pmax_MPa']/b['pmax_MPa']-1)<.03)
 check('grid_contact_fraction_d'+str(dum),abs(a['contact_fraction_1D']-b['contact_fraction_1D'])<.025)
dump('grid_convergence.csv',conv)
# Split short-scale texture from long-scale height error: tolerances are hypotheses.
scale_rows=[]
L=I['period_um']*1e-6; xx=np.arange(I['grid'])*L/I['grid']
for dum,long_amp in itertools.product([10,25],[0,.05,.1,.25]):
 zz=(.25*np.cos(2*np.pi*xx/(47.5e-6))+long_amp*np.cos(2*np.pi*xx/L))*1e-6
 r,pr=contact(30e6,.49,dum*1e-6,'layer',I['grid'],zz);r['long_amplitude_um']=long_amp;scale_rows.append(r)
check('scale_split_load_and_KKT',all(r['relative_load_error']<1e-10 and r['kkt_error_um']<1e-7 for r in scale_rows))
dump('scale_separation.csv',scale_rows)
profile_rows=[]
for key,pr in profiles.items():
 for j in range(I['grid']): profile_rows.append(dict(case=key,x_um=pr['x'][j]*1e6,height_um=pr['z'][j]*1e6,pressure_MPa=pr['p'][j]/1e6,gap_um=pr['gap'][j]))
dump('pressure_profiles.csv',profile_rows)

skins=[]
for lam,dum,ts,Empa in itertools.product([47.5,190],[5,10,25],[.2,1,3,5],[10,30,100]):
 q=2*np.pi/(lam*1e-6); K=kernel(np.array([q]),Empa*1e6,I['nu'],dum*1e-6)[0]; B=1e9*(ts*1e-6)**3/(12*(1-.35**2)); ratio=1/(1+B*q**4*K)
 skins.append(dict(wavelength_um=lam,substrate_d_um=dum,substrate_E_MPa=Empa,skin_t_um=ts,skin_E_GPa=1,skin_nu=.35,plate_stiffening_Bq4K=B*q**4*K,retained_compliance_ratio=ratio,skin_t_over_wavelength=ts/lam,thin_plate_screen=ts/lam<=.05,measured_composite=False))
check('skin_reduces_normal_compliance',all(0<r['retained_compliance_ratio']<=1 for r in skins))
dump('skin_stiffening.csv',skins)
# Coupling magnitude diagnostic from Menga et al. eqs. 9-11 and 21.
# Not a solved frictional contact; no Coulomb coefficient is inferred.
coupling=[]
for lam,dum,nnu,muc in itertools.product([47.5,190],[2,5,10,25,50],[.3,.49,.5],[.03,.1,.3]):
 q=2*np.pi/(lam*1e-6); zz=q*dum*1e-6; ez=np.exp(-2*zz); den=(3-4*nnu)*(1+ez*ez)/2+(2*zz*zz+5-12*nnu+8*nnu*nnu)*ez
 C=4*(1-nnu)*(2+zz*zz-6*nnu+4*nnu*nnu)*ez/den
 S12=(1+nnu)*(C-(1-2*nnu))
 S22=kernel(np.array([q]),1,nnu,dum*1e-6)[0]*q
 eta=muc*abs(S12)/S22
 coupling.append(dict(wavelength_um=lam,d_um=dum,nu=nnu,mu_c_assumed=muc,normal_tangential_kernel_ratio=eta,below_0p1_diagnostic=eta<.1,not_a_friction_solution=True))
check('coupling_finite',all(math.isfinite(r['normal_tangential_kernel_ratio']) for r in coupling))
dump('coupling_diagnostic.csv',coupling)

cost=[];throughput=[]
for area,dum,ts in itertools.product([2000,20000],[5,10,25,50],[0,1,3]):
 N=I['grains_at_2000m2']*area/2000; A=N*I['pads_per_grain']*(I['pad_side_um']*1e-6)**2
 mass=A*(dum+ts)*1e-6*I['coating_density_kg_m3']; raw=mass*I['raw_price_JPY_kg']/I['mass_yield']
 cost.append(dict(area_m2=area,substrate_d_um=dum,skin_t_um=ts,coated_pad_area_m2=A,finished_added_mass_kg=mass,assumed_raw_JPY_kg=I['raw_price_JPY_kg'],yield_fraction=I['mass_yield'],raw_only_JPY_excl_tax=raw,full_installed_cost=False))
 for width,speed in itertools.product([.5,1],[5,20]):
  hrs=A/(width*speed*60*.7*.8)
  throughput.append(dict(area_m2=area,d_um=dum,skin_t_um=ts,width_m=width,speed_m_min=speed,availability=.7,area_yield=.8,operating_clock_hours=hrs,year4000h_line_equivalents=hrs/4000))
check('cost_scaling_10x',abs(cost[12]['finished_added_mass_kg']/cost[0]['finished_added_mass_kg']-10)<1e-10)
dump('material_cost.csv',cost);dump('coating_throughput.csv',throughput)

fric=[]
for row in rows:
 if row['model']!='layer':continue
 for tau in [.03,.1,.3]:
  fric.append(dict(E_MPa=row['E_MPa'],d_um=row['d_um'],contact_fraction_1D=row['contact_fraction_1D'],tau_assumed_MPa=tau,mu_interface_only=tau*1e6*row['contact_fraction_1D']/I['mean_pressure_Pa'],predicted_ski_mu=False))
dump('area_shear_tradeoff.csv',fric)
check('tau_budget_identity',all(abs(r['tau_max_kPa_for_mu0p1_other0p02']*1000*r['contact_fraction_1D']/I['mean_pressure_Pa']-.08)<1e-12 for r in rows))
# Frequency is a sampling requirement, not a viscoelastic simulation.
frequency=[]
for v,lam in itertools.product([.1,2,5,10],[47.5,190,1000]):frequency.append(dict(speed_m_s=v,wavelength_um=lam,passage_frequency_Hz=v/(lam*1e-6),not_storage_modulus_measurement=True))
dump('frequency_requirements.csv',frequency)

plt.rcParams.update({'font.size':10})
fig,axs=plt.subplots(2,2,figsize=(12,8),layout='constrained')
for dum,key in [(2,'2'),(10,'10'),(25,'25'),(50,'50')]:
 pr=profiles[key];axs[0,0].plot(pr['x']*1e6,pr['p']/1e6,label=f'{dum} um')
axs[0,0].set(xlabel='Position within periodic patch (um)',ylabel='Normal pressure (MPa)',title='30 MPa elastic layer; nu=0.49');axs[0,0].legend(ncol=2)
for kind,style in [('layer','-o'),('winkler','--s')]:
 rr=[r for r in rows if r['model']==kind and r['E_MPa']==30]
 axs[0,1].plot([r['d_um'] for r in rr],[r['contact_fraction_1D'] for r in rr],style,label=kind)
axs[0,1].axhline([r for r in rows if r['model']=='halfspace' and r['E_MPa']==30][0]['contact_fraction_1D'],color='k',linestyle=':',label='half-space')
axs[0,1].set(xlabel='Layer thickness (um)',ylabel='Contact fraction in 1-D patch',ylim=(0,1.05),title='Boundary conditions change the answer');axs[0,1].legend()
for tau in [.03,.1,.3]:
 rr=[r for r in fric if r['E_MPa']==30 and r['tau_assumed_MPa']==tau]
 axs[1,0].plot([r['d_um'] for r in rr],[r['mu_interface_only'] for r in rr],'-o',label=f'tau = {tau} MPa')
axs[1,0].axhline(.1,color='k',linestyle=':');axs[1,0].set(xlabel='Layer thickness (um)',ylabel='Interface shear contribution only',title='More contact can increase dry friction');axs[1,0].legend()
rr=[r for r in cost if r['area_m2']==2000 and r['skin_t_um']==1]
axs[1,1].plot([r['substrate_d_um'] for r in rr],[r['raw_only_JPY_excl_tax']/1e6 for r in rr],'-o')
axs[1,1].set(xlabel='Layer thickness + 1 um skin (um)',ylabel='Raw material only (million JPY)',title='2,000 m2 bed; all six pads on every grain')
fig.suptitle('Cycle 79 | assumed materials; normal contact model, not ski validation',fontsize=14)
fig.savefig(HERE/'layer_tradeoffs.png',dpi=180);plt.close(fig)

fig,ax=plt.subplots(figsize=(11,5),layout='constrained');ax.set(xlim=(0,11),ylim=(0,5));ax.axis('off')
from matplotlib.patches import Rectangle, FancyArrowPatch, Polygon
ax.add_patch(Rectangle((.5,1.2),4.2,.8,color='#7c8995'));ax.text(2.6,1.6,'Rigid local branch support',ha='center',color='white')
ax.add_patch(Rectangle((.5,2),4.2,.65,color='#75b7a5'));ax.text(2.6,2.28,'Continuous elastic layer',ha='center')
xx=np.linspace(.5,4.7,200); yy=2.75+.1*np.cos(8*np.pi*(xx-.5)/4.2)
ax.fill_between(xx,2.6,yy,color='#75b7a5');ax.plot(xx,yy,color='#375b9b',lw=6);ax.text(2.6,3.15,'Optional low-shear skin: changes stiffness',ha='center')
ax.plot([.4,4.8],[3.6,3.6],color='black',lw=5);ax.text(2.6,4.0,'Ski / normal contact',ha='center')
ax.text(.5,.45,'Local pad section only; thickness exaggerated.\nNo sliding joint, no oil-filled cavity.',fontsize=10)
# Open particle is a functional drawing, not CAD or an isotropic packing model.
center=np.array([8.3,2.7]);
for angle in [0,60,120,180,240,300]:
 a=np.deg2rad(angle);end=center+1.55*np.array([np.cos(a),np.sin(a)])
 ax.plot([center[0],end[0]],[center[1],end[1]],color='#7c8995',lw=14,solid_capstyle='round');ax.plot(end[0],end[1],'o',ms=17,color='#75b7a5')
ax.text(8.3,4.6,'Pads on an open free particle',ha='center');ax.text(8.3,.5,'Keep gaps between branches open.\nDo not form a continuous course mat.',ha='center')
ax.annotate('Functional idea H79-L\nFinite edges / 3-D not solved',xy=(8.3,2.7),xytext=(6,.95),fontsize=9,arrowprops=dict(arrowstyle='->'))
fig.suptitle('One-piece layer alternative; shape, bonding and wear remain unproven',fontsize=14)
fig.savefig(HERE/'concept.png',dpi=180);plt.close(fig)

counts={p.name:sum(1 for _ in csv.DictReader(p.open(encoding='utf-8'))) for p in HERE.glob('*.csv')}
summary=dict(cycle=79,physical_trials=0,success_probability=None,math_checks=len(checks),row_counts=counts,comparison_rows_excluding_profile_samples=sum(v for k,v in counts.items() if k!='pressure_profiles.csv'),profile_samples=counts['pressure_profiles.csv'],key_contacts=[r for r in rows if r['E_MPa']==30],key_skin=[r for r in skins if r['substrate_E_MPa']==30 and r['substrate_d_um']==10 and r['wavelength_um']==47.5],key_cost=[r for r in cost if r['area_m2']==2000 and r['skin_t_um']==1],scope='1-D normal elastic contact; zero physical experiments; completed material and friction unproven')
(HERE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');(HERE/'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(HERE/'requirements.txt').write_text('numpy=='+np.__version__+'\nscipy=='+scipy.__version__+'\nmatplotlib=='+matplotlib.__version__+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(checks=len(checks),rows=counts,physical_trials=0,success_probability=None)))
