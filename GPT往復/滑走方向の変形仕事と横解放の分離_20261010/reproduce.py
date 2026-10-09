from pathlib import Path
import sys,json,hashlib,itertools,math
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'計算部品'))
from load_unload_foundation import response,integrate_path,allowed_depth
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
    checks=[]
    def check(name,truth):
        if not truth:raise AssertionError(name)
        checks.append(dict(name=name,passed=True))
    cases=[]
    for name,r,f in [('dissipative_support',.2,1.),('limited_dissipative_contacts',.2,.25),('reversible_limit',1.,1.)]:
        c=response(700.,.12,.15,.65,20e6,r,f);c['name']=name;cases.append(c)
    ref=cases[0];Cnew=.15+.65*(1-.25*(1-.2))
    comp=response(700.,.12,.15,.65,20e6*ref['effective_contact_length_m']/Cnew,.2,.25)
    comp['name']='limited_contacts_equal_depth';cases.append(comp)
    check('equal depth stiffness compensation',math.isclose(comp['indentation_m'],ref['indentation_m']))
    ni=integrate_path(comp)
    check('compensated force numerical balance',abs(ni['normal_N']-700)<1e-4)
    check('compensated work numerical balance',abs(ni['drag_N']-comp['drag_N'])<1e-6)
    costs=[]
    for area in [2000,20000]:
        mass=area*.45*150;saving=12000*200*(.01-.001)*500
        costs.append(dict(area_m2=area,bed_mass_kg=mass,annual_saving_JPY_if_loss_reduced=saving,
          horizon_years=3,extra_initial_JPY_per_kg_cap=3*saving/mass,
          status='hypothetical gross savings, no evidence H108 reduces loss, no quote'))
    check('annual cost arithmetic',math.isclose(costs[0]['annual_saving_JPY_if_loss_reduced'],10800000))
    check('small area three year gross unit cap',math.isclose(costs[0]['extra_initial_JPY_per_kg_cap'],240))
    check('large area three year gross unit cap',math.isclose(costs[1]['extra_initial_JPY_per_kg_cap'],24))
    quadrature=[]
    for r,f in [(.2,1.),(.2,.25),(1.,1.),(math.sqrt(.5),.37)]:
        c=response(700.,.12,.15,.65,20e6,r,f)
        for steps in [500,1000,2000,4000]:
            n=integrate_path(c,steps)
            eN=abs(n['normal_N']-c['normal_N'])/c['normal_N']
            eF=abs(n['drag_N']-c['drag_N'])/max(1.,abs(c['drag_N']))
            quadrature.append(dict(r=r,f=f,steps=steps,relative_normal_error=eN,scaled_drag_error=eF))
            check('normal quadrature '+str((r,f,steps)),eN<1e-5)
            check('work quadrature '+str((r,f,steps)),eF<1e-5)
    check('elastic limit dissipates zero',cases[2]['drag_N']==0)
    c=cases[0];twice=response(1400.,.12,.15,.65,20e6,.2)
    check('linear foundation depth scales with load',math.isclose(twice['indentation_m'],2*c['indentation_m']))
    check('load doubling quadruples work',math.isclose(twice['drag_N'],4*c['drag_N']))
    fast=response(700.,.12,.15,.65,20e6,.2,1.,20.)
    check('rate independent force',fast['drag_N']==c['drag_N'])
    check('power speed conversion',fast['power_W']==2*c['power_W'])
    check('fixed depth admissibility inversion',math.isclose(allowed_depth(c['mu_deformation'],.15,.65,.2,1.),c['indentation_m']))
    check('zero budget nonelastic allows zero depth',allowed_depth(0,.15,.65,.2,1.)==0)
    check('elastic depth unbounded only by this work criterion',allowed_depth(.01,.15,.65,1.,1.) is None)
    grid=[response(N,.12,a,.65,K,r,f) for N,a,K,r,f in itertools.product([300.,700.,1200.],[.05,.15,.30],[10e6,20e6,50e6],[.1,.5,.9],[.1,.5,1.])]
    check('grid count',len(grid)==243)
    check('nonnegative loss and support',all(x['loss_J_per_m2']>=0 and x['peak_pressure_Pa']>0 for x in grid))
    check('work balance in all rows',all(math.isclose(x['drag_N'],x['mu_deformation']*x['normal_N'],abs_tol=1e-12) for x in grid))
    budgets=[dict(mu_budget=m,front_m=a,rear_m=b,r=r,f=f,depth_limit_m=allowed_depth(m,a,b,r,f)) for m,a,b,r,f in itertools.product([.005,.02],[.002,.15],[.002,.65],[.2,.8],[.25,1.])]
    # Surface term is a hypothetical coefficient, never a measured whole-snow COF.
    totals=[dict(case=c['name'],surface_mu_assumed=mu,mu_sum=mu+c['mu_deformation']) for c,mu in itertools.product(cases,[.03,.06,.10])]
    scales=[]
    for a,b,d in [(.15,.65,.003),(.002,.002,.0001)]:
        for r,f in [(.2,1.),(.2,.25),(.9,1.)]:
            scales.append(dict(front_m=a,rear_m=b,indentation_m=d,r=r,f=f,
              mu_deformation=d*f*(1-r)/(a+b*(1-f*(1-r)))))
    deps=['計算部品/load_unload_foundation.py','GPT往復/濡れ軟化とエッジ支持の識別_20261009/model.md','GPT往復/動的接触と圧力分布の滑走面検証_20261009/model.md']
    results=dict(cycle=108,physical_trials=0,success_probability=None,model='prescribed triangular track profile and independent bilinear unilateral foundation; uncalibrated',
      dependency_hashes={p:sha(R/p) for p in deps},representative_cases=cases,quadrature=quadrature,grid=grid,depth_budgets=budgets,assumed_surface_totals=totals,scale_examples=scales,cost_envelopes=costs)
    val=dict(status='analytic_and_numerical_consistency_only',count=len(checks),checks=checks,physical_validation=False)
    return results,val
if __name__=='__main__':
    res,val=run()
    if '--check' in sys.argv:
        assert json.loads((D/'results.json').read_text())==res
        assert json.loads((D/'validation.json').read_text())==val
        print('Stored result reproduction passed')
    else:
        for name,obj in [('results.json',res),('validation.json',val)]:
            (D/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(dict(checks=val['count'],rows=len(res['grid']),cases=res['representative_cases'],max_error=max(x['relative_normal_error'] for x in res['quadrature'])),ensure_ascii=False))
