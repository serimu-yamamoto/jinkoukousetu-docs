from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parent
dep=P.parents[1]/'.deps'
if dep.exists():sys.path.insert(0,str(dep))
import numpy as np
import scipy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=json.loads((P/'results.json').read_text(encoding='utf8'))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
rows=[x for x in R['thermal_cases'] if x['radius_um']==.5 and x['h_W_m2K']==500 and x['parallel_branches']==12]
fig,ax=plt.subplots(1,2,figsize=(12.4,5.1),layout='constrained')
ls=[x['length_um'] for x in rows]
ax[0].plot(ls,[1000*x['root_onset_s'] for x in rows],color='#E17C30',marker='o',label='Root starts melting (coupled)')
ax[0].plot(ls,[1000*x['tip_full_melt_s'] if x['tip_full_melt_s'] is not None else np.nan for x in rows],color='#176E88',marker='o',label='Tip cell fully melts (coupled)')
ax[0].axhline(R['disconnected']['root_onset_s']*1000,ls='--',color='#E17C30',alpha=.65,label='Independent root, cycle27 limit')
ax[0].axhline(R['disconnected']['tip_full_melt_s']*1000,ls='--',color='#176E88',alpha=.65,label='Independent fine branch limit')
ax[0].annotate('L=10 um: tip not fully molten\nbefore root melting starts',(10,18),fontsize=9)
ax[0].set(xlabel='Fine branch length (um)',ylabel='Elapsed heating time (ms)',title='A. Conduction heats the root and delays the tip',ylim=(0,40),xticks=ls)
ax[0].legend(fontsize=8,loc='center right');ax[0].grid(alpha=.2)
x=np.arange(5);labels=['Independent\ncycle27','L=10','L=25','L=50','L=100']
priorlo=(R['disconnected']['tip_full_melt_s']+1000*.5e-6/.03)/.8*1000
priorhi=R['disconnected']['root_onset_s']/1.2*1000
uppers=[priorhi]+[v['windows'][1]['nominal_upper_s']*1000 for v in rows]
lowers=[priorlo]+[v['windows'][1]['tip_nominal_lower_s']*1000 if v['windows'][1]['tip_nominal_lower_s'] is not None else np.nan for v in rows]
ax[1].plot(x,uppers,'s',color='#E17C30',ms=7,label='Maximum nominal time: root')
ax[1].plot(x,lowers,'o',color='#176E88',ms=7,label='Minimum nominal time: tip + shape scale')
for i,(lo,hi) in enumerate(zip(lowers,uppers)):
    if not np.isnan(lo):ax[1].plot([i,i],[lo,hi],color='#277C59' if lo<hi else '#B94C4C',lw=3)
ax[1].annotate('No tip melt',(1,33),ha='center',fontsize=9)
ax[1].set(xticks=x,xticklabels=labels,ylabel='Nominal residence time (ms)',title='B. The narrow 1,000 Pa s interval disappears',ylim=(23,45))
ax[1].legend(fontsize=8,loc='upper right');ax[1].grid(alpha=.2)
fig.suptitle('H28: fixed-geometry enthalpy diagnostic, r=0.5 um, 12 branches, gas 150 C, h=500 W/(m2 K)',fontsize=11)
fig.savefig(P/'figure1_coupled_heat.png',dpi=160);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12.4,5.1),layout='constrained')
ca=np.linspace(.5,.9,100);ev=(1-ca)/ca-.01
for rec,col in [(0,'#176E88'),(.7,'#E17C30')]:
    added=ev*.63*(1-rec)/.6*25/.8
    ax[0].plot(ca*100,added,color=col,lw=2,label=f'Assumed heat recovery {rec:.0%}')
ax[0].set(xlabel='Cake solid mass fraction (%)',ylabel='Additional drying energy cost (JPY/good kg)',title='A. Dewater before thermal drying',ylim=(0,37))
ax[0].text(.04,.94,'Good yield 80%; 25 JPY/kWh; efficiency 60%\nWater endpoint 0.01 kg/kg polymer\nEnergy sensitivity only; plant cost excluded',transform=ax[0].transAxes,va='top',fontsize=9,bbox=dict(facecolor='white',alpha=.9,edgecolor='none'))
ax[0].legend(loc='upper right',bbox_to_anchor=(1,.73),fontsize=9);ax[0].grid(alpha=.2)
water=np.array([199,1,.01]);xs=np.arange(3)
ax[1].bar(xs,water,color=['#176E88','#E17C30','#277C59'],width=.55)
ax[1].set_yscale('log');ax[1].set(xticks=xs,xticklabels=['0.5% slurry','50% cake','Drying endpoint'],ylabel='Water (kg / kg polymer feed)',title='B. Circulating water is not evaporation duty',ylim=(.003,1000))
for xx,yy in zip(xs,water):ax[1].text(xx,yy*1.25,f'{yy:g}',ha='center')
ax[1].text(.03,.08,'Slurry to cake: remove 198 kg/kg mechanically\nCake to endpoint: evaporate 0.99 kg/kg\nCirculation is not fresh-water consumption.',transform=ax[1].transAxes,fontsize=9,bbox=dict(facecolor='white',alpha=.9,edgecolor='none'))
ax[1].grid(axis='y',alpha=.2)
fig.suptitle('H28: wet recovery scenario; 70-90% cake solids and drying endpoint are unverified assumptions',fontsize=11)
fig.savefig(P/'figure2_recovery_water.png',dpi=160);plt.close(fig)
print(json.dumps({'figures':2,'matplotlib':matplotlib.__version__,'numpy':np.__version__,'scipy':scipy.__version__}))
