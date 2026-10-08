"""Capillary reopening constraints, drainage entry and material budget.
Uncalibrated component hypotheses, not ski performance or success probabilities.
Run with Python standard library: python -X utf8 calculate.py
"""
from pathlib import Path
import json,math,csv,itertools
P=Path(__file__).resolve().parent
x=json.loads((P/'inputs.json').read_text(encoding='utf8'))
w=x['water']
def gamma(T):
 t=1-(T+273.15)/w['critical_temperature_K']
 return w['B_N_m']*t**w['exponent']*(1+w['b']*t)
G=gamma(w['calculation_temperature_C'])
def parameters(R,vstar,theta_deg):
 theta=math.radians(theta_deg);V=vstar*R**3
 return dict(R=R,V=V,theta=theta,F0=2*math.pi*R*G*math.cos(theta),A=1.05*math.sqrt(R/V),B=2.5*R/V,sc=(1+theta/2)*V**(1/3))
def force(s,p):
 return p['F0']/(1+p['A']*s+p['B']*s*s)
def work(p):
 d=math.sqrt(4*p['B']-p['A']**2)
 return 2*p['F0']/d*(math.atan((2*p['B']*p['sc']+p['A'])/d)-math.atan(p['A']/d))
def kcrit(g,p):
 # Net outward force: k(g-s)/2 - F(s). All positive before rupture is sufficient
 # for overdamped, quasistatic reopening along the stipulated path.
 if g<=p['sc']:return None, None
 candidates=[0.0,p['sc']]
 # Stationary points of D(s)=(1+A*s+B*s*s)*(g-s).
 a=-3*p['B'];b=2*(p['B']*g-p['A']);c=p['A']*g-1
 disc=b*b-4*a*c
 if disc>=0:
  for s in [(-b+math.sqrt(disc))/(2*a),(-b-math.sqrt(disc))/(2*a)]:
   if 0<s<p['sc']:candidates.append(s)
 critical_s=max(candidates,key=lambda s:2*force(s,p)/(g-s))
 return 2*force(critical_s,p)/(g-critical_s),critical_s
def stiffness(b):return 3*b['E_hypothesis_Pa']*(math.pi*b['radius_m']**4/4)/b['length_m']**3
def applicable(b,g):
 s=x['beam_screen'];r=b['radius_m'];L=b['length_m']
 return (L/(2*r)>=s['minimum_length_over_diameter']-1e-12 and g/(2*L)<=s['maximum_tip_deflection_over_length']+1e-12 and 1.5*r*g/(L*L)<=s['maximum_geometric_surface_strain']+1e-12)
bridge_rows=[]
for R,g,v,th in itertools.product(x['bridge']['tip_radii_m'],x['bridge']['unloaded_gaps_m'],x['bridge']['volume_over_R_cubed'],x['bridge']['contact_angles_deg']):
 p=parameters(R,v,th);kc,cs=kcrit(g,p)
 bridge_rows.append(dict(tip_radius_m=R,gap_m=g,volume_over_R_cubed=v,angle_deg=th,rupture_distance_m=p['sc'],contact_force_N=p['F0'],separation_work_J=work(p),critical_stiffness_N_m=kc,critical_position_m=cs,reference_gap_allows_quasistatic_rupture=g>p['sc']))
cases=[]
for b,br in itertools.product(x['beams'],bridge_rows):
 k=stiffness(b);kc=br['critical_stiffness_N_m']
 cases.append(dict(beam=b['id'],**br,beam_stiffness_N_m=k,linear_beam_screen=applicable(b,br['gap_m']),satisfies_stipulated_force_path=(kc is not None and k>kc),force_margin=(k/kc if kc else None),note='Computed condition only; no measured restoration or success probability'))
r=x['bridge']['reference'];p=parameters(r['tip_radius_m'],r['volume_over_R_cubed'],r['contact_angle_deg']);g=r['gap_m'];kc,crit_s=kcrit(g,p)
ref=[]
for b in x['beams']:
 k=stiffness(b)
 ref.append(dict(id=b['id'],radius_um=b['radius_m']*1e6,length_um=b['length_m']*1e6,E_hypothesis_MPa=b['E_hypothesis_Pa']/1e6,k_N_m=k,k_required_N_m=kc,force_ratio=k/kc,initial_restoring_force_uN=k*g/2*1e6,initial_capillary_force_uN=p['F0']*1e6,linear_beam_screen=applicable(b,g),satisfies_stipulated_force_path=k>kc,geometric_max_strain=1.5*b['radius_m']*g/b['length_m']**2))
# Energy alone can pass while initial force remains trapped.
energy_coefficient=g*p['sc']/2-p['sc']**2/4
kenergy=work(p)/energy_coefficient
kcounter=(kenergy+2*p['F0']/g)/2
counter=dict(k_energy_only_N_m=kenergy,k_chosen_N_m=kcounter,k_force_path_N_m=kc,available_work_until_rupture_J=kcounter*energy_coefficient,bridge_separation_work_J=work(p),initial_restoring_force_N=kcounter*g/2,initial_capillary_force_N=p['F0'],scope='Constructed energy-versus-force counterexample; not a fabricated material test')
# A second counterexample: initial reopening force passes but the path stalls.
gnear=1.02*p['sc'];kn,kns=kcrit(gnear,p);kstart=2*p['F0']/gnear;kmid=math.sqrt(kstart*kn)
near_counter=dict(unloaded_gap_m=gnear,rupture_distance_m=p['sc'],initial_only_threshold_N_m=kstart,full_path_threshold_N_m=kn,k_chosen_N_m=kmid,initial_restoring_force_N=kmid*gnear/2,initial_capillary_force_N=p['F0'],restoring_force_before_rupture_N=kmid*(gnear-p['sc'])/2,capillary_force_before_rupture_N=force(p['sc'],p),scope='Constructed narrow-gap counterexample; no dynamic reopening time inferred')
head=[]
for a,th in itertools.product(x['drainage']['pore_radii_m'],x['drainage']['advancing_angles_deg']):
 h=-2*G*math.cos(math.radians(th))/(w['density_for_head_kg_m3']*w['g_m_s2']*a)
 head.append(dict(pore_radius_m=a,advancing_angle_deg=th,entry_head_m=h,minimum_pore_radius_for_head_m=a*h/x['drainage']['allowable_head_hypothesis_m']))
pressure=[dict(force_N=f,pad_radius_m=R,minimum_mean_pressure_Pa=f/(math.pi*R*R)) for f,R in itertools.product(x['pressure']['forces_N'],x['pressure']['pad_radii_m'])]
e=x['economics'];vbase=e['arms_per_grain']*math.pi*e['base_arm_radius_m']**2*e['base_arm_length_m'];M=e['base_volume_m3']*e['base_bulk_density_kg_m3']
cost=[]
for b in x['beams']:
 added=e['arms_per_grain']*math.pi*b['radius_m']**2*b['length_m'];ratio=added/vbase;dm=M*ratio
 cost.append(dict(beam=b['id'],added_cylinder_volume_m3_per_grain=added,added_volume_relative_to_base=ratio,added_material_kg=dm,new_bulk_density_kg_m3=e['base_bulk_density_kg_m3']*(1+ratio),added_purchase_JPY=dm*e['price_hypothesis_JPY_kg'],added_annual_material_JPY=dm*e['price_hypothesis_JPY_kg']*e['annual_replacement_fraction']))
# Equal-stiffness taper: integrate compliance, do not infer performance from shape.
def simpson(fun,n=2000):
 h=1/n
 return h/3*(fun(0)+fun(1)+4*sum(fun(i*h) for i in range(1,n,2))+2*sum(fun(i*h) for i in range(2,n,2)))
t=x['taper'];tapers=[];L=t['length_m'];rc=t['control_radius_m'];E=t['E_hypothesis_Pa'];kcontrol=3*E*math.pi*rc**4/(4*L**3)
for alpha in t['alpha']:
 J=simpson(lambda u:(1-u)**2/(1-alpha*u)**(4/3));r0=rc*(3*J)**.25;rt=r0*(1-alpha)**(1/3)
 H=1 if alpha==0 else 3/(5*alpha)*(1-(1-alpha)**(5/3))
 volume=math.pi*r0*r0*L*H;vc=math.pi*rc*rc*L
 compliance=4*L**3*J/(E*math.pi*r0**4);rho_ratio=x['economics']['arms_per_grain']*volume/vbase;dm=M*rho_ratio
 epsroot=4*(kcontrol*g/2)*L/(math.pi*E*r0**3)
 tapers.append(dict(alpha=alpha,length_m=L,root_radius_m=r0,tip_stem_radius_m=rt,compliance_m_N=compliance,k_N_m=1/compliance,force_margin=kcontrol/kc,volume_relative_to_uniform_control=volume/vc,max_nominal_surface_strain=epsroot,root_length_over_diameter=L/(2*r0),added_material_kg=dm,added_purchase_JPY=dm*e['price_hypothesis_JPY_kg'],note='Does not include spherical caps, transitions or stress concentrations'))
root_cases=[]
for label,kb in [('B_short',ref[1]['k_N_m']),('T_taper180',kcontrol)]:
 for kr in x['root_support']['stiffness_N_m']:
  ke=kb*kr/(kb+kr)
  root_cases.append(dict(component=label,branch_k_N_m=kb,root_k_N_m=kr,effective_k_N_m=ke,force_margin=ke/kc,minimum_root_k_N_m=kc*kb/(kb-kc),satisfies_stipulated_force_path=ke>kc))
checks=[]
def chk(name,condition):
 checks.append(dict(name=name,passed=bool(condition)))
 if not condition:raise AssertionError(name)
chk('IAPWS50C rounds to published67.94mN/m',round(G*1000,2)==67.94)
chk('Surface tension decreases over chosen temperatures',gamma(0)>gamma(20)>gamma(50)>0)
chk('Reference unloaded gap exceeds rupture length',g>p['sc'])
# Separate midpoint integration and sampled maximization verify closed forms.
maxworkerror=0.0;maxgriddifference=0.0
for br in bridge_rows:
 pp=parameters(br['tip_radius_m'],br['volume_over_R_cubed'],br['angle_deg']);n=4000;ds=pp['sc']/n
 val=sum(force((i+.5)*ds,pp)*ds for i in range(n));maxworkerror=max(maxworkerror,abs(val-work(pp))/work(pp))
 if br['critical_stiffness_N_m'] is not None:
  gg=br['gap_m'];kg=max(2*force(pp['sc']*i/n,pp)/(gg-pp['sc']*i/n) for i in range(n+1));ka=br['critical_stiffness_N_m']
  chkval=ka>=kg*(1-1e-12) and (ka-kg)/ka<1e-5
  if not chkval:raise AssertionError('kcrit extrema not reproduced')
  maxgriddifference=max(maxgriddifference,abs(ka-kg)/ka)
chk('Analytic bridge work matches midpoint quadrature',maxworkerror<1e-6)
chk('Analytic path threshold matches dense grid',maxgriddifference<1e-5)
chk('Energy can pass while initial opening force fails',counter['available_work_until_rupture_J']>work(p) and counter['initial_restoring_force_N']<p['F0'])
chk('Initial force can pass but full opening path fail',near_counter['initial_restoring_force_N']>p['F0'] and near_counter['restoring_force_before_rupture_N']<near_counter['capillary_force_before_rupture_N'])
chk('Narrow-gap critical threshold matches dense path',math.isclose(kn,max(2*force(p['sc']*i/5000,p)/(gnear-p['sc']*i/5000) for i in range(5001)),rel_tol=1e-5))
chk('Reference short beam satisfies hypothetical path',next(v for v in ref if v['id']=='B_short')['satisfies_stipulated_force_path'])
chk('10x softening can reverse path decision',not next(v for v in ref if v['id']=='B_softened')['satisfies_stipulated_force_path'])
chk('Reference comparisons satisfy geometric beam screens',all(v['linear_beam_screen'] for v in ref))
cb=next(v for v in x['beams'] if v['id']=='C_long_equal_volume');db=next(v for v in x['beams'] if v['id']=='D_short_equal_volume')
chk('C and D cylinder volumes equal',math.isclose(cb['radius_m']**2*cb['length_m'],db['radius_m']**2*db['length_m']))
chk('Equal-volume stiffness ratio1024',math.isclose(stiffness(db)/stiffness(cb),1024))
chk('Narrower hydrophobic pore requires greater head',all(next(v for v in head if v['advancing_angle_deg']==th and v['pore_radius_m']==25e-6)['entry_head_m']>next(v for v in head if v['advancing_angle_deg']==th and v['pore_radius_m']==500e-6)['entry_head_m'] for th in x['drainage']['advancing_angles_deg']))
chk('Drainage threshold obeys specified5mm target',all(math.isclose(v['entry_head_m']*v['pore_radius_m']/v['minimum_pore_radius_for_head_m'],x['drainage']['allowable_head_hypothesis_m']) for v in head))
chk('Smaller support projection raises stress lower bound',all(next(v for v in pressure if v['force_N']==f and v['pad_radius_m']==5e-6)['minimum_mean_pressure_Pa']>next(v for v in pressure if v['force_N']==f and v['pad_radius_m']==30e-6)['minimum_mean_pressure_Pa'] for f in x['pressure']['forces_N']))
chk('Base material mass108t',M==108000)
chk('B reset fingers add25percent cylinder material',math.isclose(next(v for v in cost if v['beam']=='B_short')['added_volume_relative_to_base'],.25))
chk('Tapers preserve target compliance',all(math.isclose(v['k_N_m'],kcontrol,rel_tol=1e-10) for v in tapers))
chk('Uniform taper limit restores control radius and volume',math.isclose(tapers[0]['root_radius_m'],rc,rel_tol=1e-10) and math.isclose(tapers[0]['volume_relative_to_uniform_control'],1,rel_tol=1e-10))
chk('Taper family meets geometric beam screening',all(v['root_length_over_diameter']>=5 and v['max_nominal_surface_strain']<=.02 and g/(2*L)<=.1 for v in tapers))
chk('Taper compliance integration converges',all(abs(simpson(lambda u:(1-u)**2/(1-v['alpha']*u)**(4/3),4000)-simpson(lambda u:(1-u)**2/(1-v['alpha']*u)**(4/3),2000))<1e-9 for v in tapers))
chk('Free root gives no relative restoring stiffness',all(v['effective_k_N_m']==0 for v in root_cases if v['root_k_N_m']==0))
chk('Root stiffness threshold closes series compliance',all(math.isclose(v['branch_k_N_m']*v['minimum_root_k_N_m']/(v['branch_k_N_m']+v['minimum_root_k_N_m']),kc) for v in root_cases))
chk('Budget is not physical test count',x['physical_tests_our_material']==0 and x['success_probability'] is None)
result=dict(physical_tests_our_material=0,success_probability=None,water_surface_tension_N_m={str(t):gamma(t) for t in w['temperatures_C']},reference_bridge=dict(**p,gap_m=g,kcrit_N_m=kc,work_J=work(p)),reference_beams=ref,energy_counterexample=counter,narrow_gap_counterexample=near_counter,bridge_conditions=bridge_rows,beam_bridge_cases=cases,drainage=head,pressure=pressure,economics=cost,taper=tapers,root_support=root_cases,case_count=len(cases),note='No fit to ski data; no success frequency from parameter grid; a force-path pass is only conditional component evidence.')
for name,obj in [('results.json',result),('validation.json',dict(count=len(checks),all_passed=True,checks=checks,max_relative_work_quadrature_error=maxworkerror,max_relative_threshold_grid_difference=maxgriddifference,scope='Algebra, limiting behavior and stated model only'))]:
 (P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')
with (P/'component_cases.csv').open('w',encoding='utf8',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=list(cases[0]),lineterminator='\n');writer.writeheader();writer.writerows(cases)
print(json.dumps(dict(cases=len(cases),bridge_conditions=len(bridge_rows),checks=len(checks),reference=ref,energy_counterexample=counter),ensure_ascii=False))
