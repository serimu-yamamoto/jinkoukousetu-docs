from pathlib import Path
import sys, json, math
P=Path(__file__).resolve().parent
local_deps=P.parents[1]/'.deps'
if local_deps.exists(): sys.path.insert(0,str(local_deps))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=json.loads((P/'results.json').read_text(encoding='utf8'))
I=json.loads((P/'inputs.json').read_text(encoding='utf8'))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})
colors=['#136F8A','#E17C30','#6E4D94','#277C59']
fig,axes=plt.subplots(1,2,figsize=(12.8,5.2),layout='constrained')
ax=axes[0]
ref=R['thermal_reference'][0]
eta=np.logspace(1,4,300)
j=I['thermal']['residence_fraction_uncertainty']
lo=(ref['fine']['full_melt_s']+eta*0.5e-6/0.03)/(1-j)*1000
hi=ref['nominal_upper_s']*1000
ax.loglog(eta,lo,color=colors[0],lw=2,label='Lower: fine melt + shape-time scale')
ax.axhline(hi,color=colors[1],lw=2,label='Upper: support melting onset')
ax.fill_between(eta,lo,hi,where=lo<hi,color=colors[0],alpha=.15,label='Conditional nominal-time interval')
ax.axvline(ref['eta_limit_Pa_s'],color='#666666',ls=':',lw=1)
ax.text(0.03,.95,"""r fine = 0.5 um; r support = 10 um
T gas = 150 C; h = 500 W/(m2 K)
Residence uncertainty +/-20%""",transform=ax.transAxes,va='top',fontsize=9)
ax.set(xlabel='Assumed melt viscosity (Pa s)',ylabel='Nominal residence time (ms)',title='A. Heat selectivity is viscosity dependent',ylim=(4,400),xlim=(10,10000))
ax.legend(loc='lower right',fontsize=8)
ax.grid(alpha=.18,which='both')
ax=axes[1]
length=np.logspace(0,2.2,300)
for n,r in enumerate([.5,1,5]):
    ratio=8*.072*(length*1e-6)**2/(3*300e6*(r*1e-6)**3)
    valid=(length/r>=10)&(ratio<=.1)
    ax.loglog(length,ratio,color=colors[n],alpha=.32,ls='--',label=f'r = {r:g} um (no valid segment)' if not valid.any() else None)
    if valid.any(): ax.loglog(length[valid],ratio[valid],color=colors[n],lw=2.7,label=f'r = {r:g} um (valid segment)')
ax.axhline(.1,color='#555555',ls=':',label='Small-deflection cutoff')
ax.set(xlabel='Free branch length (um)',ylabel='Linear diagnostic: deflection / length',title='B. Wet bending penalizes long, fine branches',ylim=(1e-5,1e3),xlim=(1,160))
ax.text(.03,.96,"""E = 300 MPa; gamma = 0.072 N/m; b = 1
Solid segments require L/r >= 10 and d/L <= 0.1
Dashed extensions are outside the model domain.""",transform=ax.transAxes,va='top',fontsize=9)
ax.legend(loc='lower right',fontsize=8)
ax.grid(alpha=.18,which='both')
fig.suptitle('H27: uncalibrated single-branch diagnostics; not grain-production or snow-performance evidence',fontsize=12)
fig.savefig(P/'figure1_process_window.png',dpi=160)
plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(12.8,5.2),layout='constrained')
ax=axes[0]
y=np.linspace(.4,1,100)
for col,c in zip(colors,[.03,.05,.12,.18]):
    a=next(x for x in R['factory_cases'] if x['c']==c and x['yield_good']==.8 and x['recovery']==.999 and x['heat_recovery']==.7)
    ax.plot(y,a['cost_JPY_per_feed_kg']/y,color=col,lw=2,label=f'Polymer fraction {c:.0%}')
ax.axhline(500,color='#555555',ls='--',label='500 JPY/kg comparison only')
ax.scatter([.8],[R['factory_reference']['cost_JPY_per_good_kg']],color=colors[2],s=50,zorder=4)
ax.set(xlabel='Good grain yield (fraction)',ylabel='Hypothetical production cost (JPY/good kg)',title='A. Yield must carry the full production cost',xlim=(.4,1),ylim=(300,1200))
ax.text(.03,.96,"""Recovery 99.9%; assumed heat recovery 70%
New finishing / QC cost not established
Pretax; no vendor quotation""",transform=ax.transAxes,va='top',fontsize=9)
ax.legend(loc='upper right',bbox_to_anchor=(1,.73),fontsize=8)
ax.grid(alpha=.18)
ax=axes[1]
rec=np.linspace(.99,.9999,150)
s=(1-.12)/.12
ax.plot(rec*100,np.full_like(rec,s/.8),color=colors[0],lw=2,label='Solvent circulated / good kg')
ax.plot(rec*100,s*(1-rec)/.8,color=colors[1],lw=2,label='Makeup / good kg')
ax.set_yscale('log')
ax.set(xlabel='Solvent recovery (%)',ylabel='Solvent mass (kg / good kg)',title='B. Recovery saves makeup, not circulation',xlim=(99,99.99),ylim=(5e-4,20))
ax.text(.03,.72,"""Polymer fraction 12%; good yield 80%
Makeup is not an allowed release.
Initial 20,000 m2 bed: 1,080 t good product
30 days x 16 h: 2.25 t/h good product
and 20.6 t/h solvent circulation.""",transform=ax.transAxes,va='top',fontsize=9)
ax.legend(loc='lower left',fontsize=8)
ax.grid(alpha=.18,which='both')
fig.suptitle('H27: scenario economics for closed hydrocarbon flash processing; excludes wet antisolvent route',fontsize=12)
fig.savefig(P/'figure2_cost_and_circulation.png',dpi=160)
plt.close(fig)
print(json.dumps({'figures':['figure1_process_window.png','figure2_cost_and_circulation.png'],'matplotlib':matplotlib.__version__,'numpy':np.__version__}))
