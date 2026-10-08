"""Cycle 54: kinematic and geometric diagnostics, NOT material performance prediction."""
from pathlib import Path
import csv,json,math
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
def put(name,x): (P/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def table(name,rows):
    with (P/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def analytic(deg):
    b=math.radians(deg)
    return 0.0 if b==0 else .5-math.sin(2*b)/(4*b)
def numerical(deg,n,extra=0):
    # x = X sin(t), beta = b sin(t). Constant N; mu multiplier optional.
    b=math.radians(deg);num=den=0
    for j in range(n):
        t=2*math.pi*(j+.5)/n;s=math.sin(b*math.sin(t))**2
        work=abs(math.cos(t))*(1+extra*s)
        num+=work*s;den+=work
    return num/den
rot=[]
for b in I['rotation_amplitudes_deg']:
    for n in I['integration_steps']:
        k=numerical(b,n)
        rot.append(dict(amplitude_deg=b,steps=n,analytic_CS=analytic(b),numerical_CS=k,abs_error=abs(k-analytic(b))))
f=1-(1-I['groove_width_um']/I['groove_pitch_um'])**2
tex=[]
for loss in I['wear_land_loss_um']:
    d=max(0,I['groove_depth_um']-loss)
    tex.append(dict(land_loss_um=loss,remaining_depth_um=d,groove_area_fraction=f,
      ideal_unfiltered_Sa_um=2*f*(1-f)*d,ideal_unfiltered_Sq_um=d*math.sqrt(f*(1-f)),
      land_area_fraction=1-f if d>0 else 1,pressure_multiplier_if_all_load_on_lands=1/(1-f) if d>0 else 1,
      open_channel_cross_section_ratio=d/I['groove_depth_um'],
      mass_remaining_fraction_vs_flat_cap=((I['cap_thickness_um']-loss)-f*d)/I['cap_thickness_um']))
# Same areal Sa, different maximum steps and load bearing fractions.
same=[]
for frac in [.05,.19,.5]:
    target=.5; depth=target/(2*frac*(1-frac))
    same.append(dict(groove_area_fraction=frac,Sa_um=target,depth_um=depth,land_pressure_multiplier=1/(1-frac)))
# Counterexample: equal-distance longitudinal reversals have CS=0, not an isotropic path.
paths=[('straight_reverse', [0,180], [1,1]),('two_directions_0_90',[0,90],[1,1]),('rotation_pm30',[-30,30],[1,1]),('uniform_azimuth',list(range(360)),[1]*360)]
path=[]
for label,angles,weights in paths:
    den=sum(weights);xx=sum(w*math.cos(math.radians(a))**2 for a,w in zip(angles,weights))/den
    yy=1-xx;xy=sum(w*math.cos(math.radians(a))*math.sin(math.radians(a)) for a,w in zip(angles,weights))/den
    eig=(1-math.sqrt((xx-yy)**2+4*xy*xy))/2
    path.append(dict(path=label,work_fraction_transverse_to_prescribed_x=yy,minimum_transverse_work_fraction=max(0,eig),not_material_orientation_solution=True))
coat=[]
for thickness in I['cap_thicknesses_um']:
    area=I['cap_count_per_particle']*(I['cap_side_um']*1e-6)**2
    flat_mass=area*thickness*1e-6*I['cap_density_kg_m3']*I['candidate_particle_count']
    removed=area*f*I['groove_depth_um']*1e-6*I['cap_density_kg_m3']*I['candidate_particle_count']
    for price in I['cap_price_yen_kg']:
        coat.append(dict(thickness_um=thickness,flat_cap_mass_kg=flat_mass,grooved_cap_mass_kg=flat_mass-removed,
          cap_price_yen_kg=price,net_material_yen=(flat_mass-removed)*price,
          minimum_life_gain_vs_body_only=(I['candidate_body_mass_kg']*I['body_price_yen_kg']+(flat_mass-removed)*price)/(I['candidate_body_mass_kg']*I['body_price_yen_kg'])))
sel=next(x for x in coat if x['thickness_um']==5 and x['cap_price_yen_kg']==3000)
basecost=I['candidate_body_mass_kg']*I['body_price_yen_kg']
cost=[]
for life in I['functional_life_multiplier']:
    cost.append(dict(assumed_life_multiplier=life,assumed_life_years=life*I['body_life_years'],
       annual_whole_batch_replacement_yen=(basecost+sel['net_material_yen'])/(life*I['body_life_years']),
       ratio_to_body_only_annual_material_cost=(1+sel['net_material_yen']/basecost)/life))
checks=[]
def chk(name,cond):
    checks.append(dict(name=name,passed=bool(cond)))
    if not cond: raise AssertionError(name)
chk('zero_rotation_zero_CS',analytic(0)==0)
chk('central_30deg_analytic',abs(analytic(30)-(.5-3*math.sqrt(3)/(4*math.pi)))<1e-14)
chk('integration_max_error_40000',max(x['abs_error'] for x in rot if x['steps']==40000)<1e-8)
chk('integration_converges_30deg',abs(numerical(30,40000)-analytic(30))<abs(numerical(30,400)-analytic(30)))
chk('published_central_value_agrees_within_0_001_not_exact',abs(analytic(30)-I['published_central_CS'])<.001)
chk('constant_azimuth_offset_does_not_create_CS',abs(path[0]['minimum_transverse_work_fraction'])<1e-12)
chk('equal_orthogonal_directions_half',abs(path[1]['minimum_transverse_work_fraction']-.5)<1e-12)
chk('discrete_pm30_quarter_not_sinusoidal',abs(path[2]['minimum_transverse_work_fraction']-.25)<1e-12)
chk('uniform_azimuth_half',abs(path[3]['minimum_transverse_work_fraction']-.5)<1e-12)
chk('cross_groove_union_no_double_count',abs(f-.19)<1e-12)
chk('selected_Sa',abs(tex[0]['ideal_unfiltered_Sa_um']-.4617)<1e-12)
chk('partial_wear_channel_area_ratio',abs(tex[2]['open_channel_cross_section_ratio']-2/3)<1e-12)
chk('groove_disappears',tex[-1]['remaining_depth_um']==0 and tex[-1]['ideal_unfiltered_Sa_um']==0)
chk('Sa_does_not_define_depth',same[0]['depth_um']>5*same[-1]['depth_um'])
chk('mass_cost_monotone_thickness',coat[0]['grooved_cap_mass_kg']<coat[3]['grooved_cap_mass_kg']<coat[6]['grooved_cap_mass_kg'])
chk('fixed_added_mass_removed_volume',all(abs((x['flat_cap_mass_kg']-x['grooved_cap_mass_kg'])-(coat[0]['flat_cap_mass_kg']-coat[0]['grooved_cap_mass_kg']))<1e-9 for x in coat))
chk('half_life_doubles_material_cost',abs(cost[1]['annual_whole_batch_replacement_yen']/cost[2]['annual_whole_batch_replacement_yen']-2)<1e-12)
chk('no_physical_probability',I['physical_tests']==0 and I['success_probability'] is None)
for name,rows in [('rotation.csv',rot),('texture_wear.csv',tex),('same_Sa.csv',same),('paths.csv',path),('cap_cost.csv',coat),('life_cost.csv',cost)]: table(name,rows)
result=dict(cycle=54,base_commit=I['base_commit'],physical_tests=0,success_probability=None,
 central_CS_30=analytic(30),source_table_CS=I['published_central_CS'],source_table_difference=analytic(30)-I['published_central_CS'],
 CS_if_friction_weight_varies=numerical(30,40000,extra=2),texture_selected=tex[0],texture_after_0_5um_wear=tex[2],coating_selected=sel,
 body_only_material_yen=basecost,life_sensitivity=cost,
 limitations=['Kinematic CS is not wear or success probability.','No friction coefficient or life is predicted.','Areal unfiltered Sa is not the 2010 paper profile Ra.','Cap count, manufacture, attachment and load share unproved.','Remaining channel area is not a prediction of water flow or drainage recovery.'])
put('results.json',result);put('validation.json',dict(passed=len(checks),checks=checks))
print(json.dumps(dict(checks=len(checks),CS30=result['central_CS_30'],Sa=tex[0]['ideal_unfiltered_Sa_um'],cap_mass_kg=sel['grooved_cap_mass_kg'],cap_yen=sel['net_material_yen']),ensure_ascii=False))
