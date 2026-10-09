from pathlib import Path
import sys,json,csv,math
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Polygon
from matplotlib.font_manager import FontProperties
fp=FontProperties(fname='C:/Windows/Fonts/meiryo.ttc')
plt.rcParams.update({'font.family':fp.get_name(),'font.size':10,'axes.unicode_minus':False})
R=json.loads((D/'results.json').read_text())
def rows(n):
    with (D/(n+'.csv')).open(encoding='utf-8') as f:return list(csv.DictReader(f))
fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
w=[float(x['binder_mass_fraction'])*100 for x in rows('composition')]
m=[float(x['random_cut_equal_pressure_mu']) for x in rows('composition')]
ax[0].plot(w,m,'o-',color='#156c96',label='無作為断面・両相の圧力が等しい仮定')
ax[0].axhline(.04,color='#aa3333',ls='--',label='仮目標 0.04')
ax[0].set(xlabel='結合材の重量割合 [%]',ylabel='診断模型の摩擦係数',title='少量配合 ≠ 結晶面だけが接触')
ax[0].legend(fontsize=8,loc='upper left');ax[0].grid(alpha=.2)
vals=[x for x in rows('coupled_binder') if float(x['pressure_MPa'])==4 and x['min_anchor_and_surface_fraction']]
xx=[float(x['wet_allowable_shear_MPa_assumed']) for x in vals]
yy=[float(x['min_anchor_and_surface_fraction'])*100 for x in vals]
ax[1].plot(xx,yy,'o-',label='表面露出割合 = 保持面積割合の場合',color='#b46820')
ax[1].axhline(100/35,ls='--',color='#aa3333',label='表面荷重割合の上限 2.86%')
ax[1].scatter([4.28],[5],s=75,color='#257753',zorder=5)
ax[1].annotate('裏側保持案：保持5%・表面1%\\n必要せん断強度 4.28MPa'.replace('\\n','\n'),xy=(4.28,5),xytext=(8,14),arrowprops={'arrowstyle':'->'},fontsize=9)
ax[1].set(xlabel='濡れた後の許容せん断強度 [MPa]（仮入力）',ylabel='必要な保持面積の割合 [%]',ylim=(0,36),title='保持と滑走面を分ける条件')
ax[1].legend(fontsize=8,loc='upper right');ax[1].grid(alpha=.2)
fig.suptitle('第73巡：摩擦・保持の診断計算（実測性能ではない）',fontsize=14)
fig.savefig(D/'figure1_binder.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,5),layout='constrained')
a=ax[0];a.set_xlim(0,10);a.set_ylim(0,7);a.axis('off')
a.add_patch(Rectangle((.5,5.8),9,.45,color='#454b55'))
a.text(5,6.5,'スキーソール（相手材）',ha='center')
for x in [1,3,5,7]:
    a.add_patch(Rectangle((x,4.25),1.5,1.2,facecolor='#9bd4e8',edgecolor='#216783'))
    a.add_patch(Rectangle((x+.3,3.65),.9,.65,facecolor='#e5ad70',edgecolor='#865928'))
a.add_patch(Rectangle((.7,3.05),8.2,.6,facecolor='#c7dbc9',edgecolor='#386947'))
a.text(5,2.7,'荷重座を支える骨格：材種は未確定',ha='center',fontsize=9)
a.annotate('滑る面の露出を測る',xy=(5.6,5.46),xytext=(3.5,5.55),fontsize=9)
a.annotate('結合材は裏面・凹部へ\\n上面への回り込みを抑える'.replace('\\n','\n'),xy=(7.5,3.9),xytext=(5.4,1.1),arrowprops={'arrowstyle':'->'},fontsize=9)
a.text(.6,.2,'H73-B：H47裏面保持 × H72広い支持面\\n模式図。寸法比・結晶形・量産性は未実証。'.replace('\\n','\n'),fontsize=9)
a.set_title('材料を増やす前に、置く場所を変える')
c=rows('pad_costs')
ts=[1,5,10];mins=[];maxs=[]
for t in ts:
    v=[float(x['partial_initial_JPY_ex_tax'])/1e6 for x in c if float(x['pad_thickness_um'])==t]
    mins.append(min(v));maxs.append(max(v))
ax[1].bar([0,1,2],mins,color='#287d9e',label='仮単価の下側')
ax[1].bar([0,1,2],[hi-lo for hi,lo in zip(maxs,mins)],bottom=mins,color='#c9dce5',label='仮単価による幅')
ax[1].set_xticks([0,1,2],[str(x) for x in ts])
ax[1].set(xlabel='機能層の等価厚さ [µm]',ylabel='原料＋面積加工の部分費用 [百万円・税別]',title='2,000m²・450mm床の全深度に配置')
ax[1].legend(fontsize=9);ax[1].grid(axis='y',alpha=.2)
fig.suptitle('結晶面と結合部の配置、および費用の感度',fontsize=14)
fig.savefig(D/'figure2_design_cost.png',dpi=150);plt.close(fig)
print(json.dumps({'figures':2,'physical_trials':0}))
