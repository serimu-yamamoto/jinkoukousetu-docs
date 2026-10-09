"""Cycle 78: support dimensions and a passive two-tip rocker. Conditional mechanics only."""
from pathlib import Path
import sys,json,math,csv
D=Path(__file__).resolve().parent
if (D.parents[1]/'.deps').exists():sys.path.insert(0,str(D.parents[1]/'.deps'))
import numpy as np
from scipy.optimize import brentq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
I=json.loads((D/'inputs.json').read_text(encoding='utf-8'));R=I['reference'];S=I['supports'];B=I['rocker'];C=I['cost']
W=R['W0_N'];K=R['Ktotal_N_m'];delta=W/K;checks=[]
def ck(name,ok,value=None):
 checks.append(dict(name=name,passed=bool(ok),value=value))
 if not ok:raise AssertionError(name)
def js(name,obj):(D/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def csvout(name,rows):
 with (D/name).open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def g(c):return 3*math.pi*c*c/8+3*math.pi*c**4/16
def f(c):return math.pi*(.5*c**3+.3*c**5)
def c_from_load(F,a):return 0. if F<=0 else brentq(lambda c:R['p0_Pa']*a*a*f(c)-F,0,10,xtol=1e-14)
def contact_indent(F,a):return R['p0_Pa']*a/R['E_contact_Pa']*g(c_from_load(F,a))
ck('reference_load',math.isclose(W,.031415926535897934,rel_tol=1e-14))
ck('nominal_support_stroke',math.isclose(delta,1.5707963267948966e-6,rel_tol=1e-14))
# Axial cylindrical post tuned to K/N, base clamped, top free under lateral force.
posts=[]
for n in S['N']:
 k=K/n;load=W/n;a=R['a0_m']/math.sqrt(n);outer=1.5*a
 for E in S['E_Pa']:
  for Lum in S['length_um']:
   L=Lum*1e-6;A=k*L/E;r=math.sqrt(A/math.pi);J=math.pi*r**4/4;G=E/(2*(1+S['nu']))
   Fn=load;Ft=.1*Fn;epsn=Fn/(E*A);epsb=4*Ft*L/(math.pi*r**3*E)
   y=Ft*L**3/(3*E*J)+Ft*L/(.9*G*A)
   # Euler fixed-free effective length 2L; only a diagnostic for slender rods.
   Pcr=math.pi**2*E*J/(2*L)**2;lam=4*L/r
   posts.append(dict(N=n,E_Pa=E,L_um=Lum,r_um=r*1e6,k_N_m=k,F_mN=Fn*1000,axial_strain=epsn,linear_outer_fiber_strain=epsn+epsb,mu_lateral_assumed=.1,lateral_deflection_over_L=y/L,Euler_fixed_free_Pcr_over_F=Pcr/Fn,slenderness=lam,Euler_slender_screen=bool(lam>=20),within_tip_outer_radius=bool(r<=outer),small_deflection_screen=bool(max(delta/L,y/L)<=.1),linear_model_stable=bool(Pcr>Fn),candidate_validated=False))
ck('post_axial_stiffness_inversion',all(abs(x['axial_strain']*x['L_um']*1e-6/delta-1)<1e-12 for x in posts))
for n in S['N']:
 for E in S['E_Pa']:
  vals=[x['Euler_fixed_free_Pcr_over_F'] for x in posts if x['N']==n and x['E_Pa']==E]
  expected=math.pi*(K/n)**2/(16*E*(W/n))
  ck('Euler_length_independence_N'+str(n)+'_E'+str(E),max(abs(v/expected-1) for v in vals)<1e-12)
csvout('axial_posts.csv',posts)
# Four fixed-guided beams: k=4 E w t^3/L^3; end rotations constrained.
beams=[]
for n in S['N']:
 k=K/n;a=R['a0_m']/math.sqrt(n);b=1.5*a;pitch=3*a+R['outer_gap_m']
 for E in S['beam_E_Pa']:
  for Lum in S['beam_length_um']:
   L=Lum*1e-6
   for tum in S['beam_thickness_um']:
    t=tum*1e-6;w=k*L**3/(S['beam_count']*E*t**3)
    eps=3*t*delta/L**2;epsD=3*t*S['design_stroke_m']/L**2
    limit_width=2*math.pi*(b+L/2)/S['beam_count']
    beams.append(dict(N=n,E_Pa=E,L_um=Lum,t_um=tum,required_width_um=w*1e6,nominal_max_strain=eps,at_2p5um_strain=epsD,outer_diameter_um=2*(b+L)*1e6,original_pitch_um=pitch*1e6,beam_slender_screen=bool(L/t>=5),small_stroke_screen=bool(S['design_stroke_m']/L<=.1+1e-12),radial_width_screen=bool(w<=limit_width),fits_independent_original_cell=bool(2*(b+L)<=pitch+1e-15),candidate_validated=False))
ck('beam_target_stiffness',all(abs(S['beam_count']*x['E_Pa']*x['required_width_um']*1e-6*(x['t_um']*1e-6)**3/(x['L_um']*1e-6)**3/(K/x['N'])-1)<1e-12 for x in beams))
csvout('fixed_guided_beams.csv',beams)
# Uniaxial linear energy-capacity bound. Not a bound for arbitrary multiaxial or nonlinear structures.
ener=[]
for area in C['area_m2']:
 heads=C['grain_count_per_2000']*C['heads_per_grain']*area/2000
 for E in S['E_Pa']:
  for eps in S['strain_budgets']:
   vhead=W*delta/(E*eps**2);mass=vhead*heads*C['rho_kg_m3']
   for price in C['unit_JPY_kg']:
    ener.append(dict(area_m2=area,E_Pa=E,assumed_elastic_strain_limit=eps,volume_per_original_head_um3=vhead*1e18,support_mass_lower_bound_kg=mass,ideal_uniform_axial_length_um=delta/eps*1e6,raw_price_assumed_JPY_kg=price,raw_cost_floor_JPY=mass/C['yield']*price,multiaxial_universal_bound=False))
ck('energy_capacity_identity',all(math.isclose(x['volume_per_original_head_um3']*1e-18*.5*x['E_Pa']*x['assumed_elastic_strain_limit']**2,.5*W*delta,rel_tol=1e-12) for x in ener))
csvout('uniaxial_energy_bound.csv',ener)
# Two-tip local rocker: assigned pair load, rigid arms, quasi-static increasing height mismatch.
# q=(Fhigh-Flow)/Fpair. Rotation lowers the high tip by l*theta.
def rocker(n,span_um,rolling_um,kappa,bridges):
 a=R['a0_m']/math.sqrt(n);pitch=3*a+R['outer_gap_m'];l=pitch/2;pair=2*W/n;dh=span_um*1e-6
 cap=bridges*2*math.pi*B['water_bridge_radius_m']*B['gamma_N_m']*B['bridge_moment_arm_m']
 resist=pair*rolling_um*1e-6+cap
 def defdiff(q):return contact_indent(pair*(1+q)/2,a)-contact_indent(pair*(1-q)/2,a)
 def load_diff(remain):
  if remain<=0:return 0.
  if remain>=defdiff(1):return 1.
  return brentq(lambda q:defdiff(q)-remain,0,1,xtol=1e-13)
 def tq(th):return l*pair*load_diff(dh-2*l*th)-kappa*th-resist
 qlocked=load_diff(dh)
 if dh==0 or tq(0)<=0:theta=0.;state='locked_or_aligned'
 elif kappa==0 and resist==0:theta=dh/(2*l);state='ideal_motion'
 else:theta=brentq(tq,0,dh/(2*l),xtol=1e-15);state='moving'
 q=load_diff(dh-2*l*theta);Fhi=pair*(1+q)/2;Flo=pair*(1-q)/2
 c1=c_from_load(Fhi,a);c2=c_from_load(Flo,a)
 residual=tq(theta)
 # Center fulcrum modeled separately as an elastic cylinder on a plane.
 width=math.sqrt(4*pair*B['bearing_radius_m']/(math.pi*B['bearing_E_star_Pa']*B['bearing_line_length_m']))
 ppeak=2*pair/(math.pi*width*B['bearing_line_length_m'])
 travel=B['bearing_radius_m']*theta
 margin=B['bearing_half_width_m']-width-travel
 budget=B['load_imbalance_budget']*l*pair
 # Worst differential-load torque bound with full geometric alignment rotation.
 bound=(resist+kappa*dh/(2*l))/(l*pair)
 return dict(N=n,height_span_um=span_um,rolling_resistance_arm_um=rolling_um,kappa_Nm_rad=kappa,water_bridges=bridges,pair_force_mN=pair*1000,lever_half_span_um=l*1e6,locked_imbalance=qlocked,imbalance=q,high_load_mN=Fhi*1000,low_load_mN=Flo*1000,theta_deg=theta*180/math.pi,tip_c_high=c1,tip_c_low=c2,outer_radius_valid=bool(max(c1,c2)<=1.5+1e-12),state=state,torque_residual_Nm=residual,resisting_moment_Nm=resist,ten_percent_moment_budget_Nm=budget,upper_imbalance_bound=min(1,bound),fulcrum_contact_half_width_um=width*1e6,fulcrum_peak_MPa=ppeak/1e6,fulcrum_contact_margin_um=margin*1e6,fulcrum_width_screen=bool(margin>=0),full_array_equilibrium_validated=False)
rocks=[]
for n in B['N']:
 for dh in B['height_span_um']:
  for b in B['rolling_arm_um']:
   for kap in B['torsion_Nm_rad']:
    for z in B['water_bridge_count']:rocks.append(rocker(n,dh,b,kap,z))
ck('rocker_pair_force_balance',all(abs((x['high_load_mN']+x['low_load_mN'])/x['pair_force_mN']-1)<1e-12 for x in rocks))
ck('rocker_torque_balance_when_moving',max(abs(x['torque_residual_Nm']) for x in rocks if x['state']=='moving')<1e-14)
ck('locked_torque_within_threshold',all(x['torque_residual_Nm']<=1e-15 for x in rocks if x['state']=='locked_or_aligned'))
ck('rocker_never_worsens_pair_load_in_this_model',all(x['imbalance']<=x['locked_imbalance']+1e-12 for x in rocks))
ck('rocker_bound',all(x['imbalance']<=x['upper_imbalance_bound']+1e-10 for x in rocks))
ck('ideal_rocker_equal_load',all(abs(x['imbalance'])<1e-12 for x in rocks if x['rolling_resistance_arm_um']==0 and x['kappa_Nm_rad']==0 and x['water_bridges']==0))
ck('rolling_loss_can_lock',any(x['state']=='locked_or_aligned' and x['height_span_um']>0 and x['rolling_resistance_arm_um']==20 for x in rocks))
csvout('rocker_pairs.csv',rocks)
# Four spatial height patterns: a common translating base cannot correct relative heights.
# This invariance is exact for identical independent contact laws and a shared translation.
common=[]
for dh in B['height_span_um']:
 n=16;a=R['a0_m']/4;heights=np.r_[dh*1e-6,np.zeros(15)];heights-=np.mean(heights)
 def cinv(d):
  d=np.maximum(d,0)/(R['p0_Pa']*a/R['E_contact_Pa']);aa=3*np.pi/8;bb=3*np.pi/16
  return np.sqrt(2*d/(aa+np.sqrt(aa*aa+4*bb*d)))
 def total(d):
  cs=cinv(d+heights);return np.sum(R['p0_Pa']*a*a*np.pi*(.5*cs**3+.3*cs**5))
 d=brentq(lambda d:total(d)-W,-max(heights),1e-4,xtol=1e-18)
 cs=cinv(d+heights);loads=R['p0_Pa']*a*a*np.pi*(.5*cs**3+.3*cs**5)
 for commonK in (2000,20000,200000):
  common.append(dict(height_span_um=dh,common_base_k_N_m=commonK,common_sink_um=W/commonK*1e6,load_fraction_max=float(max(loads)/W),load_fraction_unchanged=True,scope='rigid plate translation only; rotation/elastic coupling excluded'))
ck('shared_translation_does_not_equalize',max(x['load_fraction_max'] for x in common if x['height_span_um']==.5)-min(x['load_fraction_max'] for x in common if x['height_span_um']==.5)<1e-15)
csvout('common_translation.csv',common)
# Leaf lever stock only. A full binary tree requires N-1 joints but is not modeled.
levercost=[]
for area in C['area_m2']:
 heads=C['grain_count_per_2000']*C['heads_per_grain']*area/2000
 for n in B['N']:
  a=R['a0_m']/math.sqrt(n);span=3*a+R['outer_gap_m'];pairs=n/2
  v=span*C['lever_width_m']*C['lever_thickness_m']
  mass=heads*pairs*v*C['rho_kg_m3']
  for price in C['unit_JPY_kg']:
   levercost.append(dict(area_m2=area,N=n,leaf_rocker_count=heads*pairs,full_binary_tree_joint_count_if_used=heads*(n-1),leaf_bar_mass_kg=mass,raw_price_JPY_kg=price,leaf_bar_raw_cost_JPY=mass/C['yield']*price,fulcrum_hinge_catch_and_assembly_included=False,bar_stiffness_validated=False))
csvout('lever_stock_cost.csv',levercost)

# Torque budget including adverse lateral force; not a solved dynamic rocker trajectory.
moments=[]
for n in (4,16):
 a=R['a0_m']/math.sqrt(n);l=(3*a+R['outer_gap_m'])/2;pair=2*W/n
 cap=5*2*math.pi*B['water_bridge_radius_m']*B['gamma_N_m']*B['bridge_moment_arm_m']
 theta_limit=2*math.pi/180;kappa=2e-9
 for b_um in (.1,1,5):
  allowed=B['load_imbalance_budget']*l-b_um*1e-6-cap/pair-kappa*theta_limit/pair
  for mu in (.04,.1,.2):
   for h_um in (5,10,25,50):
    bound=(b_um*1e-6+cap/pair+kappa*theta_limit/pair+mu*h_um*1e-6)/l
    moments.append(dict(N=n,b_um=b_um,mu_assumed=mu,h_um=h_um,rotation_bound_deg=2,capillary_bridges=5,imbalance_bound_from_torque=bound,within_ten_percent_moment_budget=bool(bound<=.1),max_h_um_for_budget=max(0,allowed/mu*1e6),zero_height_already_over_budget=bool(allowed<0),normal_only_solution_not_reused_as_proof=True))
csvout('lateral_moment_budget.csv',moments)
ck('lateral_moment_increases_imbalance_bound',all(x['imbalance_bound_from_torque']>x['mu_assumed']*x['h_um']*1e-6/((3*R['a0_m']/math.sqrt(x['N'])+R['outer_gap_m'])/2) for x in moments))
ck('micrometre_fulcrum_margin_unit',all(-20<x['fulcrum_contact_margin_um']<10 for x in rocks))

ck('probability_not_filled',I['physical_trials']==0 and I['success_probability'] is None)
# Dimensioned functional schematic; no claim of manufacturable final CAD.
fig,axs=plt.subplots(1,3,figsize=(13,4.4),layout='constrained')
ax=axs[0]
for n,col in [(4,'#17609a'),(16,'#d26936')]:
 xx=[x for x in beams if x['N']==n and x['E_Pa']==1e9 and x['t_um']==5]
 ax.plot([x['outer_diameter_um'] for x in xx],[100*x['at_2p5um_strain'] for x in xx],'-',color=col,label=f'N={n}, t=5 um')
 for x in xx: ax.plot(x['outer_diameter_um'],100*x['at_2p5um_strain'],'o',color=col,markerfacecolor=col if x['beam_slender_screen'] and x['small_stroke_screen'] else 'white')
ax.axhline(2,color='gray',ls='--',label='2% assumed screen');ax.set(yscale='log',xlabel='Required envelope diameter (um)',ylabel='Linear maximum strain (%)',title='Linear beam diagnostic; hollow: outside screen');ax.legend(fontsize=8);ax.grid(alpha=.2)
ax=axs[1]
for dh,col in [(.1,'#17609a'),(.5,'#d26936'),(1,'#597b2f')]:
 rr=[x for x in rocks if x['N']==16 and x['height_span_um']==dh and x['kappa_Nm_rad']==2e-9 and x['water_bridges']==5]
 ax.plot([x['rolling_resistance_arm_um'] for x in rr],[x['imbalance']*100 for x in rr],'o-',label=f'height {dh} um')
ax.axhline(10,color='gray',ls='--',label='10% comparison budget');ax.set(xlabel='Effective resisting arm b (um)',ylabel='Pair force imbalance (%)',title='Normal load only; lateral moment is separate');ax.legend(fontsize=8);ax.grid(alpha=.2)
ax=axs[2]
for E,col in [(1e8,'#17609a'),(1e9,'#d26936')]:
 rr=[x for x in ener if x['area_m2']==2000 and x['E_Pa']==E and x['raw_price_assumed_JPY_kg']==500]
 ax.plot([x['assumed_elastic_strain_limit']*100 for x in rr],[x['support_mass_lower_bound_kg']/1000 for x in rr],'o-',label=f'E={E/1e9:g} GPa')
ax.set(xscale='log',yscale='log',xlabel='Assumed elastic strain budget (%)',ylabel='Ideal support mass floor (t)',title='Uniaxial model; 2,000 m2, all depths');ax.legend(fontsize=8);ax.grid(alpha=.2)
fig.savefig(D/'support_rocker_cost.png',dpi=160);plt.close(fig)
fig,ax=plt.subplots(figsize=(11,5.2),layout='constrained');ax.set_aspect('equal');ax.set_xlim(-65,65);ax.set_ylim(-25,40);ax.axis('off')
ax.plot([-48,48],[25,25],lw=5,color='#596779');ax.text(0,30,'Ski base (normal load + lateral friction)',ha='center',fontsize=11)
ax.plot([-23.75,-23.75],[11.10,25],lw=7,color='#59a1b8');ax.plot([23.75,23.75],[11.90,25],lw=7,color='#59a1b8')
ax.plot([-30,30],[11,12],lw=8,color='#c68b57')
xs=np.linspace(-10,10,101);ys=10-xs*xs/(2*250)
ax.fill_between(xs,-2,ys,color='#5b7b55');ax.plot([-18,18],[-3,-3],lw=5,color='#5b7b55')
ax.annotate('',xy=(23.75,-7),xytext=(-23.75,-7),arrowprops=dict(arrowstyle='<->'));ax.text(0,-12,'47.5 um tip spacing (N=16 leaf pair)',ha='center',fontsize=10)
ax.annotate('Load-bearing seat\nR=250 um; axial length 100 um',xy=(0,9),xytext=(-60,15),arrowprops=dict(arrowstyle='->'),fontsize=9)
ax.annotate('Retaining hinge\n(not dimensioned here)',xy=(29,11.8),xytext=(36,16),arrowprops=dict(arrowstyle='->'),fontsize=9)
ax.text(0,-21,'Drainage, lateral restraint and captive assembly require a separate complete design.',ha='center',fontsize=10)
ax.set_title('H78-R: local two-tip mechanism; schematic only, no completed particle CAD',fontsize=12)
fig.savefig(D/'rocker_concept.png',dpi=160);plt.close(fig)
counts={'axial_posts.csv':len(posts),'fixed_guided_beams.csv':len(beams),'uniaxial_energy_bound.csv':len(ener),'rocker_pairs.csv':len(rocks),'common_translation.csv':len(common),'lever_stock_cost.csv':len(levercost),'lateral_moment_budget.csv':len(moments)}
key=[x for x in rocks if x['N']==16 and x['height_span_um']==.5 and x['kappa_Nm_rad']==2e-9 and x['water_bridges']==5]
summary=dict(cycle=78,physical_trials=0,success_probability=None,row_counts=counts,total_rows=sum(counts.values()),math_checks=len(checks),nominal_stroke_um=delta*1e6,rocker_key=key,moment_key=[x for x in moments if x['N']==16 and x['b_um']==1 and x['mu_assumed']==.1],post_key=[x for x in posts if x['N']==16 and ((x['E_Pa']==1e9 and x['L_um']==250) or (x['E_Pa']==1e8 and x['L_um']==50))],beam_key=[x for x in beams if x['N']==16 and x['E_Pa']==1e9 and x['L_um']==25 and x['t_um']==5],mass_keys=[x for x in ener if x['area_m2']==2000 and x['E_Pa'] in (1e8,1e9) and x['raw_price_assumed_JPY_kg']==500],scope='Static local models; no full-particle or full-array validation')
js('summary.json',summary);js('checks.json',dict(total=len(checks),passed=sum(x['passed'] for x in checks),checks=checks,physical_validation=False))
(D/'requirements.txt').write_text('numpy=='+np.__version__+'\nscipy=='+__import__('scipy').__version__+'\nmatplotlib=='+matplotlib.__version__+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(cycle=78,rows=sum(counts.values()),checks=len(checks),physical_trials=0)))
