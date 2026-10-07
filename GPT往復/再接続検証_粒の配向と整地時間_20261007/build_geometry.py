"""Generate rounded comparison grains as binary STL in millimetres; no mechanical claim."""
from pathlib import Path
import json, math, struct, sys, os
H=Path(__file__).resolve().parent; root=H.parent.parent
if (root/".deps").exists(): sys.path.insert(0,str(root/".deps"))
os.environ.setdefault("MPLCONFIGDIR",str(root/".scratch"/"mpl"))
import numpy as np
from collections import Counter
from scipy.optimize import minimize
I=json.loads((H/"inputs.json").read_text(encoding="utf-8")); G=I["ring"]
results=json.loads((H/"results.json").read_text(encoding="utf-8"))
R=G["center_radius_um"]/1000; a=G["tube_radius_um"]/1000; mode=G["wave_number"]

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
        o.write(b"Cycle10 geometry comparison; units mm; not validated material".ljust(80,b" "))
        o.write(struct.pack("<I",len(f)))
        for p in tri:
            norm=np.cross(p[1]-p[0],p[2]-p[0]);norm=norm/np.linalg.norm(norm)
            o.write(struct.pack("<12fH",*norm,*p.flatten(),0))

def build_all():
    records=[];models=[]
    for h in G["wave_heights_um"]:
        vc,fc=mesh(h,81,24,6);vf,ff=mesh(h)
        coarse=validate(vc,fc);fine=validate(vf,ff)
        analytical=next(x["solid_volume_mm3"] for x in results["geometries"] if x["height_um"]==h)
        fine["relative_volume_error"]=abs(fine["volume_mm3"]/analytical-1)
        coarse["relative_volume_error"]=abs(coarse["volume_mm3"]/analytical-1)
        assert fine["relative_volume_error"]<.006 and fine["relative_volume_error"]<coarse["relative_volume_error"]
        tri=vf[ff]
        signed=np.einsum("ij,ij->i",tri[:,0],np.cross(tri[:,1],tri[:,2]))/6
        centroid=np.sum(signed[:,None]*(tri[:,0]+tri[:,1]+tri[:,2])/4,axis=0)/signed.sum()
        p=np.linspace(math.radians(G["opening_deg"])/2,2*math.pi-math.radians(G["opening_deg"])/2,4001)
        centres=np.column_stack((R*np.cos(p),R*np.sin(p),(h/1000)*np.cos(mode*p)))
        def support_height(x):
            th,az=x
            n=np.array([math.sin(th)*math.cos(az),math.sin(th)*math.sin(az),math.cos(th)])
            return float(n@centroid-np.min(centres@n)+a)
        candidates=[]
        for th in [0,.25,.7,1.3,2.1,2.8,math.pi]:
            for az in np.linspace(0,2*math.pi,6,endpoint=False):
                opt=minimize(support_height,[th,az],method="Nelder-Mead",options={"maxiter":400,"xatol":1e-8,"fatol":1e-11})
                candidates.append((float(opt.fun),float(math.degrees(math.acos(abs(math.cos(opt.x[0])))))))
        best=min(candidates)
        support={"centre_of_mass_mm":centroid.tolist(),"minimum_height_found_mm":best[0],"tilt_from_original_plane_normal_deg":best[1],"vertical_up_height_mm":support_height([0,0]),"vertical_down_height_mm":support_height([math.pi,0]),"scope":"42-start local search of gravity support on a rigid plane. Centreline sampled at 4001 points, mesh mass centroid. No certified global optimum or dynamic packing proof."}
        name="R0_planar" if h==0 else f"R1_wave_{h}um"
        write_stl(H/(name+".stl"),vf,ff)
        records.append({"name":name,"height_um":h,"analytic_volume_mm3":analytical,"coarse":coarse,"final":fine,"gravity_support":support})
        models.append((h,vf,ff))
    (H/"mesh_validation.json").write_text(json.dumps(records,indent=2)+"\n",encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig=plt.figure(figsize=(13,5),layout="constrained")
    for j,(h,v,f) in enumerate(models):
        ax=fig.add_subplot(1,3,j+1,projection="3d")
        poly=Poly3DCollection(v[f],facecolors=["#adcddd","#7aaccc","#568fb5"][j],edgecolor="none",alpha=1,shade=True)
        ax.add_collection3d(poly)
        ax.set(xlim=(-.31,.31),ylim=(-.31,.31),zlim=(-.16,.16),xlabel="x (mm)",ylabel="y (mm)",zlabel="z (mm)",title=("R0 planar" if h==0 else f"R1: wave h = {h} um"))
        ax.set_box_aspect((1,1,.52));ax.view_init(28,38)
    fig.suptitle("Rounded open grains | geometric candidates, not proven snow substitutes",fontsize=14)
    fig.savefig(H/"grain_geometry.png",dpi=160);plt.close(fig)
    print(json.dumps({"models":len(records),"triangles_each":[x["final"]["triangles"] for x in records],
                      "volume_relative_deviation":[x["final"]["relative_volume_error"] for x in records]},indent=2))


if __name__=="__main__":
    build_all()
