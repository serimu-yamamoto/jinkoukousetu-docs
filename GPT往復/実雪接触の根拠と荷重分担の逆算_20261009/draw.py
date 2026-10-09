from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent;R=P.parents[1]
if (R/'.research87/deps').exists():sys.path.insert(0,str(R/'.research87/deps'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyArrowPatch
import reproduce as M
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
rows=json.loads((P/'contact_recruitment.json').read_text(encoding='utf8'))
b=M.b0;n,k=b['potential_density_m2'],b['stiffness_N_m'];h=50e-6
fig,axs=plt.subplots(2,2,figsize=(13.5,9.5),layout='constrained')
ax=axs[0,0]
gap=np.array([0,9,18,27,36,45,50])
d=M.solve(2000,n,k,h)['approach_m']*1e6
ax.vlines(range(7),gap,55,color='#91a4b8',lw=5)
ax.scatter(range(7),gap,color='#427191',s=45,label='Unloaded support tips')
ax.axhline(d,color='#b95735',lw=2,label=f'Board approach: {d:.1f} um')
for j,g in enumerate(gap):
 if g<d:ax.annotate('',(j,d),(j,g),arrowprops={'arrowstyle':'->','color':'#b95735','lw':1.5})
ax.invert_yaxis();ax.set_ylim(58,-7);ax.set_xticks([])
ax.set_ylabel('Gap from highest tip (um)')
ax.set_title('A. Height distribution recruits supports')
ax.legend(loc='lower left',fontsize=9)
ax.text(.02,.94,'Illustration; fixed roots and rigid board',transform=ax.transAxes,fontsize=9,va='top')
ax=axs[0,1]
for scale,col in zip([1,2,3,4],['#b27e52','#729095','#14768e','#875594']):
 bb=next(q for q in M.branches if q['geometry']==f'planar_only_s{scale}' and q['solid_modulus_MPa_assumed']==500)
 hs=np.linspace(0,200,200)
 vals=[M.solve(2000,bb['potential_density_m2'],bb['stiffness_N_m'],v*1e-6)['active_fraction'] for v in hs]
 ax.plot(hs,vals,label=f'Planar scale {scale}',color=col)
ax.set(xlabel='Assumed full height spread h (um)',ylabel='Active fraction',title='B. Same modulus, different recruitment',ylim=(0,1.05))
ax.legend(fontsize=9);ax.grid(alpha=.2)
ax=axs[1,0]
hs=np.linspace(0,200,200);ss=[M.solve(2000,n,k,v*1e-6) for v in hs]
ax.plot(hs,[s['mean_force_N']*1e3 for s in ss],label='Mean per active support',color='#14768e')
ax.plot(hs,[s['max_force_N']*1e3 for s in ss],label='Maximum support force',color='#b95735')
ax.axhline(5.625,color='gray',ls=':',label='All active / zero spread')
ax.set(xlabel='Assumed full height spread h (um)',ylabel='Force (mN)',title='C. Scale 3: height variation raises local loads')
ax.legend(fontsize=9);ax.grid(alpha=.2)
ax=axs[1,1]
dd=np.linspace(0,100,250)*1e-6
ax.plot(dd*1e6,[M.pressure(d,n,k,h)/1000 for d in dd],label='A: n, k',lw=3,color='#14768e')
ax.plot(dd*1e6,[M.pressure(d,2*n,k/2,h)/1000 for d in dd],label='B: 2n, k/2',lw=1.5,ls='--',color='#e5aa48')
ax.set(xlabel='Board approach (um)',ylabel='Nominal pressure (kPa)',title='D. Identical curve, different contact forces')
ax.text(.04,.68,'B has twice the active contacts\nand half the force per contact.\nNo friction or wear prediction.',transform=ax.transAxes,fontsize=10)
ax.legend(fontsize=9);ax.grid(alpha=.2)
fig.suptitle('Cycle 87 | Hypothetical support recruitment\n2 kPa, assumed 500 MPa; no physical measurements',fontsize=15)
fig.savefig(P/'contact_recruitment.png',dpi=150);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(14,8.5),layout='constrained')
ax=axs[0]
g=np.linspace(15,110,400)
upper=241.67450911525788
low=1075.9474895122114*(20/g)**2
ax.plot(g,low,color='#14768e',lw=2,label='Minimum E for <=10% wet closure')
ax.axhline(upper,color='#b95735',lw=2,label='Maximum E for >=80% dry contacts')
ax.fill_between(g,low,upper,where=low<=upper,color='#b6cdb8',alpha=.6,label='Necessary intersection only')
ax.scatter([50],[200],s=80,color='#493c70',zorder=4,label='Illustrative 200 MPa / 50 um')
ax.axvline(42.19977266530734,color='gray',ls=':')
ax.set(xlabel='Assumed initial water gap g (um)',ylabel='Assumed solid-layer modulus E (MPa)',
 title='A. Scale 3 at 2 kPa: dry / wet constraints',ylim=(0,1250),xlim=(15,110))
ax.legend(loc='upper right',fontsize=9)
ax.text(.4,.53,'20 um: no intersection\n50 um: 172.2 to 241.7 MPa\nSame height spread h = 50 um',transform=ax.transAxes,fontsize=10)
ax.grid(alpha=.2)
ax=axs[1];ax.set(xlim=(0,10),ylim=(0,10));ax.axis('off')
ax.set_title('B. Concept to test: separate contact and drainage')
ax.add_patch(Rectangle((.6,8.1),8.8,.55,color='#63717e'))
ax.text(5,8.9,'Ski base (rigid in this model)',ha='center')
# Non-scale pair of branched lamella surfaces.
ax.plot([.9,3,4.1,6.4,9],[6.3,6.3,7.55,6.3,6.3],lw=6,color='#458897')
ax.plot([.9,3,4.1,6.4,9],[3.9,3.9,5.15,3.9,3.9],lw=6,color='#458897')
ax.add_patch(Rectangle((6.8,4.05),.32,2.08,color='#be995e'))
ax.text(8.2,5.4,'Integral\nspacer?',ha='center',fontsize=10)
ax.annotate('',(2,6.05),(2,4.15),arrowprops={'arrowstyle':'<->','lw':1.4})
ax.text(1.1,5.1,'g',fontsize=14)
ax.text(.8,2.8,'Contact-height spread h and water gap g\nare different geometrical variables.',fontsize=12)
ax.text(.8,1.25,'Do not assume loose grains preserve g.\nA spacer can create a hard bypass path.\nNo material, manufacturing or wet proof yet.',fontsize=11)
ax.text(.8,.25,'Section is schematic; dimensions are not to scale.',fontsize=9,color='#555555')
fig.suptitle('Cycle 87 | Dry compliance and wet closure must be checked together\nSeparate necessary screens, not a coupled wet-contact simulation',fontsize=15)
fig.savefig(P/'design_window.png',dpi=150);plt.close(fig)
(P/'plot_metadata.json').write_text(json.dumps({'figures':['contact_recruitment.png','design_window.png'],'physical_experiments':0,'manufacturing_demonstrated':False,'third_party_figures_reproduced':False,'drawn_from':'reproduce.py analytical outputs; conceptual schematic not to scale'},indent=2)+'\n',encoding='utf8',newline='\n')
print('Generated two original diagnostic figures.')
