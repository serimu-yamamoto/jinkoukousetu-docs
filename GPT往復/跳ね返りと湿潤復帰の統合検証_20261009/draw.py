import csv,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','figure.dpi':150})
R=json.loads((P/'results.json').read_text(encoding='utf-8'));I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
def rows(name):return list(csv.DictReader((P/name).open(encoding='utf-8')))
def save(fig,name):
    fig.savefig(P/(name+'.png'),bbox_inches='tight');fig.savefig(P/(name+'.svg'),bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained');data=rows('force_branches.csv')
for mu,color in [(.3,'#3178ac'),(.6,'#cd772b'),(.8,'#ad4059')]:
    v=[r for r in data if float(r['mu'])==mu];x=[float(r['stroke_um']) for r in v]
    ax[0].plot(x,[float(r['load_force_uN']) for r in v],color=color,label=f'mu={mu}: loading')
    ax[0].plot(x,[float(r['return_force_uN']) for r in v],'--',color=color,label=f'mu={mu}: controlled return')
ax[0].set(xlabel='Cam travel (um)',ylabel='Force per cam (uN)',title='45-degree cam, 60 um wide return beams');ax[0].legend(fontsize=8)
mu=np.linspace(0,1.2,500);ax[1].plot(mu,np.degrees(np.arctan(mu)),label='Must be above: arctan(mu)')
upper=np.degrees(np.arctan(1/np.maximum(mu,1e-10)));ax[1].plot(mu,upper,label='Must be below: arctan(1/mu)')
ax[1].fill_between(mu,np.degrees(np.arctan(mu)),upper,where=mu<1,color='#5aab80',alpha=.25,label='Ideal forward / return window')
ax[1].axhline(45,color='black',ls=':');ax[1].set(xlabel='Assumed friction coefficient',ylabel='Cam angle (degrees)',ylim=(0,90),title='Higher friction eventually prevents reset');ax[1].legend(fontsize=8)
fig.suptitle('Uncalibrated H58 mechanics; no measured snow waveform or return speed',fontsize=12);save(fig,'figure1_force_return')
fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained');wet=rows('wet_return.csv')
for mu in [.3,.6,.8]:
    v=[r for r in wet if float(r['angle_deg'])==45 and float(r['mu'])==mu and float(r['preload_uN'])==0]
    ax[0].plot([float(r['bridge_radius_um']) for r in v],[float(r['residual_offset_um']) for r in v],'o-',label=f'mu={mu}')
ax[0].axhline(1,color='black',ls='--',label='Assumed 1 um reset tolerance');ax[0].set(xlabel='Ideal liquid bridge radius (um)',ylabel='Residual offset (um)',title='High dissipation can leave a wet offset');ax[0].legend(fontsize=8)
q=rows('candidate_tolerance.csv')
for k,mu in enumerate([.3,.6,.8]):
    v=[float(r['residual_offset_um']) for r in q if float(r['mu'])==mu]
    ax[1].plot([k,k],[min(v),max(v)],lw=9,alpha=.5,color=['#3178ac','#cd772b','#ad4059'][k]);ax[1].scatter([k],[max(v)],color='black');ax[1].text(k,max(v)+.09,f'{max(v):.3f}',ha='center')
ax[1].axhline(1,color='black',ls='--');ax[1].set(xticks=[0,1,2],xticklabels=['0.3','0.6','0.8'],xlabel='Assumed friction coefficient',ylabel='Residual offset range (um)',title='Wide-beam candidate: tolerance corners',ylim=(0,2.7),xlim=(-.5,2.5))
fig.suptitle('50 C water tension, ideal adhesion force; candidate margin is only 0.017 um at mu=0.6',fontsize=12);save(fig,'figure2_wet_tolerance')
fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained');e=R['whole_grain_energy'];x=np.arange(3)
ax[0].bar(x-.17,[r['cam_only_loss_fraction']*100 for r in e],width=.34,label='Cam component')
ax[0].bar(x+.17,[r['combined_loss_fraction']*100 for r in e],width=.34,label='Cam + elastic H57 core')
ax[0].set(xticks=x,xticklabels=[r['mu'] for r in e],xlabel='Assumed friction coefficient',ylabel='Dissipated energy / input energy (%)',title='Component percentage is not whole-grain performance',ylim=(0,105));ax[0].legend(fontsize=8)
prices=[1000,3000,10000];base=R['additional_flexures_mass_kg'];cand=R['candidate']['additional_flexure_mass_kg']
ax[1].bar(x-.17,[base*p/1e6 for p in prices],width=.34,label='60 um wide beams')
ax[1].bar(x+.17,[cand*p/1e6 for p in prices],width=.34,label='120 um wide candidate')
ax[1].set(xticks=x,xticklabels=['1,000','3,000','10,000'],xlabel='Assumed raw material price (JPY/kg)',ylabel='Extra flexures only (million JPY)',title='2000 m2 x 0.45 m illustrative bed');ax[1].legend(fontsize=8)
fig.suptitle('Energy ratios are not success probabilities. Costs exclude pads, processing, tax and equipment.',fontsize=12);save(fig,'figure3_energy_cost')
print('3 PNG and 3 SVG generated')
