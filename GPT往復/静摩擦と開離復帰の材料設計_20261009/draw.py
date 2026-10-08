from pathlib import Path
import sys,json,csv
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle,FancyArrowPatch
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'));R=json.loads((P/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'cycle59'})
def save(fig,name):
 fig.savefig(P/(name+'.png'),dpi=160,bbox_inches='tight');fig.savefig(P/(name+'.svg'),bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots(figsize=(9,5))
m=np.linspace(.2,.93,300);fa=R['cam']['Fa_uN']*1e-6;k1=R['cam']['k_N_m']/80
req=fa*(1+m)/(1-m)/1e-6/k1
ax.plot(m,req,color='#c0453b',lw=2,label='H58-C: reciprocal sliding return')
ax.axhline(R['opening']['E_required_for_baseline_MPa'],color='#007c83',lw=2,label='H59 necessary opening bound at 1 kPa')
ax.axvline(R['cam']['mu_max_for_1um'],color='#777',ls='--',label='H58-C limit at E50 = 80 MPa')
ax.scatter([.6,.768,.8],[R['cam'][x]['E_required_MPa'] for x in ['at_mu_06','at_published_max','at_mu_08']],color='#c0453b',zorder=4)
ax.annotate('Published steel-pair counterexample\nnot a measured coefficient for our grain',(.768,149.787),xytext=(.26,230),arrowprops={'arrowstyle':'->','color':'#555'},fontsize=9)
ax.set(xlabel='Static friction coefficient (assumed for model)',ylabel='Required effective E at 50 C (MPa)',ylim=(0,400),xlim=(.2,.93))
ax.set_title('Change the return path before increasing material stiffness',loc='left',fontweight='bold')
ax.legend(loc='upper left',fontsize=9);ax.grid(alpha=.17)
fig.text(.12,-.025,'Different assumed mechanisms/geometries. H59 curve is a necessary force bound; no material is qualified.',fontsize=9,color='#555')
save(fig,'figure1_material_bounds')
fig,axs=plt.subplots(1,2,figsize=(11,4.5),gridspec_kw={'width_ratios':[1.15,1]})
y=np.linspace(0,10,101);F=20*(15-y)
axs[0].plot(y,F,lw=2,color='#007c83',label='Opening spring: 20 N/m')
for p,col in [(1,'#4682b4'),(3,'#c0453b')]:
 resist=p*62.5+R['cam']['Fa_uN'];axs[0].axhline(resist,color=col,ls='--',label=f'Resistance: {p} kPa + water bridge')
axs[0].set(xlabel='Normal separation y (um)',ylabel='Force per module (uN)',ylim=(0,330))
axs[0].legend(fontsize=8,loc='lower left');axs[0].grid(alpha=.15)
axs[0].set_title('Must overcome resistance along the entire path',loc='left',fontsize=11)
labels=['1 kPa\npath condition met','3 kPa\npath condition fails'];x=np.arange(2)
axs[1].bar(x-.18,[2,2],.36,color='#007c83',label='Available spring work')
axs[1].bar(x+.18,[.667690415,1.917690415],.36,color='#c5a660',label='Resistance work')
axs[1].set(xticks=x,xticklabels=labels,ylabel='Work per module (nJ)',ylim=(0,2.6));axs[1].legend(fontsize=8)
axs[1].set_title('An energy-only test wrongly passes both',loc='left',fontsize=11)
fig.suptitle('H59 open-first return: conditional calculation, not a tested mechanism',fontweight='bold',y=1.03)
fig.tight_layout();save(fig,'figure2_opening_force_energy')
fig,axs=plt.subplots(1,2,figsize=(11,5))
a=axs[0];a.set_xlim(0,10);a.set_ylim(0,10);a.axis('off')
for y in [2,6.5]:
 a.add_patch(Rectangle((2,y),5,.6,color='#647a87'))
 a.add_patch(Rectangle((4,y+.6 if y==2 else y-.6),1.6,.6,color='#b45e55'))
a.text(.1,9.5,'Functional module / conceptual section',fontsize=12,fontweight='bold')
a.text(.1,8.8,'Four modules per ~500 um grain; not a fitted CAD',fontsize=9,color='#555')
a.annotate('Outer glide pad\nmechanically retained PE candidate',xy=(7,7),xytext=(.1,7.7),fontsize=9,arrowprops={'arrowstyle':'->'})
a.annotate('Internal friction faces\nclosed under load',xy=(4.8,3),xytext=(.1,4.7),fontsize=9,arrowprops={'arrowstyle':'->'})
a.annotate('',xy=(7.5,6.7),xytext=(7.5,3.2),arrowprops={'arrowstyle':'<->','color':'#007c83','lw':2})
a.text(7.8,4.4,'1. Open\nnormal\nto face',fontsize=9,color='#007c83')
a.annotate('',xy=(3.5,1),xytext=(6.5,1),arrowprops={'arrowstyle':'->','color':'#b45e55','lw':2})
a.text(1.7,.15,'2. Return tangentially after bridge breaks',fontsize=9,color='#b45e55')
a.text(.1,-.6,'Opening flexures, guards and 3D load transmission\nremain to be fitted and tested; faces are not exposed ground.',fontsize=9,color='#555')
c=axs[1];prices=np.array([1000,3000,10000]);mass=R['cost']['additional_mass_1120_kg'];prior=8849.654486472366
c.bar(np.arange(3),prior*prices/1e6,label='H58 return beams (retained)',color='#647a87')
c.bar(np.arange(3),mass*prices/1e6,bottom=prior*prices/1e6,label='H59 opening beams (added)',color='#007c83')
c.set(xticks=np.arange(3),xticklabels=['1,000','3,000','10,000'],xlabel='Assumed resin price (JPY/kg)',ylabel='Raw beam material only (million JPY)')
c.set_title('No unproved replacement credit',loc='left',fontsize=12,fontweight='bold');c.legend(fontsize=8,loc='upper left')
fig.text(.55,.0,'Excludes support cores, pads, frames, processing, loss,\ntax, factory, grooming equipment and civil works.',fontsize=9,color='#555')
fig.tight_layout(rect=[0,.12,1,1]);save(fig,'figure3_concept_cost')
print('3 figures exported to PNG and SVG; no experimental data generated')
