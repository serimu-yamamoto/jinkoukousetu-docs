"""Cycle 89: history identifiability and independent specimen accounting.
No material performance is predicted. Python standard library only.
"""
from pathlib import Path
import json, math
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
def save(name,obj):
    (P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def rank(matrix):
    a=[list(map(float,row)) for row in matrix]; r=0
    for col in range(len(a[0])):
        pivot=next((i for i in range(r,len(a)) if abs(a[i][col])>1e-12),None)
        if pivot is None: continue
        a[r],a[pivot]=a[pivot],a[r]; d=a[r][col]; a[r]=[x/d for x in a[r]]
        for j in range(len(a)):
            if j!=r:
                f=a[j][col]; a[j]=[x-f*y for x,y in zip(a[j],a[r])]
        r+=1
        if r==len(a):break
    return r
def decompose(v):
    ff,wf,fw,ww=v
    return {'baseline':ff,'candidate_history':wf-ff,'ski_history':fw-ff,'interaction':ww-wf-fw+ff}
def predict(b,m,s):
    return b['baseline']+b['candidate_history']*m+b['ski_history']*s+b['interaction']*m*s
checks=[]
def check(name,condition):
    checks.append({'name':name,'passed':bool(condition)})
    if not condition: raise AssertionError(name)
def close(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12)
X=[[1,0,0,0],[1,1,0,0],[1,0,1,0],[1,1,1,1]]
check('four_history_cells_rank_four',rank(X)==4)
check('only_fresh_and_worn_rank_two',rank([X[0],X[3]])==2)
for n in range(4):check('missing_cell_'+str(n)+'_loses_identifiability',rank(X[:n]+X[n+1:])==3)
examples=[]
for e in I['synthetic_examples']:
    b=decompose(e['mu']); pred=[predict(b,m,s) for m,s in [(0,0),(1,0),(0,1),(1,1)]]
    check(e['id']+'_reconstruction',all(close(a,c) for a,c in zip(pred,e['mu'])))
    examples.append({**e,'status':'synthetic_counterexample_not_measurement','coefficients':b})
check('all_examples_same_FF_WW',len({(e['mu'][0],e['mu'][3]) for e in examples})==1)
check('mixed_history_cases_differ',len({tuple(e['mu']) for e in examples})==3)
check('candidate_only_zero_ski_and_interaction',close(examples[0]['coefficients']['ski_history'],0) and close(examples[0]['coefficients']['interaction'],0))
check('both_only_negative_interaction',close(examples[2]['coefficients']['interaction'],-0.14))
rows=[]; donors=[]; bodies=[]
c=I['campaign']; reps=c['replicates']; mats=c['material_ids']
for mat in mats:
    for cell in I['history_order']:
        for rep in range(1,reps+1):
            eid=f'{mat}_{cell}_r{rep}'; donor=eid+'_D' if cell!='FF' else None
            cand_worn=cell[0]=='W'; ski_worn=cell[1]=='W'
            cand=(donor+'_C') if cand_worn else (eid+'_fresh_C')
            ski=(donor+'_S') if ski_worn else (eid+'_fresh_S')
            if donor:
                donors.append({'id':donor,'candidate_id':donor+'_C','ski_id':donor+'_S','dedicated_endpoint':eid,'status':'not_performed'})
                bodies.extend([{'id':donor+'_C','type':'candidate','material':mat},{'id':donor+'_S','type':'ski','material':'ski_UHMWPE'}])
            if not cand_worn:bodies.append({'id':cand,'type':'candidate','material':mat})
            if not ski_worn:bodies.append({'id':ski,'type':'ski','material':'ski_UHMWPE'})
            rows.append({'endpoint_id':eid,'material':mat,'history':cell,'independent_replicate':rep,'donor_id':donor,'candidate_id':cand,'ski_id':ski,'status':'not_performed','measured_mu':None})
check('24_independent_endpoints',len(rows)==24)
check('18_dedicated_donor_pairs',len(donors)==18)
check('30_candidates_and_30_ski_bodies',sum(b['type']=='candidate' for b in bodies)==30 and sum(b['type']=='ski' for b in bodies)==30)
check('unique_produced_body_ids',len({b['id'] for b in bodies})==len(bodies))
check('no_body_shared_between_endpoints',len({r[k] for r in rows for k in ['candidate_id','ski_id']})==2*len(rows))
check('one_endpoint_per_donor',len({r['donor_id'] for r in rows if r['donor_id']})==len(donors))
check('all_measurements_missing',all(r['measured_mu'] is None and r['status']=='not_performed' for r in rows))
used={r[k] for r in rows for k in ['candidate_id','ski_id']}
archived=[b['id'] for b in bodies if b['id'] not in used]
check('12_unused_donor_partners',len(archived)==12)
def budget(age,speed):
    age_hours=len(donors)*age/speed/3600
    endpoint_hours=len(rows)*c['endpoint_distance_m']/speed/3600
    return {'age_distance_m':age,'speed_m_s':speed,'age_hours':age_hours,'endpoint_hours':endpoint_hours,'contact_motion_hours':age_hours+endpoint_hours,'setup_count':len(donors)+len(rows),'full_cost_yen':None,'assumed_machine_only_yen':{str(rate):(age_hours+endpoint_hours)*rate for rate in I['sensitivity']['assumed_machine_rates_yen_h']}}
base=budget(c['default_age_distance_m'],c['default_speed_m_s'])
check('default_motion_50_plus_1_over_15_hours',close(base['contact_motion_hours'],50+1/15))
check('default_751000_yen_not_total',close(base['assumed_machine_only_yen']['15000'],751000))
long=budget(30000,0.25)
check('slow_30km_motion_hours',close(long['contact_motion_hours'],600+4/15))
check('speed_shortens_time_not_validates_equivalence',close(budget(10000,5)['contact_motion_hours'],base['contact_motion_hours']/5))
check('pressure_load_arithmetic_source1',close(0.1*150,15))
check('distance_arithmetic_source1',close(0.25*168*3600/1000,151.2))
check('probability_remains_null',I['evidence_status']['success_probability'] is None)
R={'schema_version':1,'physical_experiments_performed':0,'success_probability':None,'identifiability':{'only_FF_WW_rank':2,'four_cells_rank':4,'unknown_coefficients':4},'synthetic_counterexamples':examples,'campaign':{'endpoint_count':len(rows),'conditioning_count':len(donors),'candidate_bodies':30,'ski_bodies':30,'unused_donor_partners':archived,'default_motion_and_assumed_cost':base},'motion_budget_sensitivity':[budget(a,v) for a in I['sensitivity']['age_distance_m'] for v in I['sensitivity']['speed_m_s']]}
save('results.json',R)
save('specimen_allocation.json',{'status':'not_performed','endpoint_runs':rows,'conditioning_runs':donors,'bodies':bodies,'unused_partners':archived})
save('validation.json',{'kind':'arithmetic_and_identifiability_checks_not_physical_tests','count':len(checks),'all_passed':all(x['passed'] for x in checks),'checks':checks})
print(json.dumps({'checks':len(checks),'passed':True,'endpoint_runs_not_performed':len(rows),'conditioning_runs_not_performed':len(donors),'motion_hours_only':base['contact_motion_hours'],'physical_trials':0}))
