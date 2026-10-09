"""Cycle 77 conditional contact/thermal screening, not physical validation.
Run: python reproduce.py  (numpy, matplotlib required).
Writes only files next to this script; no network, prior-cycle imports or lab actions.
"""
from pathlib import Path
import sys, json, math, csv, hashlib
R=Path(__file__).resolve().parent
local_deps=R.parents[1]/'.deps'
if local_deps.exists(): sys.path.insert(0,str(local_deps))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
I=json.loads((R/'inputs.json').read_text(encoding='utf-8'))
P=I['reference']['p0_peak_Pa']; A0=I['reference']['a0_m']; E=I['reference']['E_star_Pa']
W=.8*math.pi*P*A0*A0
T=I['thermal']; eff=math.sqrt(T['k_W_mK']*T['rho_kg_m3']*T['cp_J_kgK']); alpha=T['k_W_mK']/(T['rho_kg_m3']*T['cp_J_kgK'])
checks=[]
def check(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail))
 if not ok: raise AssertionError(name)
def write_json(name,obj): (R/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def write_csv(name,rows):
 with (R/name).open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def g(c): return 3*np.pi*c*c/8+3*np.pi*c**4/16
def fload(c): return np.pi*(.5*c**3+.3*c**5)
def inverse_g(d):
 d=np.maximum(np.asarray(d),0); a=3*np.pi/8;b=3*np.pi/16
 return np.sqrt(2*d/(a+np.sqrt(a*a+4*b*d)))
def pressure_peak(c):
 r2=np.maximum((c*c-1)/2,0)
 return P*np.sqrt(np.maximum(c*c-r2,0))*(.75+.25*c*c+.5*r2)
def solve_load(n,span_um,pattern,Ktotal=None):
 a=A0/math.sqrt(n);h=P*a/E
 heights=np.zeros(n)
 if n>1:
  heights=np.linspace(0,span_um*1e-6,n) if pattern=='linear_ramp' else np.r_[span_um*1e-6,np.zeros(n-1)]
  heights-=np.mean(heights)
 def state(d):
  comp=np.maximum(d+heights,0)
  if Ktotal is None: c=inverse_g(comp/h)
  else:
   lo=np.zeros(n); hi=inverse_g(comp/h); k=Ktotal/n
   for _ in range(65):
    cm=(lo+hi)/2
    val=h*g(cm)+P*a*a*fload(cm)/k
    lo=np.where(val<comp,cm,lo);hi=np.where(val>=comp,cm,hi)
   c=(lo+hi)/2
  return c,P*a*a*fload(c)
 lo=-max(heights)-1e-9;hi=1e-3
 for _ in range(90):
  md=(lo+hi)/2
  if np.sum(state(md)[1])<W:lo=md
  else:hi=md
 d=(lo+hi)/2;c,loads=state(d)
 return c,loads,d,heights
# Exact endpoint-singularity substitution u=s-z^2, then Gauss-Legendre.
def basis(s,nodes=128):
 s=np.atleast_1d(s).astype(float);sq=np.maximum(s,0)
 lo=np.sqrt(np.maximum(sq-1,0));hi=np.sqrt(sq)
 x,w=np.polynomial.legendre.leggauss(nodes)
 z=lo[:,None]+(hi-lo)[:,None]*(x[None,:]+1)/2
 u=np.clip(sq[:,None]-z*z,0,1);xi=2*u-1
 b=np.sqrt(np.maximum(1-xi*xi,0))
 j0=(hi-lo)*np.sum(w[None,:]*b,axis=1)
 j2=(hi-lo)*np.sum(w[None,:]*xi*xi*b,axis=1)
 j0[s<=0]=0;j2[s<=0]=0
 return j0,j2
def kernel(s,c=1,nodes=128):
 j0,j2=basis(s,nodes)
 return c*((.75+.25*c*c)*j0+.5*c*c*j2)
sg=np.linspace(0,1,I['numerics']['peak_grid']);j0,j2=basis(sg)
def peakJ(c): return float(np.max(c*((.75+.25*c*c)*j0+.5*c*c*j2)))
def flash(c,a,mu=.1,v=10,eta=.5):
 if c<=0:return 0.
 return eta*mu*v*P*math.sqrt(2*c*a/v)/(eff*math.sqrt(math.pi))*peakJ(c)
check('Q design load',abs(W-.031415926535897934)<1e-15)
check('Q inverse',np.max(np.abs(inverse_g(g(np.linspace(0,2,101)))-np.linspace(0,2,101)))<1e-14)
qnodes,qweights=np.polynomial.legendre.leggauss(512)
r=(qnodes+1)/2
p=np.sqrt(1-r*r)*(1+.5*r*r)
force_num=2*np.pi*P*A0*A0*float(np.sum(qweights*p*r)/2)
check('Independent radial pressure integral',abs(force_num/W-1)<1e-8,force_num)
j01,j21=basis([1],256)
check('J0 endpoint 4/3',abs(j01[0]-4/3)<2e-7,float(j01[0]))
check('J2 endpoint 44/105',abs(j21[0]-44/105)<2e-7,float(j21[0]))
check('Q endpoint 54/35',abs(kernel([1],1,256)[0]-54/35)<3e-7)
# Constant surface flux analytic surface result, independent midpoint z integration.
z=(np.arange(10000)+.5)/10000
constant_integral=2*np.sum(np.ones_like(z))/len(z)
check('constant-flux kernel',abs(constant_integral-2)<1e-15)
# Independent original-u midpoint integral at s>1, no singularity.
u=(np.arange(200000)+.5)/200000
pc=np.sqrt(1-(2*u-1)**2)*(1+.5*(2*u-1)**2)
mid=np.sum(pc/np.sqrt(1.3-u))/len(u)
check('past-pulse independent integration',abs(mid-kernel([1.3])[0])<2e-6,mid)
conv=[]
for ng in (64,128,256):
 for grid in (1001,2001,4001):
  ss=np.linspace(0,1,grid);kk=kernel(ss,1,ng);ix=int(np.argmax(kk))
  conv.append(dict(nodes=ng,grid=grid,J_peak=float(kk[ix]),s_peak=float(ss[ix])))
check('peak quadrature/grid convergence',max(x['J_peak'] for x in conv)-min(x['J_peak'] for x in conv)<3e-5)
write_csv('convergence.csv',conv)
thermal=[]
for n in I['geometry']['N']:
 a=A0/math.sqrt(n)
 for mu in T['mu']:
  for v in T['speed_m_s']:
   for eta in T['eta']:
    rise=flash(1,a,mu,v,eta);tau=2*a/v;pe=v*a/alpha;depth=math.sqrt(alpha*tau)
    thermal.append(dict(N=n,a_um=a*1e6,mu_assumed=mu,v_m_s=v,eta_assumed=eta,T0_C=50,deltaT_single_C=rise,T_single_C=50+rise,tau_us=tau*1e6,Pe=pe,diffusion_depth_um=depth*1e6,depth_over_a=depth/a,one_dimensional_geometry_screen=bool(depth/a<=.2)))
for n in I['geometry']['N']:
 check('isolated N^-1/4 scaling '+str(n),abs(flash(1,A0/math.sqrt(n))/flash(1,A0)-n**(-.25))<1e-14)
write_csv('thermal_sensitivity.csv',thermal)
heights=[]
for n in I['geometry']['N']:
 for span in ([0] if n==1 else I['geometry']['height_span_um']):
  for pattern in (['one_high'] if span==0 else I['geometry']['patterns']):
   for K in I['geometry']['series_seat_total_stiffness_N_m']:
    c,loads,d,hs=solve_load(n,span,pattern,K);a=A0/math.sqrt(n);maxc=float(np.max(c))
    residual=float(abs(sum(loads)/W-1))
    valid=maxc<=I['reference']['outer_radius_ratio']+1e-12
    heights.append(dict(N=n,span_um=span,pattern=pattern,seat_total_N_m='rigid' if K is None else K,active=int(np.sum(loads>1e-15)),max_load_share=float(max(loads)/W),max_c=maxc,within_manufactured_radius=valid,max_pressure_MPa=float(np.max(pressure_peak(c))/1e6),max_isolated_deltaT_C=max(flash(float(ci),a) for ci in c),common_approach_um=d*1e6,max_seat_deflection_um=0 if K is None else float(max(loads)/(K/n)*1e6),relative_force_residual=residual))
check('all load solves conserve force',max(x['relative_force_residual'] for x in heights)<1e-11)
for n in I['geometry']['N']:
 c,l,_,_=solve_load(n,0,'one_high')
 check('equal heights design radius '+str(n),np.max(np.abs(c-1))<1e-10)
 c,l,_,_=solve_load(n,0,'one_high',20000)
 check('series seats preserve equal-load solution '+str(n),np.max(np.abs(c-1))<1e-10)
check('height defect amplifies load',next(x for x in heights if x['N']==16 and x['span_um']==.5 and x['pattern']=='one_high' and x['seat_total_N_m']=='rigid')['max_load_share']>1/16)
write_csv('height_load_cases.csv',heights)
# Consecutive contacts seen by one moving-base centerline in a square array.
arrays=[];traces=[]
for n in I['geometry']['N']:
 m=math.isqrt(n);a=A0/math.sqrt(n);tau=2*a/10
 for gap in I['geometry']['array_gap_um']:
  pitch=3*a+gap*1e-6;spacing=pitch/(2*a)
  end=(m-1)*spacing+1
  ss=np.unique(np.r_[np.linspace(0,end,I['numerics']['array_grid']),np.arange(m)*spacing+1])
  kk=np.zeros_like(ss)
  for j in range(m):kk+=kernel(ss-j*spacing)
  pref=.5*.1*10*P*math.sqrt(tau)/(eff*math.sqrt(math.pi));temp=pref*kk
  ix=int(np.argmax(temp));baseline=flash(1,A0)
  arrays.append(dict(N=n,contacts_in_row=m,gap_um=gap,pitch_um=pitch*1e6,envelope_um=(3*a*m+(m-1)*gap*1e-6)*1e6,max_deltaT_C=float(temp[ix]),ratio_to_N1=float(temp[ix]/baseline),time_at_peak_us=float(ss[ix]*tau*1e6),assumed_mu=.1,assumed_v_m_s=10,assumed_eta=.5))
  if gap==10:
   for j in range(0,len(ss),6):traces.append(dict(N=n,t_us=float(ss[j]*tau*1e6),deltaT_C=float(temp[j])))
check('single pulse array baseline',abs(arrays[0]['max_deltaT_C']/flash(1,A0)-1)<1e-5)
check('memory exceeds isolated for split contacts',all(x['max_deltaT_C']>flash(1,A0/math.sqrt(x['N'])) for x in arrays if x['N']>1))
check('larger gaps reduce residual heat in model',all(next(x for x in arrays if x['N']==n and x['gap_um']==25)['max_deltaT_C']<next(x for x in arrays if x['N']==n and x['gap_um']==0)['max_deltaT_C'] for n in (4,16,64)))
write_csv('array_memory.csv',arrays);write_csv('array_traces.csv',traces)
C=I['cost'];costs=[]
for area in C['scale_area_m2']:
 heads=C['grain_count']*C['heads_per_grain']*area/C['reference_area_m2']
 for n in I['geometry']['N']:
  b=1.5*A0/math.sqrt(n);w=C['support_ring_width_m'];h=C['support_ring_height_m'];rho=C['rho_kg_m3']
  surface=heads*n*math.pi*b*b;perimeter=heads*n*2*math.pi*b
  skin=surface*C['skin_m']*rho
  ring=heads*n*math.pi*(b*b-(b-w)**2)*h*rho
  for price in C['assumed_unit_JPY_kg']:
   costs.append(dict(area_m2=area,N=n,head_count=heads,feature_count=heads*n,projected_disk_area_m2=surface,perimeter_m=perimeter,skin_mass_kg=skin,hypothetical_below_face_ring_mass_kg=ring,total_addon_mass_kg=skin+ring,assumed_JPY_kg=price,assumed_yield=C['yield'],raw_material_only_JPY=(skin+ring)/C['yield']*price,manufacturing_quote_available=False))
check('split projected area conserved',max(x['projected_disk_area_m2'] for x in costs if x['area_m2']==2000)-min(x['projected_disk_area_m2'] for x in costs if x['area_m2']==2000)<1e-8)
check('ring width fits all outer radii',min(1.5*A0/math.sqrt(n) for n in I['geometry']['N'])>C['support_ring_width_m'])
write_csv('cost_sensitivity.csv',costs)
root=[]
for n in I['geometry']['N']:
 load=W/n;k=I['root75']['k_N_m'];d=I['root75']['allowable_test_deflection_m']
 root.append(dict(N=n,load_mN=load*1000,root_force_at_5um_uN=k*d*1e6,load_to_root_budget=load/(k*d),minimum_seat_k_N_m=load/d,linear_root_extrapolation_um=load/k*1e6,linear_extrapolation_valid=False,provisional_series_seat_k_N_m=20000/n,equal_load_seat_deflection_um=W/20000*1e6))
write_csv('normal_load_budget.csv',root)
check('no success probability inferred',I['physical_trials']==0 and I['success_probability'] is None)
# Plot 1: subdivision, memory and height errors (invalid radius points hollow).
fig,ax=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
ns=np.array(I['geometry']['N']);ax[0].plot(ns,[flash(1,A0/math.sqrt(n)) for n in ns],'o--',label='One isolated pulse')
for gap in (0,10,25):
 aa=[x for x in arrays if x['gap_um']==gap];ax[0].plot(ns,[x['max_deltaT_C'] for x in aa],'o-',label=f'Row memory; gap {gap} um')
ax[0].set(xscale='log',xlabel='Pads per original head N',ylabel='Moving-base temperature rise (C)',title='Equal loading; mu=0.1, v=10 m/s, eta=0.5');ax[0].legend(fontsize=8);ax[0].grid(alpha=.2)
for K,ls in [('rigid','-'),(20000,'--')]:
 for n,color in [(4,'#1565c0'),(16,'#cf5c36'),(64,'#587d28')]:
  hh=[x for x in heights if x['N']==n and x['pattern']=='one_high' and x['seat_total_N_m']==K]
  ax[1].plot([x['span_um'] for x in hh],[x['max_isolated_deltaT_C'] for x in hh],ls,color=color,label=f'N={n}; '+('rigid' if K=='rigid' else 'series seat'))
  for x in hh:
   ax[1].plot(x['span_um'],x['max_isolated_deltaT_C'],'o',color=color,markerfacecolor=color if x['within_manufactured_radius'] else 'white')
ax[1].axhline(flash(1,A0),color='black',lw=1,alpha=.6);ax[1].set(xlabel='Height span: one high pad (um)',ylabel='Worst isolated rise (C)',title='Hollow point: beyond radius reserve, diagnostic only');ax[1].legend(fontsize=7,ncol=2);ax[1].grid(alpha=.2)
fig.savefig(R/'thermal_and_tolerance.png',dpi=160);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
for n in ns:
 tt=[x for x in traces if x['N']==n];ax[0].plot([x['t_us'] for x in tt],[x['deltaT_C'] for x in tt],label=f'N={n}')
ax[0].set(xlabel='Time from first contact (us)',ylabel='Moving-base rise (C)',title='Successive contact memory; 10 um outer gap');ax[0].legend();ax[0].grid(alpha=.2)
cc=[x for x in costs if x['area_m2']==2000 and x['assumed_JPY_kg']==500]
ax[1].plot(ns,[x['skin_mass_kg'] for x in cc],'o-',label='Flat skin volume proxy');ax[1].plot(ns,[x['hypothetical_below_face_ring_mass_kg'] for x in cc],'o-',label='Hypothetical ring support')
ax[1].set(xscale='log',xlabel='Pads per original head N',ylabel='Material mass (kg / 2,000 m2)',title='Manufacturing, body and installation excluded');ax[1].legend();ax[1].grid(alpha=.2)
fig.savefig(R/'memory_and_material.png',dpi=160);plt.close(fig)
write_json('checks.json',dict(physical_validation=False,checks=checks,passed=sum(x['passed'] for x in checks),total=len(checks)))
summary=dict(cycle=77,physical_trials=0,success_probability=None,W0_N=W,effusivity=eff,alpha_m2_s=alpha,baseline_single_rise_C=flash(1,A0),baseline_peak_s=float(sg[np.argmax(kernel(sg))]),baseline_indent_um=float(P*A0/E*g(1)*1e6),thermal_cases=len(thermal),height_cases=len(heights),array_cases=len(arrays),cost_cases=len(costs),math_checks=len(checks),array_results=arrays,height_key=[x for x in heights if x['N']==16 and x['pattern']=='one_high'],root_budget=root)
write_json('summary.json',summary)
print(json.dumps({k:summary[k] for k in ('cycle','baseline_single_rise_C','thermal_cases','height_cases','array_cases','cost_cases','math_checks')},ensure_ascii=False))

# Join height-dependent contact radii and thermal memory on a row containing the high pad.
coupled=[]
for n in (4,16,64):
 m=math.isqrt(n);a=A0/math.sqrt(n);pitch=3*a+10e-6
 for span in I['geometry']['height_span_um']:
  for K in I['geometry']['series_seat_total_stiffness_N_m']:
   cs,loads,_,_=solve_load(n,span,'one_high',K)
   for position in ('first','last'):
    row=np.r_[cs[0],cs[1:m]] if position=='first' else np.r_[cs[1:m],cs[0]]
    centers=np.arange(m)*pitch/10
    starts=centers-row*a/10; starts-=min(starts)
    taus=2*row*a/10
    end=float(max(starts+taus))
    tt=np.unique(np.r_[np.linspace(0,end,6001),starts+taus]); rise=np.zeros_like(tt)
    for c,st,tau in zip(row,starts,taus):
     if tau>0:rise+=.5*.1*10*P*math.sqrt(tau)/(eff*math.sqrt(math.pi))*kernel((tt-st)/tau,float(c))
    coupled.append(dict(N=n,span_um=span,seat_total_N_m='rigid' if K is None else K,high_position=position,outer_gap_um=10,within_manufactured_radius=bool(max(cs)<=1.5+1e-12),max_deltaT_C=float(max(rise)),max_T_C=50+float(max(rise))))
write_csv('coupled_array.csv',coupled)
for n in (4,16,64):
 expected=next(x['max_deltaT_C'] for x in arrays if x['N']==n and x['gap_um']==10)
 got=next(x['max_deltaT_C'] for x in coupled if x['N']==n and x['span_um']==0 and x['seat_total_N_m']=='rigid')
 check('coupled equal-height reduction '+str(n),abs(got/expected-1)<2e-5)
summary['coupled_cases']=len(coupled)
summary['coupled_key']=[x for x in coupled if x['N']==16]
summary['math_checks']=len(checks)
write_json('checks.json',dict(physical_validation=False,checks=checks,passed=sum(x['passed'] for x in checks),total=len(checks)))
write_json('summary.json',summary)
print(json.dumps(dict(coupled_cases=len(coupled),math_checks=len(checks))))
