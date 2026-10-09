from mobility import *
import copy
def main():
 inp=json.loads((D/'inputs.json').read_text(encoding='utf-8'));M=json.loads((D/'mobility_results.json').read_text(encoding='utf-8'));cfg=inp['finite_path']
 f=next(f for f in F if f['model']=='C3' and f['pose_id']==3)
 mode=next(r for r in M['mobility'] if r['model']=='C3' and r['pose']==3 and r['heading_deg']==180 and r['rotation_component_cap']==1)
 params=copy.deepcopy(I);params['pair']['certificate_gap_mm']=0.00001;params['pair']['max_nodes']=160000
 RA=np.array(f['central_rotation']);w=np.array(mode['rotation_scaled']);v0=np.array(mode['translation_per_mm'])
 z0=support_points('C3',np.array([0.,0.,1.]),R,a,RA)[0];rows=[]
 for side in [-0.1,0,0.1]:
  v=v0+np.array([0,side,0])
  for s in ([0,0.001,0.005,0.01,0.02] if side==-0.1 else [0.02]):
   rot=Rotation.from_rotvec(w*s/R).as_matrix()@RA;center=v*s
   ds=[distance_bracket('C3',rot,np.array(n['rotation']),center,np.array(n['center']),params) for n in f['supports']]
   gap=z0-support_points('C3',np.array([0.,0.,1.]),R,a,rot)[0]-center[2]
   rows.append(dict(sideways_per_forward=side,travel_mm=s,center_mm=center.tolist(),rotation=rot.tolist(),plate_gap_mm=float(gap),support_distances=ds,all_endpoint_lower_bounds_clear=gap>=0 and all(x['clearance_lower_mm']>=0 for x in ds),continuous_free_path_proven=False))
   print(json.dumps(dict(side=side,s=s,min_gap_lower_um=min(x['clearance_lower_mm'] for x in ds)*1000)),flush=True)
 ref=json.loads((P/'numerical_audit.json').read_text(encoding='utf-8'))['refined_C3_pose3'];fr=copy.deepcopy(f);fr['points']=ref['points'];fr['normals']=ref['normals']
 refined=[]
 for deg in [0,90,180]:
  for cap in [0,1]:
   old=mobility(f,math.radians(deg),cap);new=mobility(fr,math.radians(deg),cap)
   refined.append(dict(heading_deg=deg,cap=cap,old=old,refined=new))
 # Exact archived arc volume SUM is an upper bound, because intersections counted twice.
 V=math.pi*a*a*(3*math.radians(210)*R)+6*2*math.pi*a**3/3
 rho=inp['manufacturing']['density_kg_m3'];mass=V*1e-9*rho
 N=inp['manufacturing']['inventory_kg']/mass
 factory=dict(volume_sum_upper_mm3=V,particle_mass_upper_kg=mass,particle_count_lower=N,minimum_grains_per_second=N/(inp['manufacturing']['production_hours']*3600),serial_10000_per_second_max_kg_per_1000h=mass*10000*3600*1000,claim='Conditional bounds at specified polymer density, not production quote or physical yield.')
 out=dict(physical_tests=0,success_probability=None,corrected_path_endpoints=rows,refined_contact_mobility=refined,manufacturing=factory)
 (D/'correction_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps(dict(corrected_endpoints=len(rows),refined_lp=len(refined),manufacturing=factory)))
if __name__=='__main__':main()
