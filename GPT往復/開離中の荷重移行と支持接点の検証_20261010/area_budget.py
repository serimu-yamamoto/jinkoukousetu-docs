from reproduce import *
D0=json.loads((D/'load_sharing_results.json').read_text(encoding='utf-8'))
rows=[]
for r in D0['cases']:
 if r['lam']!=1:continue
 for force_unit_mN,nominal_limit_MPa in itertools.product([.5,2,5],[1,5,10]):
  peak_mN=r['max_support_force']*force_unit_mN
  area=peak_mN*1000/nominal_limit_MPa
  rows.append(dict(pattern=r['pattern'],lambda_value=1,force_unit_mN=force_unit_mN,assumed_nominal_limit_MPa=nominal_limit_MPa,required_nominal_area_um2=area,equivalent_square_side_um=math.sqrt(area),not_measured_strength=True))
c=next(r for r in D0['cases'] if r['lam']==1 and r['pattern']=='central_block');d=next(r for r in D0['cases'] if r['lam']==1 and r['pattern']=='dispersed')
ratio=c['max_support_force']/d['max_support_force'];wr=c['max_support_node_displacement']/d['max_support_node_displacement']
assert ratio>1 and wr>1
for r in rows:assert abs(r['required_nominal_area_um2']*r['assumed_nominal_limit_MPa']/1000-r['force_unit_mN']*next(x['max_support_force'] for x in D0['cases'] if x['lam']==1 and x['pattern']==r['pattern']))<1e-10
out=dict(physical_tests=0,success_probability=None,scope='Nominal area requirement under assumed force and allowable pressure; not Hertz contact area, strength evidence, material mass, cost estimate or rated safety.',cases=rows,central_to_distributed_peak_ratio=ratio,central_to_distributed_nodal_deflection_ratio=wr,checks=len(rows)+2)
(D/'area_budget.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(cases=len(rows),checks=out['checks'],peak_ratio=ratio,nodal_displacement_ratio=wr)))
