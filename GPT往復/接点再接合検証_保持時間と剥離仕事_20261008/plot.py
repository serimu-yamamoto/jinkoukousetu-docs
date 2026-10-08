from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
R=json.loads((P/'results.json').read_text(encoding='utf8'))
I=json.loads((P/'inputs.json').read_text(encoding='utf8'))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
colors=['#24609c','#109b87','#df8535','#985b9f']
fig,ax=plt.subplots(1,2,figsize=(12,4.8))
sep=np.geomspace(.01,1e6,450)
for t,col in zip(I['kinetics']['t90_s'],colors):
    kh=math.log(10)/t; td=R['machine_summary']['reference_dwell_s']; u0=math.exp(-kh*td); b0=1-u0
    ks=1/sep
    b=b0+u0*kh/(kh+ks)*(-np.expm1(-(kh+ks)*600))
    ax[0].plot(sep,b,color=col,label=f'Assumed t90 = {t:g} s')
ax[0].set(xscale='log',xlabel='Mean contact-loss time after roller (s)',ylabel='Bonded fraction of eligible contacts',ylim=(0,1.04),title='Healing competes with contact separation')
ax[0].axhline(.9,color='#777',linestyle=':',linewidth=1)
ax[0].legend(loc='lower right',fontsize=9);ax[0].grid(alpha=.2)
rows=sorted([x for x in R['pressure_cases'] if x['normal_load_fraction']==1],key=lambda x:x['patch_length_m'])
x=[r['patch_length_m'] for r in rows]
ax[1].plot(x,[r['nominal_Pa']/1000 for r in rows],'-o',color=colors[0],label='Nominal pressure')
ax[1].set(xscale='log',yscale='log',xlabel='Roller / skirt footprint length (m)',ylabel='Nominal pressure (kPa)',title='Longer contact spreads the same normal load')
axr=ax[1].twinx();axr.plot(x,[r['dwell_s'] for r in rows],'-s',color=colors[2],label='Dwell time')
axr.set(yscale='log',ylabel='Dwell time (s)');axr.spines['right'].set_visible(True)
ax[1].grid(alpha=.2);ax[1].text(.2,.82,'4 t, slope 30 deg, width 20 m, speed 0.6 m/s\nPressure x dwell = 2.832 kPa s (nominal)',transform=ax[1].transAxes,fontsize=9,bbox={'facecolor':'white','alpha':.85,'edgecolor':'none'})
fig.suptitle('Cycle 26 | Uncalibrated contact model, not material recovery or project success',fontsize=12)
fig.text(.015,.018,'Left: 0.083 s forced contact + 600 s rest; formed bonds assumed stable. Right: all normal load on one uniform footprint.',fontsize=9)
fig.tight_layout(rect=[0,.055,1,.92]);fig.savefig(P/'01_retention_and_roller.png',dpi=160);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,4.8))
for gc,col in zip(I['cohesive']['Gc_J_m2'],colors):
    df=2*gc/1e6*1e6;d0=.1*df
    x=np.concatenate([np.linspace(max(d0*.01,.0001),d0,30),np.linspace(d0,df,100)])
    y=np.where(x<=d0,x/d0,(df-x)/(df-d0))
    ax[0].plot(x,y,color=col,label=f'Gc = {gc:g} J/m2')
ax[0].set(xscale='log',xlabel='Normal opening (micrometres)',ylabel='Traction (MPa)',title='Same peak strength, different release distance',ylim=(0,1.1),xlim=(.001,300))
ax[0].legend(loc='lower left',fontsize=9);ax[0].grid(alpha=.2)
for process,col in zip([0,100,300],colors):
    rows=sorted([x for x in R['cost_cases'] if x['contact_phase_JPY_kg']==3000 and x['localization_JPY_kg']==process],key=lambda x:x['w'])
    ax[1].plot([100*x['w'] for x in rows],[x['remaining_JPY']/1e6 for x in rows],'-o',color=col,label=f'Process {process} JPY / finished kg')
ax[1].axhline(0,color='#555',linewidth=1)
ax[1].set(xscale='log',xlabel='Contact-phase mass fraction (%)',ylabel='Annual remaining budget (million JPY)',title='Small material fraction still needs cheap processing')
ax[1].legend(loc='lower left',fontsize=9);ax[1].grid(alpha=.2)
fig.suptitle('Cycle 26 | Hypothetical separation law and cost assumptions',fontsize=12)
fig.text(.015,.018,'Left: triangular cohesive law, not ski friction. Right: 2,000 m2 cost example; phase price 3,000 JPY/kg; extra regeneration excluded.',fontsize=9)
fig.tight_layout(rect=[0,.055,1,.92]);fig.savefig(P/'02_release_and_cost.png',dpi=160);plt.close(fig)
print(json.dumps({'figures':2,'matplotlib':matplotlib.__version__,'numpy':np.__version__}))
