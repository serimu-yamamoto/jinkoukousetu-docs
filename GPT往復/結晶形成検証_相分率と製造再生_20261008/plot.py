"""Original diagnostic figures generated from results; not measured performance."""
from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
R=json.loads((P/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130})
fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
rows=[r for r in R['route_balances'] if r['product_fraction']==1]
labels=['POM\n0.2 g/L','PLA spray\n2.5 g/L; y=.66','DBE25\n25 g/L','DBE50\n50 g/L','DBE100\n100 g/L']
bars=ax[0].bar(labels,[r['recipe_liquid_L_per_kg_product'] for r in rows],color=['#ad6552','#39758e','#6b8f70','#6b8f70','#6b8f70'])
ax[0].set_yscale('log');ax[0].set_ylim(5,14000)
for bar,row in zip(bars,rows):
 ax[0].text(bar.get_x()+bar.get_width()/2,bar.get_height()*1.15,f"{row['recipe_liquid_L_per_kg_product']:,.1f}",ha='center')
ax[0].set_ylabel('Integrated recipe liquid [L/kg collected product]')
ax[0].set_title('Dilution and collection yield dominate liquid duty')
ax[0].grid(axis='y',alpha=.2)
ax[0].text(.98,.95,'POM / DBE: ideal yield=1 assumed\nWashes and tank inventories excluded',transform=ax[0].transAxes,va='top',ha='right',fontsize=9)
for h in I['thermal']['sensible_heat_recovery_fractions']:
 rows=[r for r in R['thermal_regeneration_cases'] if r['sensible_recovery_fraction']==h]
 ax[1].loglog([r['processed_fraction']*100 for r in rows],[r['input_energy_kWh'] for r in rows],'o-',label=f'Sensible recovery {h:.0%}')
ax[1].set_xlabel('Bed mass processed per closure [%]')
ax[1].set_ylabel('Input electricity [kWh / closure]')
ax[1].set_title('H24-A: whole grain heats; low phase=10%')
ax[1].legend(loc='upper left');ax[1].grid(alpha=.2)
fig.suptitle('Cycle24 | Recipe / thermal bounds, not process or skiing validation',fontsize=13)
fig.savefig(P/'01_recipe_and_heat.png');plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
for eta in I['phase_drift']['conversion_fraction_per_heating']:
 n=list(range(101));low=[I['phase_drift']['initial_low_fraction']*(1-eta)**v*100 for v in n]
 ax[0].plot(n,low,label=f'Conversion {eta:.0%}/heating')
ax[0].axhline(5,color='#a34936',ls='--',label='Assumed minimum 5%')
ax[0].set_xlabel('Number of heating cycles of one particle')
ax[0].set_ylabel('Remaining low-melting mass [% of particle]')
ax[0].set_title('H24-A: conversion consumes the low-melting reserve')
ax[0].legend(fontsize=8,loc='upper right');ax[0].grid(alpha=.2)
for price in I['minority_phase']['prices_JPY_kg']:
 rows=[r for r in R['minority_material_costs'] if r['phase_JPY_kg']==price]
 ax[1].plot([r['fraction']*100 for r in rows],[r['remaining_annual_JPY']/1e6 for r in rows],'o-',label=f'Phase {price:,} JPY/kg')
ax[1].axhline(0,color='black',ls='--')
ax[1].axhline(1.3788,color='#a34936',ls=':',label='H24-B 5% phase: 1%/closure heat')
ax[1].set_xlabel('High-price phase replacing host mass [%]')
ax[1].set_ylabel('Annual margin before regeneration [million JPY]')
ax[1].set_title('Material and regeneration share the same allowance')
ax[1].legend(fontsize=8);ax[1].grid(alpha=.2)
fig.suptitle('Cycle24 | Unmeasured conversion rates and hypothetical costs',fontsize=13)
fig.savefig(P/'02_phase_and_cost.png');plt.close(fig)
print('Generated2figures; matplotlib '+matplotlib.__version__)
