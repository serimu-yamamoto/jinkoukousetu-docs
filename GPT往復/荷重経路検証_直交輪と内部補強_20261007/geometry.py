"""One-piece rounded R4 prototype geometries. NOT production drawings or strength validation."""
from pathlib import Path
import sys,json,math,struct
from collections import Counter
H=Path(__file__).resolve().parent;root=H.parent.parent
if (root/'.deps').exists():sys.path.insert(0,str(root/'.deps'))
import numpy as np
import manifold3d as md
R=.24;a=.022;mode=3;G={'opening_deg':120}
def frame(phi,h):
    c=np.array([R*math.cos(phi),R*math.sin(phi),h*math.cos(mode*phi)])
    t=np.array([-R*math.sin(phi),R*math.cos(phi),-mode*h*math.sin(mode*phi)])
    t=t/np.linalg.norm(t); n=np.array([math.cos(phi),math.sin(phi),0.]); b=np.cross(t,n)
    return c,t,n,b

def mesh(height_um,narc=161,ncross=48,ncap=12):
    h=height_um/1000;lo=math.radians(G["opening_deg"])/2;hi=2*math.pi-lo
    rings=[];angles=np.arange(ncross)*2*math.pi/ncross
    cs,ts,ns,bs=frame(lo,h); ce,te,ne,be=frame(hi,h)
    for alpha in np.linspace(math.pi/2,0,ncap+1)[1:]:
        rings.append(cs-a*math.sin(alpha)*ts+a*math.cos(alpha)*(np.cos(angles)[:,None]*ns+np.sin(angles)[:,None]*bs))
    for phi in np.linspace(lo,hi,narc)[1:]:
        c,t,n,b=frame(phi,h)
        rings.append(c+a*(np.cos(angles)[:,None]*n+np.sin(angles)[:,None]*b))
    for alpha in np.linspace(0,math.pi/2,ncap+1)[1:-1]:
        rings.append(ce+a*math.sin(alpha)*te+a*math.cos(alpha)*(np.cos(angles)[:,None]*ne+np.sin(angles)[:,None]*be))
    v=np.vstack(([cs-a*ts],*rings,[ce+a*te]))
    f=[]
    for j in range(ncross):
        k=(j+1)%ncross;f.append((0,1+k,1+j))
    for row in range(len(rings)-1):
        p=1+row*ncross;q=p+ncross
        for j in range(ncross):
            k=(j+1)%ncross;f.extend([(p+j,p+k,q+k),(p+j,q+k,q+j)])
    end=len(v)-1; start=end-ncross
    for j in range(ncross):
        k=(j+1)%ncross;f.append((end,start+j,start+k))
    return v,np.array(f,dtype=int)

def validate(v,f):
    tri=v[f];vol=float(np.einsum("ij,ij->i",tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6)
    edges=Counter(tuple(sorted((int(a),int(b)))) for face in f for a,b in zip(face,[face[1],face[2],face[0]]))
    directed=Counter((int(a),int(b)) for face in f for a,b in zip(face,[face[1],face[2],face[0]]))
    area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
    ok=all(n==2 for n in edges.values()) and all(directed[(b,a)]==n for (a,b),n in directed.items())
    assert ok and vol>0 and np.all(area>0)
    return {"vertices":len(v),"triangles":len(f),"volume_mm3":vol,"every_edge_two_faces":True,"consistent_orientation":True,
            "nonzero_face_areas":True,"scope":"Closed oriented surface, volume convergence; not global self-intersection, manufacturing or mechanical proof."}

def write_stl(path,v,f):
    tri=v[f].astype(np.float32)
    with path.open("wb") as o:
        o.write(b"Cycle11 R4 prototype; units mm; unvalidated material".ljust(80,b" "))
        o.write(struct.pack("<I",len(f)))
        for p in tri:
            norm=np.cross(p[1]-p[0],p[2]-p[0]);norm=norm/np.linalg.norm(norm)
            o.write(struct.pack("<12fH",*norm,*p.flatten(),0))


def torus(n=160,m=48):
    phi=np.arange(n)*2*math.pi/n;alpha=np.arange(m)*2*math.pi/m;v=[]
    for p in phi:
        for t in alpha:v.append((a*math.sin(t),(R+a*math.cos(t))*math.cos(p),(R+a*math.cos(t))*math.sin(p)))
    f=[]
    for i in range(n):
        for j in range(m):
            p=i*m+j;q=((i+1)%n)*m+j;pp=i*m+(j+1)%m;qq=((i+1)%n)*m+(j+1)%m
            f.extend([(p,q,qq),(p,qq,pp)])
    return np.array(v),np.array(f)

def part(v,f):
    p=md.Manifold(md.Mesh(vert_properties=v.astype(np.float32),tri_verts=f.astype(np.uint32)))
    assert p.status()==md.Error.NoError
    return p

def shape(opening,n,m,c):
    G['opening_deg']=opening;v,f=mesh(0,n,m,c);one=part(v,f);tv,tf=torus(n-1,m)
    obj=one+one.rotate((90,0,0))+part(tv,tf)
    assert obj.status()==md.Error.NoError and len(obj.decompose())==1
    return obj

def main():
    records=[]
    for opening in [120,150]:
        coarse=shape(opening,81,24,6);obj=shape(opening,161,48,12);raw=obj.to_mesh();v=np.asarray(raw.vert_properties[:,:3]);f=np.asarray(raw.tri_verts)
        rec=validate(v,f);rec.update(opening_deg=opening,wire_diameter_um=44,connected_components=1,coarse_fine_volume_change=abs(obj.volume()-coarse.volume())/obj.volume(),manifold_status='NoError',mesh_is_linear_mechanics_model=False)
        write_stl(H/f'R4_open{opening}_wire44um.stl',v,f)
        rec['registered_intersection_samples']=[]
        for s in [.24,.28,.32,.38,.46,.58]:
            inter=obj ^ obj.translate((s,.06,.06));vol=float(inter.volume());assert vol<1e-12
            rec['registered_intersection_samples'].append({'s_mm':s,'intersection_volume_mm3':vol})
        records.append(rec)
        scad='// Millimetres. R4 comparison concept; material and manufacture unvalidated.\n$fn=128; R=0.24; a=0.022; opening='+str(opening)+';\nmodule C(){rotate([0,0,opening/2]) rotate_extrude(angle=360-opening) translate([R,0,0]) circle(r=a); for(p=[opening/2,360-opening/2])translate([R*cos(p),R*sin(p),0])sphere(r=a);}\nunion(){C(); rotate([90,0,0])C();rotate([0,90,0])rotate_extrude()translate([R,0,0])circle(r=a);}\n'
        (H/f'R4_open{opening}.scad').write_text(scad,encoding='utf-8')
    (H/'geometry_validation.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'shapes':2,'one_piece':True,'samples_without_intersection':12,'volume_relative_changes':[x['coarse_fine_volume_change'] for x in records]},indent=2))
if __name__=='__main__':main()
