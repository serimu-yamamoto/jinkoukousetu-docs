"""Exact arc support and certified first-touch height via interval covering balls.
Dimensions mm. Contacts and force directions from the maximizing sample are
approximate even when height is bracketed; they are not force-closure proofs.
"""
from pathlib import Path
import sys,json,math,heapq,itertools
H=Path(__file__).resolve().parent;ROOT=H.parent.parent
if (ROOT/'.deps').exists():sys.path.insert(0,str(ROOT/'.deps'))
import numpy as np
from scipy.spatial.transform import Rotation

def arcs(model,R=.24,opening=150):
    al=math.radians(opening/2);e=np.eye(3)
    if model=='R4':return [(e[0],e[1],al,2*math.pi-al),(e[0],e[2],al,2*math.pi-al),(e[1],e[2],0.,2*math.pi)]
    if model=='C3':return [(e[0],e[1],al,2*math.pi-al),(e[1],e[2],al,2*math.pi-al),(e[2],e[0],al,2*math.pi-al)]
    if model=='S3':return [(e[0],e[1],0.,2*math.pi),(e[1],e[2],0.,2*math.pi),(e[2],e[0],0.,2*math.pi)]
    raise ValueError(model)

def point(arc,t,R,rot):return rot@(R*(arc[0]*math.cos(t)+arc[1]*math.sin(t)))
def support_points(model,n,R,a,rot):
    candidates=[]
    for arc in arcs(model):
        p=math.atan2(n@(rot@arc[1]),n@(rot@arc[0]))%(2*math.pi);ts=[arc[2],arc[3]]
        if arc[2]<=p<=arc[3]:ts.append(p)
        if math.hypot(n@(rot@arc[0]),n@(rot@arc[1]))<1e-12:
            ts.extend(t for t in [math.pi/2,math.pi,3*math.pi/2] if arc[2]<=t<=arc[3])
        for t in ts:candidates.append(point(arc,t,R,rot)+a*n)
    pts=np.array(candidates);hv=pts@n;mx=hv.max();ans=pts[hv>=mx-1e-10]
    unique=[]
    for p in ans:
        if not any(np.linalg.norm(p-q)<1e-9 for q in unique):unique.append(p)
    return float(mx),np.array(unique)

def first_contact(model,rotA,rotB,offset,inp):
    g=inp['geometry'];R=g['R_mm'];a=g['wire_radius_mm'];r=2*a;parts=arcs(model);heap=[];counter=itertools.count();best=-math.inf;bestdata=None;nodes=0
    def bounds(ia,ib,la,ha,lb,hb):
        nonlocal best,bestdata,nodes
        ma=(la+ha)/2;mb=(lb+hb)/2;pa=point(parts[ia],ma,R,rotA)+offset;pb=point(parts[ib],mb,R,rotB);d=pb-pa;xy2=float(d[:2]@d[:2]);cover=2*R*(math.sin((ha-la)/4)+math.sin((hb-lb)/4));rr=r+cover
        nodes+=1
        if xy2>rr*rr:return
        upper=float(d[2]+math.sqrt(max(0.,rr*rr-xy2)))
        if xy2<=r*r:
            lower=float(d[2]+math.sqrt(max(0.,r*r-xy2)))
            if lower>best:best=lower;bestdata=(ia,ib,ma,mb,pa.copy(),pb.copy())
        if upper>best:heapq.heappush(heap,(-upper,next(counter),(ia,ib,la,ha,lb,hb)))
    segments=[]
    for i,arc in enumerate(parts):
        n=math.ceil((arc[3]-arc[2])/inp['pair']['initial_arc_span_rad']);ts=np.linspace(arc[2],arc[3],n+1)
        segments.extend((i,float(lo),float(hi)) for lo,hi in zip(ts[:-1],ts[1:]))
    for ia,la,ha in segments:
        for ib,lb,hb in segments:bounds(ia,ib,la,ha,lb,hb)
    while heap and -heap[0][0]-best>inp['pair']['certificate_gap_mm'] and nodes<inp['pair']['max_nodes']:
        neg,_,(ia,ib,la,ha,lb,hb)=heapq.heappop(heap)
        if -neg<=best:continue
        if ha-la>=hb-lb:
            m=(la+ha)/2;bounds(ia,ib,la,m,lb,hb);bounds(ia,ib,m,ha,lb,hb)
        else:
            m=(lb+hb)/2;bounds(ia,ib,la,ha,lb,m);bounds(ia,ib,la,ha,m,hb)
    upper=max(best,-heap[0][0]) if heap else best
    if bestdata is None:return dict(found=False,nodes=nodes)
    ia,ib,ta,tb,pa,pb=bestdata;pa[2]+=best;n=(pa-pb)/r;q=pa-a*n
    htop,top=support_points(model,np.array([0.,0.,1.]),R,a,rotA);top=top+offset+np.array([0.,0.,best])
    unique_top=len(top)==1;analysis=None
    if unique_top:
        d=top[0]-q;v=d/np.linalg.norm(d);c1=float(v[2]);c2=float(v@n)
        analysis=dict(top_mu_required=None if c1<=0 else math.sqrt(max(0.,1-c1*c1))/c1,bottom_mu_required=None if c2<=0 else math.sqrt(max(0.,1-c2*c2))/c2,top_cosine=c1,bottom_cosine=c2,line_direction=v.tolist(),finite_compressive_two_force_solution=c1>0 and c2>0)
    return dict(found=True,height_lower_mm=best,height_upper_mm=upper,height_gap_um=(upper-best)*1000,certificate_reached=upper-best<=inp['pair']['certificate_gap_mm'],nodes=nodes,arc_ids=[ia,ib],arc_parameters=[ta,tb],bottom_centerline=pb.tolist(),top_centerline=pa.tolist(),representative_contact=q.tolist(),representative_normal=n.tolist(),top_contact_points=top.tolist(),unique_top=unique_top,two_force_analysis=analysis,scope='Two-force analysis assumes one lower point and a unique upper point. Other simultaneous contacts are not excluded by a height bracket; no stability or success-rate claim.')

def main():
    I=json.loads((H/'inputs.json').read_text(encoding='utf-8'));rng=np.random.default_rng(I['pair']['seed']);RA=Rotation.random(I['pair']['random_orientations'],random_state=rng).as_matrix();RB=Rotation.random(I['pair']['random_orientations'],random_state=rng).as_matrix();off=np.r_[I['pair']['lateral_offset_mm'],0.];rows=[]
    for model in I['geometry']['models']:
        for j,(qa,qb) in enumerate(zip(RA,RB)):
            ans=first_contact(model,qa,qb,off,I);ans.update(model=model,pose_id=j,rotation_top=qa.tolist(),rotation_bottom=qb.tolist(),lateral_offset=off.tolist());rows.append(ans)
            print(json.dumps({'model':model,'pose':j,'height_gap_um':ans.get('height_gap_um'),'nodes':ans['nodes']}),flush=True)
    dirs=np.vstack([Rotation.random(256,random_state=rng).apply([0,0,1]),np.eye(3),-np.eye(3),np.array(list(itertools.product([-1.,1.],repeat=3)))/math.sqrt(3)]);calipers=[];R=I['geometry']['R_mm'];a=I['geometry']['wire_radius_mm']
    for model in I['geometry']['models']:
        widths=[support_points(model,n,R,a,np.eye(3))[0]+support_points(model,-n,R,a,np.eye(3))[0] for n in dirs]
        length=sum(hi-lo for _,_,lo,hi in arcs(model))*R;nends=0 if model=='S3' else (4 if model=='R4' else 6);vol=math.pi*a*a*length+nends*2*math.pi*a**3/3
        calipers.append(dict(model=model,width_min_sample_mm=min(widths),width_max_sample_mm=max(widths),width_ratio_sample=max(widths)/min(widths),widths_mm=widths,centerline_length_mm=length,volume_sum_upper_mm3=vol,cap_count=nends,scope='Volume is union upper bound (sum before intersections). Width range is sampled, not a proven extremum.'))
    out=dict(metadata={'physical_tests':0,'success_probability':None,'scope':I['pair']['scope']},cases=rows,calipers=calipers,directions=dirs.tolist())
    (H/'pair_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
