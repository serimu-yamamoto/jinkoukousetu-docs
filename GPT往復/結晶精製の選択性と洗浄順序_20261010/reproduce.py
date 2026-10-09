from pathlib import Path
import sys,json,math,hashlib,subprocess
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent
R=D.parents[1]
sys.path.insert(0,str(R/'計算部品'))
from washing_selectivity import *
checks=[]
def check(name,value):
    if not value: raise AssertionError(name)
    checks.append(name)
def close(a,b): return math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-11)
deps=['GPT往復/結晶接触材の粒度基準と保持量監査_20261010/results.json',
      'GPT往復/反応晶析と局部再生の物量検証_20261009/calculate.py']
hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in deps}
# Existing prior-cycle material basis, not re-estimated here.
old=json.loads((R/deps[0]).read_text())
reference=old['reference_coating']
check('prior named coating reference selected',reference['finished_mass_kg']==135000 and reference['weight_fraction']==0.01 and reference['target_area_fraction']==1)
check('prior coating basis',reference['coating_kg']==1350)
# Model regression against old inline ideal KCl wash.
legacy=[]
for n in range(5):
    val=0.1*74.55*1000*batch_fraction(0.1,1.0,n)
    original=0.1*74.55*1000*(0.1/(0.1+1.0))**n
    check('legacy wash n='+str(n),close(val,original))
    legacy.append({'n':n,'mg_per_kg_ideal':val})
check('zero wash',close(batch_fraction(1,0,10),1))
check('zero liquid transmission',close(concentration_fraction(3,0,.2),1.6))
check('clean ideal concentration',close(concentration_fraction(10,1),math.exp(-10)))
check('product retention exact zero loss',close(product_yield(12,0),1))
check('recycled water concentration floor b/s',close(concentration_fraction(100,.5,.001),.002))
check('per product ratio accounting',close(impurity_per_product_ratio(10,1,.01),math.exp(-9.9)))
# Independent RK4 integration for c and y.
ode=[]
for s,p,b in [(1,0,0),(1,.001,0),(.5,.01,0),(1,.01,.0009),(.5,.01,.0002),(0,.01,.1),(1,1,.2),(.2,.5,0)]:
    d=10; steps=10000; dt=d/steps;c=y=1.0
    def advance(z,f):
        k1=f(z);k2=f(z+dt*k1/2);k3=f(z+dt*k2/2);k4=f(z+dt*k3)
        return z+dt*(k1+2*k2+2*k3+k4)/6
    for _ in range(steps):
        c=advance(c,lambda z:b-s*z)
        y=advance(y,lambda z:-p*z)
    ac=concentration_fraction(d,s,b); ay=product_yield(d,p)
    check('independent ODE '+str((s,p,b)),close(c,ac) and close(y,ay))
    ode.append({'s':s,'p':p,'b':b,'D':d,'c_abs_error':abs(c-ac),'y_abs_error':abs(y-ay)})
target=.001
clean=[]
for s in (1,.5):
    for p in (.001,.01):
        t=first_target(s,p,0,target)
        expected=-math.log(target)/(s-p)
        check('clean target root '+str((s,p)),close(t['D'],expected))
        inv=delivered_inventory(1350,.5,t['D'],p,2000)
        check('delivered mass conservation '+str((s,p)),close(inv['input_kg']*inv['yield_fraction'],1350))
        clean.append({'solute_transmission':s,'product_transmission':p,'inlet_ratio':0,'target_q':target,
                      'D':t['D'],'c':concentration_fraction(t['D'],s),'q':impurity_per_product_ratio(t['D'],s,p),**inv})
recycle=[]
for b in (0,.0002,.0005,.0009,.001):
    t=first_target(1,.01,b,target,30)
    # Fine grid provides an independent bounded check of analytic minimizer.
    qgrid=min(impurity_per_product_ratio(i/1000,1,.01,b) for i in range(30001))
    check('minimum vs grid b='+str(b),abs(qgrid-t['minimum']['ratio'])<1e-9)
    recycle.append({'s':1,'p':.01,'b':b,**t,
                    'q_at_D_10':impurity_per_product_ratio(10,1,.01,b),
                    'q_at_D_20':impurity_per_product_ratio(20,1,.01,b),
                    'q_at_D_30':impurity_per_product_ratio(30,1,.01,b)})
check('recycling counterexample target impossible in range',recycle[3]['D'] is None)
check('recycling over washing can increase ratio',recycle[3]['q_at_D_30']>recycle[3]['minimum']['ratio'])
check('no purification when product passes faster',first_target(.1,.2,0)['D'] is None)
check('dirty inlet no initial improvement',close(minimum_ratio(.5,.01,.5)['D'],0))
limits=[]
for y in (.9,.95,.99):
    r=clean_water_selectivity_limit(target,y)
    d=-math.log(target)/(1-r)
    check('selectivity threshold both constraints '+str(y),close(product_yield(d,r),y) and close(impurity_per_product_ratio(d,1,r),target))
    limits.append({'diagnostic_target_q':target,'minimum_yield':y,'maximum_product_to_solute_transmission_ratio':r})
for func,args in [(batch_fraction,(0,1,2)),(concentration_fraction,(1,-.1,0)),(product_yield,(1,1.1)),(first_target,(1,0,0,0))]:
    try:func(*args)
    except ValueError:check('invalid input '+func.__name__,True)
    else:raise AssertionError('invalid accepted')
routes=[
 {'route':'single_batch','total_wash_over_hold':10,'stages':1,'c_assuming_no_product_loss':batch_fraction(1,10,1)},
 {'route':'five_stage_batch','total_wash_over_hold':10,'stages':5,'c_assuming_no_product_loss':batch_fraction(1,2,5)},
 {'route':'continuous','total_wash_over_hold':10,'stages':None,'c_assuming_no_product_loss':concentration_fraction(10,1)}]
sequence=[
 {'route':'crystal_fraction_before_fixing','mass_basis_kg':1350,'hold_L_per_kg_assumed':.5,'D_assumed':10,'wash_m3':1350*.5*10/1000},
 {'route':'whole_finished_grains_after_fixing','mass_basis_kg':135000,'hold_L_per_kg_assumed':.2,'D_assumed':10,'wash_m3':135000*.2*10/1000}]
check('sequence arithmetic ratio',close(sequence[1]['wash_m3']/sequence[0]['wash_m3'],40))
sodium=5.7*23/40
inventory={'example':'US12221403B2 Example 2-2','NaOH_listed_g':5.7,'product_reported_g':36.0,
 'atomic_formula_mass_assumptions_g_per_mol':{'NaOH':40,'Na':23,'NaCl':58.44},
 'listed_input_sodium_g':sodium,'listed_input_sodium_g_per_kg_product':sodium/36*1000,
 'listed_input_NaCl_equivalent_g_per_kg_product':5.7/40*58.44/36*1000,
 'listed_input_sodium_kg_at_1350kg_product':sodium/36*1350,
 'additional_pH_adjustment_NaOH_g':None,'product_residual_sodium_g_per_kg':None,
 'product_residual_solvent':None,'note':'Input inventory only, not product residue. Counterion, partition and unreported additions unknown.'}
check('listed sodium input',close(inventory['listed_input_sodium_g_per_kg_product'],91.04166666666667))
data={'cycle':111,'physical_trials':0,'success_probability':None,'prior_reference':reference,'dependency_hashes':hashes,
 'diagnostic_not_safety_target':target,'washing_routes':routes,'sequence_comparison':sequence,
 'clean_water_delivered_cases':clean,'recycled_water_cases':recycle,'selectivity_constraints':limits,
 'listed_process_inventory':inventory,'legacy_regression':legacy,'independent_ode':ode}
validation={'count':len(checks),'checks':checks,'passed':True,'physical_validation':False,
 'scope':'Algebra, numerical ODE, limiting cases and model regression only; no measured washing or skiing.'}
def encoded(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
if '--check' in sys.argv:
    for name,x in [('results.json',data),('validation.json',validation)]:
        checkbytes=(D/name).read_bytes()
        assert checkbytes==encoded(x),'Stored result mismatch '+name
    print('REPRODUCTION_OK '+str(validation['count'])+' mathematical checks; physical_trials=0')
else:
    for name,x in [('results.json',data),('validation.json',validation)]: (D/name).write_bytes(encoded(x))
    print(json.dumps({'checks':len(checks),'routes':routes,'clean':clean,'recycle':recycle,'limits':limits,'sequence':sequence,'inventory':inventory},ensure_ascii=False))
