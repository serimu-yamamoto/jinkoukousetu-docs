"""Research meshes for W0 and W1. Texture and production tolerances omitted.
Python 3.12, numpy 2.3.5, manifold3d 3.5.4. Use repository .deps if present.
"""
import sys, json, math, struct, collections
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'.deps'))
import numpy as np
import manifold3d as md
from analyze_seats import P, R, r, re, theta, protective_support, seat_support

def backbone(N):
    sec=md.CrossSection.circle(r,N).translate((R,0))
    a=math.degrees(theta)
    m=md.Manifold.revolve(sec,4*N,360-2*a).rotate((0,0,a))
    for s in [-1,1]:
        m=m+md.Manifold.sphere(re,N).translate((R*math.cos(theta),s*R*math.sin(theta),0))
    return m

def seats(c,N):
    bodies=[]
    for a in c['seat_angles_deg']:
        t=math.radians(a)
        bodies.append(md.Manifold.sphere(1,N).scale(c['axes']).rotate((0,0,a)).translate((c['rho']*math.cos(t),c['rho']*math.sin(t),0)))
    result=bodies[0]
    for b in bodies[1:]:result=result+b
    return result

def arrays(m):
    mesh=m.to_mesh()
    return np.asarray(mesh.vert_properties)[:,:3],np.asarray(mesh.tri_verts)

def meshcheck(m):
    v,f=arrays(m);count=collections.Counter()
    for a,b,c in f:
        for x,y in [(a,b),(b,c),(c,a)]:count[tuple(sorted((int(x),int(y))))]+=1
    closed=all(x==2 for x in count.values())
    n_parts=len(m.decompose())
    assert closed and 'NoError' in str(m.status()) and n_parts==1 and m.volume()>0
    return dict(status=str(m.status()),vertices=len(v),triangles=len(f),each_edge_two_faces=closed,
                connected_components=n_parts,euler=len(v)-len(count)+len(f),volume_mm3=m.volume(),area_mm2=m.surface_area())

def save_stl(m,name):
    v,f=arrays(m)
    with (HERE/name).open('wb') as out:
        out.write(b'Units mm; nominal untextured geometry; research review only'.ljust(80,b' '))
        out.write(struct.pack('<I',len(f)))
        for ids in f:
            a,b,c=v[ids];normal=np.cross(b-a,c-a);norm=np.linalg.norm(normal)
            if norm:normal/=norm
            out.write(struct.pack('<12fH',*normal,*a,*b,*c,0))

def color(hexcolor,k):
    return '#'+''.join(f'{int(int(hexcolor[i:i+2],16)*k):02x}' for i in [1,3,5])

def project(objects,cx,cy,scale):
    U=np.array([.819,-.574,0]); V=np.array([.287,.410,-.866]); W=np.cross(U,V)
    light=np.array([.1,-.4,1]);light/=np.linalg.norm(light); polygons=[]
    for obj,col in objects:
        v,f=arrays(obj)
        for ids in f:
            vs=v[ids];n=np.cross(vs[1]-vs[0],vs[2]-vs[0]);l=np.linalg.norm(n)
            if l==0:continue
            n/=l
            points=' '.join(f'{cx+scale*x:.2f},{cy+scale*y:.2f}' for x,y in zip(vs@U,vs@V))
            polygons.append((float(np.mean(vs@W)),f'<polygon points="{points}" fill="{color(col,.72+.28*abs(n@light))}"/>'))
    return ''.join(x for _,x in sorted(polygons))

def scad():
    t='''// Units mm. Review geometry; no applied texture, load or manufacturing certification.
$fn=128;
candidate=1; // 0 = exposed thick seat, 1 = W1_one, 3 = W1_three
R=0.25; r=0.03; re=0.05; gap=0.02; theta=asin((2*re+gap)/(2*R));
module backbone(){ union(){
 rotate([0,0,theta]) rotate_extrude(angle=360-2*theta) translate([R,0]) circle(r=r);
 for(s=[-1,1]) translate([R*cos(theta),s*R*sin(theta),0]) sphere(r=re);
}}
module seat(a){ rotate([0,0,a]) translate([0.22,0,0]) scale([0.04,0.035,candidate==0?0.045:0.02]) sphere(r=1); }
union(){backbone(); if(candidate==3){ for(a=[60,180,300]) seat(a); } else seat(180); }
'''
    (HERE/'内側保持座.scad').write_text(t,encoding='utf-8')

def figure(previews,records):
    x=['''<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1040" viewBox="0 0 1500 1040"><style>text{font-family:Meiryo,'Noto Sans CJK JP',sans-serif;fill:#173149}.h{font-size:28px;font-weight:700}.t{font-size:21px}.s{font-size:18px}.bad{fill:#b64132}.good{fill:#14785a}</style><rect width="1500" height="1040" fill="#f3f7f9"/>
<text x="40" y="50" class="h">内側の保持座は、厚くするより面内へ広げる</text>
<text x="40" y="88" class="t">理想形状と剛体平面の接触を検証。実ソール・荷重・50℃での保護は別の検証。</text>''']
    labels=[('W0：厚い座の反例','80 × 70 × 90µm / 1か所'),('W1a：薄い内側座','80 × 70 × 40µm / 1か所'),('W1b：座を3か所へ','80 × 70 × 40µm / 3か所')]
    for j,((body,seat),rec,(label,sub)) in enumerate(zip(previews,records,labels)):
        ox=30+j*490
        x.append(f'<rect x="{ox}" y="115" width="470" height="430" fill="white" rx="15"/><text x="{ox+20}" y="157" class="h">{label}</text><text x="{ox+20}" y="192" class="s">{sub}</text>')
        x.append(project([(body,'#5d8ba3'),(seat,'#dfac51')],ox+235,342,430))
        margin=rec['analytic_plane_margin_lower_mm']*1000
        if j==0:
            x.append(f'<text x="{ox+20}" y="480" class="t bad">斜めの平面へ保持座が先に当たる</text><text x="{ox+20}" y="514" class="s">明示した方向で約13.2µm露出</text>')
        else:
            x.append(f'<text x="{ox+20}" y="480" class="t good">全方向の理想保護余裕 ≥ {margin:.0f}µm</text><text x="{ox+20}" y="514" class="s">外向き形状差2µmを含めて ≥ 8µm</text>')
    x.append('''<rect x="30" y="565" width="705" height="421" fill="white" rx="15"/>
<text x="55" y="608" class="h">平らな板に対する条件</text>
<path d="M 80 690 L 680 690" stroke="#182f45" stroke-width="6"/>
<circle cx="130" cy="728" r="38" fill="#5d8ba3"/><circle cx="630" cy="728" r="38" fill="#5d8ba3"/>
<ellipse cx="380" cy="763" rx="100" ry="39" fill="#dfac51"/>
<path d="M 305 723 L 555 723" stroke="#dfac51" stroke-width="2" stroke-dasharray="5 4"/>
<path d="M 553 692 L 553 721" stroke="#14785a" stroke-width="3"/>
<text x="578" y="717" class="s good">余裕</text>
<text x="77" y="842" class="t">どの方向でも、座より骨格が先に触れる。</text>
<text x="77" y="879" class="s">ただし骨格の摩耗・変形と座の位置ずれが</text>
<text x="77" y="911" class="s">この余裕を使い切ると、保護は失われる。</text>
<text x="77" y="947" class="s">模式図。凸包を閉じた殻として製造しない。</text>
<rect x="755" y="565" width="715" height="421" fill="#e3edf1" rx="15"/>
<text x="780" y="608" class="h">同時に残る条件</text>
<text x="785" y="660" class="t">中心を軸にした貫通円の直径</text>
<text x="785" y="698" class="h">G3：400µm → W1：356µm以上*</text>
<text x="785" y="735" class="s">* 座の外向き差2µmを含む。充填床の水路径ではない。</text>
<text x="785" y="791" class="t">仮の完成粒価格の上限</text>
<text x="785" y="831" class="h">W1a：約587円/kg / W1b：約554円/kg</text>
<text x="785" y="867" class="s">同じ粒数・仮の充填状態、年額1,900万円枠。</text>
<text x="785" y="913" class="s">刃・皮膚・異物の入り込み、柔らかいソール、</text>
<text x="785" y="947" class="s">雪の保持と再整地・全方向の抜け止めは未実証。</text>
<text x="40" y="1020" class="s">物理試験0件。20万方向の数値照合は実験回数・成功確率ではない。全方向条件は本文の解析式で示す。</text></svg>''')
    (HERE/'内側保持座_全方向の保護と反例.svg').write_text(''.join(x),encoding='utf-8')

def main():
    analytic=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    records=[];preview=[]
    for c,row in zip(P['candidates'],analytic['candidates']):
        levels=[]
        for N in P['mesh_quality']:
            core=backbone(N);s=seats(c,N);m=core+s
            ch=meshcheck(m);ch['quality']=N;ch['core_volume_mm3']=core.volume();ch['net_seat_added_volume_mm3']=m.volume()-core.volume();levels.append(ch)
            if N==16:preview.append((core,s))
        conv=abs(levels[-1]['volume_mm3']-levels[-2]['volume_mm3'])/levels[-1]['volume_mm3']
        assert conv<.01
        addconv=abs(levels[-1]['net_seat_added_volume_mm3']-levels[-2]['net_seat_added_volume_mm3'])/levels[-1]['net_seat_added_volume_mm3']
        assert addconv<.01
        assert levels[-1]['volume_mm3']<=row['union_volume_upper_mm3']
        save_stl(m,c['id']+'.stl')
        # Fixed-pose intersection cannot decrease on adding solids to both grains.
        sep=2*R*math.cos(theta)
        facing=lambda o:o.transform(((-1,0,0,sep),(0,0,1,0),(0,1,0,0)))
        old=(core^facing(core)).volume();new=(m^facing(m)).volume()
        assert new>=old-1e-10
        records.append(dict(id=c['id'],levels=levels,last_relative_volume_change=conv,
                            last_relative_added_volume_change=addconv,
                            prior_fixed_pose_intersection_volume_mm3=old,
                            new_fixed_pose_intersection_volume_mm3=new,
                            scope='Nominal untextured meshes; fixed pose only, not insertion, all paths or retention under force.'))
    scad();figure(preview,analytic['candidates'])
    (HERE/'mesh_validation.json').write_text(json.dumps(dict(manifold_version='3.5.4',numpy_version=np.__version__,shapes=records,physical_validation=False),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(records))

if __name__=='__main__':main()
