from pathlib import Path
import json, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter
from model import case
HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"results.json").read_text(encoding="utf-8"))
plt.rcParams.update({"font.size":11,"axes.spines.top":False,"axes.spines.right":False})
fig,ax=plt.subplots(2,2,figsize=(13,9),layout="constrained")
colors=["#a44a58","#237f89","#7863a3","#bd861c"]
kinds=["cantilever_tip","pin_pin_mid","spring_spring_mid","fixed_fixed_mid"]
labels=["Free end","Two pin supports","Rotational springs","Two fixed supports"]
lengths=[10*(20**(i/180)) for i in range(181)]
for kind,color,label in zip(kinds,colors,labels):
    rows=[case(2,L,300,1,kind) for L in lengths]
    ax[0,0].loglog(lengths,[r["relative_gap_closure_index"] for r in rows],"--",color=color,alpha=.5)
    good=[r["relative_gap_closure_index"] if r["linear_diagnostic_scope"] and r["before_pair_contact"] else float("nan") for r in rows]
    ax[0,0].loglog(lengths,good,color=color,lw=2,label=label)
ax[0,0].axhline(1,color="black",lw=1)
ax[0,0].set(title="Same branch, different internal supports",xlabel="Span / free length (micrometres)",ylabel="Linear gap-closure index",ylim=(.001,1200))
ax[0,0].set_xticks([10,20,50,100,200],labels=["10","20","50","100","200"])
ax[0,0].xaxis.set_minor_formatter(NullFormatter())
ax[0,0].legend(fontsize=9,loc="upper left")
ax[0,0].grid(which="both",alpha=.15)
ax[0,0].text(.98,.03,"d = 2 um; E = 300 MPa assumed\n50 C water; F = pi gamma d; gap = 10 um\nDashed: outside stated diagnostic scope",transform=ax[0,0].transAxes,ha="right",fontsize=9)
ratios=[.1*(100**(i/100)) for i in range(101)]
ax[0,1].semilogx(ratios,[1+1/(2*x) for x in ratios],color=colors[1],lw=2)
ax[0,1].axvline(5,color=colors[3],ls="--")
ax[0,1].plot([5],[1.1],"o",color=colors[3])
ax[0,1].set(title="A supporting junction must resist motion",xlabel="Each support stiffness / beam stiffness",ylabel="Total deflection / rigid-support deflection",ylim=(1,6.4))
ax[0,1].text(.97,.89,"Two equal translating supports\nMidspan load; linear springs\nRatio 5 gives 10% added deflection",ha="right",va="top",transform=ax[0,1].transAxes,fontsize=10,bbox=dict(facecolor="white",edgecolor="none",alpha=.95))
ax[0,1].grid(alpha=.2)
water=R["water_inventory"][:5]
xs=range(len(water))
ax[1,0].bar(xs,[120]*len(water),color="#63717c",label="Dry grain mass")
ax[1,0].bar(xs,[x["total_bulk_density_kg_m3"]-120 for x in water],bottom=120,color="#85c5d0",label="Specified retained water")
ax[1,0].set_xticks(list(xs),labels=[f'{100*x["pore_saturation"]:g}%' for x in water])
ax[1,0].set(title="Small pore saturation can add substantial mass",xlabel="Specified pore-water saturation",ylabel="Bulk density (kg / cubic metre)",ylim=(0,370))
ax[1,0].legend(fontsize=9,loc="upper left")
ax[1,0].text(.03,.49,"All voids assumed accessible\nNo rain or drainage-time prediction",transform=ax[1,0].transAxes,fontsize=9)
cost=R["cost_sensitivity"]
cx=[100*x["added_mass_fraction"] for x in cost]
cy=[x["reform_fees"][1]["all_in_ceiling_JPY_kg"] for x in cost]
ax[1,1].plot(cx,cy,"o-",color=colors[2])
for x,y in zip(cx,cy):ax[1,1].annotate(f"{y:.2f}",(x,y),xytext=(0,7),textcoords="offset points",ha="center",fontsize=10)
ax[1,1].set(title="Added material consumes the same annual budget",xlabel="Added dry material mass (%)",ylabel="All-in reform fee ceiling (JPY / kg)",ylim=(5.8,12.4),xlim=(-.6,10.6))
ax[1,1].text(.97,.97,"1% reformed per closure; 240 closures/year\nInherited pretax assumptions; not a quote\nNo simultaneous allowance for price uplift",ha="right",va="top",transform=ax[1,1].transAxes,fontsize=9)
ax[1,1].grid(alpha=.2)
fig.suptitle("Cycle 18 | Internal support, wet-dry sensitivity and cost\nPhysical grain, ski response and 50 C durability remain unverified",fontsize=16)
fig.savefig(HERE/"overview.png",dpi=170)
