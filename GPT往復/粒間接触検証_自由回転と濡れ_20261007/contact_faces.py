"""Check whether a high-friction internal face is actually touched by support grains."""
import json
from cluster import H,np,wrench_lp

def main():
 I=json.loads((H/'inputs.json').read_text(encoding='utf-8'));C=json.loads((H/'cluster_results.json').read_text(encoding='utf-8'));rows=[];R=I['geometry']['R_mm'];a=I['geometry']['wire_radius_mm']
 for x in C['fixtures']:
  points=np.array(x['points']);normals=np.array(x['normals']);centers=points[1:]+a*normals[1:];radial=-np.sum(normals[1:]*centers,axis=1)/R;coeff=[.6 if r<0 else .1 for r in radial]
  row=dict(model=x['model'],pose_id=x['pose_id'],outward_radial_cosine=radial.tolist(),friction_by_face=coeff,geometry_valid=x['neighbor_geometry_valid'])
  if x['neighbor_geometry_valid']:
   inn=wrench_lp(points,normals,.1,coeff,R,outer=False);out=wrench_lp(points,normals,.1,coeff,R,outer=True);row.update(inner=inn,outer=out,classification='feasible_inner' if inn['success'] else ('infeasible_outer' if out['status']==2 else 'unresolved'))
  rows.append(row)
 out=dict(physical_tests=0,success_probability=None,cases=rows,scope='Radial sign classifies the representative patch only. It does not guarantee a patch is protected from a real ski or accessible in a bed. Friction values are assumed, not measured.')
 (H/'face_results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({'cases':len(rows),'physical_tests':0,'success_probability':None}))
if __name__=='__main__':main()
