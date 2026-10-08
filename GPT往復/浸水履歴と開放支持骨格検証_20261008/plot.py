"""Reproduce two diagnostic figures; these are not material performance predictions."""
import json,sys,math
from pathlib import Path
P=Path(__file__).resolve().parent
local=P.parents[1]/'.deps'
if local.exists():sys.path.insert(0,str(local))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
R=json.loads((P/'results.json').read_text(encoding='utf8'))
I=json.loads((P/'inputs.json').read_text(encoding='utf8'))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})
fig,ax=plt.subplots(1,3,figsize=(15,4.8),layout='constrained')
a=R['membrane_shortcut_audit']; x=[v['diameter_um'] for v in a]
ax[0].errorbar(x,[v['entry_bar'] for v in a],yerr=[v['entry_error_bar'] for v in a],fmt='o',capsize=4,label='S1: measured saline entry')
ax[0].plot(x,[v['shortcut_bar'] for v in a],'s--',color='#c56b22',label='Unsafe shortcut (not calibrated)')
ax[0].set(xscale='log',yscale='log',xlabel='Nominal membrane pore diameter (um)',ylabel='Liquid entry pressure (bar)',title='A. Apparent angle is not a pore calibration')
from matplotlib.ticker import FixedLocator, FixedFormatter, NullFormatter
ax[0].xaxis.set_major_locator(FixedLocator(x)); ax[0].xaxis.set_major_formatter(FixedFormatter([str(v) for v in x])); ax[0].xaxis.set_minor_formatter(NullFormatter())
ax[0].legend(fontsize=8,loc='upper right');ax[0].grid(alpha=.2)
seq=I['scenarios']['pressure_cycle_kPa']; times=range(len(seq))
ax[1].plot(times,seq,'ko-',label='Imposed water minus air pressure')
h=[v for v in R['pressure_histories'] if v['temperature_C']==50 and v['diameter_um']==10]
ax[1].axhline(h[0]['advancing_threshold_Pa']/1000,color='#8c5fb3',ls='--',label='Entry: advancing 120 deg')
for row,col in zip(h,['#2878a4','#c45a26']):
    ax[1].axhline(row['receding_threshold_Pa']/1000,color=col,ls=':',label=f"Release: receding {row['receding_deg']} deg")
ax[1].set(xlabel='History step (not elapsed time)',ylabel='Pressure difference (kPa)',title='B. Ideal 10 um cylinder, pure water, 50 C',xticks=list(times));ax[1].legend(fontsize=8,loc='upper right');ax[1].grid(alpha=.2)
for j,(row,col) in enumerate(zip(h,['#2878a4','#c45a26'])):
    states=[int(v['wet']) for v in row['states']]
    ax[2].plot(times,states,'o--' if j else 'o-',color=col,markerfacecolor='none' if j else col,label=f"Receding {row['receding_deg']} deg")
ax[2].set(ylim=(-.15,1.22),xlabel='History step (state after pressure change)',ylabel='Pore state',yticks=[0,1],yticklabels=['Dry','Wet'],xticks=list(times),title='C. After rain: hysteresis can retain water')
ax[2].legend(fontsize=9);ax[2].grid(alpha=.2)
fig.suptitle('Cycle 30 | Published observations and ideal pressure-history counterexamples',fontsize=14)
fig.savefig(P/'figure1_wetting_history.png');plt.close(fig)
fig,axes=plt.subplots(2,2,figsize=(13,9),layout='constrained')
coords={'in':(0,0),'upper':(1,1),'lower':(1,-1),'out':(2,0)}
for axis,net in zip(axes[0],R['network_counterexamples']):
    for (u,v,pressure),d in zip(net['edges'],net['diameters_um']):
        x0,y0=coords[u];x1,y1=coords[v];axis.plot([x0,x1],[y0,y1],lw=5 if d==30 else 2,color='#2878a4' if d==30 else '#ce7334')
        axis.text((x0+x1)/2,(y0+y1)/2+.14,f'{d} um',ha='center',bbox={'facecolor':'white','edgecolor':'none','alpha':.9})
    for k,(x,y) in coords.items():axis.scatter(x,y,s=80,c='#40464d',zorder=4);axis.text(x,y-.21,k,ha='center')
    axis.set(xlim=(-.3,2.3),ylim=(-1.6,1.6),title=f"Same pore counts, {net['name']} paths\nBreakthrough {net['breakthrough_Pa']/1000:.2f} kPa")
    axis.set_axis_off();axis.text(1,1.45,'Ideal 50 C, intrinsic advancing angle 120 deg',ha='center',fontsize=9)
axis=axes[1,0];p0=I['scenarios']['initial_gas_pressure_Pa'];eps=np.linspace(0,.55,100)
for k,ls in [(1,'-'),(1.4,'--')]:axis.plot(eps,p0*((.9/(.9-eps))**k-1)/1000,ls,label=f'Polytropic exponent {k}')
axis.set(xlabel='Cell compression (constant section, solid fraction 0.1)',ylabel='Excess cell gas pressure (kPa)',title='Sealed-cell gas: a thermodynamic scale only')
axis.text(.02,.94,'NOT macroscopic foam stress\nNo leakage, skeleton buckling or water',transform=axis.transAxes,va='top',fontsize=9)
axis.legend(loc='lower right',fontsize=9);axis.grid(alpha=.2)
axis=axes[1,1];f=next(r for r in R['factory'] if r['area_m2']==2000 and r['yield_assumed']==1)
axis.bar([0],[f['one_stage_occupied_m3']],color='#667888',label='Single saturation: 9 h')
axis.bar([1],[f['pretreatment_occupied_m3']],color='#2878a4',label='Pretreatment: 12 h')
axis.bar([1],[f['second_stage_occupied_m3']],bottom=[f['pretreatment_occupied_m3']],color='#ce7334',label='Second saturation: 2 h')
for x,v in [(0,f['one_stage_occupied_m3']),(1,f['two_stage_occupied_m3'])]:axis.text(x,v+.08,f'{v:.2f}',ha='center')
axis.set(xticks=[0,1],xticklabels=['One stage','Two stages'],ylabel='Sum of material-occupied inventory (m3)',ylim=(0,4.8),title='225 kg/h: count every saturation stage')
axis.legend(loc='upper left',fontsize=8);axis.text(.02,.02,'Not vessel size, price, or equal product quality.\nYield 100%; excludes drying / molding / handling.',transform=axis.transAxes,fontsize=8)
fig.suptitle('Cycle 30 | Connectivity, gas dependence and factory inventory',fontsize=14)
fig.savefig(P/'figure2_structure_and_process.png');plt.close(fig)
print('Rendered 2 diagnostic figures; physical tests = 0')
