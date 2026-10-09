"""Two original analytic figures. Requires matplotlib; --deps PATH optional."""
from pathlib import Path
import json,sys
if "--deps" in sys.argv:sys.path.insert(0,sys.argv[sys.argv.index("--deps")+1])
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
P=Path(__file__).resolve().parent;R=json.loads((P/"results.json").read_text(encoding="utf-8"))
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False,"figure.facecolor":"#f8fafc","axes.facecolor":"white","savefig.facecolor":"#f8fafc"})
s=next(x for x in R["hybrid_rows"] if x["id"]=="S15_E1000")
fig,ax=plt.subplots(1,2,figsize=(12,5.4),layout="constrained")
fig.suptitle("PMP support core + PE contact faces: a conditional structure\nIllustration and calculations only; no bonded sample has been made",fontsize=14)
a=ax[0];tc=s["core_um"];tt=s["total_um"];ts=15
for y,h,c,label in [(0,ts,"#93c5fd","PE face 15 um"),(ts,tc,"#fbbf24","PMP core 100.48 um"),(ts+tc,ts,"#93c5fd","PE face 15 um")]:
 a.add_patch(Rectangle((0,y),4,h,facecolor=c,edgecolor="#334155",linewidth=1))
 a.text(2,y+h/2,label,ha="center",va="center",fontsize=10)
a.annotate("Bare core at cut edge",xy=(4,ts+tc/2),xytext=(4.4,ts+tc/2+28),arrowprops={"arrowstyle":"->","color":"#b91c1c"},color="#b91c1c",fontsize=9)
a.annotate("",xy=(-.3,0),xytext=(-.3,tt),arrowprops={"arrowstyle":"<->"})
a.text(-.6,tt/2,"Total 130.48 um",rotation=90,ha="center",va="center")
a.text(0,-22,"Same areal mass: 111.6 g/m2\nInterface and side coverage are unproven",fontsize=10)
a.set_xlim(-1,6.5);a.set_ylim(-40,155);a.axis("off")
vals=[1,s["D_ratio_to_porous_reference"],s["D_ratio_to_porous_reference"]*s["independent_layer_D_ratio_to_bonded"]]
ax[1].bar([0,1,2],vals,color=["#64748b","#0369a1","#c2410c"],width=.58)
for j,v in enumerate(vals):ax[1].text(j,v+.04,f"{v:.3f}",ha="center")
ax[1].set_ylim(0,1.35);ax[1].set_ylabel("Bending rigidity / porous reference")
ax[1].set_xticks([0,1,2],["Porous\nreference","Hybrid\nfully bonded","Hybrid\nindependent layers"])
ax[1].text(.03,.96,"Assumed: PE E = 500 MPa, PMP E = 1000 MPa\nIndependent-layer case is an ideal comparison,\nnot a measured or guaranteed delamination bound.",transform=ax[1].transAxes,va="top",fontsize=9)
fig.savefig(P/"core_skin_sections.png",dpi=180);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,5.3),layout="constrained")
fig.suptitle("Thicker contact faces demand a stiffer core at equal mass\nNo measured 50 C modulus or manufacturing quotation",fontsize=14)
x=[q["skin_each_um"] for q in R["frontiers"]];y=[q["core_modulus_MPa_required_to_match_D0"] for q in R["frontiers"]]
ax[0].plot(x,y,"o-",color="#0369a1",linewidth=2)
for a,b in zip(x,y):ax[0].annotate(f"{b:.0f} MPa",(a,b),xytext=(0,10),textcoords="offset points",ha="center")
ax[0].set_xlim(0,35);ax[0].set_ylim(0,3750);ax[0].set_xlabel("PE thickness on EACH face (um)")
ax[0].set_ylabel("Required PMP core modulus (MPa)")
ax[0].set_title("Match the assumed porous-reference rigidity")
ax[0].grid(alpha=.18)
for q,c in [(0,"#64748b"),(100,"#0369a1"),(300,"#c2410c")]:
 pts=[v for v in R["cost_rows"] if v["skin_each_um"]==15 and v["additional_conversion_yen_gross_kg_assumed"]==q]
 ax[1].plot([v["core_raw_price_yen_kg_assumed"] for v in pts],[v["incremental_total_yen_ex_tax"]/1e6 for v in pts],"o-",label=f"Extra conversion {q} JPY/gross kg",color=c)
ax[1].set_xlabel("Assumed PMP raw-material price (JPY/kg)")
ax[1].set_ylabel("Added cost vs equal-mass PE inventory (million JPY)")
ax[1].set_title("135 t; PE faces 15 um; PE raw price 500 JPY/kg")
ax[1].legend(fontsize=8,loc="upper left");ax[1].grid(alpha=.18)
ax[1].text(.98,.02,"Ex tax; same yield assumed\nNo film quote or total project cost",transform=ax[1].transAxes,ha="right",fontsize=9)
fig.savefig(P/"stiffness_cost_frontiers.png",dpi=180);plt.close(fig)
(P/"plot_metadata.json").write_text(json.dumps({"original_figures":["core_skin_sections.png","stiffness_cost_frontiers.png"],"data_source":"results.json","physical_test_data":False,"visual_review_required":True},indent=2)+"\n",encoding="utf-8",newline="\n")
print("2 original figures generated")
