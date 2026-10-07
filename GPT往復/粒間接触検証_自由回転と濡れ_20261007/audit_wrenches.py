"""Separate numerical evidence for contact resolution and wrench feasibility."""
import json,copy,math
from pair_geometry import H,np,first_contact
from cluster import basis,wrench_lp
from scipy.optimize import linprog

def matrix(points,normals,mut,mui,R,edges=16,outer=True):
 cols=[];factor=1/math.cos(math.pi/edges) if outer else 1
 for j,(p,n) in enumerate(zip(points,normals)):
  Q=basis(n);mu=(mut if j==0 else (mui[j-1] if isinstance(mui,list) else mui))*factor
  for t in np.arange(edges)*2*math.pi/edges:
   f=Q@np.array([mu*math.cos(t),mu*math.sin(t),1]);cols.append(np.r_[f,np.cross(p/R,f),int(j==0)])
 return np.array(cols).T

def main():
 I=json.loads((H/'inputs.json').read_text(encoding='utf-8'));C=json.loads((H/'cluster_results.json').read_text(encoding='utf-8'));F=json.loads((H/'face_results.json').read_text(encoding='utf-8'));R=I['geometry']['R_mm'];certs=[];b=np.r_[np.zeros(6),1.]
 for x in C['fixtures']:
  if not x['neighbor_geometry_valid']:continue
  jobs=[(str(i),f['outer'],f['mu_top'],f['mu_internal']) for i,f in enumerate(x['force_cases'])]
  face=next(z for z in F['cases'] if z['model']==x['model'] and z['pose_id']==x['pose_id']);jobs.append(('selective_face',face['outer'],.1,face['friction_by_face']))
  for case,ans,mut,mui in jobs:
   if ans['status']!=2:continue
   A=matrix(np.array(x['points']),np.array(x['normals']),mut,mui,R);sol=linprog(np.zeros(7),A_ub=-A.T,b_ub=np.zeros(A.shape[1]),A_eq=b[None,:],b_eq=[-1],bounds=[(None,None)]*7,method='highs');assert sol.success
   y=sol.x;minimum=float((A.T@y).min());normalization=float(b@y);assert minimum>-1e-7 and abs(normalization+1)<1e-9
   certs.append(dict(model=x['model'],pose_id=x['pose_id'],case=case,y=y.tolist(),minimum_A_transpose_y=minimum,b_dot_y=normalization))
 coarse=next(x for x in C['fixtures'] if x['model']=='C3' and x['pose_id']==3);fineI=copy.deepcopy(I);fineI['pair']['certificate_gap_mm']/=10;fineI['pair']['max_nodes']=2000000;RA=np.array(coarse['central_rotation']);points=[np.array(coarse['points'][0])];normals=[np.array(coarse['normals'][0])];comparison=[]
 for j,phi in enumerate(I['cluster']['azimuth_deg']):
  t=math.radians(I['cluster']['polar_deg']);p=math.radians(phi);d=np.array([math.sin(t)*math.cos(p),math.sin(t)*math.sin(p),math.cos(t)]);Q=basis(d);RB=np.array(coarse['supports'][j]['rotation']);touch=first_contact('C3',Q.T@RA,Q.T@RB,np.zeros(3),fineI);z=touch['height_lower_mm'];pt=Q@np.array(touch['representative_contact'])-z*d;nn=Q@np.array(touch['representative_normal']);points.append(pt);normals.append(nn);pc=np.array(coarse['points'][j+1]);nc=np.array(coarse['normals'][j+1]);comparison.append(dict(support=j,height_gap_um=touch['height_gap_um'],certificate_reached=touch['certificate_reached'],contact_location_change_um=float(np.linalg.norm(pt-pc)*1000),normal_change_deg=math.degrees(math.acos(float(np.clip(nn@nc,-1,1)))),center_change_um=float(np.linalg.norm(-z*d-np.array(coarse['supports'][j]['center']))*1000)))
 fine=wrench_lp(np.array(points),np.array(normals),0,.6,R);out=dict(physical_tests=0,success_probability=None,farkas_certificates=certs,refined_C3_pose3=dict(comparisons=comparison,points=np.array(points).tolist(),normals=np.array(normals).tolist(),force_case=fine,scope='Selected numerical refinement only; no certified normal error or physical stability result.'))
 (H/'numerical_audit.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({'infeasibility_certificates':len(certs),'refined_fixture_feasible':fine['success'],'physical_tests':0}))
if __name__=='__main__':main()
