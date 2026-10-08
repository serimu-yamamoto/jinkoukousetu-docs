"""Cycle 59: material qualification bounds, NOT prediction of skiing success."""
from pathlib import Path
import csv, json, math
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
checks=[]
def ck(name,ok):
    if not ok: raise SystemExit('FAILED: '+name)
    checks.append(name)
def close(a,b): return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-13)
def write(name,obj): (P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def csvout(name,rows):
    with (P/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def stiffness(E,b,t,l):return E*1e6*b*1e-6*(t*1e-6)**3/(2*(l*1e-6)**3)
C=I['cam'];O=I['opening'];G=I['geometry'];S=I['sensitivity'];M=I['manufacturer']
k=stiffness(C['E_MPa'],C['width_um'],C['thickness_um'],C['length_um'])
Fa=2*math.pi*C['bridge_radius_um']*1e-6*C['gamma_N_m']
s=math.tan(math.radians(C['angle_deg']));tol=C['return_tolerance_um']*1e-6
mu_max=(k*tol*s*s-Fa)/(s*(k*tol+Fa))
def cam(E,mu):
    K=stiffness(E,C['width_um'],C['thickness_um'],C['length_um'])
    rp=(s+mu)/(1-mu*s) if mu*s<1-1e-12 else None
    rm=(s-mu)/(1+mu*s)
    return {'E_MPa':E,'mu_static':mu,'stiffness_N_m':K,'forward_finite':rp is not None,'return_direction':rm>1e-12,'residual_um':min(C['stroke_um'],Fa/(K*s*rm)*1e6) if rm>1e-12 else C['stroke_um'],'E_required_MPa':Fa/(s*rm*tol)/stiffness(1,C['width_um'],C['thickness_um'],C['length_um']) if rm>1e-12 else None,'pressure_to_start_at_full_stroke_kPa':4*K*C['stroke_um']*1e-6*s*rp/O['area_m2']/1000 if rp is not None else None}
cm=[cam(e,m) for e in S['E_MPa'] for m in S['mu_static']]
csvout('cam_material_bounds.csv',cm)
raw=list(csv.DictReader((P/'published_static_water.csv').open(encoding='utf-8')))
vals=[float(r['mu_'+str(h)+'A']) for r in raw for h in [75,80,83,93]]
source_eval=[]
for r in raw:
 for h in [75,80,83,93]:
    m=float(r['mu_'+str(h)+'A']);rr=cam(80,m)
    source_eval.append({'source_row':r['source_row'],'hardness_ShA':h,'published_mu_static':m,'hypothetical_residual_um':rr['residual_um'],'hypothetical_required_E50_MPa':rr['E_required_MPa'],'transfer_to_our_material_valid':False})
csvout('published_counterexamples.csv',source_eval)
# Sliding loss uses kinetic friction; opening from rest uses static friction.
kin=[]
for ms in S['mu_static']:
 for md in S['mu_dynamic']:
    if md>ms:continue
    rp=(s+md)/(1-md*s);rm=(s-md)/(1+md*s)
    kin.append({'mu_static':ms,'mu_dynamic':md,'kinetic_loss_fraction':1-rm/rp,'static_restart_possible':ms*s<1-1e-12 and ms<s-1e-12,'static_wet_residual_um':cam(80,ms)['residual_um']})
csvout('static_kinetic_separation.csv',kin)
ko=stiffness(O['E_MPa'],O['width_um'],O['thickness_um'],O['length_um'])
y0=O['predeflection_um']*1e-6
area=O['area_m2'];n=O['modules_per_grain']
def opening(E,pressure,fraction,adhesion,break_um):
    K=ko*E/O['E_MPa'];d=break_um*1e-6;W=pressure*1000*area*fraction/n;A=Fa*adhesion
    margin=K*(y0-d)-W-A
    work=K*(y0*d-.5*d*d);required=(W+A)*d
    return {'E50_MPa':E,'residual_pressure_kPa':pressure,'load_fraction':fraction,'adhesion_multiplier':adhesion,'required_separation_um':break_um,'stroke_available':d<y0,'end_force_margin_uN':margin*1e6,'available_work_nJ':work*1e9 if d<=y0 else None,'required_work_nJ':required*1e9,'necessary_force_condition':d<y0 and margin>0,'energy_only_condition':d<=y0 and work>required}
op=[opening(e,p,f,a,d) for e in S['E_MPa'] for p in S['residual_pressure_kPa'] for f in S['opening_load_fractions'] for a in S['adhesion_multipliers'] for d in S['bridge_break_um']]
csvout('opening_force_path.csv',op)
baseline=opening(100,1,1,1,10);half=opening(50,1,1,1,10)
# An energy-passing but force-failing case is deliberately retained.
counter=opening(100,3,1,1,10)
complete_pressure=(ko*(y0-10e-6)-Fa)*n/area/1000
start_pressure=(ko*y0-Fa)*n/area/1000
closure_pressure=ko*y0*n/area/1000
Ereq_open=(1000*area/n+Fa)/(ko*(y0-10e-6))*O['E_MPa']
N=G['course_area_m2']*G['bed_depth_m']*G['packing_fraction']/((G['W_um']*1e-6)**2*G['H_um']*1e-6)
volume=N*n*2*O['width_um']*O['thickness_um']*O['length_um']*1e-18
cost=[]
for rho in [1120,1010]:
 mass=volume*rho
 for price in S['prices_yen_kg']:
    cost.append({'density_kg_m3':rho,'incremental_mass_kg':mass,'raw_price_yen_kg':price,'raw_cost_yen':mass*price,'tax_rate_assumption':.1,'raw_cost_with_assumed_tax_yen':mass*price*1.1,'processing_frames_pads_factory_civil_included':False})
csvout('additional_opening_cost.csv',cost)
thermal=M['linear_thermal_expansion_per_K']*(50-23)*120
wet=((1+M['water_mass_fraction_immersion']*M['density_kg_m3']/1000)**(1/3)-1)*120
# Constant adhesive force is an intentionally simplified force envelope.
R={'cycle':59,'physical_tests':0,'success_probability':None,'published_static_rows':len(raw),'published_static_values':len(vals),'published_mu_min':min(vals),'published_mu_max':max(vals),'cam':{'k_N_m':k,'Fa_uN':Fa*1e6,'mu_max_for_1um':mu_max,'at_mu_06':cam(80,.6),'at_published_max':cam(80,max(vals)),'at_mu_08':cam(80,.8)},'opening':{'k_N_m':ko,'baseline':baseline,'half_E_counterexample':half,'energy_only_counterexample':counter,'complete_pressure_kPa':complete_pressure,'start_pressure_kPa':start_pressure,'closure_pressure_no_adhesion_kPa':closure_pressure,'E_required_for_baseline_MPa':Ereq_open,'root_strain_proxy_at_preload':1.5*O['thickness_um']*O['predeflection_um']/O['length_um']**2,'energy_per_grain_nJ':n*ko*(y0*10e-6-.5*(10e-6)**2)*1e9},'material_dimensions':{'thermal_one_sided_120um_23to50_um':thermal,'ideal_volume_addition_water_one_sided_120um_um':wet,'sum_only_if_same_gap_closing_sign_um':thermal+wet,'measured_gap_change':None},'cost':{'grain_count':N,'added_beam_volume_m3':volume,'additional_mass_1120_kg':volume*1120,'additional_mass_1010_kg':volume*1010},'rows':{'cam':len(cm),'source_counterexamples':len(source_eval),'static_kinetic':len(kin),'opening':len(op),'cost':len(cost)}}
over=[]
for rho in [200,400,600]:
 for depth in [.1,.3,.45]:
    press=rho*9.80665*depth*math.cos(math.radians(30))/1000
    oo=opening(100,press,1,1,10)
    over.append({'assumed_bulk_density_kg_m3':rho,'normal_depth_m':depth,'slope_deg':30,'mean_drained_normal_pressure_kPa':press,'necessary_opening_force_condition':oo['necessary_force_condition'],'end_force_margin_uN':oo['end_force_margin_uN']})
csvout('bed_overburden.csv',over)
R['overburden']={'critical_mean_density_kg_m3_at_045m_30deg':complete_pressure*1000/(9.80665*.45*math.cos(math.radians(30))),'force_chains_water_pressure_not_included':True}
R['rows']['overburden']=len(over)
ck('overburden doubles with bulk density',close(over[2]['mean_drained_normal_pressure_kPa']*2,over[5]['mean_drained_normal_pressure_kPa']))
ck('600 kg m3 deepest bed defeats baseline opener',not over[8]['necessary_opening_force_condition'])
ck('source table 13 rows 52 coefficients',len(raw)==13 and len(vals)==52)
ck('source min and max verified against table',min(vals)==.211 and max(vals)==.768)
ck('published maximum is not universally assigned',all(not x['transfer_to_our_material_valid'] for x in source_eval))
ck('H58 stiffness independent reproduction',close(k,17.375573285869734))
ck('zero friction dry cam reversible',close((s-0)/(1+0*s),(s+0)/(1-0*s)))
ck('static threshold satisfies return force',close(k*tol*s*(s-mu_max)/(1+mu_max*s),Fa))
ck('mu .6 below threshold but .768 above',.6<mu_max<.768)
ck('mu 1 has no reciprocal cam interval',not cam(80,1)['forward_finite'] and not cam(80,1)['return_direction'])
ck('doubling E halves unsaturated residual',close(cam(80,.6)['residual_um'],2*cam(160,.6)['residual_um']))
ck('opening nominal k20',close(ko,20))
ck('opening baseline endpoint force',close(baseline['end_force_margin_uN'],100-62.5-Fa*1e6))
ck('full-path baseline passes necessary conditions',baseline['necessary_force_condition'] and baseline['energy_only_condition'])
ck('energy alone gives false pass at 3kPa',counter['energy_only_condition'] and not counter['necessary_force_condition'])
ck('20um bridge exceeds 15um free travel',not opening(100,.25,.25,1,20)['stroke_available'])
ck('halved modulus fails baseline',not half['necessary_force_condition'])
ck('higher background pressure narrows release',complete_pressure<start_pressure<closure_pressure)
ck('required modulus equality',abs(opening(Ereq_open,1,1,1,10)['end_force_margin_uN'])<1e-8)
ck('force integral equals spring energy',close((ko*y0+ko*(y0-10e-6))*.5*10e-6,ko*(y0*10e-6-.5*(10e-6)**2)))
ck('four modules work sum',close(R['opening']['energy_per_grain_nJ'],8))
ck('mass-volume relation',close(R['cost']['additional_mass_1120_kg']/R['cost']['additional_mass_1010_kg'],1120/1010))
ck('thermal one-side expansion',close(thermal,.5508))
ck('water volume proxy inversion',close((1+wet/120)**3,1+.012*1.01))
ck('no probability manufactured',R['success_probability'] is None and R['physical_tests']==0)
write('results.json',R);write('validation.json',{'kind':'algebra and transcription checks, not physical validation','count':len(checks),'checks':checks,'passed':True})
print(json.dumps({'checks':len(checks),'mu_limit':mu_max,'E_at_mu0768':R['cam']['at_published_max']['E_required_MPa'],'opening':baseline,'complete_pressure_kPa':complete_pressure,'mass_kg':volume*1120,'physical_tests':0},ensure_ascii=False))
