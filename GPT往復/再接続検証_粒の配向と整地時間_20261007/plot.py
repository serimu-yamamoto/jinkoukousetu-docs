"""Original figures from cycle-10 JSON and binary STL."""
from pathlib import Path
import json, math, sys, os, struct
H=Path(__file__).resolve().parent;root=H.parent.parent
if (root/".deps").exists():sys.path.insert(0,str(root/".deps"))
os.environ.setdefault("MPLCONFIGDIR",str(root/".scratch"/"mpl"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
R=json.loads((H/"results.json").read_text(encoding="utf-8"))
X=json.loads((H/"crossed_results.json").read_text(encoding="utf-8"))
plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
blue="#21669a";orange="#b65329";green="#298070"
fig,ax=plt.subplots(2,2,figsize=(12,9),layout="constrained")
o=R["orientation"]
ax[0,0].plot([x["cap_deg"] for x in o],[x["relative_link_volume"] for x in o],marker="o",color=blue)
ax[0,0].set(xlabel="Maximum normal tilt in a uniformly populated cap (deg)",ylabel="Ideal link volume / isotropic value",title="A  Parallel planar rings lose geometric links",ylim=(-.03,1.1))
ax[0,0].text(.04,.85,"Closed, infinitely thin rings only\nNot real capture or holding strength",transform=ax[0,0].transAxes,fontsize=9)
v=o[1:]
ax[0,1].semilogy([x["cap_deg"] for x in v],[x["R0_density_to_recover_isotropic_mean_kg_m3"] for x in v],marker="o",color=orange)
ax[0,1].axhline(158.0186,color=green,ls="--",label="Prior budget-derived density cap")
ax[0,1].set(xlabel="Maximum normal tilt (deg)",ylabel="Formal density to restore mean links (kg/m3)",title="B  Densification alone can exhaust the budget")
ax[0,1].legend(fontsize=9)
times=R["vibration"]["time_comparisons"]
ax[1,0].bar(["8 s reference","60 s reference","120 s reference"],[x["gravity_similarity_only_s"] for x in times],color=blue)
ax[1,0].axhline(.4/.6,color=orange,ls="--",label="0.4 m / 0.6 m/s exposure")
ax[1,0].set(ylabel="Gravity-only scaled time (s)",title="C  Scaling does not prove processing time")
ax[1,0].legend(fontsize=9)
for dwell in [2,15,30]:
 v=[x for x in R["selective_reconditioning"] if x["depth_m"]==.3 and x["conditioning_time_assumed_s"]==dwell]
 ax[1,1].loglog([x["damaged_area_fraction_assumed"]*100 for x in v],[x["three_cells_m3"] for x in v],marker="o",label=f"Assumed conditioning {dwell} s")
ax[1,1].set(xlabel="Assumed damaged area (%)",ylabel="Three-cell capacity (m3)",title="D  Selective repair: 300 mm depth retained")
ax[1,1].legend(fontsize=9)
fig.suptitle("Cycle 10 | Geometric and process comparisons, not physical trials",fontsize=15)
fig.savefig(H/"orientation_and_process.png",dpi=160);plt.close(fig)

def triangles(path):
 b=path.read_bytes();n=struct.unpack_from("<I",b,80)[0]
 dt=np.dtype([("normal","<f4",(3,)),("v","<f4",(3,3)),("attr","<u2")])
 assert len(b)==84+50*n
 return np.frombuffer(b,dtype=dt,offset=84,count=n)["v"].astype(float)

tri=triangles(H/"R2_crossed_wire44um.stl")
fig=plt.figure(figsize=(14,5.3),layout="constrained")
for j,dx in enumerate([.58,.44,.24]):
 ax=fig.add_subplot(1,3,j+1,projection="3d")
 for t,col in [(tri,blue),(tri+np.array([dx,.06,.06]),orange)]:
  ax.add_collection3d(Poly3DCollection(t,facecolors=col,edgecolor="none",shade=True,alpha=.85))
 ax.set(xlim=(-.3,.85),ylim=(-.32,.38),zlim=(-.32,.38),xlabel="x (mm)",ylabel="y (mm)",zlabel="z (mm)",
        title=f"Relative centre: ({dx:.2f}, 0.06, 0.06) mm")
 ax.set_box_aspect((1.15,.7,.7));ax.view_init(26,-60)
fig.suptitle("R2-L registered translation | reverse path also exists; no self-locking claim",fontsize=15)
fig.savefig(H/"registered_path.png",dpi=150);plt.close(fig)

fig,ax=plt.subplots(figsize=(12,6.2),layout="constrained")
ax.set_xlim(0,12);ax.set_ylim(0,6);ax.axis("off")
def box(x,y,w,h,title,body,color):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=.05",facecolor=color,edgecolor="#bdc6cd"))
 ax.text(x+.15,y+h-.23,title,fontsize=12,weight="bold",va="top",color="#17344b")
 ax.text(x+.15,y+h-.73,body,fontsize=10,va="top",linespacing=1.6,color="#17344b")
ax.text(.05,5.65,"P1: selective collection + staged reconditioning + controlled finishing",fontsize=15,weight="bold")
box(.1,3.45,3.5,1.75,"Collect damaged material","Preserve the 300 mm repair requirement\nMeasure the damaged fraction\nSmooth remaining areas separately","#eaf1f7")
box(4.05,3.45,3.7,1.75,"Recondition in separate cells","Fill / closed conditioning / discharge\nEach parcel gets a full closed interval\nThree alternating cells; no dead time assumed","#e4f2ec")
box(8.2,3.45,3.6,1.75,"Return and finish","Meter to the required elevation\nControl orientation and compaction\nCheck edge release and drainage","#eaf1f7")
for x in [3.65,7.8]:ax.annotate("",xy=(x+.32,4.3),xytext=(x,4.3),arrowprops={"arrowstyle":"->","lw":2,"color":blue})
box(.1,.35,5.65,2.3,"Sizing example, NOT a selected machine","1,000 x 20 m; damaged area 10%; depth 0.30 m\n38 min processing window -> average 0.263 m3/s\nAssumed 15 s conditioning -> 3 x 3.95 m3 cells\nStartup, peak collection and valve downtime need margins","#fff1e7")
box(6.15,.35,5.65,2.3,"What this changes","A material residence time can exceed local pass time.\nUniform full-depth damage requires much larger capacity.\nNo quoted equipment cost or verified recovery time.\nGravity-only vibration scaling cannot set the dwell time.","#fff1e7")
fig.savefig(H/"selective_reconditioning.png",dpi=160);plt.close(fig)
print("Rendered 3 comparison/process figures")
