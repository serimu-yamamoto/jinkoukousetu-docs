"""Original H53 diagrams; calculated sensitivities, not experimental images."""
import sys,csv,json
from pathlib import Path
P=Path(__file__).resolve().parent
deps=P.parents[1]/".deps"
if deps.exists():sys.path.insert(0,str(deps))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle,Circle
font=Path("C:/Windows/Fonts/meiryo.ttc")
if font.exists():fm.fontManager.addfont(str(font));plt.rcParams["font.family"]=fm.FontProperties(fname=str(font)).get_name()
plt.rcParams.update({"font.size":10,"axes.unicode_minus":False,"svg.fonttype":"path","svg.hashsalt":"H53"})
def rows(name):
    with (P/name).open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def save(fig,name):
    fig.savefig(P/(name+".png"),dpi=170,facecolor="white")
    fig.savefig(P/(name+".svg"),facecolor="white",metadata={"Date":None})
    p=P/(name+".svg")
    p.write_text("\n".join(x.rstrip() for x in p.read_text(encoding="utf-8").splitlines())+"\n",encoding="utf-8",newline="\n")
    plt.close(fig)
r=json.loads((P/"results.json").read_text(encoding="utf-8"))
cuts=rows("cutting.csv");particles=rows("particles.csv")
fig,axs=plt.subplots(1,2,figsize=(12,5.8))
for c,color in ((19.6,"#377f76"),(71,"#d28a3c"),(231,"#8864a0"),(410,"#ba5549")):
    xx=[x for x in cuts if x["shape"]=="six_cut_faces_cube" and float(x["cell_um"])==c and float(x["depth_cells"])==1]
    axs[0].plot([float(x["dimension_um"]) for x in xx],[100*float(x["affected_fraction"]) for x in xx],"o-",c=color,label=f"気泡径 {c} µm")
axs[0].set_xlabel("切り出す立方体の一辺（µm）");axs[0].set_ylabel("外周影響域の体積割合（%）")
axs[0].set_title("外周1気泡分が影響を受ける仮定")
axs[0].legend(frameon=False);axs[0].grid(alpha=.2)
for D,col in ((300,"#b87838"),(500,"#377f76"),(750,"#64799c")):
    xx=[x for x in particles if int(x["core_side_um"])==D]
    axs[1].plot([float(x["skin_um"]) for x in xx],[float(x["mass_at_phi055_t"]) for x in xx],"o-",c=col,label=f"中心一辺 {D} µm")
axs[1].axhline(107.91,c="black",ls="--",label="全発泡の体積基準")
axs[1].set_xlabel("中心を覆う緻密な皮膜厚さ（µm）");axs[1].set_ylabel("2,000 m²・450 mm床の材料量（t）")
axs[1].set_title("緻密な皮膜と6本の枝を含めた重量")
axs[1].legend(frameon=False);axs[1].grid(alpha=.2)
fig.suptitle("H53：小粒化と保護皮膜は、軽量化と同時には進まない",fontsize=14)
fig.text(.5,.025,"左：幾何模型。破れた気泡の実測割合ではない。右：充填率0.55、発泡密度218 kg/m³、緻密相1,120 kg/m³。\n密度・気泡径の異なる論文材料を同一の完成材料として合成していない。皮膜の耐水性と量産性は未実証。",ha="center",fontsize=10)
fig.tight_layout(rect=[0,.13,1,.94]);save(fig,"01-size-and-mass")

fig,axs=plt.subplots(1,2,figsize=(12,5.8))
J=[.7,.85,.95];vals=[450/j for j in J]
axs[0].bar([0,1,2],vals,color=["#bd614c","#c69643","#4f8d78"])
axs[0].axhline(450,c="black",ls="--",label="仕上げたい床厚 450 mm")
for i,val in enumerate(vals):axs[0].text(i,val+7,f"{val:.1f} mm",ha="center")
axs[0].set_xticks([0,1,2],["J=0.70","J=0.85","J=0.95"]);axs[0].set_ylim(0,720)
axs[0].set_ylabel("除荷・回復後の床厚（mm）");axs[0].set_title("荷重中だけ450 mmに合わせた反例");axs[0].legend(frameon=False,loc="lower left")
wm=rows("water.csv")
xx=[x for x in wm if float(x["depth_cells"])==1 and x["void_source"]=="published" and float(x["accessible_and_retained_fraction_assumed"])==.1]
vv=[float(x["water_t"]) for x in xx]
axs[1].bar([0,1],vv,color=["#bd614c","#4f8d78"])
for i,v in enumerate(vv):axs[1].text(i,v+.2,f"{v:.2f} t",ha="center")
axs[1].set_xticks([0,1],["6面を切る","外周は保護し両端だけ切る"])
axs[1].set_ylim(0,10);axs[1].set_ylabel("内部にアクセス・残留する水の仮定量（t）")
axs[1].set_title("500 µm、影響域細孔の10%に水が残る仮定")
fig.suptitle("H53：整地は戻った高さで決め、雨後重量は別に測る",fontsize=14)
fig.text(.5,.025,"Jは粒内体積の荷重中／回復後の比。粒間の充填率を固定した状態比較で、圧力からの予測ではない。\n右は細孔量からの感度計算。実際の雨水浸入・排水速度・残留量、泥化・滑走の判定を表していない。",ha="center",fontsize=10)
fig.tight_layout(rect=[0,.13,1,.94]);save(fig,"02-rain-and-grooming")

fig=plt.figure(figsize=(12,7));ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,12);ax.set_ylim(0,7);ax.axis("off")
ax.text(6,6.55,"H53候補：多孔中心を保ち、外周・細い枝・切断部を緻密に残す",ha="center",fontsize=15)
# Mass-model plan projection, two out-of-plane arms omitted.
for x,y,w,h in [(1,3.4,3.6,.22),(2.69,1.7,.22,3.6)]:
    ax.add_patch(Rectangle((x,y),w,h,fc="#66869e",ec="#314c5c"))
ax.add_patch(Rectangle((1.8,2.5),2,2,fc="#66869e",ec="#314c5c",lw=2))
ax.add_patch(Rectangle((1.92,2.62),1.76,1.76,fc="#e3f0ed",ec="#6b998c"))
for x,y in [(2.2,2.9),(2.7,3.0),(3.3,2.95),(2.25,3.6),(2.85,3.6),(3.3,4.0),(2.3,4.0)]:
    ax.add_patch(Circle((x,y),.15,fc="white",ec="#699789"))
ax.text(2.8,5.55,"重量を計算した6枝模型\n（図では奥行き方向の2枝を省略）",ha="center",fontsize=11)
ax.text(2.8,1.15,"中心500 µm、皮膜5 µm\n枝：半径25 µm・長さ150 µm\n雪の結晶や製造済み粒の画像ではない",ha="center",fontsize=10)
# Continuous profile concept longitudinal section.
ax.add_patch(Rectangle((6.5,2.8),4.6,1.7,fc="#66869e",ec="#314c5c",lw=2))
ax.add_patch(Rectangle((6.65,2.96),4.3,1.38,fc="#e3f0ed",ec="#6b998c"))
for x in (7,7.6,8.2,8.8,9.4,10,10.6):
    for y in (3.25,3.95):ax.add_patch(Circle((x,y),.20,fc="white",ec="#699789"))
for x in (8.1,9.6):ax.plot([x,x],[2.5,4.8],ls="--",c="#c77341",lw=2)
ax.text(8.8,5.5,"量産候補：異形材を連続形成して切断\n切断面の再封止は工場で検討",ha="center",fontsize=11)
ax.text(8.8,1.5,"細い突起は緻密相とする。表面の摩擦を別評価。\n両端封止5 µmの質量保存例：\n最終長500 µmに対し供給長541.4 µm",ha="center",fontsize=10)
ax.text(6,.35,"概念と数量下限。連続異形材と6枝粒は同一形状ではなく、加工・方向性・雪らしい解放の成立は未確認。",ha="center",fontsize=10,color="#555")
save(fig,"03-concept")
print("3 original calculation/concept figures generated.")
