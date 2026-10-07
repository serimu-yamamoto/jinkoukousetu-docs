from pathlib import Path
import json,sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
p=Path(__file__).parent
r=json.loads((p/'results.json').read_text(encoding='utf-8'))
f=FontProperties(fname='C:/Windows/Fonts/meiryo.ttc')
plt.rcParams['font.family']=f.get_name()
plt.rcParams['axes.unicode_minus']=False
fig,ax=plt.subplots(1,3,figsize=(15,5.4),layout='constrained')
fig.suptitle('材料の変更だけでは決まらない：接触圧・薄膜・重量の条件付き比較',fontsize=16)
for E,col in [(1e8,'#2677a2'),(3e8,'#cc7433'),(1e9,'#618657')]:
 rows=[x for x in r['contact_sweep'] if x['nominal_pressure_Pa']==5400 and x['active_fraction']==.3 and x['E_star_Pa']==E]
 ax[0].plot([x['R_m']*1e6 for x in rows],[x['maximum_pressure_Pa']/1e6 for x in rows],color=col,label=f'E*={E/1e6:.0f} MPa（仮定）')
 for x in rows:ax[0].scatter(x['R_m']*1e6,x['maximum_pressure_Pa']/1e6,color=col,facecolors=col if x['small_contact_screen'] else 'white',zorder=4)
ax[0].set(xlabel='局所曲率半径 (µm)',ylabel='Hertz式の最大接触圧 (MPa)',title='接触を広げると局所圧は下がる')
ax[0].legend(fontsize=8,loc='upper right')
ax[0].text(.02,.02,'白抜き：a/R > 0.2。参考値のみ\n5.4 kPa・有効支持割合30%・ピッチ0.6 mm',transform=ax[0].transAxes,fontsize=8)
rows=[x for x in r['coating_sweep'] if x['E_coat_over_core']==.2]
ax[1].plot([x['t_m']*1e6 for x in rows],[x['additive_volume_fraction']*100 for x in rows],'o-',label='外へ追加した体積増 (%)',color='#cc7433')
ax[1].plot([x['t_m']*1e6 for x in rows],[(1-x['fixed_outer_EI_ratio'])*100 for x in rows],'s-',label='外径固定時の曲げ剛性減 (%)',color='#2677a2')
ax[1].set(xlabel='膜厚 (µm)',ylabel='変化 (%)',title='微細な線では「薄膜」も大きい')
ax[1].legend(fontsize=8)
ax[1].text(.04,.65,'基準線径60µm、同心円断面\n膜/芯の弾性率比0.2という仮定',transform=ax[1].transAxes,fontsize=8)
rows=r['materials_cost'];labs=['PE計算基準','POM','POM/HDPE\n31.3 wt%']
ax[2].bar(labs,[x['EAC_at_500_yen']/1e6 for x in rows],color=['#2677a2','#b86d55','#618657'])
ax[2].axhline(19,color='#913333',linestyle='--',label='仮の充当可能年額 19百万円')
ax[2].set(ylabel='年間換算費用 (百万円/年)',title='同じ形状・粒数の材料置換')
ax[2].set_ylim(0,26);ax[2].legend(fontsize=8,loc='upper left')
for i,x in enumerate(rows):ax[2].text(i,x['EAC_at_500_yen']/1e6+.4,f'{x["EAC_at_500_yen"]/1e6:.2f}',ha='center',fontsize=10)
for a in ax:a.grid(axis='y',alpha=.2);a.set_axisbelow(True)
fig.supxlabel('物理試験ではありません。材料の50℃合格・滑走摩擦・安全性を予測する図ではありません。',fontsize=11)
fig.savefig(p/'接触_薄膜_採算.png',dpi=160)
fig.savefig(p/'接触_薄膜_採算.svg')
print('Saved PNG and SVG from computed results.')
