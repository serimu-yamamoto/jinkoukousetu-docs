"""Central rigid grain supported by three fixed grains and a flat platen.
Contact sites approximate certified first-touch heights; neighboring grains are
checked for overlap independently. This is a small fixture, not a settled bed.
"""
import math,json,copy,heapq,itertools
from pair_geometry import H,np,arcs,point,support_points,first_contact,Rotation
from scipy.optimize import linprog

def basis(n):
    n=np.array(n,dtype=float);n/=np.linalg.norm(n);v=np.array([1.,0,0]) if abs(n[0])<.8 else np.array([0.,1,0]);u=np.cross(n,v);u/=np.linalg.norm(u);v=np.cross(n,u);return np.column_stack([u,v,n])

def distance_bracket(model,rotA,rotB,centerA,centerB,I):
    R=I['geometry']['R_mm'];parts=arcs(model);best=math.inf;heap=[];counter=itertools.count();nodes=0
    def add(ia,ib,la,ha,lb,hb):
        nonlocal best,nodes
        pa=point(parts[ia],(la+ha)/2,R,rotA)+centerA;pb=point(parts[ib],(lb+hb)/2,R,rotB)+centerB
        d=float(np.linalg.norm(pa-pb));cover=2*R*(math.sin((ha-la)/4)+math.sin((hb-lb)/4));best=min(best,d);low=max(0.,d-cover);nodes+=1
        if low<best:heapq.heappush(heap,(low,next(counter),(ia,ib,la,ha,lb,hb)))
    segments=[]
    for i,arc in enumerate(parts):
        n=math.ceil((arc[3]-arc[2])/(math.pi/4));ts=np.linspace(arc[2],arc[3],n+1);segments.extend((i,float(lo),float(hi)) for lo,hi in zip(ts[:-1],ts[1:]))
    for ia,la,ha in segments:
        for ib,lb,hb in segments:add(ia,ib,la,ha,lb,hb)
    while heap and best-heap[0][0]>I['pair']['certificate_gap_mm'] and nodes<I['pair']['max_nodes']:
        low,_,(ia,ib,la,ha,lb,hb)=heapq.heappop(heap)
        if low>=best:continue
        if ha-la>=hb-lb:
            m=(la+ha)/2;add(ia,ib,la,m,lb,hb);add(ia,ib,m,ha,lb,hb)
        else:
            m=(lb+hb)/2;add(ia,ib,la,ha,lb,m);add(ia,ib,la,ha,m,hb)
    low=min(best,heap[0][0]) if heap else best;a=I['geometry']['wire_radius_mm']
    return dict(clearance_lower_mm=low-2*a,clearance_upper_mm=best-2*a,nodes=nodes,certificate_gap_um=(best-low)*1000,disjoint=low>=2*a,overlapping=best<2*a)

def wrench_lp(points,normals,mu_top,mu_internal,R,edges=16,outer=False):
    columns=[];dirs=[];factor=1/math.cos(math.pi/edges) if outer else 1
    for j,(p,n) in enumerate(zip(points,normals)):
        B=basis(n);mu=(mu_top if j==0 else (mu_internal[j-1] if isinstance(mu_internal,list) else mu_internal))*factor
        for angle in np.arange(edges)*2*math.pi/edges:
            force=B@np.array([mu*math.cos(angle),mu*math.sin(angle),1.]);columns.append(np.r_[force,np.cross(p/R,force),1. if j==0 else 0.]);dirs.append(force)
    A=np.array(columns).T;b=np.r_[np.zeros(6),1.];sol=linprog(np.ones(A.shape[1]),A_eq=A,b_eq=b,bounds=(0,None),method='highs')
    ans=dict(success=bool(sol.success),status=int(sol.status),edges=edges,outer_cone=outer,mu_top=mu_top,mu_internal=mu_internal)
    if sol.success:
        weights=sol.x.reshape(-1,edges);forces=np.einsum('ij,ijk->ik',weights,np.array(dirs).reshape(-1,edges,3));ratios=[];fn=[]
        for f,n in zip(forces,normals):
            z=float(f@n);t=np.linalg.norm(f-z*n);ratios.append(float(t/max(z,1e-30)));fn.append(z)
        ans.update(residual=float(np.linalg.norm(A@sol.x-b)),forces_normalized=forces.tolist(),normal_components=fn,actual_friction_ratios=ratios,total_support_normal=sum(fn[1:]))
    return ans

def main():
    I=json.loads((H/'inputs.json').read_text(encoding='utf-8'));P=json.loads((H/'pair_results.json').read_text(encoding='utf-8'));out=[];R=I['geometry']['R_mm'];a=I['geometry']['wire_radius_mm'];rng=np.random.default_rng(13132026)
    for model in I['geometry']['models']:
        for pose in I['cluster']['poses']:
            RA=np.array(next(x for x in P['cases'] if x['model']==model and x['pose_id']==pose)['rotation_top']);top=support_points(model,np.array([0.,0,1]),R,a,RA)[1];assert len(top)==1
            supports=[];points=[top[0]];normals=[np.array([0.,0.,-1.])]
            for j,phi in enumerate(I['cluster']['azimuth_deg']):
                theta=math.radians(I['cluster']['polar_deg']);ph=math.radians(phi);d=np.array([math.sin(theta)*math.cos(ph),math.sin(theta)*math.sin(ph),math.cos(theta)]);Q=basis(d);RB=Rotation.random(random_state=np.random.default_rng(I['cluster']['seed_base']+pose*3+j)).as_matrix();touch=first_contact(model,Q.T@RA,Q.T@RB,np.zeros(3),I)
                z=touch['height_lower_mm'];center=-z*d;p=Q@np.array(touch['representative_contact'])-z*d;n=Q@np.array(touch['representative_normal']);supports.append(dict(rotation=RB.tolist(),center=center.tolist(),height_gap_um=touch['height_gap_um'],certificate_reached=touch['certificate_reached']));points.append(p);normals.append(n)
            separation=[]
            for i,j in itertools.combinations(range(3),2):
                A=supports[i];B=supports[j];d=distance_bracket(model,np.array(A['rotation']),np.array(B['rotation']),np.array(A['center']),np.array(B['center']),I);d['pair']=[i,j];separation.append(d)
            platen_gaps=[float(top[0,2]-support_points(model,np.array([0.,0,1]),R,a,np.array(s['rotation']))[0]-s['center'][2]) for s in supports]
            valid=all(x['disjoint'] for x in separation) and min(platen_gaps)>=0;results=[]
            if valid:
                for mut,mui in itertools.product(I['cluster']['mu_top'],I['cluster']['mu_internal']):
                    inner=wrench_lp(points,normals,mut,mui,R,outer=False);outer=wrench_lp(points,normals,mut,mui,R,outer=True);results.append(dict(mu_top=mut,mu_internal=mui,inner=inner,outer=outer,classification='feasible_inner' if inner['success'] else ('infeasible_outer' if outer['status']==2 else 'unresolved')))
            row=dict(model=model,pose_id=pose,central_rotation=RA.tolist(),supports=supports,points=np.array(points).tolist(),normals=np.array(normals).tolist(),neighbor_clearances=separation,neighbor_platen_gaps_mm=platen_gaps,neighbor_geometry_valid=valid,contact_geometry_tolerance_um=I['pair']['certificate_gap_mm']*1000,force_cases=results,scope='Three fixed neighbors; no contact couples, no gravity, no elastic relaxation, no extra contacts search. Static wrench feasibility at approximate sites, not full grain-bed stability.')
            out.append(row);print(json.dumps({'model':model,'pose':pose,'disjoint_neighbors':valid,'force_cases':len(results)}),flush=True)
    (H/'cluster_results.json').write_text(json.dumps(dict(physical_tests=0,success_probability=None,fixtures=out),indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
