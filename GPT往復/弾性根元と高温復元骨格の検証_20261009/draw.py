from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parent;deps=P.parents[1]/".research94"/"deps"
if deps.exists():sys.path.insert(0,str(deps))
import numpy,scipy,matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
r=json.loads((P/"results.json").read_text(encoding="utf-8"))
fig,(ax,bx)=plt.subplots(1,2,figsize=(11,5.5),gridspec_kw={"width_ratios":[1,1.25]})
fig.subplots_adjust(left=.06,right=.97,top=.86,bottom=.22,wspace=.32)
for y,a,label in [(2,0,"All body"),(1,.1,"10% root"),(0,.4,"40% root")]:
    ax.add_patch(Rectangle((0,y),.75,.12,facecolor="#77A5CC",edgecolor="#23475B"))
    if a:ax.add_patch(Rectangle((0,y),a*.75,.12,facecolor="#E6A060",edgecolor="#734C27"))
    ax.plot([0,0],[y-.12,y+.24],color="#333",lw=3)
    ax.annotate(label,(.375,y+.12),xytext=(0,16),textcoords="offset points",ha="center")
ax.set(xlim=(-.07,.85),ylim=(-.3,2.6),xlabel="Position along the 0.75 mm arm")
ax.set_yticks([]);ax.set_title("Root placement (schematic)",loc="left",fontsize=11)
ax.text(.0,-.17,"Root = orange; body = blue",transform=ax.transAxes,fontsize=9)
ids=["body","root10","root40","all_soft"];labels=["Body","Root 10%","Root 40%","All soft"]
fem=[r["fem_finest"][i]["mean_tip_deflection_um"] for i in ids]
beam=[]
for i in ids:
    f=r["fem_finest"][i]
    beam.append(next(x for x in r["beam_cases"] if x["alpha"]==f["alpha"] and x["root_E_MPa_assumed"]==f["root_E_MPa_assumed"])["bending_deflection_um"])
xx=list(range(4))
bx.bar([x-.17 for x in xx],beam,width=.32,color="#A7B4C0",label="Bending-only beam")
bx.bar([x+.17 for x in xx],fem,width=.32,color="#276795",label="2-D plane-stress FEM")
bx.set_xticks(xx,labels);bx.set_ylabel("Tip displacement (micrometres)")
bx.set_title("Equal end load: 5.625 mN",loc="left",fontsize=11)
bx.grid(axis="y",alpha=.2);bx.legend(frameon=False,fontsize=9)
fig.suptitle("Local elastic material changes support, not proven recovery",fontsize=14)
fig.text(.03,.045,"Hypothetical E: body 500 MPa, root 200 MPa. No measured 50 C modulus, creep, bond strength or recovery.",fontsize=9,color="#555")
fig.savefig(P/"root_layout_comparison.png",dpi=160);plt.close(fig)
env={"python":sys.version,"numpy":numpy.__version__,"scipy":scipy.__version__,"matplotlib":matplotlib.__version__}
(P/"environment.json").write_text(json.dumps(env,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"figure":"root_layout_comparison.png","environment":env}))
