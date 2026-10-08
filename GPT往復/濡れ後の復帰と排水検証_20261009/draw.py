from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parent
optional=P.parents[1]/'.deps'
if optional.exists():sys.path.insert(0,str(optional))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from matplotlib.patches import Circle,Rectangle
font=Path('C:/Windows/Fonts/meiryo.ttc')
if font.exists():
 fm.fontManager.addfont(str(font));plt.rcParams['font.family']=fm.FontProperties(fname=str(font)).get_name()
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','axes.unicode_minus':False})
r=json.loads((P/'results.json').read_text(encoding='utf8'));p=r['reference_bridge'];s=np.linspace(0,p['sc'],401)
F=lambda ss:p['F0']/(1+p['A']*ss+p['B']*ss*ss)
def save(fig,name):
 fig.savefig(P/(name+'.png'),dpi=160,bbox_inches='tight');fig.savefig(P/(name+'.svg'),bbox_inches='tight',metadata={'Date':None});plt.close(fig)
 svg=P/(name+'.svg');svg.write_text('\n'.join(v.rstrip() for v in svg.read_text(encoding='utf8').splitlines())+'\n',encoding='utf8',newline='\n')
fig,ax=plt.subplots(1,3,figsize=(15,4.5),layout='constrained')
e=r['energy_counterexample'];a=ax[0]
a.plot(s*1e6,F(s)*1e6,label='水の引力',lw=2,color='#007c91');a.plot(s*1e6,e['k_chosen_N_m']*(p['gap_m']-s)/2*1e6,label='復元力（エネルギー反例）',color='#c45632',lw=2);a.set_title('A  エネルギーが足りても始動できない');a.set_xlabel('接点の隙間 s（µm）');a.set_ylabel('各枝に働く力（µN）');a.legend(fontsize=9);a.grid(alpha=.2)
n=r['narrow_gap_counterexample'];a=ax[1]
a.plot(s*1e6,F(s)*1e6,label='水の引力',lw=2,color='#007c91');a.plot(s*1e6,n['k_chosen_N_m']*(n['unloaded_gap_m']-s)/2*1e6,label='復元力（狭い隙間）',color='#c45632',lw=2);a.set_title('B  開き始めても経路の途中で止まる');a.set_xlabel('接点の隙間 s（µm）');a.legend(fontsize=9);a.grid(alpha=.2)
a=ax[2];u=np.linspace(0,1,301)
for alpha,col in [(0,'#63778b'),(.9,'#17836a')]:
 t=next(v for v in r['taper'] if v['alpha']==alpha);rad=t['root_radius_m']*(1-alpha*u)**(1/3)*1e6
 a.plot(u*t['length_m']*1e6,rad,color=col,label='一様枝' if alpha==0 else 'テーパー枝 α=0.9',lw=2);a.plot(u*t['length_m']*1e6,-rad,color=col,lw=2)
a.set_title('C  同じ曲げ剛性で枝材を17.75％減');a.set_xlabel('根元からの距離（µm）');a.set_ylabel('中心からの半径（µm）');a.legend(fontsize=9);a.grid(alpha=.2)
fig.suptitle('H50：濡れた接点の復帰経路と枝の減量（未校正の局所模型）',fontsize=14);save(fig,'01_reopening_path')
fig,ax=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
for th,col in [(100,'#467aa0'),(110,'#a8731c'),(120,'#ad4141')]:
 a=np.array([25,100,500])*1e-6;G=r['water_surface_tension_N_m']['50'];h=-2*G*math.cos(math.radians(th))/(1000*9.81*a)
 ax[0].loglog(a*1e6,h*1000,'o-',label=f'前進接触角 {th}°',color=col)
from matplotlib.ticker import ScalarFormatter,NullFormatter
ax[0].set_xticks([25,100,500]);ax[0].xaxis.set_major_formatter(ScalarFormatter());ax[0].xaxis.set_minor_formatter(NullFormatter())
ax[0].axhline(5,color='#333333',ls='--',label='仮の許容水頭5mm');ax[0].set(xlabel='理想円管の半径（µm）',ylabel='侵入に必要な水頭（mm）',title='全面撥水では入口が排水を妨げ得る');ax[0].legend(fontsize=9);ax[0].grid(alpha=.2)
R=np.array([5,15,30])*1e-6
for f in [.001,.003,.008]:ax[1].loglog(R*1e6,f/(np.pi*R**2)/1e6,'o-',label=f'荷重 {f*1000:g}mN')
ax[1].set_xticks([5,15,30]);ax[1].xaxis.set_major_formatter(ScalarFormatter());ax[1].xaxis.set_minor_formatter(NullFormatter())
ax[1].set(xlabel='支持面の投影半径（µm）',ylabel='平均面圧の下限（MPa）',title='接点の微小化は面圧を上げる');ax[1].legend(fontsize=9);ax[1].grid(alpha=.2)
fig.suptitle('H50：水を避ける形と荷重を支える形の両立条件',fontsize=14);save(fig,'02_drainage_pressure')
fig,ax=plt.subplots(1,2,figsize=(12,5),layout='constrained');t=next(v for v in r['taper'] if v['alpha']==.9);u=np.linspace(0,1,401);xx=u*t['length_m']*1e6;rad=t['root_radius_m']*(1-.9*u)**(1/3)*1e6
a=ax[0]
for sign in [-1,1]:
 y=sign*25*np.ones_like(u);a.fill_between(xx,y-rad,y+rad,color='#8aa5b8',alpha=.85);a.add_patch(Circle((180,sign*25),15,fc='#56798e',ec='white'))
 # Closed-state outline only; beam shape for tapered beam is not claimed here.
 a.add_patch(Circle((180,sign*15),15,fill=False,ec='#c45632',ls='--'))
 a.add_patch(Rectangle((-10,sign*25-18),10,36,color='#414c58'))
a.annotate('',xy=(205,10),xytext=(205,-10),arrowprops={'arrowstyle':'<->','color':'#222222'});a.text(210,0,'無荷重隙間\n20µm',va='center');a.annotate('',xy=(0,-65),xytext=(180,-65),arrowprops={'arrowstyle':'<->'});a.text(90,-76,'枝長180µm',ha='center');a.set_xlim(-20,285);a.set_ylim(-85,75);a.set_aspect('equal');a.axis('off');a.set_title('局所部品の比較図：別々の根元を固定した模型');a.text(0,60,'実線：無荷重の位置  ／  破線：接触時の先端位置',fontsize=9);a.text(0,-51,'先端球面 R15µm／枝半径16.84→7.82µm',fontsize=9)
a=ax[1];a.axis('off');a.set_title('H50の構成へ反映する条件');items=[('荷重座','短い根元へ圧縮力を流す。\n復帰枝に冬のmN級荷重を兼任させない。'),('復帰枝','短いテーパーで水の引力に抗して戻す。\n戻る時間と50℃湿潤疲労は未測定。'),('水の通り道','閉じた袋・平行面の長い狭窄を避ける。\n全面撥水に頼らず、入口と下地排水を両方確認。'),('結晶面','LLなどの候補面を保持する。\nこの図は結晶生成や実ソール摩擦の実証ではない。')]
for i,(title,txt) in enumerate(items):
 y=.86-i*.22;a.text(.01,y,title,color='#155d67',weight='bold',fontsize=12,transform=a.transAxes);a.text(.22,y,txt,va='top',fontsize=10,transform=a.transAxes)
fig.suptitle('H50構造案：荷重座・復帰枝・排水路を分ける（完成粒の3D設計ではない）',fontsize=13);save(fig,'03_component_concept')
print('3 figures generated; PNG and SVG each')
