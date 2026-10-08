import json, math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter
ROOT=Path(__file__).resolve().parent
r=json.loads((ROOT/'results.json').read_text(encoding='utf-8'))
i=json.loads((ROOT/'inputs.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':10,'figure.dpi':150,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,3,figsize=(15,4.8),layout='constrained')
for ta,col in [(30,'#197a86'),(50,'#ab4261')]:
    rows=[x for x in r['thermal_scales'] if x['ambient_C']==ta and x['Nu']==2 and x['gamma_N_m']==.03 and x['illustrative_mu_Pa_s']==100]
    ax[0].loglog([x['radius_um'] for x in rows],[x['energy_plus_prescribed_latent_s'] for x in rows],'-o',color=col,label=f'Energy proxy: air {ta} C')
ax[0].loglog([x['radius_um'] for x in rows],[x['viscocapillary_scale_s'] for x in rows],'--',color='#d18b16',label='Capillary scale: assumed 100 Pa s')
ax[0].set(xlabel='Model sphere radius (micrometres)',ylabel='Time scale (s)',title='Heat removal and shape relaxation')
ax[0].set_xticks([25,50,125,250,500],labels=['25','50','125','250','500'])
ax[0].xaxis.set_minor_formatter(NullFormatter())
ax[0].set(xlim=(20,650),ylim=(.012,25))
ax[0].grid(alpha=.2,which='both');ax[0].legend(fontsize=8)
ax[0].text(.02,.02,'No branch-formation or crystal-kinetics model',transform=ax[0].transAxes,fontsize=8)
s=i['shape']; mean=s['outer_radius_mm']/(1+s['amplitude'])
theta=[2*math.pi*j/720 for j in range(721)]
rad=[mean*(1+s['amplitude']*math.cos(s['lobes']*t)) for t in theta]
ax[1].fill([rr*math.cos(t) for rr,t in zip(rad,theta)],[rr*math.sin(t) for rr,t in zip(rad,theta)],color='#98c6cc',edgecolor='#197a86')
ax[1].plot([.3*math.cos(t) for t in theta],[.3*math.sin(t) for t in theta],'--',color='#777',lw=.8)
ax[1].set(aspect='equal',xlim=(-.36,.36),ylim=(-.36,.36),xlabel='mm',ylabel='mm',title='X17 prescribed solid cross section')
ax[1].text(.5,-.22,'0.6 mm diameter; cut ends unrounded\nNot a proven snow-like particle',transform=ax[1].transAxes,ha='center',fontsize=9)
ax[2].loglog([100*x['reform_fraction_per_closure'] for x in r['operation']],[x['all_in_regeneration_fee_ceiling_JPY_kg'] for x in r['operation']],'-o',color='#197a86')
for x in r['operation']:
    ax[2].annotate(f"{x['all_in_regeneration_fee_ceiling_JPY_kg']:.2f}",(100*x['reform_fraction_per_closure'],x['all_in_regeneration_fee_ceiling_JPY_kg']),xytext=(7,7),textcoords='offset points',fontsize=9)
ax[2].set(xlabel='Bed mass reformed each closure (%)',ylabel='All-in regeneration fee ceiling (JPY/kg)',xlim=(.07,8),ylim=(1.2,180),title='Inherited budget; 240 closures/year')
ax[2].grid(alpha=.2,which='both')
ax[2].text(.02,.02,'Pretax hypothetical budget, not a price quote',transform=ax[2].transAxes,fontsize=8)
fig.suptitle('Cycle 17 | Process and cost comparisons; physical performance remains unverified',fontsize=14)
fig.savefig(ROOT/'overview.png')
plt.close(fig)
print('overview.png generated')
