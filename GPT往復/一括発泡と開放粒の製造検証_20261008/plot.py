from pathlib import Path
import json, sys
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
I=json.loads((P/'inputs.json').read_text(encoding='utf-8')); R=json.loads((P/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white'})
fig,ax=plt.subplots(1,2,figsize=(12,4.6),layout='constrained')
s=np.linspace(0,1,200)
for rho in [50,120,240,400]:
    m=450*rho; vp=450-m/1250
    ax[0].plot(s*100,(m+1000*vp*s)/1000,label=f'{rho} kg/m³ dry envelope',lw=2)
    ax[1].plot(s*100,(rho+(1-rho/1250)*1000*s)/1000,lw=2)
ax[0].scatter([0,10,50,100],[108,144.36,289.8,471.6],color='#dc6b20',zorder=5)
ax[0].set(xlabel='Retained water / internal pore volume (%)',ylabel='Material + retained water lifted (t)',title='A. Same 2,000 m² × 0.45 m bed; 50% envelopes')
ax[0].legend(fontsize=8,loc='upper left');ax[0].grid(alpha=.2)
ax[1].axhline(1,color='black',ls='--',lw=1,label='neutral free immersion')
ax[1].axvline(100*95/101,color='#dc6b20',ls=':',label='240 kg/m³: 94.1% filled')
ax[1].set(xlabel='Internal pores filled with water (%)',ylabel='Envelope-average mass / displaced water mass',title='B. Ideal free immersion with trapped air')
ax[1].legend(fontsize=8,loc='lower right');ax[1].grid(alpha=.2)
fig.suptitle('Assumed geometry: dry solid 1,250 kg/m³. Not measured rain uptake or slope stability.',fontsize=11)
fig.savefig(P/'figure1_water_and_buoyancy.png',dpi=160);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,4.6),layout='constrained')
labels=['DCM circulation','Water, low wash','Water, high wash']
vals=[2400,96800,336800]
ax[0].barh(labels,vals,color=['#417caa','#6bafbd','#276d7a'])
ax[0].set_xscale('log');ax[0].set_xlim(1e3,1e6)
for k,v in enumerate(vals): ax[0].text(v*1.05,k,f'{v:,.0f}',va='center',fontsize=9)
ax[0].set(xlabel='Cumulative liquid throughput (m³), log scale',title='A. Laboratory recipe scaled to 108 t good material')
ax[0].text(.02,-.25,'90% good yield; no solvent/water reuse credited.\nCirculation volume is not tank size or fresh purchase.',transform=ax[0].transAxes,fontsize=9)
for yy,c in [(0.5,'#b6474d'),(0.7,'#e0a549'),(0.9,'#417caa')]:
    prices=np.linspace(100,1500,200)
    ax[1].plot(prices,108000/yy*prices/1e6,label=f'{yy:.0%} good yield',color=c,lw=2)
ax[1].axhline(50,color='black',ls='--',lw=1,label='JPY 50 M example allocation')
ax[1].set(xlabel='Raw feed price (JPY/kg), assumed',ylabel='Initial raw-material purchase (JPY million)',title='B. Processing, plant, transport and tax excluded')
ax[1].legend(fontsize=8);ax[1].grid(alpha=.2)
fig.suptitle('Manufacturing sensitivities, not quotations or a funded construction budget.',fontsize=11)
fig.savefig(P/'figure2_process_and_cost.png',dpi=160);plt.close(fig)
print('Saved 2 diagnostic figures.')
