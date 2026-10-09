from pathlib import Path
import sys,csv,json,math
P=Path(__file__).resolve().parent
# Optional local environment only; not an archived dependency copy.
sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
R=json.loads((P/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'cycle61'})
C={'elastic':'#777777','balanced':'#007f86','large_branch':'#c55b28','balanced_unrelaxed':'#7554a3'}
def save(fig,name):
    fig.savefig(P/(name+'.png'),dpi=160,bbox_inches='tight',facecolor='white')
    fig.savefig(P/(name+'.svg'),bbox_inches='tight',facecolor='white',metadata={'Date':None})
    plt.close(fig)
def box(ax,x,y,w,h,text,fc='#edf4f4',ec='#25787c'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.01',fc=fc,ec=ec,lw=1.5))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=11,linespacing=1.6)
def arrow(ax,a,b):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=16,color='#40545c',lw=1.5))
fig,ax=plt.subplots(figsize=(12,6.8));ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
ax.text(.01,.97,'H61: separate contact braking from contact-free recovery',weight='bold',fontsize=17)
box(ax,.02,.66,.28,.2,'1. Contact exists\nSliding consumes energy\nThen static friction holds')
box(ax,.36,.66,.28,.2,'2. Normal opener + drainage\nRemove contact AND liquid bridge\nOpening history is not solved here')
box(ax,.70,.66,.28,.2,'3. No contact / no bridge\nFriction cannot damp motion\nMaterial loss is one damping route')
arrow(ax,(.30,.76),(.36,.76));arrow(ax,(.64,.76),(.70,.76))
box(ax,.08,.20,.22,.24,'Normal support core\n+ separate opening flexure\nPrior H57 / H60 constraints',fc='#f4f1e9',ec='#918064')
box(ax,.48,.32,.42,.13,'Return flexure: equilibrium stiffness k0')
box(ax,.48,.11,.42,.13,'Frequency-dependent branch: kd -- eta\nMaxwell spring and dashpot in series')
ax.plot([.42,.42],[.16,.39],color='#007f86',lw=2);ax.plot([.94,.94],[.16,.39],color='#007f86',lw=2)
ax.plot([.42,.48],[.39,.39],color='#007f86',lw=2);ax.plot([.90,.94],[.39,.39],color='#007f86',lw=2)
ax.plot([.42,.48],[.17,.17],color='#007f86',lw=2);ax.plot([.90,.94],[.17,.17],color='#007f86',lw=2)
ax.text(.69,.52,'Prefer loss within existing flexure before adding a bonded pad',ha='center',fontsize=11,weight='bold',color='#007f86')
ax.text(.01,.02,'Constitutive / functional schematic, not a manufactured grain or assembly drawing.\nThe three stages are not yet validated as one trajectory. No 50 C wet prototype; no success probability.',fontsize=10,color='#5b6267')
save(fig,'01_concept')
h=list(csv.DictReader((P/'time_history.csv').open(encoding='utf-8')))
f=list(csv.DictReader((P/'frequency_response.csv').open(encoding='utf-8')))
fig,axs=plt.subplots(2,2,figsize=(12,8.2),layout='constrained')
fig.suptitle('Conditional dynamics: damping helps free return but can arrest contact slip early',fontsize=16,weight='bold')
sel=R['first_friction_event'][:4];a=axs[0,0]
a.bar([str(x['alpha']) for x in sel],[x['x_stop_um'] for x in sel],color=['#777','#75b8b3','#007f86','#c55b28'])
a.axhline(1,ls='--',color='#555',lw=1);a.set(xlabel='Maxwell branch stiffness / k0 (r = 1)',ylabel='Offset at first stop (um)',title='A. Contact: first stop, fixed normal reaction')
for j,z in enumerate(sel):a.text(j,z['x_stop_um']+.12,f"{z['x_stop_um']:.3f}",ha='center')
a.set_ylim(0,8.7)
for name in C:
    rr=[z for z in h if z['case']==name];t=[float(z['time_us']) for z in rr]
    axs[0,1].plot(t,[float(z['x_um']) for z in rr],label=name,color=C[name],lw=1.6)
    e0=next(z['initial_energy_nJ'] for z in R['free_return'] if z['case']==name)
    axs[1,0].semilogy(t,[max(1e-15,float(z['energy_nJ'])/e0) for z in rr],color=C[name],label=name)
axs[0,1].axhspan(-1,1,color='#007f86',alpha=.1);axs[0,1].set(xlim=(0,160),xlabel='Time (us)',ylabel='Offset (um)',title='B. Free return: separate 10 um initial condition');axs[0,1].legend(fontsize=8,ncol=2)
axs[1,0].axhline(.01,ls='--',color='#555',lw=1);axs[1,0].set(xlim=(0,450),ylim=(1e-5,1.3),xlabel='Time (us)',ylabel='Remaining mechanical energy / initial',title='C. Energy includes mass and Maxwell spring')
for name in ['balanced','large_branch']:
    rr=[z for z in f if z['case']==name];axs[1,1].semilogx([float(z['frequency_Hz']) for z in rr],[float(z['loss_factor']) for z in rr],color=C[name],label=name)
axs[1,1].axvline(R['f0_Hz'],color='#555',ls=':',lw=1,label='baseline f0 (assumed mass)')
axs[1,1].set(xlabel='Frequency (Hz)',ylabel='Loss stiffness / storage stiffness',title='D. Loss is frequency-dependent, not constant');axs[1,1].legend(fontsize=8)
for a in axs.ravel():a.grid(alpha=.14,axis='y')
fig.supxlabel('All curves use assumed local parameters; no material fit, particle rebound measurement or ski trial.',fontsize=10)
save(fig,'02_dynamics')
fig,axs=plt.subplots(1,2,figsize=(12,5.5),layout='constrained')
fig.suptitle('Adding a tiny damping pad is not automatically inexpensive',fontsize=16,weight='bold')
for dg,col in [(1,'#c55b28'),(10,'#007f86')]:
    z=[x for x in R['cost_lower_bounds'] if x['deltaG_MPa']==dg]
    axs[0].plot([x['strain_limit']*100 for x in z],[x['material_yen_tax_excluded']/1e6 for x in z],'-o',color=col,label=f'delta G = {dg} MPa (assumed)')
    axs[1].plot([x['strain_limit']*100 for x in z],[x['volume_um3_per_module'] for x in z],'-o',color=col,label=f'delta G = {dg} MPa')
axs[0].set(yscale='log',xlabel='Allowable shear strain (%)',ylabel='Additional material only (million JPY, ex tax)',title='A. Uniform-shear lower bound; 4 modules / grain')
axs[1].axhline(2000,color='#555',ls='--',label='20 x 20 x 5 um pad')
axs[1].set(yscale='log',xlabel='Allowable shear strain (%)',ylabel='Damping material volume per module (um^3)',title='B. Small pad requires 118% strain at delta G = 1 MPa')
for ax in axs:ax.legend(fontsize=9);ax.grid(alpha=.15)
fig.supxlabel('2000 m^2 x 0.45 m, packing 0.55; density 1120 kg/m^3 and price 3000 JPY/kg assumed.\nNot quotations. Excludes supports, joining, tooling, yield, civil works, equipment and tax.',fontsize=10)
save(fig,'03_volume_cost')
print('3 PNG + 3 SVG figures generated')
