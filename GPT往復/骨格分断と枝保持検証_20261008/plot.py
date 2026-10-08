from pathlib import Path
import json,sys,csv
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'));R=json.loads((P/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':10,'figure.facecolor':'white','axes.spines.top':False,'axes.spines.right':False})
rows=list(csv.DictReader((P/'beam_profiles.csv').open(encoding='utf-8')))
fig=plt.figure(figsize=(14,4.7),layout='constrained');ax1=fig.add_subplot(131);ax2=fig.add_subplot(132);ax3=fig.add_subplot(133,projection='3d')
colors={0:'#68869b',1:'#1f77b4',5:'#c76b27'}
for a in [0,1,5]:
 rr=[x for x in rows if float(x['a'])==a and float(x['N_over_V'])==0]
 x=np.array([float(z['x_over_L']) for z in rr]);rad=[float(z['r_um']) for z in rr];stress=[float(z['surface_normal_MPa']) for z in rr]
 ax1.plot(x,rad,color=colors[a],label=f'a={a}',lw=2);ax2.plot(x,stress,color=colors[a],lw=2)
ax1.set(xlabel='Position x / L',ylabel='Radius (µm)',title='A. Same strut volume; L = 600 µm');ax1.legend();ax1.grid(alpha=.2)
ax2.axvspan(.4,.6,color='#a3c38f',alpha=.2);ax2.set(xlabel='Position x / L',ylabel='Surface bending stress (MPa)',title='B. Parallel-end sidesway; V = 0.1 mN');ax2.grid(alpha=.2)
vec=np.array([[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]])/np.sqrt(3)*300
for i,v in enumerate(vec):
 ax3.plot([0,v[0]],[0,v[1]],[0,v[2]],color='#1f77b4',lw=5);ax3.scatter(*v,color='#c76b27',s=30)
ax3.scatter(0,0,0,s=120,color='#34495e');ax3.set(xlabel='µm',ylabel='µm',zlabel='µm',title='C. Ideal four-arm node after midpoint cuts')
ax3.set_box_aspect((1,1,1));ax3.view_init(22,35)
fig.suptitle('Stress diagnostic and schematic centerlines; no measured fracture strength or ski performance.',fontsize=11)
fig.savefig(P/'figure1_cut_location_and_node.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
pp=np.linspace(.65,1,200);ax[0].plot(pp*100,pp**4*100,'k--',label='p⁴: independent-cut isolated-node expectation')
for mode,color,label in [('uniform','#c76b27','Cuts anywhere along a strut'),('central_band','#1f77b4','Cuts prescribed within central 20%')]:
 rr=[x for x in R['network']['summary'] if x['mass_profile_a']==1 and x['mode']==mode and x['removed_length_fraction']==.05 and x['p_input']>0]
 ax[0].plot([x['p_input']*100 for x in rr],[x['geometry_only_mass_fraction_mean']*100 for x in rr],'o-',color=color,label=label)
 ax[0].fill_between([x['p_input']*100 for x in rr],[x['geometry_only_mass_fraction_min']*100 for x in rr],[x['geometry_only_mass_fraction_max']*100 for x in rr],color=color,alpha=.15)
ax[0].set(xlabel='Input probability of cutting each strut (%)',ylabel='Isolated nodes or geometric retained mass (%)',title='A. Geometry ledger; a = 1, kerf length = 5% L')
ax[0].legend(fontsize=8,loc='upper left');ax[0].grid(alpha=.2)
for mode,color,label in [('uniform','#c76b27','Uniform cut locations'),('central_band','#1f77b4','Central-band cut locations')]:
 rr=[x for x in R['cost'] if x['mass_profile_a']==1 and x['p_input']==.9 and x['mode']==mode]
 ax[1].plot([x['passes'] for x in rr],[x['JPY_per_good_kg'] for x in rr],'o-',color=color,label=label)
ax[1].set(xlabel='Passes, assuming full network remanufacture each pass',ylabel='Raw + assumed processing (JPY/geometric-good kg)',title='B. a = 1; raw 600 + process 100 JPY/kg')
ax[1].set_xticks([1,2,3,4]);ax[1].legend(fontsize=9);ax[1].grid(alpha=.2)
fig.suptitle('Prescribed cut locations and arbitrary arm gate. Fractions are NOT physical success probabilities.',fontsize=11)
fig.savefig(P/'figure2_fragment_mass_and_reprocessing.png',dpi=150);plt.close(fig)
print('Two figures saved.')
