import json,copy
from elastic_free import H,np,build,evaluate

def main():
 I=json.loads((H/'inputs.json').read_text(encoding='utf-8'));C=json.loads((H.parent/'粒間接触検証_自由回転と濡れ_20261007/cluster_results.json').read_text(encoding='utf-8'));rows=[];profiles=[]
 for x in C['fixtures']:
  if not x['neighbor_geometry_valid']:continue
  chosen=[f for f in x['force_cases'] if f['inner']['success']]
  if not chosen:continue
  model=build(x['model'],x['central_rotation'],x['points'],x['normals'],R=I['geometry']['R_mm'],a=I['geometry']['wire_radius_mm'],E=I['material']['E_MPa'],nu=I['material']['nu'],kappa=I['material']['shear_factor'],quad=I['calculation']['quadrature_points'],interior=I['calculation']['interior_points'])
  for case in chosen:
   forces=np.array(case['inner']['forces_normalized'])*I['calculation']['force_mN']/1000;full=evaluate(model,forces);record=dict(model=x['model'],pose_id=x['pose_id'],mu_top=case['mu_top'],mu_internal=case['mu_internal'],force_mN=I['calculation']['force_mN'],response=full);rows.append(record)
   if x['pose_id']==3 and ((x['model']=='C3' and case['mu_top']==0) or (x['model'] in ['R4','S3'] and case['mu_top']==.1)):
    profiles.append(dict(model=x['model'],pose_id=3,response=evaluate(model,forces,profiles=True)))
  print(json.dumps({'model':x['model'],'pose':x['pose_id'],'cases':len(chosen)}),flush=True)
 out=dict(physical_tests=0,success_probability=None,scope=I['scope'],cases=rows,profiles=profiles)
 (H/'elastic_results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({'total_cases':len(rows),'physical_tests':0}))
if __name__=='__main__':main()
