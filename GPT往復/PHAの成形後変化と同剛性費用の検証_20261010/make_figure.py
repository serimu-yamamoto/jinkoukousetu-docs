from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent
D=P.parents[1]/'.research97/deps'
if D.exists():sys.path.insert(0,str(D))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
r=json.loads((P/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(14,5.7),layout='constrained')
colors=['#0072B2','#D55E00'];age=np.geomspace(1,200,400)
for m,c in zip(I['source']['materials'],colors):
 b=m['power_exponent'];u=m['exponent_reported_plus_minus'];dr=lambda n:100*((1+8/age)**n-1)
 axes[0].plot(age,dr(b),color=c,label=m['name'])
 axes[0].fill_between(age,dr(b-u),dr(b+u),color=c,alpha=.17)
axes[0].axhline(2,color='#555555',ls=':',label='Assumed 2% drift limit')
axes[0].axvline(72,color='#555555',ls='--',lw=1)
axes[0].set(xscale='log',yscale='log',xlabel='Age at start of 8-hour interval (hours)',ylabel='Predicted modulus increase (%)',title='A. Aging-fit interpolation; NOT a 50 C service prediction',ylim=(.2,70))
axes[0].legend(loc='upper right',fontsize=9);axes[0].grid(alpha=.15,which='both')
E=np.geomspace(200,1600,200);pmax=500*930/1210*(E/200)**(1/3)
axes[1].plot(E,pmax,color='#009E73',lw=2)
for row in r['raw_price_ceilings']:
 if row['material']=='PHBHHx':
  axes[1].scatter(row['assumed_E50_MPa'],row['max_raw_price_JPY_kg_for_parity'],color='#009E73')
  axes[1].annotate(f"{row['max_raw_price_JPY_kg_for_parity']:.0f}",(row['assumed_E50_MPa'],row['max_raw_price_JPY_kg_for_parity']),xytext=(5,-15),textcoords='offset points',fontsize=10)
axes[1].axhline(1000,color='#999999',ls='--',label='Assumed 1,000 JPY/kg scenario')
axes[1].set(xlabel='Assumed PHA modulus at 50 C (MPa)',ylabel='PHA raw-price ceiling (JPY/kg, tax excluded)',title='B. Equal bending stiffness: raw resin cost parity',ylim=(250,1150),xlim=(150,1720))
axes[1].text(.04,.94,'PE reference assumptions:\nE50 = 200 MPa, density = 930 kg/m3,\nraw price = 500 JPY/kg\nPHA density = 1210 kg/m3',transform=axes[1].transAxes,va='top',fontsize=10,bbox={'facecolor':'white','edgecolor':'none','alpha':.95})
axes[1].legend(loc='lower right',fontsize=9);axes[1].grid(alpha=.15)
fig.suptitle('H97: control post-forming drift, then qualify geometry and cost',fontsize=15)
fig.savefig(P/'aging_and_price_bounds.png',dpi=160)
print(json.dumps({'figures':1,'experimental_product_data':False}))
