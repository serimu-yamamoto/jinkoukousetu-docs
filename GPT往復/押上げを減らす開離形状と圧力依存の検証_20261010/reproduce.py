from pathlib import Path
import json,math,sys
D=Path(__file__).resolve().parent
I=json.loads((D/'inputs.json').read_text(encoding='utf-8'))
checks=[]
def ck(name,cond):
    if not cond: raise AssertionError(name)
    checks.append(name)
def close(a,b,tol=1e-10):return abs(a-b)<=tol*max(1,abs(a),abs(b))
def q(mu,d):
    if mu*d>=1:raise ValueError('No finite forward sliding solution in constrained ramp model')
    return (mu+d)/(1-mu*d)
def slope(x,h,l,profile):
    return h/l if profile=='straight' else math.pi*h/(2*l)*math.sin(math.pi*x/l)
def simpson(f,l,n=2000):
    step=l/n
    return step/3*(f(0)+f(l)+sum((4 if j%2 else 2)*f(j*step) for j in range(1,n)))
rows=[]
for profile in I['path_profiles']:
 for h in I['escape_height_mm']:
  for mu in I['particle_contact_mu']:
   for p in I['pressure_kPa']:
    l=I['escape_run_mm'];c=I['release_c0_kPa']
    d=lambda x:slope(x,h,l,profile)
    # kPa * mm = J/m2 exactly. Isolated release spring is in parallel horizontally.
    work=simpson(lambda x:p*q(mu,d(x))+c*(1-x/l),l)
    heat=simpson(lambda x:mu*p*(1+d(x)**2)/(1-mu*d(x)),l)
    lift=p*h;spring=c*l/2
    ck(f'energy-{profile}-{h}-{mu}-{p}',close(work,heat+lift+spring,1e-10))
    if profile=='straight':ck(f'closed-form-{h}-{mu}-{p}',close(work,p*q(mu,h/l)*l+spring))
    m=max(q(mu,d(j*l/2000)) for j in range(2001))
    rows.append(dict(profile=profile,h_mm=h,run_mm=l,mu=mu,p_kPa=p,max_ramp_ratio=m,work_J_m2=work,friction_J_m2=heat,lift_J_m2=lift,parallel_release_J_m2=spring))
for mu in I['particle_contact_mu']:
 ck('flat-limit-'+str(mu),q(mu,0)==mu)
 ck('slope-monotonic-'+str(mu),q(mu,0.04)<q(mu,0.4))
ck('frictionless-lift',close(q(0,0.4),0.4))
try:q(2,0.5);valid=False
except ValueError:valid=True
ck('no-finite-solution-guard',valid)
# Solve the independent two-vector force balance, and verify work at points.
for mu,d in [(0.2,0.04),(0.4,0.4),(0.1,1),(0,0.3)]:
 angle=math.atan(d);p=20;R=p/(math.cos(angle)-mu*math.sin(angle));F=R*(math.sin(angle)+mu*math.cos(angle))
 ck('vector-balance-'+str((mu,d)),close(F,p*q(mu,d)))
 ck('local-energy-'+str((mu,d)),close(F,p*d+mu*R*math.sqrt(1+d*d)))
# Same total resistance at one pressure, different response at other pressures.
mu=0.2;refp=20;da=0.4;db=0.04;ca=3;cb=ca+refp*(q(mu,da)-q(mu,db))
matched=[dict(p_kPa=p,deep_kPa=ca+p*q(mu,da),shallow_kPa=cb+p*q(mu,db)) for p in I['pressure_kPa']]
ck('one-pressure-match',close(matched[1]['deep_kPa'],matched[1]['shallow_kPa']))
ck('pressure-order-reversal',matched[0]['deep_kPa']<matched[0]['shallow_kPa'] and matched[2]['deep_kPa']>matched[2]['shallow_kPa'])
# Single straight slope inversion; B is an arbitrary diagnostic, not a snow target.
inverse=[];B=I['pressure_ratio_diagnostic'];l=I['escape_run_mm']
for mu in [0.1,0.2,0.3,0.4]:
 if mu>B:inverse.append(dict(mu=mu,feasible=False,d_max=None,straight_h_max_mm=None,cosine_h_max_mm=None));continue
 dm=(B-mu)/(1+B*mu)
 ck('inverse-'+str(mu),close(q(mu,dm),B))
 inverse.append(dict(mu=mu,feasible=True,d_max=dm,straight_h_max_mm=l*dm,cosine_h_max_mm=2*l*dm/math.pi))
t=I['tolerance'];hw=t['nominal_h_mm']+t['plus_h_mm'];lw=t['nominal_run_mm']-t['minus_run_mm'];dw=math.pi*hw/(2*lw)
tolerance=dict(worst_h_mm=hw,worst_run_mm=lw,d_max=dw,ratio_at_mu02=q(0.2,dw),ratio_at_mu04=q(0.4,dw))
ck('tolerance-conditional-not-universal',tolerance['ratio_at_mu02']<B<tolerance['ratio_at_mu04'])
# Apparatus units: NOT real ski speed or prototype dimensions.
s=I['source_conditions'];area=math.pi*(s['snow_diameter_mm']/1000)**2/4
apparatus=dict(source_area_m2=area,normal_load_N_at_25_kPa=25000*area,normal_load_N_at_100_kPa=100000*area,source_rate_m_s=s['snow_shear_mm_min']/60000,source_six_mm_duration_s=6/(s['snow_shear_mm_min']/60))
ck('source-rate-conversion',close(apparatus['source_rate_m_s'],1.3333333333333333e-5))
ck('source-duration',close(apparatus['source_six_mm_duration_s'],450))
# Equal-height restoration can leave the release path geometry changed.
rain=dict(mu=0.2,p_kPa=20,c0_kPa=3,before_h_mm=0.02,after_h_mm=0.2,run_mm=l)
rain['before_kPa']=3+20*q(0.2,0.02/l);rain['after_kPa']=3+20*q(0.2,0.2/l)
rain['ratio']=rain['after_kPa']/rain['before_kPa']
ck('rain-geometry-counterexample',rain['ratio']>2)
# Exact pressure sweep recovers assumed intercept and slope. No measured fit.
recovered_m=(matched[2]['shallow_kPa']-matched[0]['shallow_kPa'])/(50-5)
recovered_c=matched[0]['shallow_kPa']-5*recovered_m
ck('identify-pressure-slope',close(recovered_m,q(0.2,db)))
ck('identify-intercept',close(recovered_c,cb))
cost=[];C=I['cost']
for unit in C['incremental_processing_JPY_kg']:
 for tooling in C['tooling_JPY']:
  extra=C['inventory_kg']*unit+tooling
  loss=extra/(C['inventory_kg']*C['replacement_JPY_kg']*C['events'])
  ck('cost-balance-'+str((unit,tooling)),close(loss*C['inventory_kg']*C['replacement_JPY_kg']*C['events'],extra))
  cost.append(dict(processing_JPY_kg=unit,tooling_JPY=tooling,incremental_JPY=extra,required_loss_reduction_fraction_per_event=loss,required_loss_reduction_percentage_points_per_event=loss*100))
O=I['orientation'];tilt=[]
for angle in O['uphill_tilt_deg']:
 total=math.atan(O['local_straight_slope'])+math.radians(angle);dt=math.tan(total)
 tilt.append(dict(tilt_deg=angle,total_slope=dt,ramp_ratio=q(O['mu'],dt)))
angle_limit=math.degrees(math.atan((B-O['mu'])/(1+B*O['mu']))-math.atan(O['local_straight_slope']))
ck('local-low-ramp-fails-after-tilt',tilt[0]['ramp_ratio']<B<tilt[1]['ramp_ratio'])
R=dict(orientation=dict(cases=tilt,diagnostic_max_uphill_tilt_deg=angle_limit),evidence=I['evidence'],rows=rows,single_pressure_match=dict(deep_c0_kPa=ca,shallow_c0_kPa=cb,cases=matched),inverse=inverse,tolerance=tolerance,rain=rain,apparatus=apparatus,cost=cost)
V=dict(checks=len(checks),passed=True,names=checks.copy(),physical_tests=0,success_probability=None)
for name,obj in [('results.json',R),('validation.json',V)]:
 data=json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
 if '--check' in sys.argv:ck('byte-reproduction-'+name,(D/name).read_text(encoding='utf-8')==data)
 else:(D/name).write_text(data,encoding='utf-8',newline='\n')
print(json.dumps(dict(rows=len(rows),checks=V['checks'],physical_tests=0,success_probability=None,byte_check='--check' in sys.argv)))
