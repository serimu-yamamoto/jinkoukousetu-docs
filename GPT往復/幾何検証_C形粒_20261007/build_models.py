"""Export review meshes, not manufacturing-certified CAD.
Dependencies: numpy, manifold3d==3.5.4. Install separately or in repository .deps.
Analytic proofs in analyze.py apply to ideal surfaces, not these tessellations.
"""
from pathlib import Path
import sys, json, math, struct, collections
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'.deps'))
import numpy as np
import manifold3d as md
from analyze import geometry,P

def build(q,N):
    sec=md.CrossSection.circle(q['r_mm'],N).translate((q['R_mm'],0))
    theta=math.degrees(q['theta_rad'])
    m=md.Manifold.revolve(sec,4*N,360-2*theta).rotate((0,0,theta))
    for s in [1,-1]:
        tip=(q['R_mm']*math.cos(q['theta_rad']),s*q['R_mm']*math.sin(q['theta_rad']),0)
        m=m+md.Manifold.sphere(q['re_mm'],N).translate(tip)
    return m

def arrays(m):
    mesh=m.to_mesh()
    return np.asarray(mesh.vert_properties)[:,:3],np.asarray(mesh.tri_verts)

def meshcheck(m):
    v,f=arrays(m); counts=collections.Counter()
    for a,b,c in f:
        for i,j in [(a,b),(b,c),(c,a)]:counts[tuple(sorted((int(i),int(j))))]+=1
    status=str(m.status()); closed=all(n==2 for n in counts.values())
    assert 'NoError' in status and closed and m.volume()>0
    return dict(status=status,vertices=len(v),triangles=len(f),each_edge_two_faces=closed,
        euler=len(v)-len(counts)+len(f),volume_mm3=m.volume(),area_mm2=m.surface_area())

def stl(m,name):
    v,f=arrays(m)
    with (HERE/name).open('wb') as out:
        out.write(b'Units: mm; research geometry only; ideal-path proof separate'.ljust(80,b' '))
        out.write(struct.pack('<I',len(f)))
        for ids in f:
            a,b,c=v[ids];normal=np.cross(b-a,c-a);length=np.linalg.norm(normal)
            if length>0:normal=normal/length
            out.write(struct.pack('<12fH',*normal,*a,*b,*c,0))

def facing(m,c):
    return m.transform(((-1,0,0,c),(0,0,1,0),(0,1,0,0)))

def scad():
    text='// Units mm. Capped circular-tube model; no manufacturing/force validation.\n$fn=128;\n'
    text+='module grain(D=0.6,d=0.06,De=0.10,g=0.02){\n R=(D-De)/2; t=asin((De+g)/(2*R));\n union(){ rotate([0,0,t]) rotate_extrude(angle=360-2*t) translate([R,0]) circle(r=d/2);\n for(s=[-1,1]) translate([R*cos(t),s*R*sin(t),0]) sphere(r=De/2); } }\n'
    text+='// candidate: 1=G1, 2=G2, 3=G3. pair=true shows checked facing-gap pose.\n'
    text+='candidate=3; pair=false; separation=0.5;\n De=candidate==3?0.10:0.06; g=candidate==1?0.04:0.02;\n grain(De=De,g=g);\n if(pair) multmatrix([[-1,0,0,separation],[0,0,1,0],[0,1,0,0],[0,0,0,1]]) grain(De=De,g=g);\n'
    (HERE/'C形粒.scad').write_text(text,encoding='utf-8')

def color(base,factor):
    rgb=[int(base[i:i+2],16) for i in (1,3,5)]
    return '#'+''.join(f'{max(0,min(255,int(x*factor))):02x}' for x in rgb)

def projected(objects,cx,cy,scale,offset=(0,0,0)):
    U=np.array([.819,-.574,0]);V=np.array([.287,.410,-.866]);W=np.cross(U,V)
    light=np.array([.1,-.4,1]); light/=np.linalg.norm(light)
    polygons=[]
    for m,col in objects:
        vert,faces=arrays(m);vert=vert-np.array(offset)
        for ids in faces:
            vs=vert[ids];norm=np.cross(vs[1]-vs[0],vs[2]-vs[0]);length=np.linalg.norm(norm)
            if length==0:continue
            norm/=length
            pts=' '.join(f'{cx+scale*x:.2f},{cy+scale*y:.2f}' for x,y in zip(vs@U,vs@V))
            polygons.append((float(np.mean(vs@W)),f'<polygon points="{pts}" fill="{color(col,.75+.25*abs(np.dot(norm,light)))}"/>'))
    return ''.join(s for _,s in sorted(polygons))

def svg(previews,rows):
    head='<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1100" viewBox="0 0 1600 1100"><style>text{font-family:Yu Gothic,Meiryo,sans-serif;fill:#193c50}.h{font-size:28px;font-weight:700}.t{font-size:23px}.s{font-size:19px}.note{fill:#5b7280}</style><rect width="1600" height="1100" fill="#f3f7fa"/>'
    parts=[head,'<text x="55" y="58" class="h">C形粒：二つの隙間が向き合うと、狭い隙間でも抜ける場合がある</text>',
        '<text x="55" y="96" class="t note">丸い断面・丸い端部の理想形状。全方向の保持や材料強度を証明した図ではありません。</text>']
    q=rows[0];m=previews[0]
    for j,(c,label) in enumerate([(3*q['R_mm'],'離れた状態'),(q['critical_separation_mm'],'すり抜けの最接近'),(q['R_mm'],'絡んで見える状態')]):
        x=50+j*510
        parts.append(f'<rect x="{x}" y="126" width="490" height="358" rx="18" fill="white"/><text x="{x+22}" y="169" class="h">G1：{label}</text>')
        parts.append(projected([(m,'#4a9bbb'),(facing(m,c),'#df9b51')],x+245,306,325,(c/2,0,0)))
        parts.append(f'<text x="{x+22}" y="447" class="t">中心距離 {c:.4f} mm</text>')
    parts.append('<text x="62" y="526" class="t">G1は、動き全体を通じて表面間隔が10.71µm以上。ばねを曲げずに逆向きにも抜ける。</text>')
    captions=[('G1：線径60µm／隙間40µm','この経路は通過する'),('G2：線径60µm／隙間20µm','この経路は衝突。ただし公差に弱い'),('G3：端部径100µm／隙間20µm','この経路を妨げる余裕を増やす')]
    for j,(q,m,(label,sub)) in enumerate(zip(rows,previews,captions)):
        x=50+j*510
        parts.append(f'<rect x="{x}" y="558" width="490" height="402" rx="18" fill="white"/><text x="{x+20}" y="602" class="t">{label}</text>')
        parts.append(projected([(m,'#508dad')],x+245,750,400))
        parts.append(f'<text x="{x+20}" y="875" class="s">{sub}</text><text x="{x+20}" y="913" class="s note">包絡径 0.6 mm ／ 作動力・疲労は未評価</text>')
    parts.append('<text x="55" y="1004" class="t">G3の体積上限はG1比＋8.81％。全ての抜け道を塞いだ証明ではありません。</text>')
    parts.append('<text x="55" y="1044" class="s note">3Dメッシュから投影。接触判定は図の見た目ではなく、報告書の連続経路の解析式によります。</text></svg>')
    (HERE/'C形粒_立体と抜け道.svg').write_text(''.join(parts),encoding='utf-8')

def main():
    shapes=[geometry(x) for x in P['candidates']]
    rows=json.loads((HERE/'results.json').read_text(encoding='utf-8'))['candidates']
    records=[];previews=[];pairs=[]
    for q in shapes:
        levels=[];model=None
        for N in [16,32,64]:
            model=build(q,N);check=meshcheck(model);check['quality']=N;levels.append(check)
            if N==16:previews.append(model)
        assert abs(levels[-1]['volume_mm3']-levels[-2]['volume_mm3'])/levels[-1]['volume_mm3']<.01
        assert q['volume_lower_mm3']*.99<=model.volume()<=q['volume_upper_mm3']*1.001
        stl(model,q['id']+'.stl')
        cs=2*q['R_mm']*math.cos(q['theta_rad']);b=facing(model,cs)
        overlap=(model^b).volume();pairs.append(dict(id=q['id'],critical_pose_intersection_volume_mm3=overlap,
            note='Single tessellated pose check, not continuous or all-direction proof.'))
        if q['id']=='G1':
            assert overlap<1e-12
            stl(model+b,'G1_最接近する二粒.stl')
        else:assert overlap>0
        records.append(dict(id=q['id'],quality_levels=levels,
            stl_units='mm',meshes_are_approximations=True))
    scad();svg(previews,rows)
    meta=dict(manifold3d_version='3.5.4',numpy_version=np.__version__,mesh_checks=records,
        critical_pose_checks=pairs,scope='Review meshes; no physical, fabrication, or all-pose validation.')
    (HERE/'mesh_validation.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(meshes=4,checks=[{'id':r['id'],'volume':r['quality_levels'][-1]['volume_mm3'],'faces':r['quality_levels'][-1]['triangles']} for r in records],intersections=pairs),indent=2))
if __name__=='__main__':main()
