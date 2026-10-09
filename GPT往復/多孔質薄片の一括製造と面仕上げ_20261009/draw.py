from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent
extra=P.parents[1]/".research85"/"deps"
if extra.exists():sys.path.insert(0,str(extra))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Circle,Rectangle
import numpy as np
plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
def cross(x,y,L,w):
    b=L/2;c=w/2
    return np.array([[-c,-b],[c,-b],[c,-c],[b,-c],[b,c],[c,c],[c,b],[-c,b],[-c,c],[-b,c],[-b,-c],[-c,-c]])+[x,y]
fig,axs=plt.subplots(2,2,figsize=(12,9),layout="constrained")
ax=axs[0,0]
for i in range(2):
 for j in range(2):
    ax.add_patch(Polygon(cross(i*1.1,j*1.1,1,.25),facecolor="#4c91b8",edgecolor="black",lw=.5))
    ax.add_patch(Circle((i*1.1,j*1.1),.05,color="white"))
ax.set(xlim=(-.6,1.7),ylim=(-.6,1.7),aspect="equal",xlabel="mm",ylabel="mm",title="Isolated crosses: 35.5% sheet retained")
ax=axs[0,1]
for i in range(-9,10):
 for j in range(-9,10):
    if (i+2*j)%5==0:
      ax.add_patch(Polygon(cross(i*.25,j*.25,.74,.24),facecolor=plt.cm.Set3((i+3*j)%12/11),edgecolor="#34495e",lw=.5))
      ax.add_patch(Circle((i*.25,j*.25),.05,color="white"))
ax.set(xlim=(-.95,.95),ylim=(-.95,.95),aspect="equal",xlabel="mm",ylabel="mm",title="Nested crosses: 92.7% sheet retained")
ax.text(.02,.02,"10 um nominal gap; sharp corners\nNot a demonstrated cutting process",transform=ax.transAxes,fontsize=9,bbox={"facecolor":"white","alpha":.9,"edgecolor":"none"})
ax=axs[1,0]
ax.add_patch(Rectangle((0,0),1,.2,facecolor="#afc9d3",hatch="...",edgecolor="#345"))
ax.add_patch(Rectangle((1.5,.01),1,.18,facecolor="#afc9d3",hatch="...",edgecolor="#345"))
ax.add_patch(Rectangle((1.5,.01),1,.015,facecolor="#31738f"))
ax.add_patch(Rectangle((1.5,.175),1,.015,facecolor="#31738f"))
ax.annotate("",xy=(1.45,.1),xytext=(1.05,.1),arrowprops={"arrowstyle":"->"})
ax.text(.5,.24,"Before: 0.200 mm\n40% void",ha="center")
ax.text(2,.24,"After: 0.180 mm\n15 um dense face / side",ha="center")
ax.text(1.25,-.055,"Void collapse conserves polymer mass.\nSmoothness and bending benefit are unproven.",ha="center")
ax.set(xlim=(-.1,2.6),ylim=(-.12,.36),title="Idealized local densification (section)")
ax.axis("off")
ax=axs[1,1];ax.axis("off")
steps=["1  Porous UHMWPE precursor sheet","2  Conditional face densification","3  Parallel shaping + through-holes","4  Edge finishing, cleaning, grading","5  Dry / drained-wet 50 C tests"]
for k,txt in enumerate(steps):
    y=.93-k*.17
    ax.text(.06,y,txt,transform=ax.transAxes,va="center",bbox={"boxstyle":"round,pad=.4","facecolor":"#edf2f4","edgecolor":"#74909b"})
    if k<4:ax.annotate("",xy=(.12,y-.115),xytext=(.12,y-.045),xycoords="axes fraction",arrowprops={"arrowstyle":"->"})
ax.set_title("H85 factory concept - not manufactured")
fig.suptitle("Manufacturing geometry, not proof of snow-like ski performance",fontsize=14)
fig.savefig(P/"manufacturing_concept.png",dpi=180);plt.close(fig)

nested=json.loads((P/"nested_geometry.json").read_text(encoding="utf8"))
cost=json.loads((P/"material_heat_costs.json").read_text(encoding="utf8"))
routes=json.loads((P/"route_comparison.json").read_text(encoding="utf8"))
fig,ax=plt.subplots(1,2,figsize=(12,6),layout="constrained")
ax[0].plot([v["nominal_gap_between_outer_edges_mm"]*1000 for v in nested],[v["geometric_retention"]*100 for v in nested],"o-",color="#206e8c")
ax[0].axhline(35.5079354,color="#b65f49",ls="--",label="Isolated layout reference")
ax[0].scatter([10],[92.7187259],s=90,facecolors="none",edgecolors="black",label="Representative assumption")
ax[0].set(xlabel="Nominal gap between outer edges (um)",ylabel="Geometric sheet retention (%)",ylim=(0,103),title="Wider gaps consume the yield benefit")
ax[0].legend(loc="lower left",fontsize=9);ax[0].grid(alpha=.2)
base=[next(v for v in cost if v["area_m2"]==2000 and v["assumed_recovery_fraction_of_all_reject_mass"]==r and v["assumed_thermal_efficiency"]==.4)["selected_material_plus_heat_yen_ex_tax"]/1e6 for r in [0,.9]]
new=[next(v for v in routes if v["area_m2"]==2000 and v["recovery_fraction"]==r)["selected_material_plus_heat_yen_ex_tax"]/1e6 for r in [0,.9]]
x=np.arange(2);ax[1].bar(x-.18,base,.36,label="Isolated");ax[1].bar(x+.18,new,.36,label="Nested (10 um gap)")
for xx,ys in [(x-.18,base),(x+.18,new)]:
 for a,b in zip(xx,ys):ax[1].text(a,b+3,f"{b:.1f}",ha="center",fontsize=10)
ax[1].set(xticks=x,xticklabels=["No scrap recovery","90% assumed recovery"],ylabel="Million JPY, excluding tax",title="Powder + selected process heat ONLY",ylim=(0,250))
ax[1].legend(fontsize=9)
fig.suptitle("2,000 m2 x 0.45 m x assumed 150 kg/m3 = 135 t",fontsize=14)
fig.get_layout_engine().set(rect=(0,.07,1,.93))
fig.text(.5,.02,"No vendor quote. Excludes cutting, tools, edge finishing, labour, factory and ski-area equipment.",ha="center",fontsize=10)
fig.savefig(P/"yield_cost_tradeoff.png",dpi=180);plt.close(fig)
(P/"plot_metadata.json").write_text(json.dumps({"figures":["manufacturing_concept.png","yield_cost_tradeoff.png"],"physical_experiments":0,"source":"own geometry and calculations; no copied third-party images","matplotlib":matplotlib.__version__,"manufacturing_demonstrated":False},indent=2)+"\n",encoding="utf8",newline="\n")
print("2 original figures generated; no physical result.")
