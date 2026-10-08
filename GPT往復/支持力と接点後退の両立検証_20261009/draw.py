"""Reproducible scientific plots of assumed models; no experimental data."""
import csv, json, sys
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','figure.dpi':150})
def rows(name):return list(csv.DictReader((P/name).open(encoding='utf-8')))
R=json.loads((P/'results.json').read_text(encoding='utf-8'))
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
C=I['cell']; theta0=np.deg2rad(C['theta0_deg'])
def save(fig,name):
    fig.savefig(P/(name+'.png'),bbox_inches='tight')
    fig.savefig(P/(name+'.svg'),bbox_inches='tight')
    plt.close(fig)
# Projected pressure is based on a square nominal footprint, not a bed stress prediction.
a=rows('hinge_force.csv'); fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
for E in I['hinge_moduli_MPa']:
    v=[r for r in a if float(r['modulus_MPa'])==E and float(r['strain'])>0]
    ax[0].plot([float(r['strain'])*100 for r in v],[float(r['projected_pressure_kPa']) for r in v],marker='o',label=f'Hinge E = {E:g} MPa')
ax[0].axhline(20,color='black',ls='--',label='20 kPa design scenario')
ax[0].set(yscale='log',xlabel='Cell shortening (%)',ylabel='Projected pressure (kPa)',title='Thin hinges alone: low load capacity')
ax[0].legend(fontsize=8,loc='lower right')
x=np.linspace(0,15,121); e=x/100; theta=np.arcsin((1-e)*(C['a']+np.sin(theta0))-C['a']); w=2*R['geometry']['L_um']*1e-6*np.cos(theta)
ph=C['hinges']*R['hinge_design_point']['hinge_k_Nm_rad']*(theta0-theta)/w/R['geometry']['footprint_m2']/1000
for retention in [.25,.5,.75,1]:
    p=ph+retention*R['core_stiffness_N_m']*e*R['geometry']['H0_um']*1e-6/R['geometry']['footprint_m2']/1000
    ax[1].plot(x,p,label=f'Core stiffness retained: {retention:.0%}')
ax[1].axhline(20,color='black',ls='--');ax[1].axvline(R['fixed_center_release_threshold_strain']*100,color='#91702a',ls=':',label='Fixed-center opening threshold')
ax[1].set(xlabel='Cell shortening (%)',ylabel='Projected pressure (kPa)',title='Core + hinges: finite operating window',ylim=(0,33))
ax[1].legend(fontsize=8,loc='upper left')
fig.suptitle('H57 screening only: 50 C material properties are assumptions',fontsize=13)
save(fig,'figure1_force_window')
# Geometric interference and the independently idealized gas support alternative.
a=rows('core_clearance.csv'); fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
for b in I['core']['widths_um']:
    v=[r for r in a if float(r['core_width_um'])==b and float(r['poisson'])==.3]
    ax[0].plot([float(r['strain'])*100 for r in v],[float(r['side_gap_um']) for r in v],marker='o',label=f'Core width {b} um')
ax[0].axhline(10,color='black',ls='--',label='Assumed 10 um margin');ax[0].axvspan(15,20,color='gray',alpha=.12)
ax[0].set(xlabel='Cell shortening (%)',ylabel='Clearance on each side (um)',title='Core bulging can block contact retreat',xlim=(0,20))
ax[0].legend(fontsize=8)
g=rows('gas_core.csv')
for label,key in [('Equilibrated at 50 C','operating_temperature_equilibrated'),('Sealed at 23 C; heated at fixed volume','sealed_at_23C_fixed_volume_heated_to_50C')]:
    v=[r for r in g if r['assembly_case']==key]
    ax[1].plot([float(r['strain'])*100 for r in v],[float(r['projected_support_kPa']) for r in v],marker='o',label=label)
ax[1].axhline(20,color='black',ls='--',label='20 kPa scenario');ax[1].axvspan(15,20,color='gray',alpha=.12)
ax[1].set(xlabel='Cell shortening (%)',ylabel='Gas-only projected support (kPa)',title='Gas support is not a free replacement',xlim=(0,20))
ax[1].legend(fontsize=8,loc='upper left')
fig.suptitle('Uncalibrated clearance / ideal-gas models; shaded region exceeds chosen travel',fontsize=12)
save(fig,'figure2_clearance_gas')
# Raw material component only, not a quotation for a course or equipment.
a=rows('core_cost.csv'); fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
widths=I['core']['widths_um'];prices=I['cost']['core_prices_yen_kg'];xx=np.arange(len(widths))
for k,price in enumerate(prices):
    v=[next(float(r['core_only_cost_yen'])/1e6 for r in a if float(r['core_width_um'])==b and float(r['core_price_yen_kg'])==price) for b in widths]
    ax[0].bar(xx+(k-1)*.24,v,width=.24,label=f'{price:,} JPY/kg')
ax[0].set(xticks=xx,xticklabels=widths,xlabel='Core width (um)',ylabel='Core-only material cost (million JPY)',title='2000 m2 x 0.45 m; envelope packing = 0.55')
ax[0].legend(fontsize=8)
req=[];mass=[]
cr=rows('core_clearance.csv')
for b in widths:
    req.append(float(next(r for r in cr if float(r['core_width_um'])==b)['core_modulus_required_kPa']))
    mass.append(float(next(r for r in a if float(r['core_width_um'])==b)['total_core_mass_kg'])/1000)
ax[1].plot(widths,req,'o-',color='#276c9e',label='Required effective modulus')
ax[1].set(xlabel='Core width (um)',ylabel='Effective core modulus (kPa)',title='Smaller core: less mass, higher required modulus')
ax2=ax[1].twinx();ax2.plot(widths,mass,'s--',color='#ad572b');ax2.set_ylabel('Core mass (t)',color='#ad572b');ax[1].set_ylim(0,600);ax2.set_ylim(0,40)
fig.suptitle('Component cost sensitivity: excludes cage, coating, manufacturing, tax, equipment and civil works',fontsize=11)
save(fig,'figure3_component_cost')


fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
e=np.linspace(0,.15,401); theta=np.arcsin((1-e)*(C['a']+np.sin(theta0))-C['a']); w=2*R['geometry']['L_um']*1e-6*np.cos(theta); d=e*R['geometry']['H0_um']*1e-6
ph=C['hinges']*R['hinge_design_point']['hinge_k_Nm_rad']*(theta0-theta)/w/R['geometry']['footprint_m2']/1000
pr=R['progressive_core']; Fcore=pr['soft_stiffness_N_m']*d+pr['added_stiffness_N_m']*np.maximum(0,d-pr['transition_shortening_um']*1e-6)
for retention in [.5,.75,1]:ax[0].plot(e*100,ph+retention*Fcore/R['geometry']['footprint_m2']/1000,label=f'Two-stage, retained {retention:.0%}')
ax[0].plot(e*100,ph+R['core_stiffness_N_m']*d/R['geometry']['footprint_m2']/1000,'--',color='gray',label='Linear core reference')
ax[0].scatter([pr['transition_cell_strain']*100,15],[5,100],color='black',zorder=5,label='Inverse design constraints')
ax[0].set(xlabel='Cell shortening (%)',ylabel='Projected pressure (kPa)',title='Two-stage support: specified curve, not measured',xlim=(0,15),ylim=(0,108));ax[0].legend(fontsize=8)
for qq in [1.04,1.09,1.25,1.5]:
    gap=(R['geometry']['W0_um']/np.sqrt(qq)-w*1e6)
    ax[1].plot(e*100,gap,label=f'Fixed-center density ratio q = {qq}')
ax[1].axhline(0,color='black',lw=1);ax[1].axhline(10,color='#91702a',ls='--',label='Assumed 10 um release margin')
ax[1].set(xlabel='Cell shortening (%)',ylabel='Pair clearance (um; negative = overlap)',title='Dense packing defeats the same support curve',xlim=(0,15));ax[1].legend(fontsize=8)
fig.suptitle('H57-B: smooth transitions, fatigue, 3D orientation and wet friction remain untested',fontsize=12)
save(fig,'figure4_progressive_support')

print('4 PNG and 4 SVG generated; no measured performance represented')
