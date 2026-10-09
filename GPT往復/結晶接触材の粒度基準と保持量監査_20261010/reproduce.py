from pathlib import Path
import json,sys,hashlib,itertools,math
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'計算部品'))
from powder_inventory import distribution,retention,coating,loss_budget
def calculate():
 checks=[]
 def check(name,x):
  if not x:raise AssertionError(name)
  checks.append(dict(name=name,passed=True))
 specs=[('number_only',[.5,10],[950,50],3),('both_number90_volume50',[1,20],[99990,10],3),('constant_thickness_plate',[1,20],[999,1],2)]
 distributions=[]
 for name,d,n,p in specs:
  x=distribution(d,n,p);x['name']=name;x['ideal_retention']=retention(x,2.8);distributions.append(x)
  check('number conserved '+name,math.isclose(sum(b['number_fraction'] for b in x['bins']),1))
  check('mass conserved '+name,math.isclose(sum(b['equal_density_mass_fraction'] for b in x['bins']),1))
 a,b,c=distributions
 check('counterexample count fine',b['number_D90_um']==1)
 check('counterexample volume median fine',b['volume_D50_um']==1)
 check('counterexample volume upper tail coarse',b['volume_D90_um']==20)
 check('counterexample independent volume sum',math.isclose(b['bins'][1]['equal_density_mass_fraction'],80000/179990))
 check('single bin quantile',distribution([3],[11])['volume_D90_um']==3)
 check('count replication invariance',math.isclose(distribution([1,20],[999900,100])['bins'][1]['equal_density_mass_fraction'],b['bins'][1]['equal_density_mass_fraction']))
 grid=[]
 for area,w,A,pad in itertools.product([2000.,20000.],[.002,.01,.05],[1.,10.,100.],[.2,1.]):
  x=coating(area*.45*150,w,A,1200.,pad);x['course_area_m2']=area;grid.append(x)
 check('36 coating scenarios',len(grid)==36)
 check('all coating mass balances',all(math.isclose(x['core_kg']+x['coating_kg'],x['finished_mass_kg']) for x in grid))
 ref=coating(135000,.01,10)
 partial=coating(135000,.01,10,1200,.2)
 check('1wt percent coat mass',ref['coating_kg']==1350)
 check('equivalent thickness independent direct volume',math.isclose(ref['equivalent_solid_thickness_um'],1350/1200/(133650*10)*1e6))
 check('targeting fifth area raises equivalent thickness fivefold',math.isclose(partial['equivalent_solid_thickness_um'],5*ref['equivalent_solid_thickness_um']))
 losses=[loss_budget(M*f,d,eta,2000.) for M,f,d,eta in itertools.product([135000.,1350000.],[.002,.01,.05],[.01,.1],[.9,.99,.999])]
 check('36 loss scenarios',len(losses)==36)
 check('all capture balances',all(math.isclose(x['captured_kg']+x['uncaptured_kg'],x['detached_kg']) for x in losses))
 ref_loss=loss_budget(1350,.01,.999,2000.)
 check('reference annual uncaptured grams',math.isclose(ref_loss['uncaptured_kg']*1000,13.5))
 check('reference replacement material cost',math.isclose(ref_loss['replacement_material_JPY_if_all_detached_unusable'],27000))
 price=[dict(finished_mass_kg=M,weight_fraction=w,price_JPY_kg=P,coating_material_JPY=M*w*P) for M,w,P in itertools.product([135000.,1350000.],[.002,.01,.05],[500.,2000.,10000.])]
 check('18 price sensitivities',len(price)==18)
 check('coating 5 parts per100 core not 5wt%',math.isclose(5/105,.047619047619047616))
 check('lossless capture limit',loss_budget(1350,.01,1,2000)['uncaptured_kg']==0)
 deps=['計算部品/powder_inventory.py','GPT往復/GPT回答_多方向探索第46巡_乾式板状結晶と保持接点の発明条件_20261009.md']
 # Locate the authoritative cycle46 report instead of inventing its date/name.
 found=list((R/'GPT往復').glob('GPT回答_多方向探索第46巡*'));assert len(found)==1;deps[1]=found[0].relative_to(R).as_posix()
 results=dict(cycle=110,physical_trials=0,success_probability=None,distributions=distributions,coating_scenarios=grid,loss_scenarios=losses,price_scenarios=price,reference_coating=ref,reference_localized_coating=partial,reference_loss=ref_loss,
  assumptions=dict(size='diameter variable for a mathematical two-bin population, not measured patent particle data',volume_law='p3 similar shapes; p2 equal thickness plates, not a laser scattering inversion',density='1200 kg/m3 reference LL nominal density from prior46; mixed crystals density unmeasured',bed='finished mass assumption area times 0.45m times150kg/m3, not fixed microstructure after coating',surface='externally coatable area, not necessarily BET area',price='sensitivity assumptions, not supplier quotation',detach='hypothetical annual loss of coating inventory, not per skier pass'),
  dependency_hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in deps})
 val=dict(count=len(checks),status='mass_geometry_arithmetic_consistency_only',physical_validation=False,checks=checks)
 return results,val
if __name__=='__main__':
 r,v=calculate()
 if '--check' in sys.argv:
  assert json.loads((D/'results.json').read_text())==r and json.loads((D/'validation.json').read_text())==v
  print('Stored result reproduction passed')
 else:
  for name,obj in [('results.json',r),('validation.json',v)]:(D/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps(dict(checks=v['count'],distributions=r['distributions'],reference_coating=r['reference_coating'],localized=r['reference_localized_coating'],loss=r['reference_loss']),ensure_ascii=False))
