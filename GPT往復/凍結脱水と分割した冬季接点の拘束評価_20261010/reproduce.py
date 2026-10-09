from pathlib import Path
import json,math,hashlib,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from shrinkage_patches import geometry,analytic,finite_elements,displacement,stress
a=json.loads((D/'inputs.json').read_text());h=a['hypothetical'];checks=[]
def ck(name,b):
 if not b:raise AssertionError(name)
 checks.append(name)
def eq(x,y):return math.isclose(x,y,rel_tol=2e-8,abs_tol=1e-10)
E=h['E_Pa'];t=h['thickness_m'];eps=h['natural_shrink_strain'];rows=[]
for lam in h['transfer_lengths_m']:
 k=E*t/(lam*lam)
 for qbar in h['footprint_shear_loads_Pa']:
  for count in h['counts']:
   g=geometry(h['face_length_m'],h['gap_m'],count);p=g['half_patch_m'];q=qbar/g['coverage'];label=str((lam,qbar,count))
   z=analytic(E,t,k,eps,p,q)
   ck('lambda inverse '+label,eq(z['lambda_m'],lam))
   ck('coverage force '+label,eq(2*p*count*q,h['face_length_m']*qbar))
   ck('free edge stress '+label,abs(stress(p,E,t,k,eps,p,q))<1e-8)
   ck('symmetry displacement '+label,eq(displacement(p,E,t,k,eps,p,q)+displacement(-p,E,t,k,eps,p,q),2*q/k))
   meshes=[]
   for n in h['mesh_elements']:
    f=finite_elements(E,t,k,eps,p,q,n)
    etau=abs(f['peak_abs_interface_shear_Pa']-z['peak_abs_interface_shear_Pa'])/max(1,z['peak_abs_interface_shear_Pa'])
    eu=max(abs(uu-displacement(xx,E,t,k,eps,p,q)) for xx,uu in zip(f['x'],f['u']))/(abs(eps)*lam+abs(q/k))
    es=max(abs(ss-stress((f['x'][i]+f['x'][i+1])/2,E,t,k,eps,p,q)) for i,ss in enumerate(f['stress_mid']))/(E*abs(eps))
    energy_error=abs(f['stored_J_per_m_width']/z['stored_J_per_m_width']-1)
    ck('reaction balance '+label+str(n),abs(f['reaction_N_per_m_width']-2*p*q)<1e-8*max(1,2*p*abs(q)))
    ck('linear residual '+label+str(n),f['residual_max']<1e-8)
    ck('positive energy '+label+str(n),f['stored_J_per_m_width']>0)
    meshes.append(dict(elements=n,relative_peak_shear_error=etau,normalized_displacement_error=eu,normalized_stress_error=es,relative_energy_error=energy_error))
   ck('fine error bound '+label,max(meshes[-1].values())<257 and max(v for key,v in meshes[-1].items() if key!='elements')<.002)
   ck('refinement improvement '+label,meshes[-1]['normalized_displacement_error']<=meshes[0]['normalized_displacement_error']+1e-10)
   ck('energy force scaling '+label,eq(analytic(E*2,t,k*2,eps,p,q*2)['stored_J_per_m_width'],2*z['stored_J_per_m_width']))
   rows.append(dict(transfer_length_m=lam,footprint_load_Pa=qbar,patch_count=count,geometry=g,local_load_Pa=q,interface_stiffness_Pa_m=k,analytic=z,total_stored_J_per_m_width=count*z['stored_J_per_m_width'],meshes=meshes))
best=[]
for lam in h['transfer_lengths_m']:
 for qbar in h['footprint_shear_loads_Pa']:
  rr=[x for x in rows if x['transfer_length_m']==lam and x['footprint_load_Pa']==qbar]
  b=min(rr,key=lambda r:r['analytic']['peak_abs_interface_shear_Pa'])
  best.append(dict(transfer_length_m=lam,footprint_load_Pa=qbar,lowest_peak_among_tested_count=b['patch_count'],peak_Pa=b['analytic']['peak_abs_interface_shear_Pa'],coverage=b['geometry']['coverage']))
ck('loads change best count',len({x['lowest_peak_among_tested_count'] for x in best if x['transfer_length_m']==.0001})>1)
for L,g,n in [(1,-1,2),(1,.5,3),(1,0,0)]:
 try:geometry(L,g,n)
 except ValueError:ck('invalid geometry '+str((L,g,n)),True)
 else:raise AssertionError('invalid accepted')
deps=['GPT往復/冬季接続と融雪排水検証_20261009/sources.json','GPT往復/冬季接続と融雪排水検証_20261009/calculate.py','GPT往復/雪の永久変形と粒接点の再配置設計_20261010/model.md','GPT往復/温暖粒形成と結晶安定化の工程分離_20261010/model.md']
data=dict(cycle=129,physical_trials=0,success_probability=None,dependency_hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in deps},patch_cases=rows,lowest_peak_among_tested=best,limits=a['limits'])
v=dict(count=len(checks),passed=True,checks=checks,physical_validation=False)
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for name,x in [('results.json',data),('validation.json',v)]:
 if '--check' in sys.argv:assert (D/name).read_bytes()==enc(x)
 else:(D/name).write_bytes(enc(x))
print(json.dumps(dict(checks=len(checks),cases=len(rows),max_final_error=max(v for r in rows for key,v in r['meshes'][-1].items() if key!='elements'),best=best,representative=[dict(n=r['patch_count'],coverage=r['geometry']['coverage'],local=r['local_load_Pa'],peak=r['analytic']['peak_abs_interface_shear_Pa'],tension=r['analytic']['peak_tensile_Pa']) for r in rows if r['transfer_length_m']==.0001 and r['footprint_load_Pa']==2000]),ensure_ascii=False))
