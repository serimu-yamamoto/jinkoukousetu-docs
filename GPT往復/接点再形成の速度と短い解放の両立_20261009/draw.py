from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent;R=P.parents[1]
if (R/'.research88/deps').exists():sys.path.insert(0,str(R/'.research88/deps'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
curves=json.loads((P/'transient_curves.json').read_text(encoding='utf8'))
colors=['#bb643e','#398393','#8562a5','#777777']
fig,ax=plt.subplots(2,2,figsize=(13.5,9.2),layout='constrained')
for c,col in zip(curves,colors):
    x=[q['u'] for q in c['samples']]
    ax[0,0].plot(x,[q['force_ratio'] for q in c['samples']],color=col,label=c['label'])
    ax[0,1].plot(x,[q['work'] for q in c['samples']],color=col,label=c['label'])
ax[0,0].set(xlabel='Local slip / single-contact release distance',ylabel='Contact stress / initial synchronous peak',title='A. Rebinding sustains resistance',xlim=(0,8),ylim=(-.02,1.03))
ax[0,0].legend(fontsize=9);ax[0,0].grid(alpha=.2)
ax[0,1].set(xlabel='Local slip / single-contact release distance',ylabel='Work / (initial peak stress x release distance)',title='B. Short release can still accumulate large work')
ax[0,1].legend(fontsize=9);ax[0,1].grid(alpha=.2)
r=np.logspace(-2,3,400)
ax[1,0].semilogx(r,.5/(1+r),color='#398393')
ax[1,0].axhline(.05,color='#bb643e',ls='--',label='Illustrative residual budget 5%')
ax[1,0].axvline(9,color='gray',ls=':')
ax[1,0].set(xlabel='r = local speed x mean off-wait / release distance',ylabel='Steady residual / initial peak',title='C. Releasing once is not releasing permanently')
ax[1,0].legend(fontsize=9);ax[1,0].grid(alpha=.2)
T=np.linspace(0,1,200)
for eta,col in zip([1,.95,.8],['#398393','#8562a5','#bb643e']):
    ax[1,1].plot(T,eta*(1-np.exp(-T/.1)),color=col,label=f'Available partners = {eta:.2f}')
ax[1,1].axhline(.95,color='gray',ls='--',label='Illustrative recovery fraction 95%')
ax[1,1].set(xlabel='Time after full release (s)',ylabel='Reformed fraction (not recovered strength)',title='D. Fast reset cannot replace missing neighbours',ylim=(0,1.04))
ax[1,1].legend(fontsize=9);ax[1,1].grid(alpha=.2)
fig.suptitle('Cycle 88 | Hypothetical contact renewal, not measured ski performance\nIdentical contacts: transient oscillations are model synchronization',fontsize=14)
fig.savefig(P/'renewal_and_recovery.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(14,8.5),layout='constrained')
v=np.logspace(-4,0,500);lo=100e-6*9/v;hi=.5/(-np.log(.05))
ax[0].loglog(v,lo,label='Minimum wait for residual <= 5%',lw=2,color='#bb643e')
ax[0].axhline(hi,color='#398393',lw=2,label='Maximum wait for 95% reset in 0.5 s')
ax[0].fill_between(v,lo,hi,where=lo<=hi,color='#b8cfba',alpha=.6,label='One-rate necessary window')
ax[0].scatter([.001,.01],[.9,.09],color='#333333',zorder=3)
ax[0].set(xlabel='Local contact slip speed (m/s), not ski speed',ylabel='Mean detached waiting time (s)',title='A. A fixed reset rate fails at sufficiently slow slip')
ax[0].text(.04,.14,'Assumed release distance: 100 um\nAll potential partners available\nBudgets are not measured snow targets',transform=ax[0].transAxes,fontsize=10)
ax[0].legend(loc='upper right',fontsize=9);ax[0].grid(alpha=.2,which='both')
ax[1].set(xlim=(0,10),ylim=(0,10));ax[1].axis('off')
ax[1].set_title('B. H88: change capture while keeping normal support')
boxes=[(1,7.7,8,1.0,'Before passage: support + available contacts','#d9e7ec'),
       (1,5.55,8,1.25,'During local slip: release, then suppress re-capture\nRetreated opening / changed orientation?','#f0ded3'),
       (1,3.2,8,1.25,'After unloading: restore opening + partner access\nReset rate and availability must be measured','#dce9d9')]
for x,y,w,h,t,col in boxes:
 ax[1].add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.12',facecolor=col,edgecolor='#556677'))
 ax[1].text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=11)
ax[1].annotate('',(5,6.95),(5,7.55),arrowprops={'arrowstyle':'->','lw':1.8})
ax[1].annotate('',(5,4.65),(5,5.4),arrowprops={'arrowstyle':'->','lw':1.8})
ax[1].text(.8,1.9,'Example: reset wait 0.1 s, local speed 0.001 m/s\nrequires sliding attachment rate <= 1/9 of reset rate.',fontsize=11)
ax[1].text(.8,.55,'Functional design requirement, not a proven mechanism.\nNo added latch, glue, timer or sensor has been assumed built.',fontsize=10)
fig.suptitle('Cycle 88 | Pass-time reformation and post-pass recovery need separate evidence',fontsize=15)
fig.savefig(P/'rate_window_and_design.png',dpi=150);plt.close(fig)
(P/'plot_metadata.json').write_text(json.dumps({'figures':['renewal_and_recovery.png','rate_window_and_design.png'],'physical_experiments':0,'manufacturing_demonstrated':False,'third_party_figures_reproduced':False},indent=2)+'\n',encoding='utf8',newline='\n')
print('Two original diagnostic figures generated.')
