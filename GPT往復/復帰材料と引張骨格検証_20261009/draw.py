"""Rebuild figures with matplotlib. Images show calculations/concepts, never experiments."""
import sys, json, csv
from pathlib import Path
HERE=Path(__file__).resolve().parent
deps=HERE.parents[1]/".deps"
if deps.exists(): sys.path.insert(0,str(deps))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch
jp=Path("C:/Windows/Fonts/meiryo.ttc")
if jp.exists(): fm.fontManager.addfont(str(jp)); plt.rcParams["font.family"]=fm.FontProperties(fname=str(jp)).get_name()
plt.rcParams.update({"font.size":10,"axes.unicode_minus":False,"svg.fonttype":"path","svg.hashsalt":"H52"})
def rows(name):
    with (HERE/name).open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def save(fig,name):
    fig.savefig(HERE/(name+".png"),dpi=170,facecolor="white")
    fig.savefig(HERE/(name+".svg"),facecolor="white",metadata={"Date":None})
    p=HERE/(name+".svg")
    p.write_text("\n".join(x.rstrip() for x in p.read_text(encoding="utf-8").splitlines())+"\n",encoding="utf-8",newline="\n")
    plt.close(fig)
m=rows("members.csv")
fig,axs=plt.subplots(1,2,figsize=(12,5.8))
for E,c in zip((1,2.66,10,100),("#375e97","#d17a26","#4c8b69","#7b6da6")):
    xx=[x for x in m if float(x["E_MPa"])==E]
    axs[0].plot([int(x["effective_panels"]) for x in xx],[float(x["pair_to_beam_volume"]) for x in xx],marker="o",color=c,label=f"E={E} MPa")
axs[0].axhline(1,color="black",ls="--",lw=1)
axs[0].set_xticks([0,1,2,3],["座屈無視\n理想下限","補強なし","有効2区間","有効3区間"])
axs[0].set_ylabel("引張材＋圧縮戻り材の体積 / 曲げ枝体積")
axs[0].set_title("枠を含めると単純な軽量化にはならない")
axs[0].legend(frameon=False)
axs[0].grid(axis="y",alpha=.25)
xx=[x for x in m if float(x["E_MPa"])==2.66]
v=[float(x["pair_to_beam_volume"]) for x in xx]
axs[1].bar(range(4),v,color=["#a8b5c5","#c85845","#3b8777","#7fa7a0"])
axs[1].axhline(1,color="black",ls="--",lw=1)
for i,val in enumerate(v):axs[1].text(i,val+.025,f"{val:.3f}",ha="center")
axs[1].set_ylim(0,1.35)
axs[1].set_xticks(range(4),["理想下限","補強なし","有効2区間","有効3区間"])
axs[1].set_title("E=2.66 MPa の仮定例")
axs[1].set_ylabel("体積比（補強・接合部の追加前）")
fig.suptitle("H52：往復2本の引張材と2本の圧縮戻り材を数えた比較",fontsize=14,y=.99)
fig.text(.5,.025,"計算条件：k=1.1 N/m、変位10 µm、ひずみ上限5%（仮定）、Euler荷重安全率2。\n「有効区間」には二方向の横支えが必要。実物の座屈・疲労・滑走試験ではない。",ha="center",fontsize=10)
fig.tight_layout(rect=[0,.13,1,.94])
save(fig,"01-member-volume")

r=json.loads((HERE/"results.json").read_text(encoding="utf-8"))
ft=.68/.71
offset=[-.025+i*.000125 for i in range(401)]
strain=[100*max(0,(250*(ft+d)+10)/(250*ft)-1) for d in offset]
slack=[max(0,-250*d) for d in offset]
fig,axs=plt.subplots(1,2,figsize=(12,5.8))
axs[0].plot([x*100 for x in offset],strain,color="#375e97",lw=2,label="最大引張ひずみ")
axs[0].axhline(5,color="#c85845",ls="--",label="5%の仮定上限")
axs[0].axvspan(-1.2,r["humidity"]["allowable_positive_frame_factor_difference"]*100,color="#4c8b69",alpha=.15,label="ひずみ＋遊びの一次選別範囲")
axs[0].set_xlabel("枠の長さ倍率 − 引張材の長さ倍率（百分率点）")
axs[0].set_ylabel("最大引張ひずみ（%）")
axs[0].set_title("濡れ基準250 µm、復帰変位10 µm")
axs[0].legend(fontsize=8,loc="upper left",frameon=False)
axs[0].grid(alpha=.2)
vals=[100*r["humidity"]["fixed_dry_spun_max_strain"],100*r["humidity"]["matched_dry_spun_max_strain"]]
axs[1].bar([0,1],vals,color=["#c85845","#4c8b69"])
axs[1].axhline(5,color="black",ls="--")
for i,val in enumerate(vals):axs[1].text(i,val+.2,f"{val:.2f}%",ha="center")
axs[1].set_xticks([0,1],["枠は縮まない","枠も同じ比率で縮む"])
axs[1].set_ylim(0,10);axs[1].set_ylabel("最大引張ひずみ（%）")
axs[1].set_title("原資料の長さ比からの計算例")
fig.suptitle("H52：乾湿の寸法差を揃える設計条件",fontsize=14,y=.99)
fig.text(.5,.025,"特許 WO2024261265A1 [0191, 0198] の乾式紡糸例：濡れ0.71、再乾燥0.68（初期乾燥長さ比）。\n図は平均値の算術例。50℃特性・誤差分布・製造ばらつき・試料の安全ひずみは未確定。",ha="center",fontsize=10)
fig.tight_layout(rect=[0,.13,1,.94])
save(fig,"02-humidity")

fig=plt.figure(figsize=(12,7.2));ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,12);ax.set_ylim(0,7.2);ax.axis("off")
def box(x,y,w,h,text,color):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.1",fc=color,ec="#45515c",lw=1))
    ax.text(x+w/2,y+h/2,text,ha="center",va="center",fontsize=11)
def arrow(a,b,color="#45515c",style="-|>"):
    ax.annotate("",b,a,arrowprops={"arrowstyle":style,"lw":2,"color":color})
ax.text(6,6.8,"H52 概念：荷重を受ける経路と、接点を戻す経路を分ける",ha="center",fontsize=16)
box(.5,4.6,2.3,1.2,"滑走板・エッジ\n接触結晶を保持した面","#edf0f3")
box(3.8,4.6,3.4,1.2,"広い荷重座＋変位止め\n大荷重は支持幹へ","#f4dec5")
box(8.2,4.6,3.2,1.2,"粒内の主支持幹\n開放空隙・排水","#dae9df")
arrow((2.9,5.2),(3.65,5.2));arrow((7.3,5.2),(8.05,5.2))
box(.5,2.3,3.2,1.2,"小さい復帰変位\n計算例10 µm","#dae6f3")
box(4.2,2.3,3.0,1.2,"往復の引張材 2本\n片方向では1本が作動","#dae6f3")
box(8.2,2.3,3.2,1.2,"圧縮戻り材 2本\n横支えは主支持幹へ","#e6def0")
arrow((2.1,4.45),(2.1,3.65))
arrow((3.8,2.9),(4.05,2.9));arrow((7.3,2.9),(8.05,2.9))
arrow((9.8,3.65),(9.8,4.45),color="#7b6da6")
ax.text(6,1.6,"水は開口から排出。枠・引張材の乾湿寸法変化を揃える。\n補強の反力・接合部・粒の全方向接触は別途3Dで成立させる。",ha="center",va="center",fontsize=12)
ax.text(6,.55,"力の経路を示す概念図。配置図・製作図・結晶成長の実証ではない。\n2.66 MPaの複合ゲルと特許の配向PVAを同一材料として扱っていない。",ha="center",fontsize=10,color="#555555")
save(fig,"03-concept")
print("Generated 3 original figures, PNG + SVG; no experimental images.")
