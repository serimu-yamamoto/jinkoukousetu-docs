"""Cycle 72: inverse elastic contact. No physical validation.
Requires numpy, matplotlib. All material and price inputs are hypothetical.
"""
from pathlib import Path
import sys,math,json,csv
D=Path(__file__).resolve().parent;R=D.parents[1]
if (R/'.deps').exists():sys.path.insert(0,str(R/'.deps'))
import numpy as np
from numpy.polynomial.legendre import leggauss
I=json.loads((D/'inputs.json').read_text(encoding='utf-8'))
nodes,weights=leggauss(128)
def integ(fn,lo,hi):
 if hi<=lo:return 0.
 t=(nodes+1)*(hi-lo)/2+lo
 return float(np.dot(weights,fn(t))*(hi-lo)/2)
def w1(x,m):
 x=np.asarray(x);h=np.sqrt(np.maximum(0,1-x*x));n=m//2
 return 2*(h-sum(math.comb(n,k)*x**(2*(n-k))*h**(2*k+1)/(2*k+1) for k in range(n+1)))
def g(x,m,k=2):
 x=np.asarray(x);base=2*m/(m+1)-w1(np.minimum(x,1),m)
 return np.where(x<=1,base,2*m/(m+1)+k*(x-1)**2)
def gp(x,m,k=2):
 x=np.asarray(x);z=np.minimum(x,1);h=np.sqrt(np.maximum(0,1-z*z));n=m//2
 base=2*m*z*sum(math.comb(n-1,j)*z**(2*(n-1-j))*h**(2*j+1)/(2*j+1) for j in range(n))
 return np.where(x<=1,base,2*k*(x-1))
def f(r,m,k=2):return 2/math.pi*integ(lambda t:g(r*np.sin(t),m,k),0,math.pi/2)
def force(c,m,k=2):
 inside=integ(lambda th:np.sin(th)*gp(np.sin(th),m,k)*np.cos(th),0,math.asin(min(c,1)))
 return 2*inside+(4*k*(c**3/3-c**2/2+1/6) if c>1 else 0)
def pressure(r,c,m,k=2):
 if r>=c:return 0.
 inside=0.
 if r<min(c,1):
  B=math.sqrt(1-r*r);end=math.asin(min(1,math.sqrt((min(c,1)**2-r*r)/(1-r*r))))
  inside=integ(lambda th:gp(np.sqrt(r*r+(B*np.sin(th))**2),m,k)/np.sqrt(r*r+(B*np.sin(th))**2)*B*np.cos(th),0,end)
 outside=0.
 if c>1:
  start=math.sqrt(max(0,max(1,r)**2-r*r));end=math.sqrt(c*c-r*r)
  def primitive(t):return t-(math.asinh(t/r) if r>0 else math.log(t))
  outside=2*k*(primitive(end)-primitive(start))
 return (inside+outside)/math.pi

checks=[]
def ck(name,v):
 checks.append({'name':name,'passed':bool(v)});assert v,name
def near(a,b,rtol=1e-7,atol=1e-10):return abs(a-b)<=atol+rtol*abs(b)
def jwrite(name,obj):
 (D/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def csvwrite(stem,rows):
 with (D/(stem+'.csv')).open('w',encoding='utf-8',newline='') as out:
  wr=csv.DictWriter(out,fieldnames=list(rows[0]),lineterminator='\n');wr.writeheader();wr.writerows(rows)
def qg(x):return 3*math.pi*x*x/8+3*math.pi*x**4/16
def qgp(x):return 3*math.pi*x/4+3*math.pi*x**3/4
def qf(x):return 3*math.pi*x*x/16+9*math.pi*x**4/128
def qforce(c):return math.pi*(.5*c**3+.3*c**5)
def qp(r,c):
 return math.sqrt(max(0,c*c-r*r))*(.75+.25*c*c+.5*r*r)
def qpeak(c):
 d=2*c*c/(3+c*c);u=max(0,(2*d-1)/(3*d))
 return qp(c*math.sqrt(u),c),c*math.sqrt(u)
def solve_radius(model,er,load,k=2):
 wanted=.8*math.pi*load/er
 if near(wanted,.8*math.pi,rtol=1e-13):return 1.
 fn=qforce if model=='Q72' else lambda c:force(c,8,k)
 lo,hi=0.,4.
 for _ in range(65):
  mid=(lo+hi)/2
  if fn(mid)<wanted:lo=mid
  else:hi=mid
 return (lo+hi)/2
p0=I['p_ref_Pa'];a=I['a_ref_m'];E=I['E_ref_Pa'];H=p0*a/E;W0=.8*math.pi*p0*a*a
# Formula checks with independent integration and known Hertz result.
ck('Q72 design pressure center',near(qp(0,1),1))
ck('outside-radius quadrature endpoint is finite',math.isfinite(pressure(1.321,1.66,8,2)))
ck('Q72 design beta',near(qforce(1)/math.pi,.8))
ck('Q72 equivalent and physical profiles agree',near(2/math.pi*integ(lambda t:qg(np.sin(t)),0,math.pi/2),qf(1)))
ck('Q72 force by independent derivative integral',near(2*integ(lambda x:x*qgp(x),0,1),qforce(1)))
ck('Q72 pressure by independent Abel transform',all(near(integ(lambda t:qgp(np.sqrt(rr*rr+t*t))/np.sqrt(rr*rr+t*t),0,math.sqrt(1-rr*rr))/math.pi,qp(rr,1)) for rr in [.0,.2,.7,.95]))
ck('Hertz inverse profile baseline',near(2/math.pi*integ(lambda th:math.pi*(np.sin(th))**2/2,0,math.pi/2),math.pi/4))
ck('Q72 analytical pressure integral',near(2*math.pi*integ(lambda th:np.sin(th)*np.cos(th)**2*(1+.5*np.sin(th)**2),0,math.pi/2),qforce(1)))
for m in [2,8,16]:
 ck('inverse power pressure '+str(m),max(abs(pressure(rr,1,m)-(1-rr**m)) for rr in [0,.1,.3,.6,.9,.99])<1e-8)
 ck('inverse power force '+str(m),near(force(1,m),math.pi*m/(m+2)))
ck('Q72 twice load radius',near(solve_radius('Q72',1,2),1.1980032241084753))
ck('Q72 profile convex',all(3*math.pi/8+27*math.pi*x*x/32>0 for x in np.linspace(0,2,101)))
# Convergence after removing integration endpoint square roots.
conv=[]
for nn in [32,64,128]:
 nodes,weights=leggauss(nn)
 conv.append({'nodes':nn,'R8_force':force(1,8),'R8_height':f(1,8),'R8_pressure_r09':pressure(.9,1,8),'R8_force_c132':force(1.32,8)})
nodes,weights=leggauss(128)
ck('inverse convergence force',abs(conv[0]['R8_force']-conv[-1]['R8_force'])<1e-9)
ck('inverse convergence height',abs(conv[0]['R8_height']-conv[-1]['R8_height'])<1e-9)
ck('inverse convergence pressure',abs(conv[0]['R8_pressure_r09']-conv[-1]['R8_pressure_r09'])<1e-9)
profiles=[]
for rr in np.linspace(0,1,101):
 for label in ['R8','Q72','Hertz']:
  hh=f(rr,8) if label=='R8' else qf(rr) if label=='Q72' else math.pi*rr*rr/4
  pp=1-rr**8 if label=='R8' else qp(rr,1) if label=='Q72' else math.sqrt(max(0,1-rr*rr))
  profiles.append({'model':label,'r_over_a':float(rr),'height_m':float(hh*H),'pressure_Pa':float(pp*p0)})
cases=[]
for model,k in [('R8',.5),('R8',2.),('R8',8.),('Q72',0.)]:
 for er in [.5,1.,2.]:
  for load in [.25,.5,1.,1.2,2.]:
   c=solve_radius(model,er,load,k)
   if model=='Q72':peak,rpeak=qpeak(c)
   else:
    grid=np.linspace(0,c,1001);pv=[pressure(float(rr),c,8,k) for rr in grid];ii=int(np.argmax(pv));peak=pv[ii];rpeak=grid[ii]
   mean=p0*.8*load/c**2;actual_peak=peak*p0*er
   cases.append({'model':model,'extension_k':k,'E_ratio':er,'load_ratio':load,'radius_ratio':c,'contact_radius_um':c*a*1e6,'peak_Pa':float(actual_peak),'peak_r_over_a':float(rpeak),'beta':mean/actual_peak,'mean_Pa':mean,'mu_old_assumed':.03+(7e5/3)/mean,'mu_improved_assumed':.03+40000/mean,'within_1_5_radius_reserve':bool(c<=1.5+1e-10)})
qrow=lambda er,load:next(x for x in cases if x['model']=='Q72' and x['E_ratio']==er and x['load_ratio']==load)
rrow=lambda er,load:next(x for x in cases if x['model']=='R8' and x['extension_k']==2 and x['E_ratio']==er and x['load_ratio']==load)
ck('same reference load and peak',near(qrow(1,1)['peak_Pa'],rrow(1,1)['peak_Pa']) and near(qrow(1,1)['mean_Pa'],rrow(1,1)['mean_Pa']))
ck('Q72 load increase needs less radius than R8 extension',qrow(1,2)['radius_ratio']<rrow(1,2)['radius_ratio'])
ck('modulus loss still raises friction',qrow(.5,1)['mu_improved_assumed']>qrow(1,1)['mu_improved_assumed'])
ck('harder material still raises peak pressure',qrow(2,1)['peak_Pa']>qrow(1,1)['peak_Pa'])
ck('Q72 full examined radius range inside 1.5',all(x['within_1_5_radius_reserve'] for x in cases if x['model']=='Q72'))
ck('radius capacity does not prove pressure constraint',qrow(2,2)['peak_Pa']>p0)
capacity=[]
for model,k in [('R8',.5),('R8',2.),('R8',8.),('Q72',0.)]:
 for reserve in [1.,1.25,1.5,2.]:
  for er in [.5,1.,2.]:
   ff=qforce(reserve) if model=='Q72' else force(reserve,8,k)
   capacity.append({'model':model,'extension_k':k,'radius_reserve':reserve,'E_ratio':er,'maximum_load_ratio_by_radius_only':er*ff/(.8*math.pi),'skin_area_multiplier':reserve**2})
# A static moment-balance ansatz, not an elastic solution for a tilted cap.
# p(r,theta)=p_radial(r)*(1+c*r*cos(theta)/a).
# For Q72 at its design contact, e/a = (3/14)c.
moment=[]
num=integ(lambda th:np.sin(th)**3*np.cos(th)**2*(1+.5*np.sin(th)**2),0,math.pi/2)
ck('radial second moment identity',near(num/(.8),3/14))
for aa in [25.,50.,100.]:
 for mu in [.04,.1,.2]:
  for h in [10.,25.,50.,100.,250.]:
   cc=14*mu*h/(3*aa);valid=cc<=1
   pk=max(qp(rr,1)*(1+cc*rr) for rr in np.linspace(0,1,10001)) if valid else None
   moment.append({'radius_um':aa,'mu':mu,'pivot_depth_um':h,'eccentricity_over_radius':mu*h/aa,'skew_c':cc,'nonnegative_ansatz':bool(valid),'beta_if_ansatz_valid':.8/pk if valid else None,'not_elastic_compatibility_solution':True})
ck('deep pivot counterexample',not next(x for x in moment if x['radius_um']==50 and x['mu']==.1 and x['pivot_depth_um']==250)['nonnegative_ansatz'])
ck('shallow support reduces skew',next(x for x in moment if x['radius_um']==50 and x['mu']==.1 and x['pivot_depth_um']==25)['skew_c']<1)
ck('invalid skew has no fake beta',all(x['beta_if_ansatz_valid'] is None for x in moment if not x['nonnegative_ansatz']))
# Geometry-only diagnostic, not a tolerance standard or a fracture threshold.
tilt=[]
for aa in [25e-6,50e-6,100e-6]:
 for EE in [250e6,500e6,1000e6]:
  ht=p0*aa/EE*qf(1)
  for eta in [.1,.5,1.]:
   tilt.append({'radius_um':aa*1e6,'E_GPa':EE/1e9,'edge_height_um':ht*1e6,'height_fraction_eta':eta,'tilt_deg_geometric_only':math.degrees(math.atan(eta*ht/(2*aa)))})
# Sharp fixed-radius overload: ideal edge singularity, not a finite real stress prediction.
edge=[]
for extra in [.1,.2,.5]:
 for rr in [.9,.99,.999,.9999]:
  edge.append({'extra_load_fraction':extra,'r_over_a':rr,'normalized_increment_pressure':extra*.8/(2*math.sqrt(1-rr*rr)),'ideal_sharp_edge_model':True})
ck('fixed radius overload grows at edge',edge[0]['normalized_increment_pressure']<edge[3]['normalized_increment_pressure'])
# Extended functional skin. Other structure and manufacturing cost excluded.
cost=[]
for reserve in [1.,1.25,1.5,2.]:
 area=I['grain_count']*6*math.pi*(a*reserve)**2
 mass=area*I['skin_thickness_m']*I['density_kg_m3']
 for price in [500,2000]:
  for forming in [10,100]:
   amount=mass*price+area*forming
   cost.append({'radius_reserve':reserve,'full_cap_diameter_um':2*a*reserve*1e6,'skin_mass_kg':mass,'functional_area_m2':area,'assumed_JPY_kg':price,'assumed_JPY_m2':forming,'partial_initial_JPY':amount,'annual_10pct_replacement_JPY':.1*amount})
ck('reserve 1.5 multiplies skin by 2.25',near(cost[8]['skin_mass_kg']/cost[0]['skin_mass_kg'],2.25))
ck('Q72 shape is micron subscale at assumed modulus',0<qf(1)*H<1e-6)
ck('probability remains undefined',I['success_probability'] is None and I['physical_tests']==0)
rows={'inverse_profiles':profiles,'load_cases':cases,'radius_capacity':capacity,'moment_cases':moment,'tilt_diagnostics':tilt,'sharp_edge_overload':edge,'reserve_costs':cost,'convergence':conv}
for stem,rr in rows.items():csvwrite(stem,rr)
result={'cycle':72,'physical_tests':0,'success_probability':None,'material_selected':False,'assumptions_only':True,'contact_force_reference_N':W0,'length_scale_m':H,'Q72_edge_height_m':qf(1)*H,'R8_edge_height_m':f(1,8)*H,'shape_difference_at_edge_m':abs(qf(1)-f(1,8))*H,'reference_mu':qrow(1,1)['mu_improved_assumed'],'comparisons':[qrow(1,1.2),rrow(1,1.2),qrow(1,2),rrow(1,2),qrow(.5,1),rrow(.5,1),qrow(2,1)],'rows':{k:len(v) for k,v in rows.items()},'row_count':sum(len(v) for v in rows.values()),'checks':len(checks),'all_checks_passed':all(x['passed'] for x in checks),'shape_success_is_not_material_success':True,'finite_layer_and_contact_coupling_solved':False,'tilt_and_friction_full_contact_solved':False}
jwrite('results.json',result);jwrite('checks.json',{'count':len(checks),'checks':checks})
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'figure.dpi':140,'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,2,figsize=(12,4.7),layout='constrained')
for lab in ['R8','Q72','Hertz']:
 rr=[v for v in profiles if v['model']==lab]
 ax[0].plot([v['r_over_a'] for v in rr],[v['height_m']*1e6 for v in rr],label=lab)
ax[0].set(xlabel='Radius / design contact radius',ylabel='Surface height from centre (micrometres)',title='Inverse contact geometry (assumed E*=0.5 GPa)');ax[0].legend()
for load,style in [(1,'-'),(2,'--')]:
 for lab,col in [('R8','#ea580c'),('Q72','#0284c7')]:
  cc=solve_radius(lab,1,load);xx=np.linspace(0,cc,201)
  yy=[pressure(float(x),cc,8) if lab=='R8' else qp(float(x),cc) for x in xx]
  ax[1].plot(xx,np.array(yy)*p0/1e6,style,color=col,label=f'{lab}, load {load:g}x')
ax[1].set(xlabel='Radius / design contact radius',ylabel='Contact pressure (MPa)',title='Pressure shape changes with load');ax[1].legend(fontsize=8)
fig.suptitle('Cycle 72 | Ideal elastic contact, not a 50 C ski test',fontsize=12);fig.savefig(D/'figure1_inverse.png');plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,4.7),layout='constrained')
for lab,col in [('R8','#ea580c'),('Q72','#0284c7')]:
 rr=[v for v in cases if v['model']==lab and (lab=='Q72' or v['extension_k']==2) and v['E_ratio']==1]
 ax[0].plot([v['load_ratio'] for v in rr],[v['radius_ratio'] for v in rr],'o-',color=col,label=lab)
ax[0].axhline(1.5,color='black',ls=':',label='Illustrative radius reserve 1.5');ax[0].set(xlabel='Normal load / design load',ylabel='Required contact-radius ratio',title='Contact reserve without an abrupt edge');ax[0].legend()
for mu in [.04,.1,.2]:
 rr=[v for v in moment if v['radius_um']==50 and v['mu']==mu]
 ax[1].plot([v['pivot_depth_um'] for v in rr],[v['skew_c'] for v in rr],'o-',label=f'mu = {mu}')
ax[1].axhline(1,color='black',ls=':',label='Nonnegative-pressure ansatz limit');ax[1].set(xlabel='Depth of reaction point below contact (micrometres)',ylabel='Required pressure skew c',title='Tangential force cannot be ignored');ax[1].legend(fontsize=8)
fig.suptitle('Reserve radius is not proof of friction, peak pressure, or material durability',fontsize=12);fig.savefig(D/'figure2_reserve.png');plt.close(fig)
print(json.dumps({'checks':len(checks),'rows':result['row_count'],'physical_tests':0,'success_probability':None,'Q72_height_um':qf(1)*H*1e6}))
