from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent
extra=P.parents[1]/".research84"/"deps"
if extra.exists():sys.path.insert(0,str(extra))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
states=json.loads((P/"paired_states.json").read_text(encoding="utf8"))
plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
h=np.geomspace(.04,10,151);s=np.geomspace(.1,3,151)
H,S=np.meshgrid(h,s);F=S/np.sqrt(H)
fig,ax=plt.subplots(figsize=(9,6),layout="constrained")
im=ax.pcolormesh(H,S,np.log10(F),shading="auto",cmap="coolwarm",vmin=-1,vmax=1)
ax.contour(H,S,F,levels=[.5,1,2],colors=["#34495e"]*3,linewidths=[1,2,1])
for q in states:
 ax.scatter(q["H_ratio"],q["S_ratio"],s=45,c="black",edgecolors="white",linewidths=.7,zorder=5)
marks=[(1,1,"Reference",(.95,1.24)),(4,1,"Harder only",(4.7,.75)),(.25,.75,"Soft + weaker",(.09,1.03)),(.5,.7,"Force looks recovered",(.62,.36)),(4,2,"Same force, half depth",(1.0,2.48)),(.25,.25,"Soft + disconnected",(.06,.15))]
for x,y,label,xy in marks:ax.annotate(label,(x,y),xytext=xy,arrowprops={"arrowstyle":"-","color":"black"},fontsize=9)
ax.set(xscale="log",yscale="log",xlabel="Penetration hardness H / H0 (assumed)",ylabel="Lateral onset parameter S / S0 (assumed)",title="Same lateral force can hide a different bed")
bar=fig.colorbar(im,ax=ax,label="log10(F_onset / F0), at the same normal load")
ax.text(.02,-.19,"Partial-width model: F/F0 = (S/S0) / sqrt(H/H0).\nAssumed states; no material measurements and no success probabilities.",transform=ax.transAxes,fontsize=9)
fig.savefig(P/"coupled_response.png",dpi=170);plt.close(fig)
labels=["Reference","Harder\nsupport","Soft +\nweaker","Soft +\ndisconnected","Matched force,\nharder bed","Apparently\nrestored"]
x=np.arange(len(states));fig,axes=plt.subplots(2,1,figsize=(10,7),sharex=True,layout="constrained")
axes[0].bar(x,[q["penetration_ratio"] for q in states],color="#276FBF")
axes[0].axhline(1,color="black",ls="--",lw=1);axes[0].set(ylabel="Penetration / reference",ylim=(0,2.3),title="Penetration and onset force must be observed together")
axes[1].bar(x-.18,[q["constant_load_onset_ratio"] for q in states],width=.36,label="Same normal load",color="#C04B27")
axes[1].bar(x+.18,[q["constant_depth_onset_ratio"] for q in states],width=.36,label="Same penetration",color="#73A942")
axes[1].axhline(1,color="black",ls="--",lw=1);axes[1].set(ylabel="Lateral onset / reference",xticks=x,xticklabels=labels,ylim=(0,2.3))
axes[1].legend(loc="upper left",ncol=2)
fig.supxlabel("Analytical counterexamples, not measured performance. New tracks are needed for each test.",fontsize=10)
fig.savefig(P/"paired_observations.png",dpi=170);plt.close(fig)
(P/"plot_metadata.json").write_text(json.dumps({"matplotlib":matplotlib.__version__,"numpy":np.__version__,"figures":["coupled_response.png","paired_observations.png"],"heatmap_model_nodes":151*151,"physical_experiments":0,"success_probability":None},indent=2)+"\n",encoding="utf8",newline="\n")
print("Rendered two analytical figures.")
