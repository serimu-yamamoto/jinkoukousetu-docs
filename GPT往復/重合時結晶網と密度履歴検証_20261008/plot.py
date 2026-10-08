"""Figures are accounting scenarios, not experimental plots."""
from pathlib import Path
import json,sys
P=Path(__file__).resolve().parent
deps=P.parents[1]/".deps"
if deps.exists():sys.path.insert(0,str(deps))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
R=json.loads((P/"results.json").read_text())
plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False,"savefig.dpi":160})
fig,ax=plt.subplots(1,2,figsize=(13,5.3),layout="constrained")
labels=["S2 research powder\nselected low / high","S4 GUR 2122\n2016 typical","S3 d-UHm\nresearch powder","S4 GUR 4120\n2016 typical","Comparison target\nNOT measured H29"]
values=[70,250,350,450,120]
colors=["#2a7f9e"]*4+["#e0a332"]
ax[0].barh(range(5),values,color=colors)
ax[0].errorbar(70,0,xerr=[[20],[20]],fmt="none",ecolor="#163c4d",capsize=5)
ax[0].set_yticks(range(5),labels)
ax[0].invert_yaxis()
ax[0].set(xlabel="Loose bulk density (kg/m³)",xlim=(0,540),title="A. Observed powders and the comparison target")
for j,v in enumerate(values):ax[0].text(v+8 if j!=0 else 100,j,str(v) if j!=0 else "50–90",va="center")
dens=[60,90,120,180,250,350,450,500]
m=[d*.45 for d in dens]
ax[1].plot(dens,m,"o-",color="#2a7f9e")
ax[1].axvline(120,color="#e0a332",linestyle="--")
ax[1].set(xlabel="Assumed FINISHED bed density (kg/m³)",ylabel="Dry material per area (kg/m²)",title="B. Same 450 mm finished depth")
ax[1].annotate("54 kg/m² at 120",xy=(120,54),xytext=(155,35),arrowprops={"arrowstyle":"->"})
ax[1].annotate("202.5 kg/m² at 450\n3.75 × material",xy=(450,202.5),xytext=(240,185),arrowprops={"arrowstyle":"->"})
fig.suptitle("Cycle 29 | Low-density powder is evidence; an enduring snow-like bed is not")
fig.savefig(P/"figure1_density_inventory.png");plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(13,5.3),layout="constrained")
for q in [.0001,.001,.01]:
    n=list(range(501))
    h=[450*((1-q)**v+(1-(1-q)**v)*120/450) for v in n]
    ax[0].plot(n,h,label=f"q = {100*q:g}% / whole-bed cycle")
ax[0].axhline(450,color="gray",linewidth=.8)
ax[0].set(xlabel="Cycles (scenario)",ylabel="Ideal reference depth (mm)",ylim=(100,480),
          title="A. Fixed mass; conversion from 120 to 450 kg/m³")
ax[0].legend(loc="lower left",fontsize=9)
ax[0].text(.03,.52,"Additive bulk volumes only;\nactual mixing / recovery not validated.",transform=ax[0].transAxes,fontsize=9,
 bbox={"facecolor":"white","edgecolor":"none","alpha":.8})
for depth in [.02,.1,.45]:
    x=[.01,.03,.1,.3,1]
    y=[20000*depth*120*(v/100)*200*500/1e6 for v in x]
    ax[1].plot(x,y,"o-",label=f"Processed depth {int(depth*1000)} mm")
ax[1].axhline(10,color="#d67d22",linestyle="--",label="Assumed ¥10m/year allowance")
ax[1].set(xscale="log",yscale="log",xlabel="Morphology rejection in processed mass (% / cycle)",
 ylabel="New material purchases (million JPY/year)",title="B. 20,000 m²; 200 cycles/year; ¥500/kg")
ax[1].legend(fontsize=9)
fig.suptitle("Cycle 29 | Unknown damage rate controls renewal cost — not a predicted service life")
fig.savefig(P/"figure2_structure_retention.png");plt.close(fig)
print("Saved 2 figures; matplotlib",matplotlib.__version__)
