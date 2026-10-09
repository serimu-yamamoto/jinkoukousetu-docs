"""Finite endpoint probes of straight-twist extrapolations. No continuous collision-free claim."""
from mobility import *
import copy,time
def main():
    inp=json.loads((D/'inputs.json').read_text(encoding='utf-8'));cfg=inp['finite_path']
    M=json.loads((D/'mobility_results.json').read_text(encoding='utf-8'))
    params=copy.deepcopy(I);params['pair']['certificate_gap_mm']=cfg['distance_gap_mm'];params['pair']['max_nodes']=cfg['max_nodes']
    rows=[]
    for model in ['R4','C3','S3']:
        fixture=next(f for f in F if f['model']==model and f['pose_id']==cfg['pose'])
        mode=next(r for r in M['mobility'] if r['model']==model and r['pose']==cfg['pose'] and r['heading_deg']==cfg['heading_deg'] and r['rotation_component_cap']==cfg['cap'])
        assert mode['success']
        RA=np.array(fixture['central_rotation']);v=np.array(mode['translation_per_mm']);w=np.array(mode['rotation_scaled'])
        z0=support_points(model,np.array([0.,0.,1.]),R,a,RA)[0]
        for s in cfg['travel_mm']:
            rot=Rotation.from_rotvec(w*s/R).as_matrix()@RA
            center=v*s
            platen=z0+mode['rise_per_mm']*s
            ztop=support_points(model,np.array([0.,0.,1.]),R,a,rot)[0]+center[2]
            pairs=[]
            for j,support in enumerate(fixture['supports']):
                distance=distance_bracket(model,rot,np.array(support['rotation']),center,np.array(support['center']),params)
                distance['support_index']=j
                distance['bracket_reached']=distance['certificate_gap_um']<=cfg['distance_gap_mm']*1000*(1+1e-9)
                pairs.append(distance)
            bound_top=platen-ztop
            rows.append(dict(model=model,pose=cfg['pose'],heading_deg=cfg['heading_deg'],cap=cfg['cap'],travel_mm=s,rotation_angle_deg=float(np.linalg.norm(w*s/R)*180/math.pi),central_rotation=rot.tolist(),center_mm=center.tolist(),platen_height_mm=platen,platen_clearance_mm=bound_top,support_distances=pairs,collision_witness=bound_top < -1e-9 or any(p['clearance_upper_mm'] < -1e-9 for p in pairs),continuous_free_path_proven=False))
            print(json.dumps(dict(model=model,travel_mm=s,plate_gap_um=bound_top*1000,min_support_upper_um=min(p['clearance_upper_mm'] for p in pairs)*1000)),flush=True)
    out=dict(physical_tests=0,success_probability=None,scope='Only prescribed endpoint probes; a collision is a counterexample to that path, not a proof no other path exists. Initial contact coordinates are approximate.',rows=rows)
    (D/'path_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(endpoints=len(rows),distance_queries=sum(len(r['support_distances']) for r in rows))))
if __name__=='__main__':main()
