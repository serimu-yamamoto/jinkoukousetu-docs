"""Plot model-assumption sensitivity; no experimental curves are present."""
import json
import sys
from pathlib import Path
if len(sys.argv)>1:
    sys.path.insert(0,sys.argv[1])  # Optional directory containing Matplotlib.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
data=json.loads((ROOT/'バーチャル試験/snow_origin_audit_results_20261006.json').read_text(encoding='utf8'))
for file in ['C:/Windows/Fonts/meiryo.ttc','C:/Windows/Fonts/YuGothM.ttc','C:/Windows/Fonts/msgothic.ttc']:
    if Path(file).exists():
        font_manager.fontManager.addfont(file)
        plt.rcParams['font.family']=font_manager.FontProperties(fname=file).get_name()
        break
plt.rcParams.update({'axes.unicode_minus':False,'font.size':13,'svg.fonttype':'path'})
fig, ax=plt.subplots(figsize=(12.4,7.9),facecolor='#f4f7f9')
ax.set_facecolor('white')
x=[100*r['theta_volume_fraction'] for r in data['rows']]
for key,label,color,style in [
    ('original','元のVT13模型','#087e8b','-'),
    ('no_assumed_boundary_lubrication','接触面の水潤滑を仮定しない','#ba4f41','--'),
    ('fluid_load_fraction_capped_at_0_25','水膜の荷重支持を25%以下に制限','#be8921','-.'),
    ('no_boundary_lubrication_or_fluid_support','水潤滑・水膜支持の両方を仮定しない','#535775',':')]:
    ax.plot(x,[r['cases'][key]['mu_median'] for r in data['rows']],style,color=color,
            marker='o',linewidth=2.5,markersize=6,label=label)
ax.set(xlim=(-1,39),ylim=(0,.215),xlabel='表層の体積含水率（%）',ylabel='摩擦係数の中央値（未校正模型）')
ax.set_xticks([0,3,6,10,20,28.8,38])
ax.grid(alpha=.2)
ax.spines[['top','right']].set_visible(False)
ax.legend(loc='upper left',fontsize=11,framealpha=.95)
fig.suptitle('「水を加えれば滑る」は、与えた潤滑仮定に左右される',fontsize=20,fontweight='bold',y=.97)
fig.text(.09,.905,'含水3%：元模型 0.088 → 接触面の水潤滑を外すと 0.161',fontsize=14,color='#913e34')
fig.text(.09,.11,'実測ではない。変更した模型も「正解」ではなく、仮定に対する感度を示す。',fontsize=12,fontweight='bold')
fig.text(.09,.077,'6条件 × 各20万組。同一乱数を使用。6つの計算点を直線で結ぶ。',fontsize=11,color='#42596a')
fig.text(.09,.045,'元コードの再現誤差：0。雪らしい滑走感・エッジ応答の合格判定は行っていない。',fontsize=11,color='#42596a')
fig.subplots_adjust(left=.09,right=.97,top=.85,bottom=.22)
for ext in ['png','svg']:
    fig.savefig(HERE/f'01_摩擦模型の仮定感度.{ext}',dpi=170)
svg_file=HERE/'01_摩擦模型の仮定感度.svg'
svg_file.write_text('\n'.join(line.rstrip() for line in svg_file.read_text(encoding='utf8').splitlines())+'\n',encoding='utf8')
plt.close(fig)
print('Assumption-sensitivity PNG and SVG written; no measured data.')
