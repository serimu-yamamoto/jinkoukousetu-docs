from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent
extra=P.parents[1]/".research86"/"deps"
if extra.exists():sys.path.insert(0,str(extra))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon,Circle,Rectangle
def load(n):return json.loads((P/n).read_text(encoding="utf8"))
g=load("geometries.json");m=load("mechanical_screen.json");w=load("wet_screen.json");p=load("production_comparison.json")
plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
fig,ax=plt.subplots(1,2,figsize=(12,6),layout="constrained")
for mode,label in [("planar_only","In-plane enlargement; thickness fixed"),("uniform_3d","All dimensions enlarged")]:
 r=[x for x in m if x["geometry"].startswith(mode) and x["solid_modulus_MPa_assumed"]==500 and x["pressure_Pa_assumed"]==2000 and x["active_support_fraction_assumed"]==1]
 ax[0].plot([1,2,3,4],[x["deflection_over_free_length"]*100 for x in r],"o-",label=label)
ax[0].set(xlabel="Scale factor s",ylabel="Tip deflection / free arm length (%)",xticks=[1,2,3,4],title="Branch compliance is not bed softness")
ax[0].legend(fontsize=8,loc="upper left");ax[0].grid(alpha=.2)
for gap in [20,50,100]:
 r=[x for x in w if x["geometry"].startswith("planar_only") and x["solid_modulus_MPa_assumed"]==500 and x["gap_um_assumed"]==gap and x["contact_angle_deg_assumed"]==0]
 ax[1].plot([1,2,3,4],[x["lambda_total"] for x in r],"o-",label=f"Assumed gap {gap} um")
ax[1].axhline(.25,color="black",ls="--",label="Uniform-gap model limit")
ax[1].set(xlabel="In-plane scale factor s",ylabel="Capillary closure parameter Lambda",xticks=[1,2,3,4],title="More compliant arms also close more easily",yscale="log")
ax[1].legend(fontsize=8,loc="upper left");ax[1].grid(alpha=.2)
fig.suptitle("Same candidate geometry, different load cases - analytical diagnostics only",fontsize=13)
fig.get_layout_engine().set(rect=(0,.10,1,.90))
fig.text(.5,.045,"Assumed Es = 500 MPa, Ec / Es = 0.36. Dry load: 2 kPa per nominal support cell.",ha="center",fontsize=10)
fig.text(.5,.015,"s=1,2 need 3D checks. Wet: fixed bases and full-face wetting. No free-particle or skiing prediction.",ha="center",fontsize=10)
fig.savefig(P/"compliance_wet_tradeoff.png",dpi=180);plt.close(fig)

fig,ax=plt.subplots(2,1,figsize=(11,8),layout="constrained")
def cross(x,L,b):
 c=b/2;h=L/2
 return np.array([[-c,-h],[c,-h],[c,-c],[h,-c],[h,c],[c,c],[c,h],[-c,h],[-c,c],[-h,c],[-h,-c],[-c,-c]])+[x,0]
centres=[0,2,4.7,8]
for s,x in zip([1,2,3,4],centres):
 gg=next(v for v in g if v["id"]==f"planar_only_s{s}")
 ax[0].add_patch(Polygon(cross(x,gg["span_mm"],gg["arm_width_mm"]),facecolor=plt.cm.Blues(.3+.15*s),edgecolor="#34495e"))
 ax[0].add_patch(Circle((x,0),gg["hole_mm"]/2,color="white"))
 ax[0].text(x,-1.75,f"s={s}\nspan {gg['span_mm']:.2f} mm",ha="center",va="top")
ax[0].set(xlim=(-.6,9.6),ylim=(-2.45,1.65),aspect="equal",xlabel="mm",title="Same final thickness: 0.180 mm; sharp outline still unmanufactured")
ax[0].set_yticks([])
ss=np.array([1,2,3,4])
ax[1].plot(ss,1/ss**2,"o-",label="Number of particles for fixed mass")
ax[1].plot(ss,1/ss,"s-",label="Total individual contour length")
ax[1].plot(ss,np.ones(4),"^-",label="Sheet area and selected powder + heat subtotal")
ax[1].set(xticks=ss,xlabel="In-plane scale factor s",ylabel="Ratio to the original geometry",ylim=(0,1.15),title="Manufacturing benefit does not equal a quoted cost saving")
ax[1].legend(fontsize=9);ax[1].grid(alpha=.2)
fig.suptitle("H86 dimensional comparison: candidate shapes, not manufactured snow",fontsize=13)
fig.savefig(P/"geometry_production.png",dpi=180);plt.close(fig)
(P/"plot_metadata.json").write_text(json.dumps({"figures":["compliance_wet_tradeoff.png","geometry_production.png"],"matplotlib":matplotlib.__version__,"physical_experiments":0,"manufacturing_demonstrated":False,"source":"own analytic calculations and geometry"},indent=2)+"\n",encoding="utf8",newline="\n")
print("2 original figures generated.")
