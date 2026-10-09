from pathlib import Path
import sys,json,csv
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
R=json.loads((P/'results.json').read_text(encoding='utf-8'));I=json.loads((P/'inputs.json').read_text(encoding='utf-8'));B=I['baseline'];E=R['baseline_events']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'cycle60'})
def save(f,n):
 f.savefig(P/(n+'.png'),dpi=150,bbox_inches='tight');f.savefig(P/(n+'.svg'),bbox_inches='tight');plt.close(f)
f,ax=plt.subplots(figsize=(9,4.8));p=np.linspace(0,20,400);N=np.maximum(62.5*p+B['normal_adhesion_uN']-300,0)
ax.plot(p,.6*N+4,lw=2,color='#147e91',label='Static holding capacity with opener reaction')
ax.plot(p,.6*(62.5*p)+4,lw=1.5,ls='--',color='#888',label='Incorrect: ignoring opener unloading the contact')
ax.axhline(277.777778,color='#b55043',label='Reset spring force at x = 10 um')
for key,col,lab in [('first_slip_pressure_kPa','#b55043','Slip begins'),('opening_pressure_kPa','#147e91','Contact opens')]:
 ax.axvline(E[key],color=col,ls=':');ax.text(E[key]+.15,600,lab+'\n'+f'{E[key]:.2f} kPa',color=col,fontsize=9)
ax.set(xlim=(20,0),ylim=(0,800),xlabel='Imposed normal pressure during unloading (kPa)',ylabel='Tangential force per module (uN)');ax.legend(loc='upper left',fontsize=8);ax.grid(alpha=.15)
ax.set_title('A reset spring can initiate sliding before the contact opens',loc='left',fontweight='bold')
f.text(.12,-.025,'Hypothetical two-axis module at assumed 50 C properties. No automatic open-first sequence.',fontsize=9,color='#555');save(f,'figure1_contact_order')
rows=list(csv.DictReader((P/'coupled_unloading_path.csv').open(encoding='utf-8')));pp=[float(r['pressure_kPa']) for r in rows];x=[float(r['tangential_offset_um']) for r in rows];y=[float(r['normal_gap_um']) for r in rows]
f,axs=plt.subplots(1,2,figsize=(11,4.6))
axs[0].plot(pp,x,lw=2,color='#b55043',label='Remaining tangential offset x');axs[0].plot(pp,y,lw=2,color='#147e91',label='Normal separation y');axs[0].axhline(10,ls=':',color='#999',label='Assumed liquid bridge rupture gap')
axs[0].set(xlim=(20,0),ylim=(0,16),xlabel='Imposed normal pressure (kPa)',ylabel='Displacement (um)');axs[0].legend(fontsize=8,loc='upper left');axs[0].grid(alpha=.15)
axs[0].set_title('Permit sliding, then require bridge rupture',fontsize=11,loc='left')
j=list(csv.DictReader((P/'static_kinetic_jump.csv').open(encoding='utf-8')))
axs[1].plot([float(r['mu_kinetic_over_static']) for r in j],[float(r['unresolved_transient_energy_nJ']) for r in j],marker='o',color='#9b7033')
axs[1].set(xlabel='Kinetic / static friction coefficient ratio',ylabel='Unresolved first jump energy (nJ/module)',ylim=(0,None));axs[1].grid(alpha=.15)
axs[1].set_title('Do not count release energy as friction loss',fontsize=11,loc='left')
f.suptitle('H60-P: quasi-static path, with an unresolved dynamic jump',fontweight='bold',y=1.02);f.tight_layout();save(f,'figure2_coupled_path')
rows=list(csv.DictReader((P/'partial_component_cost.csv').open(encoding='utf-8')));c=[r for r in rows if r['raw_price_yen_kg']=='3000'];pos=np.arange(3);f,ax=plt.subplots(figsize=(9,5));bottom=np.zeros(3)
for field,col,lab in [('return_beam_mass_kg','#647a87','Tangential reset beams'),('opening_beam_mass_kg','#147e91','Normal opening beams'),('latch_allowance_mass_kg','#bda05c','Unverified latch volume allowance')]:
 v=np.array([float(r[field])*3000/1e6 for r in c]);ax.bar(pos,v,bottom=bottom,color=col,label=lab);bottom+=v
ax.set(xticks=pos,xticklabels=['H59 / H60-P\nno added latch','H60-L\nstiffer opener','H60-L\nweaker reset + stiffer opener'],ylabel='Partial raw material cost (million JPY)');ax.legend(fontsize=9,loc='upper left');ax.set_ylim(0,75);ax.set_title('Do not make a loaded latch mechanically or financially free',loc='left',fontweight='bold');ax.grid(axis='y',alpha=.15)
f.text(.12,-.025,'At assumed 3,000 JPY/kg. Excludes core, pads, frames, fabrication, yield loss, tax, plant and grooming equipment.',fontsize=8,color='#555');save(f,'figure3_partial_cost')
print('3 diagrams rendered; all curves are conditional calculations, not experiments')
