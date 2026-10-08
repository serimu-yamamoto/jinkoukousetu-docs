"""Cycle 46: deterministic necessary-condition calculations, not success simulation.
Run with Python 3; matplotlib is only required for the two original figures.
All SI units internally. Inputs record measured-source vs assumed values.
"""
from pathlib import Path
import json, math, sys
ROOT=Path(__file__).resolve().parent
local_deps=ROOT.parents[1]/'.deps'
if local_deps.exists(): sys.path.insert(0,str(local_deps))
I=json.loads((ROOT/'inputs.json').read_text(encoding='utf-8'))
C=I['cost']; L=I['load']; K=I['kinematic']
def save(name,obj):
    (ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def required_fraction(mu_b,mu_c,drag,target):
    if target < drag+mu_c-1e-12: return None
    if target >= drag+mu_b: return 0.0
    return min(1.0,max(0.0,(mu_b+drag-target)/(mu_b-mu_c)))
def pressure_partition(f,c,p):
    pc=f*p/c; pb=(1-f)*p/(1-c)
    return pc,pb,pc/pb if pb>1e-10 else None
mass=C['bed_area_m2']*C['bed_depth_m']*C['bulk_density_kg_m3']
area=2*mass/(C['skeleton_density_kg_m3']*C['skeleton_radius_m'])
r=C['discount_rate']; n=C['years']; crf=r*(1+r)**n/((1+r)**n-1)
rho=I['candidate']['density_kg_m3']; y=C['yield_fraction']
kinematic=[]
for d in K['plate_diameters_m']:
 for u in K['speeds_m_s']:
  for t in K['contact_dwell_s']:
   kinematic.append(dict(diameter_m=d,speed_m_s=u,dwell_s=t,travel_m=u*t,travel_over_diameter=u*t/d))
loads=[]; partitions=[]
for muc in L['patch_mu']:
 for drag in L['structural_drag_over_normal']:
  f=required_fraction(L['base_mu'],muc,drag,L['illustrative_total_mu'])
  loads.append(dict(patch_mu=muc,structural_drag=drag,required_load_fraction=f,interpretation='algebraic necessary condition only' if f is not None else 'no solution for assumed coefficients'))
  if f is not None:
   for c in L['patch_contact_area_fraction']:
    pc,pb,q=pressure_partition(f,c,L['mean_contact_pressure_Pa'])
    partitions.append(dict(patch_mu=muc,structural_drag=drag,load_fraction=f,contact_area_fraction=c,patch_pressure_Pa=pc,base_pressure_Pa=pb,pressure_ratio=q))
costs=[]
for phi in C['coated_skeleton_area_fraction']:
 for thick in C['equivalent_deposit_thickness_m']:
  deposited=rho*area*phi*thick
  for price in C['candidate_price_JPY_kg']:
   initial=deposited*price/y
   available=C['annual_phase_budget_JPY']-crf*initial-C['annual_coating_process_allowance_JPY']
   max_loss=max(0,available)*y/price
   costs.append(dict(coated_area_fraction=phi,eq_thickness_m=thick,price_JPY_kg=price,deposited_kg=deposited,purchase_kg=deposited/y,initial_phase_JPY=initial,annualized_initial_JPY=crf*initial,annual_budget_remaining_JPY=available,max_annual_replacement_kg=max_loss,allowable_mean_loss_m=max_loss/(rho*area*phi),initial_and_process_fit_budget=available>=0))
rep=next(v for v in costs if v['coated_area_fraction']==C['representative_coated_fraction'] and v['eq_thickness_m']==C['representative_thickness_m'] and v['price_JPY_kg']==C['representative_price_JPY_kg'])
wear=[]
for chi in C['exposed_coating_fraction']:
 for delta in C['wear_per_local_contact_m']:
  effective_N=chi*C['local_contacts_per_day']*C['days']
  mean_depth=delta*effective_N
  lost=rho*area*C['representative_coated_fraction']*mean_depth
  wear.append(dict(exposed_fraction=chi,loss_per_local_contact_m=delta,equivalent_contacts_averaged_all_coated_area=effective_N,annual_mean_loss_m=mean_depth,annual_lost_kg=lost,annual_replenishment_JPY=lost*C['representative_price_JPY_kg']/y,inventory_turnovers=lost/rep['deposited_kg'],interpretation='demand with replenishment; without replenishment loss stops at depletion'))
thresholds=[dict(exposed_fraction=chi,max_loss_per_local_contact_m=rep['allowable_mean_loss_m']/(chi*C['local_contacts_per_day']*C['days'])) for chi in C['exposed_coating_fraction']]
manufacturing=dict(methanol_feed_kg_per_kg_isolated=I['manufacturing_example']['methanol_feed_g']/I['manufacturing_example']['isolated_product_g'],recrystallization_mass_recovery=I['manufacturing_example']['isolated_product_g']/I['manufacturing_example']['starting_crystals_g'],interpretation='laboratory example feed, not net solvent use or a scaled plant cost')
representative_f=required_fraction(.2,.03,.02,.06)
checks=[]
def check(name,condition):
 checks.append(dict(name=name,passed=bool(condition)))
 if not condition: raise AssertionError(name)
def near(a,b): return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12)
check('bed mass 108 tonnes',near(mass,108000))
check('cylinder lateral area 6 million m2',near(area,6000000))
check('cylinder area independently from volume over radius',near(area,2*(mass/1200)/30e-6))
check('0.5 m travel spans 25000 twenty-micron plates',near(.5/20e-6,25000))
check('shorter dwell lowers travel ratio proportionally',near((5*.1/10e-6)/(5*.02/10e-6),5))
check('required force fraction 16/17',near(representative_f,16/17))
check('inverse friction balance at target',near(representative_f*.03+(1-representative_f)*.2+.02,.06))
check('too high patch friction cannot satisfy target',required_fraction(.2,.08,.02,.06) is None)
check('base alone already meets loose target',near(required_fraction(.2,.03,.02,.23),0))
check('all-patch limiting equality',near(required_fraction(.2,.04,.02,.06),1))
pc,pb,q=pressure_partition(representative_f,.05,.5e6)
check('force conserved after area pressure split',near(pc*.05+pb*.95,.5e6))
check('5 percent area pressure ratio 304',near(q,304))
check('equal load/area fractions imply equal pressure',near(pressure_partition(.2,.2,1e6)[2],1))
check('representative deposit 720kg',near(rep['deposited_kg'],720))
check('representative bought mass 900kg',near(rep['purchase_kg'],900))
check('representative initial phase 9 million JPY',near(rep['initial_phase_JPY'],9000000))
check('discounted annuity returns investment',near(sum(crf/(1+r)**j for j in range(1,n+1)),1))
check('cost threshold exactly closes annual phase budget',near(crf*rep['initial_phase_JPY']+1e6+rep['max_annual_replacement_kg']*10000/.8,5e6))
check('replacement mass equals area times mean thickness',near(rep['max_annual_replacement_kg'],rho*area*.2*rep['allowable_mean_loss_m']))
check('1 percent exposed, 0.01nm per contact loses 1.728kg/year',near(wear[0]['annual_lost_kg'],1.728))
check('exposure tenfold raises mass loss tenfold',near(wear[3]['annual_lost_kg']/wear[0]['annual_lost_kg'],10))
check('greater unit price lowers fixed-budget permitted loss',costs[24]['allowable_mean_loss_m']>costs[27]['allowable_mean_loss_m'])
check('clipped solvent recovery is not treated as synthesis',manufacturing['recrystallization_mass_recovery']<1)
check('all required load fractions are in physical bounds',all(v['required_load_fraction'] is None or 0<=v['required_load_fraction']<=1 for v in loads))
check('29 independent all-success trials lower bound exceeds .9 but 28 does not',.05**(1/29)>.9 and .05**(1/28)<.9)
check('physical probability remains unknown',I['physical_tests']==0 and I['physical_success_probability'] is None)
results=dict(cycle=46,physical_tests=0,physical_success_probability=None,bed_mass_kg=mass,estimated_skeleton_lateral_area_m2=area,capital_recovery_factor=crf,kinematic=kinematic,load_conditions=loads,pressure_partitions=partitions,cost_conditions=costs,representative_cost=rep,wear_conditions=wear,wear_thresholds=thresholds,manufacturing_example=manufacturing,numerical_checks=len(checks),counts=dict(kinematic=len(kinematic),load=len(loads),pressure=len(partitions),cost=len(costs),wear=len(wear)))
save('results.json',results); save('numerical-validation.json',dict(status='passed',checks=checks,warning='Algebra and implementation checks only. No physical or human trials.'))
# Original standard plots; source figures are not reproduced.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Polygon,FancyArrowPatch
plt.rcParams.update({'font.size':10,'svg.fonttype':'none'})
fig,axs=plt.subplots(1,2,figsize=(12,4.5))
ax=axs[0]
cs=[.03+i*.0096 for i in range(99)]
ax.plot([c*100 for c in cs],[pressure_partition(representative_f,c,.5e6)[0]/1e6 for c in cs],color='#156b92')
for c in L['patch_contact_area_fraction']:
 ax.scatter(c*100,pressure_partition(representative_f,c,.5e6)[0]/1e6,color='#156b92')
ax.set(xlabel='Crystal fraction of potential contact area (%)',ylabel='Required crystal pressure (MPa)',title='A. High load share requires enough contact area',yscale='log')
ax.grid(alpha=.25); ax.text(.04,.05,'Assumed: mu crystal 0.03, base 0.20\nstructural drag 0.02, total target 0.06\nmean pressure 0.5 MPa; required load = 16/17',transform=ax.transAxes,fontsize=9,bbox=dict(facecolor='white',alpha=.85,edgecolor='none'))
ax=axs[1]
for phi,col in [(0.05,'#1a8662'),(.2,'#b05b1b'),(.8,'#8d548d')]:
 prices=list(range(1000,20001,100))
 cap=[]
 for p in prices:
  dep=rho*area*phi*.5e-6
  budget=C['annual_phase_budget_JPY']-crf*dep*p/y-1e6
  cap.append(max(0,budget)*y/p/(rho*area*phi)*1e9)
 ax.plot(prices,cap,label=f'{phi:.0%} skeleton coated',color=col)
ax.set(xlabel='Unquoted scenario price (JPY/kg)',ylabel='Allowed mean coating loss (nm/year)',title='B. Annual phase budget sets the wear limit')
ax.legend(); ax.grid(alpha=.25); ax.text(.44,.53,'5 million JPY/year phase budget\n1 million/year process allowance\n0.5 um equivalent deposit\n10 years, 8%; 80% yield\n0 means no wear allowance',transform=ax.transAxes,fontsize=8)
fig.suptitle('Necessary conditions for H46 — assumed inputs, not ski performance',fontsize=13)
fig.tight_layout(); fig.savefig(ROOT/'constraints.svg'); fig.savefig(ROOT/'constraints.png',dpi=150);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(12,4.5))
ax=axs[0]
ax.add_patch(Rectangle((.05,.78),.9,.07,facecolor='#cedce4')); ax.text(.5,.885,'UHMWPE ski base: test dry at 50 C',ha='center')
ax.add_patch(FancyArrowPatch((.3,.95),(.8,.95),arrowstyle='->',mutation_scale=16));
ax.add_patch(Polygon([[.12,.22],[.3,.22],[.46,.55],[.65,.58],[.8,.25],[.95,.3],[.75,.68],[.45,.73],[.28,.45]],facecolor='#bbdbce',edgecolor='#336c56',linewidth=2))
for x in [.46,.53,.60]:
 ax.add_patch(Polygon([[x,.72],[x+.05,.70],[x+.08,.76],[x+.01,.78]],facecolor='#edbb59',edgecolor='#876321'))
ax.annotate('Captured plate faces\nedge/root anchoring is unvalidated',xy=(.57,.74),xytext=(.06,.60),fontsize=9,arrowprops=dict(arrowstyle='->'))
ax.annotate('Open branch and drain paths\n(no continuous exposed mat)',xy=(.46,.43),xytext=(.30,.09),fontsize=9,arrowprops=dict(arrowstyle='->'))
ax.text(.5,.015,'A. H46: retained contact phase + open support',ha='center',fontsize=11)
ax=axs[1]
for yy,label,col in [(.8,'Interface slip: must measure ski/crystal friction','#156b92'),(.59,'Internal shear: finite displacement in a retained plate','#b05b1b'),(.38,'Transfer / exfoliation: count lost mass and exposure','#b8464c')]:
 ax.add_patch(Rectangle((.1,yy-.09),.78,.07,facecolor='#edbb59',edgecolor='#876321'))
 ax.add_patch(FancyArrowPatch((.25,yy),(.73,yy),arrowstyle='->',mutation_scale=16,color=col));ax.text(.05,yy+.045,label,fontsize=9)
ax.text(.5,.18,'0.5 m relative travel / 20 um plate = 25,000',ha='center',fontsize=11)
ax.text(.5,.10,'Plate shape alone does not establish endless low friction.',ha='center',fontsize=9)
ax.text(.5,.015,'B. Identify where the sliding actually occurs',ha='center',fontsize=11)
for ax in axs: ax.set(xlim=(0,1),ylim=(0,1.05));ax.axis('off')
fig.suptitle('H46 concept — NOT TO SCALE / NOT PHYSICALLY VALIDATED',fontsize=13)
fig.tight_layout();fig.savefig(ROOT/'concept.svg');fig.savefig(ROOT/'concept.png',dpi=150);plt.close(fig)
# Strip renderer trailing spaces so committed SVG passes repository whitespace checks.
for name in ['concept.svg','constraints.svg']:
    p=ROOT/name
    p.write_text('\n'.join(line.rstrip() for line in p.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'checks':len(checks),'counts':results['counts'],'representative':rep,'thresholds':thresholds},ensure_ascii=False,allow_nan=False))
