"""H66: directional stiffness of prescribed contact networks. Not physical validation.
No bending, friction, contact formation, inertia, fluid, plasticity or fracture propagation.
FCC is a numerical node arrangement, not invented material crystallography.
"""
import csv,json,math,itertools
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'));m=I['model']
checks=[]
def ck(name,ok):
 checks.append({'name':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
def save(name,obj):
 (P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def csvsave(name,rows):
 with (P/name).open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def geometry(n,jitter=0):
 p0=np.array([(i+a,j+b,k+c) for i in range(n) for j in range(n) for k in range(n) for a,b,c in [(0,0,0),(0,.5,.5),(.5,0,.5),(.5,.5,0)]],float)
 edges=np.array([(i,j) for i in range(len(p0)) for j in range(i+1,len(p0)) if abs(np.sum((p0[j]-p0[i])**2)-.5)<1e-10])
 lower=np.where(p0[:,2]==p0[:,2].min())[0];upper=np.where(p0[:,2]==p0[:,2].max())[0]
 p=p0.copy()
 if jitter:
  p+=np.random.default_rng(m['seed']).uniform(-1,1,p.shape)*jitter/math.sqrt(2)
  p[np.r_[lower,upper],2]=p0[np.r_[lower,upper],2]
 # Each perturbed spring is stress-free in its new geometry. Graph is deliberately held fixed.
 B=np.zeros((len(edges),len(p)*3));dirs=[]
 for r,(i,j) in enumerate(edges):
  v=p[j]-p[i];v/=np.linalg.norm(v);B[r,3*i:3*i+3]=-v;B[r,3*j:3*j+3]=v;dirs.append(v)
 return {'p0':p0,'p':p,'edges':edges,'B':B,'dirs':np.array(dirs),'lower':lower,'upper':upper}
def measure(g,mask,rcond=None):
 p,e,B=g['p'],g['edges'],g['B'];n=len(p);lower,upper=g['lower'],g['upper']
 fixed=np.array([3*i+a for i in np.r_[lower,upper] for a in range(3)]);free=np.array(sorted(set(range(3*n))-set(fixed)))
 A=B[mask];Bf=A[:,free];u=np.zeros((3*n,3))
 for a in range(3):u[3*upper+a,a]=1
 sol,_,rank,s=np.linalg.lstsq(Bf,-A@u,rcond=m['svd_rcond'] if rcond is None else rcond);u[free]=sol
 ext=A@u;K=ext.T@ext;reactions=A.T@ext;rf=np.max(np.abs(reactions[free])) if len(free) else 0
 rt=np.array([[sum(reactions[3*upper+a,b]) for b in range(3)] for a in range(3)])
 parent=list(range(n))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for i,j in e[mask]:parent[find(i)]=find(j)
 roots={find(i) for i in lower};span=any(find(i) in roots for i in upper)
 C=g['dirs'][mask].T@g['dirs'][mask]/mask.sum() if mask.sum() else np.zeros((3,3))
 return {'nodes':n,'potential_edges':len(e),'active_edges':int(mask.sum()),'retained_fraction':float(mask.mean()),'graph_spans_z':bool(span),'graph_components':len({find(i) for i in range(n)}),'internal_zero_modes_with_plates_fixed':int(len(free)-rank),'K_over_k':K.tolist(),'fabric':C.tolist(),'max_free_force_residual':float(rf),'reaction_energy_error':float(np.max(np.abs(rt-K)))}
def interface(g):
 p=g['p0'];e=g['edges'];mid=(p[:,2].min()+p[:,2].max())/2
 cross=(p[e[:,0],2]-mid)*(p[e[:,1],2]-mid)<0
 ci=np.where(cross)[0];v=p[e[:,1]]-p[e[:,0]]
 yz=np.array([i for i in ci if abs(v[i,0])<1e-10]);xz=np.array([i for i in ci if abs(v[i,1])<1e-10])
 return cross,yz,xz
def spaced_order(g,ids):
 mid=g['p0'][g['edges']].mean(axis=1)[:,:2];chosen=[];left=list(map(int,ids))
 while left:
  if not chosen:pick=min(left,key=lambda i:(mid[i,0],mid[i,1],i))
  else:pick=max(left,key=lambda i:(min(float(np.sum((mid[i]-mid[j])**2)) for j in chosen),-i))
  chosen.append(pick);left.remove(pick)
 return chosen
def repair_order(g):
 cut,yz,xz=interface(g);a=spaced_order(g,yz);b=spaced_order(g,xz)
 return np.array([item for pair in itertools.zip_longest(a,b) for item in pair if item is not None])
def four_direction_order(g):
 cut,_,_=interface(g);v=g['p0'][g['edges'][:,1]]-g['p0'][g['edges'][:,0]]
 groups=[]
 for axis in [0,1]:
  for sign in [1,-1]:
   ids=np.array([i for i in np.where(cut)[0] if sign*v[i,axis]*v[i,2]>0])
   groups.append(spaced_order(g,ids))
 return np.array([item for row in itertools.zip_longest(*groups) for item in row if item is not None])
def masks(g):
 e=g['edges'];cut,yz,xz=interface(g);base=~cut;out={'intact':np.ones(len(e),bool),'plane_cut':base.copy()}
 restored=len(yz);out['one_direction_restore']=base.copy();out['one_direction_restore'][yz]=True
 out['balanced_spread_restore']=base.copy();out['balanced_spread_restore'][repair_order(g)[:restored]]=True
 mid=g['p0'][e].mean(axis=1);center=(g['p0'].min(axis=0)+g['p0'].max(axis=0))/2
 nearest=lambda ids:sorted(map(int,ids),key=lambda i:(float(np.sum((mid[i,:2]-center[:2])**2)),i))
 out['balanced_cluster_restore']=base.copy();out['balanced_cluster_restore'][nearest(yz)[:restored//2]+nearest(xz)[:restored-restored//2]]=True
 out['four_direction_spread_restore']=base.copy();out['four_direction_spread_restore'][four_direction_order(g)[:restored]]=True
 for seed in m['dispersed_damage_seeds']:
  a=np.ones(len(e),bool);a[np.random.default_rng(seed).choice(len(e),int(cut.sum()),replace=False)]=False;out['dispersed_loss_'+str(seed)]=a
 return out
def flat(name,r,intact):
 K=np.array(r['K_over_k']);K0=np.array(intact['K_over_k']);ev=np.linalg.eigvalsh(K[:2,:2]);ev0=np.linalg.eigvalsh(K0[:2,:2])
 relaxed=K[:2,:2]-np.outer(K[:2,2],K[2,:2])/K[2,2] if K[2,2]>1e-12 else K[:2,:2]
 relaxed_ratio=float(np.linalg.eigvalsh(relaxed)[0]/ev0[0])
 return {'case':name,'nodes':r['nodes'],'active_edges':r['active_edges'],'retained_fraction':r['retained_fraction'],'graph_spans_z':r['graph_spans_z'],'Kx_over_k':float(K[0,0]),'Ky_over_k':float(K[1,1]),'Kz_over_k':float(K[2,2]),'Kx_ratio':float(K[0,0]/K0[0,0]),'Ky_ratio':float(K[1,1]/K0[1,1]),'Kz_ratio':float(K[2,2]/K0[2,2]),'minimum_xy_shear_ratio':float(ev[0]/ev0[0]),'minimum_xy_shear_ratio_relaxed_z':relaxed_ratio,'max_free_force_residual':r['max_free_force_residual']}
g=geometry(m['fcc_cells']);maskdict=masks(g);result={name:measure(g,mask) for name,mask in maskdict.items()};ref=result['intact'];rows=[flat(name,r,ref) for name,r in result.items()]
# Basic mechanics tests independent of the full network response.
ck('analytic_two_springs_series',math.isclose(float(np.linalg.lstsq(np.array([[1.],[-1.]]),np.array([0.,-1.]),rcond=None)[0][0]),.5))
ck('node_count108',len(g['p'])==108);ck('potential_bonds450',len(g['edges'])==450)
cut,yz,xz=interface(g);ck('cut60_equal_families',cut.sum()==60 and len(yz)==len(xz)==30)
for axis in np.eye(3):
 u=np.tile(axis,len(g['p']));ck('rigid_translation_'+str(list(axis)),np.max(np.abs(g['B']@u))<1e-12)
for axis in np.eye(3):
 u=np.cross(np.tile(axis,(len(g['p']),1)),g['p']).ravel();ck('infinitesimal_rigid_rotation_'+str(list(axis)),np.max(np.abs(g['B']@u))<1e-12)
ck('equilibrium_and_energy',all(r['max_free_force_residual']<1e-10 and r['reaction_energy_error']<1e-10 for r in result.values()))
ck('full_xy_symmetry',abs(ref['K_over_k'][0][0]-ref['K_over_k'][1][1])<1e-10)
ck('cut_no_path_and_zero_stiffness',not result['plane_cut']['graph_spans_z'] and np.max(np.abs(result['plane_cut']['K_over_k']))<1e-20)
ck('same_number_different_damage',all(result['dispersed_loss_'+str(s)]['active_edges']==result['plane_cut']['active_edges'] for s in m['dispersed_damage_seeds']))
ck('directional_repair_connected_but_no_x_support',result['one_direction_restore']['graph_spans_z'] and result['one_direction_restore']['K_over_k'][0][0]<1e-20)
ck('same_repair_budget',len({result[k]['active_edges'] for k in ['one_direction_restore','balanced_spread_restore','balanced_cluster_restore','four_direction_spread_restore']})==1)
ck('balanced_restore_two_shear_directions',np.linalg.eigvalsh(np.array(result['balanced_spread_restore']['K_over_k'])[:2,:2])[0]>0)
ck('deleting_bonds_cannot_add_stiffness',all(np.linalg.eigvalsh(np.array(ref['K_over_k'])-np.array(r['K_over_k']))[0]>-1e-10 for r in result.values()))
# Nested repair sequences, fixed number of springs; orientations are not probabilities.
repairrows=[];last=None
for count in m['repair_counts']:
 mask=~cut;mask[repair_order(g)[:count]]=True;r=measure(g,mask);repairrows.append({'restored':count,**flat('balanced_spread',r,ref)})
 if last is not None:ck('repair_monotone_'+str(count),np.linalg.eigvalsh(np.array(r['K_over_k'])-last)[0]>-1e-10)
 last=np.array(r['K_over_k'])
 mask=~cut;mask[four_direction_order(g)[:count]]=True;r=measure(g,mask);repairrows.append({'restored':count,**flat('four_direction_spread',r,ref)})
 if count<=len(yz):
  mask=~cut;mask[spaced_order(g,yz)[:count]]=True;r=measure(g,mask);repairrows.append({'restored':count,**flat('one_direction',r,ref)})
ck('full_repair_restores_reference',np.max(np.abs(last-np.array(ref['K_over_k'])))<1e-10)
jitterrows=[]
for amp in m['jitter_fraction_of_nearest_spacing']:
 gj=geometry(m['fcc_cells'],amp);mj=masks(gj);r0=measure(gj,mj['intact'])
 for name in ['one_direction_restore','balanced_spread_restore','four_direction_spread_restore']:
  jitterrows.append({'jitter_fraction':amp,**flat(name,measure(gj,mj[name]),r0)})
sizerows=[]
for n in m['size_cells']:
 gs=geometry(n);ms=masks(gs);r0=measure(gs,ms['intact'])
 for name in ['one_direction_restore','balanced_spread_restore','four_direction_spread_restore','plane_cut']:
  sizerows.append({'cells':n,**flat(name,measure(gs,ms[name]),r0)})
ck('size_direction_counterexample',all(r['Kx_ratio']<1e-20 for r in sizerows if r['case']=='one_direction_restore'))
for tol in [1e-8,1e-12]:
 rr=measure(g,maskdict['balanced_spread_restore'],tol);ck('svd_tolerance_'+str(tol),np.max(np.abs(np.array(rr['K_over_k'])-np.array(result['balanced_spread_restore']['K_over_k'])))<1e-10)
damage_rows=[]
midpoints=g['p0'][g['edges']].mean(axis=1)
for name in ['balanced_spread_restore','balanced_cluster_restore','four_direction_spread_restore']:
 for cx,cy in [(1.25,1.25),(.5,.5),(2,2)]:
  mask=maskdict[name].copy();inside=((midpoints[:,0]-cx)**2+(midpoints[:,1]-cy)**2)<=.6**2
  removed=mask & cut & inside;mask[removed]=False
  rr=measure(g,mask)
  damage_rows.append({'layout':name,'damage_center_x_cell':cx,'damage_center_y_cell':cy,'damage_radius_cell':.6,'lost_repaired_edges':int(removed.sum()),**flat('local_interface_loss',rr,ref)})
ck('local_damage_never_stiffens',all(r['Kx_ratio']<=next(x for x in rows if x['case']==r['layout'])['Kx_ratio']+1e-10 for r in damage_rows))
c=I['cost'];annuity=(1-(1+c['discount_rate'])**(-c['years']))/c['discount_rate'];costrows=[]
for avoided in c['replacement_avoidance_fraction']:
 for om in c['added_annual_maintenance_energy_JPY']:
  gross=c['prior_hypothetical_annual_connector_JPY']*avoided;net=gross-om
  costrows.append({'assumed_avoidance_fraction':avoided,'annual_gross_saved_JPY':gross,'added_annual_OandM_JPY':om,'annual_net_JPY':net,'ten_year_present_value_JPY':net*annuity,'max_extra_capex_JPY':max(0,net*annuity)})
ck('annuity_independent_sum',math.isclose(annuity,sum((1+c['discount_rate'])**(-y) for y in range(1,c['years']+1))))
ck('four_direction_repair_improves_this_spread_example',next(r for r in rows if r['case']=='four_direction_spread_restore')['minimum_xy_shear_ratio']>next(r for r in rows if r['case']=='balanced_spread_restore')['minimum_xy_shear_ratio'])
ck('physical_status',I['evidence']=={'physical_tests':0,'success_probability':None})
node_rows=[{'node':i,'x_m':v[0]*m['nearest_spacing_m']*math.sqrt(2),'y_m':v[1]*m['nearest_spacing_m']*math.sqrt(2),'z_m':v[2]*m['nearest_spacing_m']*math.sqrt(2)} for i,v in enumerate(g['p0'])]
edge_rows=[{'edge':i,'node_i':int(e[0]),'node_j':int(e[1]),'crosses_cut':bool(cut[i]),**{name:bool(mask[i]) for name,mask in maskdict.items()}} for i,e in enumerate(g['edges'])]
for name,data in [('network_cases.csv',rows),('local_damage.csv',damage_rows),('repair_curve.csv',repairrows),('jitter_screen.csv',jitterrows),('size_screen.csv',sizerows),('cost_screen.csv',costrows),('nodes.csv',node_rows),('edges_and_masks.csv',edge_rows)]:csvsave(name,data)
save('results.json',{'evidence':I['evidence'],'model':m,'cases':result,'summary':rows,'jitter':jitterrows,'size':sizerows,'cost':costrows,'local_damage':damage_rows,'annuity_factor':annuity,'counts':{'network_cases':len(rows),'repair_rows':len(repairrows),'jitter_rows':len(jitterrows),'size_rows':len(sizerows),'cost_rows':len(costrows),'local_damage_rows':len(damage_rows),'nodes':len(node_rows),'edges':len(edge_rows)}})
save('numerical_checks.json',{'passed':True,'checks':checks,'physical_tests':0})
print(json.dumps({'numerical_checks':len(checks),'cases':len(rows),'physical_tests':0}))
