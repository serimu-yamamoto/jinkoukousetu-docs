"""Ideal added contact directions, not fabricated neighboring grains."""
from reproduce import *
def main():
 c=next(f for f in F if f['model']=='C3' and f['pose_id']==3)
 rot=np.array(c['central_rotation'])
 p4=support_points('C3',np.array([0.,0.,-1.]),R,a,rot)[1][0]
 rows=[];checks=[]
 for polar,azimuth in itertools.product([30,60],[0,90,180,270]):
  th,ph=math.radians(polar),math.radians(azimuth)
  n5=np.array([math.sin(th)*math.cos(ph),math.sin(th)*math.sin(ph),math.cos(th)])
  possible=support_points('C3',-n5,R,a,rot)[1]
  assert len(possible)==1
  p5=possible[0];pp=copy.deepcopy(c['points'])+[p4.tolist(),p5.tolist()];nn=copy.deepcopy(c['normals'])+[[0,0,1],n5.tolist()]
  for mu,remove,load in itertools.product([.1,.3,.6],[1,2,3],I['loads']):
   active=[j for j in [1,2,3,4,5] if j!=remove]
   ph=math.radians(load['heading_deg']);ft=np.array([-load['q']*math.cos(ph),-load['q']*math.sin(ph),-1.])
   inner=solve(pp,nn,mu,ft,active,edges=32,peak=True);outer=solve(pp,nn,mu,ft,active,edges=32,outer=True,peak=True)
   if inner['success']:
    assert inner['residual']<1e-8 and max(inner['actual_friction_ratios'])<=mu+1e-8
    checks.append('force-'+str(len(rows)))
   assert not inner['success'] or outer['success'];checks.append('inclusion-'+str(len(rows)))
   rows.append(dict(polar_deg=polar,azimuth_deg=azimuth,point_mm=p5.tolist(),normal=n5.tolist(),mu=mu,removed_support=remove,**load,active_supports=active,inner=inner,outer=outer,classification=classify(inner,outer)))
 grouped=[]
 for polar,azimuth,mu in itertools.product([30,60],[0,90,180,270],[.1,.3,.6]):
  ss=[r for r in rows if (r['polar_deg'],r['azimuth_deg'],r['mu'])==(polar,azimuth,mu)]
  feasible=[r for r in ss if r['inner']['success']]
  grouped.append(dict(polar_deg=polar,azimuth_deg=azimuth,mu=mu,static_cases=len(ss),feasible_static_cases=len(feasible),all_specified_static_cases_feasible=len(feasible)==len(ss),worst_min_peak=max(r['inner']['max_normal'] for r in feasible) if len(feasible)==len(ss) else None,not_a_success_probability=True))
 data=dict(physical_tests=0,success_probability=None,scope='C3 pose3 with two ideal additional contact sites; placement, neighbors, deformation and engagement path not built.',cases=rows,grouped=grouped,checks=len(checks))
 (D/'two_helpers_results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps(dict(cases=len(rows),checks=len(checks),all_cases_groups=[r for r in grouped if r['all_specified_static_cases_feasible']])))
if __name__=='__main__':main()
