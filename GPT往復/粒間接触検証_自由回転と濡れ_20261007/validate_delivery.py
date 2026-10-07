"""Delivery and numerical audits. Not material or skiing validation."""
import json,math,ast,re
from urllib.parse import unquote
from pair_geometry import H,np,arcs,point,first_contact,support_points
from cluster import wrench_lp
from audit_wrenches import matrix
from wet_cost import gamma_water,volume_sum
from scipy.spatial import cKDTree

def read(n):return json.loads((H/n).read_text(encoding='utf-8'))
def finite(x):
 if isinstance(x,float):assert math.isfinite(x)
 elif isinstance(x,dict):
  for y in x.values():finite(y)
 elif isinstance(x,list):
  for y in x:finite(y)
def check_force(ans,pts,normals,mut,mui,R):
 f=np.array(ans['forces_normalized']);n=np.array(normals);p=np.array(pts)
 assert np.linalg.norm(f.sum(axis=0))<1e-7
 assert np.linalg.norm(np.cross(p/R,f).sum(axis=0))<1e-7
 assert abs(f[0]@n[0]-1)<1e-7
 for j,(fj,nj) in enumerate(zip(f,n)):
  mu=mut if j==0 else (mui[j-1] if isinstance(mui,list) else mui);fn=float(fj@nj);ft=float(np.linalg.norm(fj-fn*nj));assert fn>=-1e-8 and ft<=mu*max(fn,0)+1e-7

def main():
 I=read('inputs.json');P=read('pair_results.json');C=read('cluster_results.json');F=read('face_results.json');A=read('numerical_audit.json');W=read('wet_cost_results.json');R=I['geometry']['R_mm'];a=I['geometry']['wire_radius_mm'];checks=[]
 def check(name,ok,details=None):
  assert ok,name
  checks.append(dict(name=name,passed=True,details=details))
 check('case_counts',len(P['cases'])==36 and len(C['fixtures'])==9 and sum(len(x['force_cases']) for x in C['fixtures'])==96 and len(W['capillary'])==30)
 check('height_brackets',all(x['found'] and x['certificate_reached'] and 0<=x['height_gap_um']<=.02000001 for x in P['cases']))
 mindirect=1e9
 for x in P['cases']:
  model=x['model'];RA=np.array(x['rotation_top']);RB=np.array(x['rotation_bottom']);off=np.array(x['lateral_offset']);cloud=[]
  for arc in arcs(model):
   ts=np.linspace(arc[2],arc[3],513);cloud.extend(R*(arc[0]*math.cos(t)+arc[1]*math.sin(t)) for t in ts)
  cloud=np.array(cloud);pa=cloud@RA.T+off+np.array([0,0,x['height_upper_mm']]);pb=cloud@RB.T;dist=cKDTree(pb).query(pa)[0].min()-2*a;mindirect=min(mindirect,float(dist));assert dist>=-1e-10
  ca=np.array(x['top_centerline']);cb=np.array(x['bottom_centerline']);assert abs(np.linalg.norm(ca-cb)-2*a)<1e-10
  assert abs(np.linalg.norm(x['representative_normal'])-1)<1e-10
  outer_sphere=math.sqrt((2*(R+a))**2-float(off[:2]@off[:2]));assert x['height_lower_mm']<=outer_sphere+1e-10
 check('independent_sampled_nonpenetration',True,dict(min_sampled_surface_gap_mm=mindirect,scope='Sample audit of the analytic envelope, not its proof'))
 z=first_contact('S3',np.eye(3),np.eye(3),np.zeros(3),I);known=2*(R+a)
 check('symmetric_known_first_touch',z['height_lower_mm']<=known+1e-12 and z['height_upper_mm']>=known-1e-12,dict(known_mm=known,lower=z['height_lower_mm'],upper=z['height_upper_mm']))
 for model in I['geometry']['models']:
  for pose in range(12):
   row=next(x for x in P['cases'] if x['model']==model and x['pose_id']==pose);ref=next(x for x in P['cases'] if x['model']=='R4' and x['pose_id']==pose);assert np.allclose(row['rotation_top'],ref['rotation_top']) and np.allclose(row['rotation_bottom'],ref['rotation_bottom'])
 for pose in [0,3,7]:
  rows=[x for x in C['fixtures'] if x['pose_id']==pose]
  for j in range(3):assert all(np.allclose(x['supports'][j]['rotation'],rows[0]['supports'][j]['rotation']) for x in rows)
 check('common_prescribed_poses',True)
 invalid=[x for x in C['fixtures'] if not x['neighbor_geometry_valid']]
 check('overlap_excluded',len(invalid)==1 and invalid[0]['model']=='R4' and invalid[0]['pose_id']==7 and any(d['clearance_upper_mm']<0 for d in invalid[0]['neighbor_clearances']))
 feasible=0
 for x in C['fixtures']:
  if not x['neighbor_geometry_valid']:assert not x['force_cases'];continue
  assert all(d['clearance_lower_mm']>0 for d in x['neighbor_clearances']) and min(x['neighbor_platen_gaps_mm'])>0
  for f in x['force_cases']:
   if f['inner']['success']:check_force(f['inner'],x['points'],x['normals'],f['mu_top'],f['mu_internal'],R);feasible+=1
   assert not (f['inner']['success'] and not f['outer']['success'])
 check('saved_force_and_moment_witnesses',True,dict(feasible_inner_witnesses=feasible,scope='Count is not a physical success rate'))
 for c in A['farkas_certificates']:
  x=next(x for x in C['fixtures'] if x['model']==c['model'] and x['pose_id']==c['pose_id'])
  if c['case']=='selective_face':f=next(x for x in F['cases'] if x['model']==c['model'] and x['pose_id']==c['pose_id']);mut=.1;mui=f['friction_by_face']
  else:f=x['force_cases'][int(c['case'])];mut=f['mu_top'];mui=f['mu_internal']
  M=matrix(np.array(x['points']),np.array(x['normals']),mut,mui,R);y=np.array(c['y']);assert (M.T@y).min()>-1e-7 and abs(y[-1]+1)<1e-9
 check('independent_farkas_witnesses',len(A['farkas_certificates'])==86)
 pts=np.array([[0,0,.2],[-.2,0,-.2],[.2,0,-.2],[0,.2,-.2]]);ns=np.array([[0,0,-1],[0,0,1],[0,0,1],[0,0,1]])
 good=wrench_lp(pts,ns,0,0,R);bad=wrench_lp(np.array([[0,0,.2],[.2,0,-.2]]),ns[:2],0,0,R,outer=True)
 check('known_wrench_problems',good['success'] and bad['status']==2)
 fine=A['refined_C3_pose3'];check_force(fine['force_case'],fine['points'],fine['normals'],0,.6,R)
 check('contact_resolution_refinement',fine['force_case']['success'] and all(x['certificate_reached'] and x['height_gap_um']<=.00200001 for x in fine['comparisons']),fine['comparisons'])
 for f in F['cases']:
  x=next(x for x in C['fixtures'] if x['model']==f['model'] and x['pose_id']==f['pose_id']);p=np.array(x['points'])[1:];n=np.array(x['normals'])[1:];rad=-np.sum((p+a*n)*n,axis=1)/R;assert np.allclose(rad,f['outward_radial_cosine'])
 check('contact_face_classification',True)
 s=next(x for x in P['calipers'] if x['model']=='S3')
 check('known_closed_hoop_width',abs(s['width_min_sample_mm']-(2*R*math.sqrt(2/3)+2*a))<1e-12 and abs(s['width_max_sample_mm']-2*(R+a))<1e-12)
 for x in W['cost']:
  assert abs(volume_sum(x['model'],R,x['equal_volume_wire_diameter_um']/2000)/volume_sum('R4',R,a)-1)<1e-8
  assert abs(x['conditional_material_initial_JPY']-x['conditional_pilot_mass_kg']*500)<1e-6
 check('equal_volume_and_cost_units',True)
 check('IAPWS_50C_table',abs(gamma_water(50)-.06794)<.000005,dict(calculated_N_m=gamma_water(50),table_N_m=.06794))
 for path in H.glob('*.json'):finite(json.loads(path.read_text(encoding='utf-8')))
 for path in H.glob('*.py'):ast.parse(path.read_text(encoding='utf-8'))
 check('finite_numbers_and_syntax',True)
 for obj in [I,P['metadata'],C,F,A,W]:assert obj['physical_tests']==0 and obj['success_probability'] is None
 check('no_physical_probability_claim',True)
 docs=list(H.glob('*.md'))+[H.parent/'GPT回答_多方向探索第13巡_粒間接触と三方向開口の比較_20261007.md'];links=0
 for doc in docs:
  for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
   if re.match(r'^[a-z]+:',target) or target.startswith('#'):continue
   assert (doc.parent/unquote(target.split('#')[0])).exists(),str(doc)+':'+target;links+=1
 check('relative_links',True,dict(count=links))
 out=dict(physical_tests=0,success_probability=None,numerical_audit_only=True,checks=checks,checks_passed=len(checks));(H/'validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({'checks_passed':len(checks),'physical_tests':0,'success_probability':None}))
if __name__=='__main__':main()
