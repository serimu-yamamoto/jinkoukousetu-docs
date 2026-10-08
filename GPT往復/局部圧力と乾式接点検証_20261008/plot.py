from pathlib import Path
import json,sys
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.grid':True,'grid.alpha':.2,'figure.dpi':160})
R=json.loads((P/'results.json').read_text());I=json.loads((P/'inputs.json').read_text())
fig,ax=plt.subplots(1,2,figsize=(12,5),layout='constrained')
labels=['Initial rotating fit','Late rotating fit','Oscillating fit'];colors=['#d95f02','#1d6996','#0f8554']
for p,label,color in zip(I['source_fits']['pom_pe_parameters'],labels,colors):
 c=[q for q in R['pressure_bounds'] if q['label']==p['label']]
 ax[0].plot([q['local_pressure_cap_Pa']/1e6 for q in c],[q['total_lower_bound'] for q in c],'-o',label=label,color=color)
ax[0].axhline(.1,color='#555',ls='--',label='Illustrative total budget')
ax[0].set(xlabel='Hypothetical maximum local pressure (MPa)',ylabel='Conditional lower bound on total COF',title='Pressure cannot remove the interfacial shear floor')
ax[0].legend(fontsize=8)
for cap,color in zip([5e6,1e7,2e7,4e7],['#1d6996','#0f8554','#d95f02','#a1387a']):
 c=[q for q in R['inverse_tau0_limits'] if q['local_pressure_cap_Pa']==cap]
 ax[1].plot([q['beta'] for q in c],[q['maximum_tau0_Pa']/1e6 for q in c],'-o',color=color,label=f'Pressure cap {cap/1e6:g} MPa')
ax[1].set(xlabel='Pressure-proportional shear coefficient beta',ylabel='Maximum permitted tau0 in this model (MPa)',title='Necessary material requirements, not achieved values')
ax[1].legend(fontsize=8)
fig.suptitle('H33 source-fit stress test and inverse requirements\nOther resistance = 0.02 assumed; source fits are NOT 50 C / ski-scale calibration',fontsize=12)
fig.savefig(P/'figure1_pressure_bound.png');plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,5),layout='constrained')
ks=[100,1000,100000,None];xs=range(4)
for radius,color in [(50e-6,'#d95f02'),(.0005,'#1d6996')]:
 c=[next(q for q in R['geometry_cases'] if q['radius_m']==radius and q['height_half_range_m']==25e-6 and q['root_stiffness_N_m']==k) for k in ks]
 for a,key,scale in [(ax[0],'max_local_peak_pressure_Pa',1e-6),(ax[1],'real_area_m2',1e6)]:
  a.plot(list(xs),[q[key]*scale for q in c],'-',color=color,label=f'Crown curvature radius {radius*1e6:g} um')
  for x,q in zip(xs,c): a.scatter(x,q[key]*scale,marker='o' if q['small_contact_screen'] else 'x',color=color,s=50,zorder=4)
ax[0].set(ylabel='Maximum local Hertz pressure (MPa)',title='Compliant roots reduce concentration')
ax[1].set(ylabel='Total real contact area (mm2)',title='More load sharing enlarges the adhesive contact')
for a in ax:
 a.set_xticks(list(xs),['100','1,000','100,000','Rigid']);a.set_xlabel('Hypothetical root stiffness (N/m)');a.legend(fontsize=8)
fig.suptitle('H33 hypothetical contact geometry: 400 N, height range +/- 25 um, E* = 0.5 GPa\nx: a/R > 0.1 screening flag; o: passes geometry screen only, not yielding or wear',fontsize=12)
fig.savefig(P/'figure2_contact_sharing.png');plt.close(fig)
print('Saved two original model figures')
