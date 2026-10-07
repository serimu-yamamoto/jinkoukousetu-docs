"""Original figures from results.json. matplotlib required only for rendering."""
from pathlib import Path
import json, os, sys
H=Path(__file__).resolve().parent
root=H.parent.parent
if (root/".deps").exists(): sys.path.insert(0,str(root/".deps"))
os.environ.setdefault("MPLCONFIGDIR",str(root/".scratch"/"mpl"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
R=json.loads((H/"results.json").read_text(encoding="utf-8"))
plt.rcParams.update({"font.size":11,"axes.spines.top":False,"axes.spines.right":False,"figure.dpi":150})
blue="#17629b"; orange="#bb5225"; green="#23846b"; gray="#5b6874"

fig,axs=plt.subplots(2,2,figsize=(13,9),layout="constrained")
ax=axs[0,0]
for w in [100,20]:
 p=next(x for x in R["width_cases"] if x["width_um"]==w)["path"]
 ax.plot([x["u_um"] for x in p],[x["external_push_uN"] for x in p],label=f"Gate width {w} um",lw=2)
ax.axhline(0,color=gray,ls="--",lw=1);ax.set(xlabel="Registered insertion displacement (um)",ylabel="Required external push (uN)",title="A  The entire path matters")
ax.legend();ax.text(.03,.05,"r = 35 um; cover = 5 um; effective polarization = 0.25 T\nSliding-limit clip path; no capture or stability proof",transform=ax.transAxes,fontsize=9)
ax=axs[0,1]
for w in [100,60,30,20,15]:
 vals=sorted([x for x in R["parameter_grid"] if x["width_um"]==w and x["cover_um"]==5 and x["effective_polarization_T"]==.25],key=lambda x:x["radius_um"])
 ax.plot([v["radius_um"] for v in vals],[v["sampled_path_B_critical_T"] for v in vals],marker="o",label=f"{w} um width")
ax.axhline(.25,color=gray,ls="--",lw=1,label="Assumed 0.25 T")
ax.set(xlabel="Core radius (um)",ylabel="Critical effective polarization (T)",title="B  Narrower gates reduce ideal insertion demand");ax.legend(fontsize=8,ncol=2)
ax=axs[1,0]; v=R["steel_plane_comparator"]
ax.semilogy([x["centre_height_um"] for x in v],[x["force_uN"] for x in v],marker="o",color=orange)
ax.axhline(R["nominal"]["final_magnetic_force_uN"],ls="--",color=blue,label="Seated core-to-core force")
ax.set(xlabel="Core centre to steel plane (um)",ylabel="Ideal magnetic attraction (uN)",title="C  Steel attraction remains a design constraint");ax.legend(fontsize=9)
ax.text(.04,.08,"Infinite linear high-permeability plane\nNot a finite sharp ski-edge calculation",transform=ax.transAxes,fontsize=9)
ax=axs[1,1]
for vv in [1e-6,.001,.1]:
 p=[x for x in R["capillary"] if x["temperature_C"]==50 and x["V_over_R3"]==vv]
 ax.loglog([x["radius_um"] for x in p],[x["force_uN"] for x in p],marker="o",label=f"V/R^3 = {vv:g}")
ax.set(xlabel="Equal touching sphere radius (um)",ylabel="Water-air bridge attraction (uN)",title="D  Liquid bridge comparator at 50 C")
ax.legend(fontsize=9)
ax.text(.30,.045,"Contact angle = 0 deg; not measured PE wetting\nNo saturated-bed or evaporation prediction",transform=ax.transAxes,fontsize=9)
fig.suptitle("Cycle 9 | Component calculations, not physical success tests",fontsize=16)
fig.savefig(H/"force_comparison.png");plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(12,5.6),layout="constrained")
for f in [1,.5,.1]:
 v=[x for x in R["cost"] if x["magnetic_fraction"]==f]
 axs[0].plot([x["magnet_price_assumption_JPY_kg"] for x in v],[x["annual_equivalent_JPY"]/1e6 for x in v],marker="o",label=f"Magnetic grain fraction {f:g}")
vv=R["lean_variant"]["cost"]
axs[0].plot([x["magnet_price_assumption_JPY_kg"] for x in vv],[x["annual_equivalent_JPY"]/1e6 for x in vv],ls="--",marker="s",label="M1-L: fraction 1, smaller core")
axs[0].axhline(19,color=orange,ls="--",label="Assumed annual ceiling")
axs[0].set(xlabel="Assumed core price (JPY/kg; NOT quotes)",ylabel="Annual equivalent cost (million JPY)",title="A  Material and process cost window")
axs[0].legend(fontsize=9)
cs=R["cost"][0]
axs[1].bar(["Base W2","M1: one core\nand gate/grain"],[cs["base_mass_kg"]/900,cs["bulk_density_kg_m3"]],color=[gray,blue])
axs[1].axhline(158.0185842615,color=orange,ls="--",label="Prior budget-derived density cap")
axs[1].set(ylabel="Assumed bed bulk density (kg/m3)",title="B  Core volume replaces matrix optimistically",ylim=(0,180));axs[1].legend(fontsize=9)
axs[1].text(.04,.07,"No added boss / coating volume\nNo integrated geometry\nNo wear, safety or skiing validation",transform=axs[1].transAxes,fontsize=10,bbox={"facecolor":"white","alpha":.92,"edgecolor":"none","pad":5})
fig.suptitle("2,000 m2, 0.45 m depth | pretax, hypothetical purchase prices",fontsize=15)
fig.savefig(H/"cost_comparison.png");plt.close(fig)

fig,ax=plt.subplots(figsize=(13,6.4),layout="constrained");ax.set_xlim(0,13);ax.set_ylim(0,6);ax.axis("off")
def box(x,y,w,h,title,body,color):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=.08,rounding_size=.12",facecolor=color,edgecolor="#bcc5cd"))
 ax.text(x+.15,y+h-.28,title,fontsize=13,weight="bold",va="top",color="#183147")
 ax.text(x+.15,y+h-.8,body,fontsize=11,va="top",linespacing=1.6,color="#183147")
box(.15,3.2,3.85,2,"1   Loosen / redistribute","Reduce contact loads\nPreserve drainage pathways\nControl material transport","#edf3f7")
box(4.55,3.2,3.85,2,"2   Align / close the gate","M0: controlled mechanical motion\nM1: optional buried dipole assist\nMagnet assists, seat retains","#e5f2ed")
box(8.95,3.2,3.85,2,"3   Compact / finish","Mechanical load-bearing seat\nRounded outer supports\nMeasured edge release required","#edf3f7")
for x in [4.1,8.5]: ax.annotate("",xy=(x+.32,4.2),xytext=(x-.03,4.2),arrowprops={"arrowstyle":"->","lw":2,"color":blue})
box(.15,.35,6.1,2,"Component allocation, not a manufactured grain","Nominal M1: r = 35 um core; inner cover = 5 um\nGate: width 20 um, thickness 5 um, assumed E = 300 MPa\nSeat / core / sleeve / release path need integrated 3D design","#fff1e6")
box(6.65,.35,6.15,2,"Acceptance gates before adopting M1","Keep cores away from steel and prevent release\nVerify dry / wet / 50 C force and long-term wear\nAdded processing must fit the stated cost window","#fff1e6")
ax.text(.1,5.72,"Cycle 9 | Proposed sequence for a reversible granular surface",fontsize=17,weight="bold",color="#183147")
ax.text(.1,2.67,"No refrigeration or water-dependent primary bond. Whole-depth restoration within 60 min remains unverified.",fontsize=11,color=gray)
fig.savefig(H/"functional_sequence.png");plt.close(fig)
print("Rendered 3 original figures with matplotlib "+matplotlib.__version__)
