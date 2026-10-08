from pathlib import Path
import json,sys
root=Path(__file__).resolve().parent
deps=root.parents[1]/'.deps'
if deps.exists(): sys.path.insert(0,str(deps))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
r=json.loads((root/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white'})
fig,ax=plt.subplots(1,2,figsize=(13,5.3),layout='constrained')
press=[r['reference_machine']['nominal_pressure_Pa']/1e6]+[x['pressure_MPa'] for x in r['roller_pressure_budget']]
labels=['4 t roller\nnominal','5 MPa','10 MPa','34.5 MPa','50 MPa']
ax[0].bar(labels,press,color=['#15847d']+['#b65c47']*4)
ax[0].set_yscale('log');ax[0].set_ylabel('Nominal pressure (MPa)');ax[0].set_title('Reference footprint = 20 m x 0.05 m')
for i,v in enumerate(press):ax[0].text(i,v*1.12,f'{v:.3g}',ha='center')
ax[0].set_ylim(.015,130);ax[0].grid(axis='y',alpha=.2)
labels2=['Roller dwell','Fresh film\n(S3)','Repress\nFig. 4 (S3)','Initial film\nFig. 2/4 (S3)']
times=[r['reference_machine']['contact_time_s'],300,3600,50400]
ax[1].bar(labels2,times,color=['#15847d','#8292b1','#b65c47','#6f6b77'])
ax[1].set_yscale('log');ax[1].axhline(2400,color='#333333',ls='--',label='40 min available (assumed)')
ax[1].set_ylim(.025,200000);ax[1].set_ylabel('Time (s)');ax[1].set_title('Different operations: these are not interchangeable')
for i,v in enumerate(times):ax[1].text(i,v*1.2,f'{v:g} s',ha='center')
ax[1].legend(loc='upper left',fontsize=9);ax[1].grid(axis='y',alpha=.2)
fig.suptitle('H36 | Low-temperature pressing evidence does not establish on-slope recovery',fontsize=15)
fig.savefig(root/'figure1_pressure_and_time.png',dpi=160);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(13,5.2),layout='constrained')
for scope,label,col in [('whole_attached_particle','Whole attached particles','#b65c47'),('phase_only_if_separable','Phase only: separation NOT established','#15847d')]:
    rows=[x for x in r['processing_budgets'] if x['area_m2']==2000 and x['phase_fraction']==.02 and x['scope']==scope and x['assumed_dwell_s']==3600 and x['available_s']==28800]
    rows.sort(key=lambda x:x['repair_fraction'])
    xx=[x['repair_fraction']*100 for x in rows]
    ax[0].plot(xx,[x['processed_kg'] for x in rows],'o-',color=col,label=label)
    ax[1].plot(xx,[x['annual_allowance_JPY_kg'] for x in rows],'o-',color=col,label=label)
for a in ax:a.set_xscale('log');a.set_yscale('log');a.set_xlabel('Fraction of inventory reprocessed per event (%)');a.grid(alpha=.2)
ax[0].set_ylabel('Feed to regeneration process (kg / event)');ax[0].set_title('2,000 m2 bed; 2% phase in final mass');ax[0].legend(fontsize=9)
ax[1].set_ylabel('Allowable ALL-IN regeneration cost (JPY / kg)');ax[1].set_title('Illustrative allowance: 1 million JPY / year; 200 events')
fig.suptitle('H36 | Counting only a 2% phase understates attached-particle processing mass by 50x',fontsize=14)
fig.savefig(root/'figure2_inventory_and_allowance.png',dpi=160);plt.close(fig)
print('2 figures written')
