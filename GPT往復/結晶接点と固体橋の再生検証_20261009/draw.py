from pathlib import Path
import sys,csv,json,math
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle,FancyBboxPatch,FancyArrowPatch
import numpy as np
R=json.loads((P/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'cycle62'})
teal='#007f86';orange='#ca672b';purple='#7756a5'
def save(fig,name):
    fig.savefig(P/(name+'.png'),dpi=160,bbox_inches='tight',facecolor='white')
    fig.savefig(P/(name+'.svg'),bbox_inches='tight',facecolor='white',metadata={'Date':None});plt.close(fig)
def box(ax,x,y,w,h,t,col=teal):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.01',edgecolor=col,facecolor='#f3f7f7',lw=1.4))
    ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=11,linespacing=1.5)
fig,ax=plt.subplots(figsize=(12,7));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
ax.text(.01,.97,'H62: put the bridge material at contacts, then prove wet strength',fontsize=17,weight='bold')
box(ax,.02,.62,.28,.23,'A. Grow crystals from solution\nMg-bicarbonate / degassing\nRate and phase stability unverified',orange)
box(ax,.36,.62,.28,.23,'B. Assemble preformed fines\nCapillary flow + drying\nAvoid waiting for crystal growth',teal)
box(ax,.70,.62,.28,.23,'C. Thermally weld foam beads\nFactory comparator\nDoes not prove bonding at 50 C',purple)
for x in [.16,.5,.84]:ax.add_patch(FancyArrowPatch((x,.61),(.5,.49),arrowstyle='-|>',mutation_scale=15,lw=1.2,color='#68777b'))
box(ax,.21,.32,.58,.15,'Reusable porous carrier + small breakable bridges\nForce, fracture work, feed water and debris must all balance')
ax.text(.03,.26,'Nominal inverse design only:',weight='bold',fontsize=12,va='top')
ax.text(.03,.19,'500 um carrier; 10 um bridge length; 6.15 um bridge radius\nEffective bridge strength 10 MPa is ASSUMED, not a source measurement.',fontsize=11,va='top')
ax.text(.03,.065,'Not a CAD / built material. Route B is assembly, not warm-air crystallization.\nNo exposed fine-powder spraying or direct transfer of silica/clay safety claims.',fontsize=10,color='#5b6367',va='top')
save(fig,'01_routes')
fig,axs=plt.subplots(1,2,figsize=(12,5.8),layout='constrained');fig.suptitle('A coupled requirement: wet bridge strength x contact selectivity',fontsize=16,weight='bold')
et=np.logspace(-2,0,150)
for req,label,col,ls in [(1.35,'50 wt% solids; ideal load sharing',teal,'-'),(2.7,'50 wt% solids; half load sharing',purple,'--'),(5.4,'20 wt% solids; ideal load sharing',orange,':')]:
    axs[0].loglog(et,req/et,label=label,color=col,ls=ls,lw=2)
axs[0].axhline(10,color='#777',ls=':',lw=1);axs[0].plot(.25,10,'o',color='#222',ms=7)
axs[0].annotate('assumed nominal point',(.25,10),xytext=(.08,3),arrowprops={'arrowstyle':'->'},fontsize=9)
axs[0].set(xlim=(.01,1),ylim=(1,700),xlabel='Fraction of feed forming useful contacts',ylabel='Minimum effective wet bridge strength (MPa)',title='A. Boundary for 40 min water-energy budget')
axs[0].legend(fontsize=8,loc='upper right');axs[0].grid(alpha=.15)
vals=[R['nominal_solution']['retained_water_kg'],R['nominal_solution']['retained_water_kg']*.01,R['nominal_slurry']['carrier_water_kg'],R['uniform_coating_null']['total_solid_kg']]
labels=['A: all\ncarrier water','A: 1% water\nretained','B: 50 wt%\nselective','B: uniform\ncoating model']
axs[1].bar(range(4),vals,color=[orange,'#e6a981',teal,'#88a6a8']);axs[1].set_xticks(range(4),labels)
axs[1].set(yscale='log',ylabel='Water to remove (kg / whole 2000 m^2 bed)',title='B. Drying load depends on localization and drainage')
axs[1].axhline(200,color='#222',ls='--',label='200 kg energy-only capacity');axs[1].legend(fontsize=8)
for j,v in enumerate(vals):axs[1].text(j,v*1.15,f'{v:,.0f}',ha='center',fontsize=9)
axs[1].set_ylim(40,160000);axs[1].grid(alpha=.15,axis='y')
fig.supxlabel('100 W/m^2 net heat, 40 min after 20 min handling; no drying kinetics, reaction-rate or safety validation.\nA density 1830 kg/m^3; B bridge density 1000 kg/m^3 assumed. Passing this bound is not operational success.',fontsize=10)
save(fig,'02_process_bounds')
h=list(csv.DictReader((P/'debris_history.csv').open(encoding='utf-8')))
fig,axs=plt.subplots(1,2,figsize=(12,5.7),layout='constrained');fig.suptitle('Re-forming small bridges still needs a fines inventory and a whole-bed cost',fontsize=16,weight='bold')
for r,col in [(0,orange),(.5,purple),(.9,teal)]:
    rr=[x for x in h if float(x['renewed_fraction'])==.1 and float(x['collection_fraction'])==r]
    axs[0].semilogy([int(x['cycle']) for x in rr],[float(x['remaining_debris_kg']) for x in rr],color=col,label=f'collect {r:.0%} of debris pool each cycle')
axs[0].set(xlabel='Regeneration cycles',ylabel='Resident debris (kg)',title='A. Renew 10% of contacts per cycle (assumed)');axs[0].legend(fontsize=8);axs[0].grid(alpha=.15)
raw=[next(x['raw_carrier_cost_yen_tax_excluded']/1e6 for x in R['carrier_material_cost'] if x['foam_grain_envelope_density_kg_m3']==100 and x['material_price_yen_kg_assumed']==1000)]+[next(x['raw_material_cost_yen_tax_excluded']/1e6 for x in R['lifecycle'] if x['renewed_fraction']==f and x['collection_fraction']==0 and x['potential_reuse_fraction']==0) for f in [.1,1]]
axs[1].bar(range(3),raw,color=['#7c8f9b',teal,orange]);axs[1].set_xticks(range(3),['Initial carrier\n100 kg/m^3','360 cycles\n10% renewal','360 cycles\n100% renewal'])
axs[1].set(ylabel='Raw material only (million JPY, ex tax)',title='B. 1000 JPY/kg assumed; no recycling credit')
for j,v in enumerate(raw):axs[1].text(j,v+.8,f'{v:g}',ha='center')
axs[1].set_ylim(0,59);axs[1].grid(alpha=.15,axis='y')
fig.supxlabel('Debris is not environmental release; collection and reuse remain unverified.\nCosts exclude manufacturing, recovery, labour, energy, equipment, civil works and tax; not quotations.',fontsize=10)
save(fig,'03_inventory_cost')
print('3 PNG and 3 SVG created')
