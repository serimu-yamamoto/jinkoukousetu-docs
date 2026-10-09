from pathlib import Path
import math,json,csv
P=Path(__file__).resolve().parent;I=json.loads((P/'inputs.json').read_text(encoding='utf-8'));B=I['baseline'];G=I['geometry'];S=I['sensitivity']
C=G['area_m2']*1000/G['modules_per_grain']*1e6 # uN per kPa, per module
checks=[]
def ck(n,ok):
 if not ok:raise SystemExit('FAILED: '+n)
 checks.append(n)
def eq(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10)
def js(n,d):(P/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def out(n,rows):
 with (P/n).open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def events(b):
 fo=b['opening_k_N_m']*b['opening_predeflection_um'];fx=b['return_k_N_m']*b['initial_x_um'];a=b['normal_adhesion_uN'];ta=b['tangential_adhesion_uN']
 po=(fo-a)/C;pb=(b['opening_k_N_m']*(b['opening_predeflection_um']-b['bridge_rupture_um'])-a)/C
 ps=po+(fx-ta)/(b['mu_static']*C) if fx>ta else None
 nsl=(fx-ta)/b['mu_static'] if fx>ta else 0
 xafter=(b['mu_kinetic']*nsl+ta)/b['return_k_N_m'] if ps is not None else b['initial_x_um']
 dx=b['initial_x_um']-xafter
 return {'opening_pressure_kPa':po,'rupture_pressure_kPa':pb,'first_slip_pressure_kPa':ps,'contact_normal_at_first_slip_uN':nsl,'x_after_first_slip_um':xafter,'first_slip_jump_um':dx,'unresolved_first_jump_energy_nJ':.5*b['return_k_N_m']*dx**2/1000,'first_slip_before_opening':ps is not None and ps>po}
def state(p,b,after_event=True):
 e=events(b);ko=b['opening_k_N_m'];kx=b['return_k_N_m'];w=p*C;a=b['normal_adhesion_uN'];ta=b['tangential_adhesion_uN'];fo=ko*b['opening_predeflection_um']
 # Normal reaction balances external load, attractive bridge and opener.
 intact=not(p<e['rupture_pressure_kPa'] or (after_event and eq(p,e['rupture_pressure_kPa'])))
 aa=a if intact else 0;tt=ta if intact else 0
 N=max(w+aa-fo,0);y=max(b['opening_predeflection_um']-(w+aa)/ko,0)
 ps=e['first_slip_pressure_kPa'];sliding=ps is not None and (p<ps or (after_event and eq(p,ps)))
 if not intact:x=0;mode='bridge_broken_returned'
 elif sliding:x=min(b['initial_x_um'],(b['mu_kinetic']*N+tt)/kx);mode='contact_sliding' if N>0 else 'bridge_limited'
 else:x=b['initial_x_um'];mode='stuck'
 return {'pressure_kPa':p,'after_event':after_event,'mode':mode,'normal_reaction_uN':N,'normal_gap_um':y,'tangential_offset_um':x,'bridge_intact':intact,'normal_force_residual_uN':N+ko*(b['opening_predeflection_um']-y)-w-aa,'return_force_uN':kx*x,'static_capacity_uN':b['mu_static']*N+tt}
E=events(B)
points=[(20-i*.05,True) for i in range(401)]
for key in ['first_slip_pressure_kPa','opening_pressure_kPa','rupture_pressure_kPa']:
 p=E[key]
 if p is not None and 0<=p<=20:points.extend([(p,False),(p,True)])
points.sort(key=lambda a:(-a[0],a[1]));path=[state(p,B,a) for p,a in points];out('coupled_unloading_path.csv',path)
variants=[]
for scale in S['modulus_scales']:
 for endp in S['final_pressures_kPa']:
  for ta in S['tangential_adhesion_uN']:
   for am in S['normal_adhesion_multipliers']:
    for ms in S['mu_static']:
     b=dict(B);b.update(opening_k_N_m=B['opening_k_N_m']*scale,return_k_N_m=B['return_k_N_m']*scale,tangential_adhesion_uN=ta,normal_adhesion_uN=B['normal_adhesion_uN']*am,mu_static=ms,mu_kinetic=ms*S['mu_kinetic_fraction']);s=state(endp,b);e=events(b)
     variants.append({'modulus_scale':scale,'pressure_end_kPa':endp,'tangential_adhesion_uN':ta,'normal_adhesion_multiplier':am,'mu_static':ms,'mu_kinetic':b['mu_kinetic'],'first_slip_pressure_kPa':e['first_slip_pressure_kPa'],'normal_gap_um':s['normal_gap_um'],'x_residual_um':s['tangential_offset_um'],'bridge_broken':not s['bridge_intact'],'all_coupled_conditions':not s['bridge_intact'] and s['tangential_offset_um']<=1,'unresolved_jump_energy_nJ':e['unresolved_first_jump_energy_nJ']})
out('coupled_sensitivity.csv',variants)
# A straight loaded latch is a distinct constraint. Its extraction friction must be paid.
latch=[]
for kxscale in [1,1/3]:
 for ko in [20,30]:
  for mu in I['latch']['frictions']:
   fx=B['return_k_N_m']*kxscale*B['initial_x_um'];res=C+B['normal_adhesion_uN']+mu*fx
   margin=ko*(15-10)-res
   latch.append({'return_stiffness_scale':kxscale,'opening_k_N_m':ko,'mu_latch':mu,'held_return_force_uN':fx,'latch_extraction_resistance_uN':mu*fx,'end_force_margin_uN_at_1kPa':margin,'necessary_opening_condition':margin>0,'minimum_opening_k_N_m':res/5,'complete_release_pressure_kPa':(ko*5-B['normal_adhesion_uN']-mu*fx)/C,'closure_pressure_no_adhesion_kPa':ko*15/C})
out('latch_tradeoff.csv',latch)
# Complementarity correction: initial contact pressure is not the total applied pressure.
threshold=[]
for mu in [.1,.3,.6,.8]:
 for ta in [0,4,40,300]:
  b=dict(B);b.update(mu_static=mu,tangential_adhesion_uN=ta);e=events(b)
  threshold.append({'mu_static':mu,'tangential_adhesion_uN':ta,**e})
out('event_order.csv',threshold)
# First jump energy audit: release of elastic energy = sliding work + unresolved transient energy.
xo=B['initial_x_um'];xn=E['x_after_first_slip_um'];fk=B['mu_kinetic']*E['contact_normal_at_first_slip_uN']+B['tangential_adhesion_uN'];kx=B['return_k_N_m']
release=.5*kx*(xo**2-xn**2)/1000;work=fk*(xo-xn)/1000;unresolved=release-work
Ngr=G['course_area_m2']*G['bed_depth_m']*G['packing_fraction']/((G['W_um']*1e-6)**2*(G['H_um']*1e-6))
def mass(beams):return Ngr*beams['count']*beams['width_um']*beams['thickness_um']*beams['length_um']*1e-18*B['density_kg_m3']
mo=mass(B['opening_beams']);mx=mass(B['return_beams']);ml=Ngr*G['modules_per_grain']*I['latch']['extra_latch_volume_um3_per_module']*1e-18*B['density_kg_m3']
config=[('H59/H60-P same beams',mx,mo,0),('H60-L original reset + stiffer opener',mx,mo*1.5,ml),('H60-L weaker reset + stiffer opener',mx/3,mo*1.5,ml)]
cost=[]
for name,mx0,mo0,ml0 in config:
 for price in S['prices_yen_kg']:
  cost.append({'configuration':name,'return_beam_mass_kg':mx0,'opening_beam_mass_kg':mo0,'latch_allowance_mass_kg':ml0,'sum_partial_mass_kg':mx0+mo0+ml0,'raw_price_yen_kg':price,'raw_partial_cost_yen':(mx0+mo0+ml0)*price,'tax_included':False,'qualified_latch_geometry':False})
out('partial_component_cost.csv',cost)
jump=[]
for ratio in [.25,.5,.75,.9,1]:
 b={**B,'mu_kinetic':B['mu_static']*ratio};e=events(b)
 jump.append({'mu_kinetic_over_static':ratio,'mu_static':B['mu_static'],'mu_kinetic':b['mu_kinetic'],'first_slip_jump_um':e['first_slip_jump_um'],'unresolved_transient_energy_nJ':e['unresolved_first_jump_energy_nJ']})
out('static_kinetic_jump.csv',jump)
R={'cycle':60,'physical_tests':0,'success_probability':None,'force_conversion_uN_per_kPa':C,'baseline_events':E,'end_1kPa':state(1,B),'end_3kPa':state(3,B),'first_jump_energy':{'elastic_release_nJ':release,'constant_kinetic_resistance_work_nJ':work,'unresolved_transient_energy_nJ':unresolved,'warning':'Not all released elastic energy is accounted for by steady sliding friction. No restitution/dynamics solved.'},'partial_mass_kg':{'opening_beams':mo,'return_beams':mx,'latch_allowance':ml},'row_counts':{'path':len(path),'sensitivity':len(variants),'latch':len(latch),'order':len(threshold),'cost':len(cost)},'concept':'H60-P permits partial sliding during unload. H60-L straight loaded latch is a competing unbuilt branch. No proof of real ski feel.'}
cross=[]
for kap in [-.5,-.25,0,.25,.5]:
 for press in [.5,1,3]:
  kxy=kap*math.sqrt(B['return_k_N_m']*B['opening_k_N_m']);keff=B['opening_k_N_m']-kxy*kxy/B['return_k_N_m'];W=press*C
  yy=15-W/keff;xx=kxy*W/(B['return_k_N_m']*keff)
  cross.append({'kappa':kap,'pressure_kPa':press,'Kxy_N_m':kxy,'effective_normal_k_N_m':keff,'post_break_gap_um':yy,'post_break_x_um':xx,'post_break_state_geometrically_consistent':yy>=10,'within_assumed_1um_x':abs(xx)<=1,'normal_equilibrium_residual_uN':B['opening_k_N_m']*(15-yy)-kxy*xx-W,'tangent_equilibrium_residual_uN':B['return_k_N_m']*xx+kxy*(yy-15)})
out('cross_axis_coupling.csv',cross)
a=math.sqrt(B['return_k_N_m']*B['opening_k_N_m'])/C
kaplim=2*a/(1+math.sqrt(1+4*a*a))
R['cross_axis']={'kappa_limit_for_1um_at_1kPa_after_break':kaplim,'Kxy_limit_N_m':kaplim*math.sqrt(B['return_k_N_m']*B['opening_k_N_m']),'definition':'Kxy=kappa*sqrt(Kxx*Kyy); symmetric linear elastic stiffness; |kappa|<1 for positive definiteness. Free post-bridge state only, not full coupled trajectory.'}
R['row_counts']['cross_axis']=len(cross);R['row_counts']['jump']=len(jump)
ck('cross-axis free equilibria',all(abs(r['normal_equilibrium_residual_uN'])<1e-8 and abs(r['tangent_equilibrium_residual_uN'])<1e-8 for r in cross))
ck('zero cross coupling reproduces baseline post-break',eq(next(r for r in cross if r['kappa']==0 and r['pressure_kPa']==1)['post_break_gap_um'],R['end_1kPa']['normal_gap_um']))
ck('half cross coupling defeats 1um despite bridge clear',next(r for r in cross if r['kappa']==.5 and r['pressure_kPa']==1)['post_break_state_geometrically_consistent'] and not next(r for r in cross if r['kappa']==.5 and r['pressure_kPa']==1)['within_assumed_1um_x'])
ck('cross coupling bound algebra',eq(kaplim*C/(math.sqrt(B['return_k_N_m']*B['opening_k_N_m'])*(1-kaplim**2)),1))
ck('equal static kinetic removes first threshold jump',eq(jump[-1]['first_slip_jump_um'],0))
ck('closer friction coefficients reduce unresolved transient',jump[-2]['unresolved_transient_energy_nJ']<jump[0]['unresolved_transient_energy_nJ'])
ck('force conversion',eq(C,62.5))
ck('baseline open point reproduces H59',eq(E['opening_pressure_kPa'],4.731695335761552))
ck('baseline rupture point reproduces H59',eq(E['rupture_pressure_kPa'],1.531695335761552))
ck('nonzero reset precedes opening without latch',E['first_slip_before_opening'])
ck('threshold difference independent of opener',eq(E['first_slip_pressure_kPa']-E['opening_pressure_kPa'],(kx*10-4)/(.6*C)))
ck('normal balance every path state',all(abs(r['normal_force_residual_uN'])<1e-8 for r in path))
ck('nonpenetration',all(r['normal_gap_um']>=0 and r['normal_reaction_uN']>=0 for r in path))
ck('normal complementarity',all(abs(r['normal_gap_um']*r['normal_reaction_uN'])<1e-7 for r in path))
ck('contact static equilibria before first slip',all(r['return_force_uN']<=r['static_capacity_uN']+1e-8 for r in path if r['mode']=='stuck'))
ck('no imaginary contact friction across a gap',all(r['normal_reaction_uN']==0 for r in path if r['normal_gap_um']>0))
ck('1kPa bridge breaks and x returns',not R['end_1kPa']['bridge_intact'] and R['end_1kPa']['tangential_offset_um']==0)
ck('3kPa bridge persists despite small x',R['end_3kPa']['bridge_intact'] and R['end_3kPa']['tangential_offset_um']<1)
ck('first jump energy identity',eq(unresolved,E['unresolved_first_jump_energy_nJ']))
ck('unresolved first jump is positive',unresolved>0)
ck('first jump is within stroke',0<E['first_slip_jump_um']<10)
ck('strong shear adhesion can suppress pre-opening slip',not events({**B,'tangential_adhesion_uN':300})['first_slip_before_opening'])
ck('original latch mu .3 fails',not next(r for r in latch if r['return_stiffness_scale']==1 and r['opening_k_N_m']==20 and r['mu_latch']==.3)['necessary_opening_condition'])
ck('weaker reset stiffer opener mu .6 force bound met',next(r for r in latch if r['return_stiffness_scale']<1 and r['opening_k_N_m']==30 and r['mu_latch']==.6)['necessary_opening_condition'])
ck('higher latch friction increases extraction cost',latch[2]['end_force_margin_uN_at_1kPa']<latch[0]['end_force_margin_uN_at_1kPa'])
ck('baseline beam masses reproduce preceding cycles',eq(mo,6371.751230260105) and eq(mx,8849.654486472366))
ck('latch allowance not free',ml>0)
ck('relaxed ordering does not invent mass saving',eq(cost[0]['sum_partial_mass_kg'],mo+mx))
ck('density and quantity use external envelope',eq(Ngr,3429460598986.378))
ck('no made up success probability',R['success_probability'] is None and R['physical_tests']==0)
js('results.json',R);js('validation.json',{'kind':'algebra and path consistency, not experimental validation','count':len(checks),'passed':True,'checks':checks})
print(json.dumps({'checks':len(checks),'baseline_events':E,'end_1kPa':R['end_1kPa'],'end_3kPa':R['end_3kPa'],'mass':R['partial_mass_kg']},ensure_ascii=False))
