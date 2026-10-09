from pathlib import Path
import sys,math,json
P=Path(__file__).resolve().parent
# Optional transient dependency directory; standard installation also works.
deps=P.parents[1]/".research93"/"deps"
if deps.exists():sys.path.insert(0,str(deps))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
r=[10**(-3+i*6/400) for i in range(401)]
h=[-math.expm1(-x)/x for x in r]
fig,ax=plt.subplots(figsize=(9,5.4))
fig.subplots_adjust(left=.12,right=.97,bottom=.20,top=.90)
ax.semilogx(r,h,color="#2463A7",linewidth=2.4)
for x in [.1,10]:
    y=-math.expm1(-x)/x
    ax.scatter([x],[y],color="#B75518",zorder=5)
    ax.annotate(f"r = {x:g}, H = {y:.4f}",(x,y),xytext=(12,-24 if x==.1 else 20),textcoords="offset points")
ax.set(xlabel="L / ell: interval divided by hypothetical decay length",
ylabel="Normalized diagnostic activity H (not wear)",ylim=(0,1.08))
ax.grid(True,which="both",alpha=.15)
ax.set_title("Same 50:50 direction mixture; different change intervals",loc="left",fontsize=13)
fig.text(.02,.01,"Hypothetical exponential kernel. No material fit, wear prediction, or physical experiment.",fontsize=9,color="#555555")
fig.savefig(P/"history_activity.png",dpi=160)
plt.close(fig)
print("Rendered one original diagnostic figure; 401 points.")
