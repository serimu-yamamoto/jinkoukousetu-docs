"""Original diagrams; all values are assumptions/analytical outputs, not test data.
Requires matplotlib. Optional --deps path adds a temporary dependency directory.
"""
from pathlib import Path
import json,sys
if "--deps" in sys.argv:sys.path.insert(0,sys.argv[sys.argv.index("--deps")+1])
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Polygon
P=Path(__file__).resolve().parent
R=json.loads((P/"results.json").read_text(encoding="utf-8"))
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False,"figure.facecolor":"#f8fafc","axes.facecolor":"#ffffff","savefig.facecolor":"#f8fafc"})
rows=R["comparison_rows"]
ref=rows[0]
def get(mode):return next(x for x in rows if x["mode"]==mode and x["modulus_ratio_assumed"]==1 and x["density_kg_m3"]==930)
sel=[ref,get("equal_mass"),get("equal_bending")]
colors=["#64748b","#c2410c","#0369a1"]
fig,ax=plt.subplots(1,2,figsize=(12,5.5),layout="constrained")
fig.suptitle("A thinner solid branch trades mass against wet closure\nAnalytical comparison; 50 C moduli are assumed, not measured",fontsize=14)
xx=[0,1,2]
for i,x in enumerate(sel):
 ax[0].bar(i-.18,x["mass_ratio"],width=.34,color=colors[i],alpha=.5)
 ax[0].bar(i+.18,x["tip_compliance_ratio"],width=.34,color=colors[i])
 ax[0].text(i-.18,x["mass_ratio"]+.05,f'{x["mass_ratio"]:.3f}',ha="center",fontsize=9)
 ax[0].text(i+.18,x["tip_compliance_ratio"]+.05,f'{x["tip_compliance_ratio"]:.3f}',ha="center",fontsize=9)
ax[0].set_xticks(xx,["Porous\n180 um","Solid, equal mass\n120 um","Solid, equal bending\n154.3 um"])
ax[0].set_ylim(0,2.55);ax[0].set_ylabel("Ratio to porous reference")
ax[0].set_title("Common density and modulus (r = 1)")
ax[0].text(.03,.96,"Pale: mass | Dark: tip compliance\nSame outline and particle inventory",transform=ax[0].transAxes,va="top",fontsize=9)
for gap,ls in [(20,"-"),(50,"--")]:
 pts=[x for x in rows if x["mode"]=="equal_mass" and x["density_kg_m3"]==930]
 ax[1].plot([x["modulus_ratio_assumed"] for x in pts],[next(w["lambda"] for w in x["wet"]["rows"] if abs(w["gap_um_assumed"]-gap)<1e-6) for x in pts],ls,marker="o",label=f"Solid 120 um, gap {gap} um",color="#c2410c" if gap==20 else "#0369a1")
ax[1].axhline(.25,color="#b91c1c",linestyle=":",label="No small equilibrium above 0.25")
ax[1].axhline(.09,color="#475569",linestyle="-.",label="10% closure diagnostic: 0.09")
ax[1].set_yscale("log");ax[1].set_ylim(.012,2.8);ax[1].set_xlabel("Assumed E_solid / E_porous-skin")
ax[1].set_ylabel("Capillary closure parameter, Lambda")
ax[1].set_title("Fixed roots; full-face water bridge")
ax[1].legend(fontsize=8,loc="upper right")
ax[1].grid(axis="y",alpha=.16)
fig.savefig(P/"mass_stiffness_wet.png",dpi=180);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,5.6),layout="constrained")
fig.suptitle("Candidate manufacturing routes and a price boundary\nNo production capability or price quotation has been established",fontsize=14)
a=ax[0]
# Top view: open branch is a proposed cut shape, not grown ice.
pts=[(-1.11,-.36),(-.36,-.36),(-.36,-1.11),(.36,-1.11),(.36,-.36),(1.11,-.36),(1.11,.36),(.36,.36),(.36,1.11),(-.36,1.11),(-.36,.36),(-1.11,.36)]
a.add_patch(Polygon(pts,closed=True,facecolor="#bfdbfe",edgecolor="#0369a1",linewidth=2))
a.add_patch(plt.Circle((0,0),.15,facecolor="white",edgecolor="#0369a1"))
a.annotate("",xy=(-1.11,1.4),xytext=(1.11,1.4),arrowprops={"arrowstyle":"<->","color":"#475569"})
a.text(0,1.47,"2.22 mm outline; hole 0.30 mm",ha="center",fontsize=9)
a.text(0,-1.45,"Cut/formed particle, not a mat or grown crystal",ha="center",fontsize=9)
a.text(-1.68,-2.0,"P: fine powder > sinter > densify faces",fontsize=9,color="#475569")
a.text(-1.68,-2.32,"D: pellets > thin sheet > branch forming",fontsize=9,color="#0369a1")
a.text(-1.68,-2.64,"Both: cut, deburr, inspect, collect fines",fontsize=9)
a.set_xlim(-1.8,1.8);a.set_ylim(-2.9,1.8);a.set_aspect("equal");a.axis("off")
prices=[400,500,600,700,800,900,1000,1100,1200]
for mode,c,label in [("equal_mass","#c2410c","Equal mass (120 um)"),("equal_bending","#0369a1","Equal bending (154.3 um)")]:
 x=get(mode);p=x["production"];p0=ref["production"]
 base=p0["virgin_kg_assuming_reject_recovery"]*500+p0["gross_processed_kg"]*300
 qs=[(base-p["virgin_kg_assuming_reject_recovery"]*v)/p["gross_processed_kg"] for v in prices]
 ax[1].plot(prices,qs,color=c,label=label,linewidth=2)
ax[1].axhline(0,color="#64748b",linewidth=1)
ax[1].axhline(100,color="#64748b",linestyle=":",label="Assumed solid conversion: 100")
ax[1].set_xlabel("Assumed solid-resin price (JPY/kg, ex tax)")
ax[1].set_ylabel("Maximum solid conversion cost (JPY/gross kg)")
ax[1].set_title("Reference powder: 500 + conversion: 300")
ax[1].legend(fontsize=9);ax[1].grid(alpha=.15)
ax[1].text(.02,.03,"Negative: even zero conversion cost cannot match\nSame inventory; r = 1, density = 930 kg/m3",transform=ax[1].transAxes,fontsize=8)
fig.savefig(P/"manufacture_cost_boundary.png",dpi=180);plt.close(fig)
(P/"plot_metadata.json").write_text(json.dumps({"original_figures":["mass_stiffness_wet.png","manufacture_cost_boundary.png"],"source":"results.json; proposed outline dimensions in inputs.json","physical_test_data":False,"visual_review_required":True},indent=2)+"\n",encoding="utf-8",newline="\n")
print("2 original figures generated")
