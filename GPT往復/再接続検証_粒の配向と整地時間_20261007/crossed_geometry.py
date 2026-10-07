"""R2: two perpendicular rounded C loops, geometric insertion proof and STL.
Does not establish holding, snow friction, manufacturability or physical success."""
from pathlib import Path
import json, math, sys, itertools
H=Path(__file__).resolve().parent; root=H.parent.parent
if (root/".deps").exists():sys.path.insert(0,str(root/".deps"))
import numpy as np
import manifold3d as md
import build_geometry as B
I=json.loads((H/"inputs.json").read_text(encoding="utf-8"))
R=I["ring"]["center_radius_um"]/1000
th=math.radians(I["ring"]["opening_deg"])/2
q=I["ring"]["crossed_variant"]["registered_offset_um"]/1000
xmin=I["ring"]["crossed_variant"]["registered_x_min_um"]/1000
xmax=I["ring"]["crossed_variant"]["registered_x_max_um"]/1000

def crossed(radius_um,narc=161,ncross=48,ncap=12):
    B.a=radius_um/1000
    v,f=B.mesh(0,narc,ncross,ncap)
    one=md.Manifold(md.Mesh(vert_properties=v.astype(np.float32),tri_verts=f.astype(np.uint32)))
    assert one.status()==md.Error.NoError
    both=one+one.rotate((90,0,0))
    assert both.status()==md.Error.NoError and len(both.decompose())==1
    return both

records=[];data=[]
CV=I["ring"]["crossed_variant"]
for ar,opening in [(CV["tube_radius_um"],I["ring"]["opening_deg"]),(CV["lean_tube_radius_um"],CV["lean_opening_deg"])]:
    B.G["opening_deg"]=opening
    th=math.radians(opening)/2
    coarse=crossed(ar,81,24,6);m=crossed(ar)
    mm=m.to_mesh();v=np.asarray(mm.vert_properties[:,:3],dtype=float);f=np.asarray(mm.tri_verts,dtype=int)
    valid=B.validate(v,f);B.write_stl(H/f"R2_crossed_wire{2*ar}um.stl",v,f)
    surface_clearance=q-2*ar/1000
    # Sufficient continuous centreline bound:
    # If a cross-plane distance < q, both residual transverse coordinates < q.
    # With 2q <= R sin(th), allowed C arcs then put both angles near the rear.
    # Their possible x-difference is <= R(1-cos(th)); x translation is >= xmin.
    assert 2*q<=R*math.sin(th)+1e-12
    assert xmin-R*(1-math.cos(th))>q
    critical_x=R*math.cos(th)+math.sqrt(R*R-q*q)
    assert xmin<=critical_x<=xmax
    samples=[]
    for dx in [xmin,.30,.38,critical_x,.48,xmax]:
        intersection=m ^ m.translate((dx,q,q))
        assert intersection.status()==md.Error.NoError
        vol=intersection.volume()
        assert vol<1e-12
        samples.append({"x_mm":dx,"intersection_mm3":vol})
    tube_r=ar/1000
    volume_upper=2*(math.pi*tube_r**2*R*(2*math.pi-2*th)+4*math.pi*tube_r**3/3)
    assert m.volume()<volume_upper
    mass=volume_upper*1e-9*I["ring"]["material_density_kg_m3"]
    rho=mass*I["ring"]["number_density_m3"]
    c=I["cost"];crf=c["discount"]*(1+c["discount"])**c["years"]/((1+c["discount"])**c["years"]-1)
    M=rho*c["area_m2"]*c["depth_m"];P=M*c["assumed_price_JPY_kg"]
    budget=(c["annual_budget_JPY"]-c["initial_other_JPY"]*crf-c["annual_other_JPY"])/(crf+c["replacement"])
    record={"wire_radius_um":ar,"wire_diameter_um":2*ar,"opening_deg":opening,"connected_components":1,
            "volume_mm3":m.volume(),"volume_upper_for_cost_mm3":volume_upper,"coarse_volume_mm3":coarse.volume(),
            "relative_mesh_volume_change":abs(m.volume()/coarse.volume()-1),
            "mesh":valid,"continuous_surface_clearance_um":surface_clearance*1000,
            "path":{"x_min_mm":xmin,"x_max_mm":xmax,"y_mm":q,"z_mm":q,"critical_x_mm":critical_x,
                    "mesh_intersection_checks":samples,"reverse_path_exists":True},
            "bulk_fixed_count_kg_m3":rho,"pilot_mass_kg":M,"assumed_purchase_JPY":P,
            "annual_equivalent_JPY":c["initial_other_JPY"]*crf+c["annual_other_JPY"]+(crf+c["replacement"])*P,
            "finished_price_ceiling_JPY_kg":budget/M,
            "scope":"One registered pairwise path of identical ideal rigid grains; no random capture, retention, wet friction or 50 C mechanics."}
    records.append(record);data.append((ar,opening,v,f))
# Numerical sampling supplements, and does not replace, the analytic bound.
for record in records:
    th=math.radians(record["opening_deg"])/2
    narc=401;p=np.linspace(th,2*math.pi-th,narc)
    arcxy=np.column_stack((R*np.cos(p),R*np.sin(p),np.zeros(narc)))
    arcxz=np.column_stack((R*np.cos(p),np.zeros(narc),R*np.sin(p)))
    centres=np.vstack((arcxy,arcxz));samples=[]
    for dx in [xmin,.30,.38,record["path"]["critical_x_mm"],.48,xmax]:
        shifted=centres+np.array([dx,q,q])
        val=float(np.sqrt(np.min(np.sum((centres[:,None,:]-shifted[None,:,:])**2,axis=2))))
        assert val>=q-1e-12
        samples.append({"x_mm":dx,"sampled_min_centreline_mm":val,"analytic_lower_bound_mm":q})
    record["centreline_samples"]=samples
    T=I["ring"]["crossed_variant"]["tolerance"]
    corners=[]
    for ra,rb,da,db,wa,wb,offset in itertools.product(T["radius_um"],T["radius_um"],T["opening_delta_deg"],T["opening_delta_deg"],T["wire_radius_delta_um"],T["wire_radius_delta_um"],T["path_offset_um"]):
        tha=math.radians(record["opening_deg"]+da)/2
        thb=math.radians(record["opening_deg"]+db)/2
        bound=min(offset,ra*math.sin(tha)-offset,rb*math.sin(thb)-offset)
        xcheck=I["ring"]["crossed_variant"]["registered_x_min_um"]-(rb-ra*math.cos(tha))
        assert xcheck>bound>0
        clearance=bound-(record["wire_radius_um"]+wa)-(record["wire_radius_um"]+wb)
        corners.append({"radius_a_um":ra,"radius_b_um":rb,"opening_a_deg":record["opening_deg"]+da,"opening_b_deg":record["opening_deg"]+db,
                        "wire_a_um":record["wire_radius_um"]+wa,"wire_b_um":record["wire_radius_um"]+wb,
                        "offset_um":offset,"continuous_clearance_bound_um":clearance})
    record["tolerance_corners"]=corners
    record["worst_corner_bound"]=min(corners,key=lambda x:x["continuous_clearance_bound_um"])
    worst=record["worst_corner_bound"]
    rbmax=max(T["radius_um"])+record["wire_radius_um"]+max(T["wire_radius_delta_um"])
    record["relative_rotation_conservative_sensitivity"]=[{"angle_deg":angle,"additional_point_displacement_bound_um":2*rbmax*math.sin(math.radians(angle)/2),"remaining_worst_clearance_um":worst["continuous_clearance_bound_um"]-2*rbmax*math.sin(math.radians(angle)/2)} for angle in [0,.5,1,2,5]]
    record["small_angle_clearance_certificate_limit_deg"]=2*math.degrees(math.asin(max(0,worst["continuous_clearance_bound_um"])/(2*rbmax)))
out={"models":records,"continuous_path_proof":{"q_mm":q,
     "same_plane_bound_mm":q,"nominal_cross_plane_bound_mm":q,
     "general_bound":"min(q, Ra*sin(theta_a/2)-q, Rb*sin(theta_b/2)-q) - a_a - a_b",
     "scope":"Registered path with matched orientation; tolerances allow independent radii, gaps and wire radii. Positive bound certifies clearance only. Reverse route exists."}}
(H/"crossed_results.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
fig=plt.figure(figsize=(12,5),layout="constrained")
for j,(ar,opening,v,f) in enumerate(data):
    ax=fig.add_subplot(1,2,j+1,projection="3d")
    ax.add_collection3d(Poly3DCollection(v[f],facecolors="#779db9",edgecolor="none",shade=True))
    ax.set(xlim=(-.31,.31),ylim=(-.31,.31),zlim=(-.31,.31),xlabel="x (mm)",ylabel="y (mm)",zlabel="z (mm)",
           title=f"R2: wire {2*ar} um / opening {opening} deg")
    ax.set_box_aspect((1,1,1));ax.view_init(26,35)
fig.suptitle("Two perpendicular open loops | one-piece geometric candidate",fontsize=15)
fig.savefig(H/"crossed_geometry.png",dpi=160);plt.close(fig)
print(json.dumps({"models":len(records),"path_clearance_um":[x["continuous_surface_clearance_um"] for x in records],
                  "bulk_kg_m3":[x["bulk_fixed_count_kg_m3"] for x in records],
                  "reverse_path_exists":True},indent=2))
