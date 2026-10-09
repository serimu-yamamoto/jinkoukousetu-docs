from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent
D=P.parents[1]/'.research96/deps'
if D.exists():sys.path.insert(0,str(D))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=json.loads((P/'results.json').read_text(encoding='utf-8'))
f=json.loads((P/'finite_recovery.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,2,figsize=(14,5.7),layout='constrained')
colors={1.3:'#0072B2',1.5:'#D55E00',1.7:'#009E73'}
for row in r['cases']:
 if 'trajectory' not in row:continue
 t=np.array([v['T'] for v in row['trajectory']]);x=np.array([v['X'] for v in row['trajectory']]);ok=t>0
 mode='all members' if row['mode']=='all_SLS' else 'vertical only'
 ax[0].plot(t[ok],x[ok],color=colors[row['X_initial']],linestyle='None',marker='.' if row['mode']=='all_SLS' else 'x',markersize=3,alpha=.85,label=f"X0={row['X_initial']}, {mode}")
ax[0].set(xscale='log',xlim=(.01,180),ylim=(-.05,1.85),xlabel='Dimensionless free time T (not seconds)',ylabel='Indentation X',title='A. Return history (sparse log-time samples)')
ax[0].legend(fontsize=8,loc='lower left');ax[0].grid(alpha=.2)
rows=[v for v in f['cases'] if v['method']=='DOP853' and v['hold_T']==100]
xx=np.arange(3);yy=[v['energy_enclosure_T'] for v in rows]
ax[1].bar(xx,yy,color=['#0072B2','#009E73','#D55E00'],width=.55)
for k,y in enumerate(yy):ax[1].text(k,y+.25,f'{y:.3f}',ha='center')
ax[1].set(xticks=xx,xticklabels=['beta=0.25','beta=0.50','beta=0.75'],ylim=(0,15.5),ylabel='Energy enclosure time T (not seconds)',title='B. Position stays within 10% of initial indentation')
ax[1].text(.02,.95,'Worst bound: lambda=0.297, X0=1.396\nHold T=100; free, passive model only',transform=ax[1].transAxes,va='top',fontsize=10)
fig.suptitle('Conditional mechanics only: no fitted 50 C material, no ski test',fontsize=14)
fig.savefig(P/'recovery_history.png',dpi=160)
plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(14,5.4),layout='constrained')
x=np.linspace(0,1.7,500)
for lam,col in [(.2501,'#0072B2'),(.4,'#D55E00')]:
 F=x*(x-1)*(x-2)+lam*x
 ax[0].plot(x,F,color=col,label=f'lambda={lam}')
ax[0].axvline(1.2,color='#555555',ls=':',label='Nominal travel limit 1.2')
ax[0].scatter([1.2],[.288],color='#D55E00',zorder=4)
ax[0].annotate('Residual 0.288 = 49.8% of peak',xy=(1.2,.288),xytext=(.45,.70),arrowprops={'arrowstyle':'->'},fontsize=10)
ax[0].set(xlabel='Indentation X',ylabel='Dimensionless steady force',title='C. Return bias increases residual resistance',ylim=(-.06,.82));ax[0].legend(loc='lower left');ax[0].grid(alpha=.2)
ax[1].axis('off')
rows=[['Nominal lambda','Worst lower lambda'],['0.30','0.22275 (below 0.25)'],['0.40','0.29700 (above 0.25)'],['Nominal travel limit','Worst upper travel limit'],['1.30','1.51247 (above 1.5)'],['1.20','1.39612 (below 1.5)']]
t=ax[1].table(cellText=rows,colWidths=[.42,.58],loc='center',cellLoc='left');t.auto_set_font_size(False);t.set_fontsize(11);t.scale(1,1.8)
for i in [0,3]:
 for j in [0,1]:t[(i,j)].set_facecolor('#e8eef4');t[(i,j)].get_text().set_weight('bold')
ax[1].set_title('D. Independent +/-5% geometric bounds')
ax[1].text(.03,.07,'Box bounds, not measured tolerances or failure probability.\nThe two extrema need not occur on the same physical part.',transform=ax[1].transAxes,fontsize=10)
fig.suptitle('Design tradeoff: internal recovery still needs grain disengagement',fontsize=14)
fig.savefig(P/'force_tolerance.png',dpi=160)
print(json.dumps({'figures':2,'source':'computed results; not experimental data'}))
