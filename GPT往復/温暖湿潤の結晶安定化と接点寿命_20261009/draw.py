from pathlib import Path
import sys,json,csv
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyArrowPatch
import numpy as np
R=json.loads((P/'results.json').read_text(encoding='utf-8'));a=R['nominal']['bridge_radius_um']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'cycle63'})
teal='#007f86';orange='#c46a35';gray='#68767d'
def save(fig,name):
    fig.savefig(P/(name+'.png'),dpi=160,bbox_inches='tight',facecolor='white')
    fig.savefig(P/(name+'.svg'),bbox_inches='tight',facecolor='white',metadata={'Date':None});plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(12,5.7),layout='constrained');fig.suptitle('The same remaining volume can preserve a bridge or sever it',fontsize=17,weight='bold')
for ax in axs:
    ax.set(xlim=(-2,12),ylim=(-9,9));ax.set_aspect('equal');ax.axis('off')
    for x in [-2,10]:ax.add_patch(Rectangle((x,-7),2,14,color=gray,alpha=.4))
rr=a*np.sqrt(.86);axs[0].add_patch(Rectangle((0,-rr),10,2*rr,color=teal));axs[0].add_patch(Rectangle((0,-a),10,2*a,fill=False,ls='--',ec=gray))
axs[1].add_patch(Rectangle((0,-a),4.3,2*a,color=orange));axs[1].add_patch(Rectangle((5.7,-a),4.3,2*a,color=orange))
axs[1].annotate('1.4 um gap',xy=(5,0),xytext=(5,-8),ha='center',arrowprops={'arrowstyle':'->'})
axs[0].set_title('Uniform side loss: force ratio 0.86\n(same intrinsic strength assumed)',fontsize=12)
axs[1].set_title('Local loss across one section: no tensile path\n(compression contact may return)',fontsize=12)
fig.supxlabel('Geometrical counterexample, not a measured dissolution pattern. Original mineral phase %, solid volume %,\ncontact count and remaining strength are distinct. Neither drawing predicts the outdoor material.',fontsize=10)
save(fig,'01_contact_topology')
fig,axs=plt.subplots(1,2,figsize=(12,5.8),layout='constrained');fig.suptitle('A small neck needs sub-micron weathering control',fontsize=17,weight='bold')
w=list(csv.DictReader((P/'radial_loss.csv').open(encoding='utf-8')));xx=[float(v['radial_loss_um']) for v in w];yy=[float(v['force_retention_same_strength']) for v in w]
axs[0].plot(xx,yy,color=teal,lw=2);lim=R['nominal']['radial_loss_limit_um'];axs[0].axhline(.8,color=gray,ls='--');axs[0].axvline(lim,color=orange,ls='--');axs[0].annotate(f'20% force loss at {lim:.3f} um',(lim,.8),xytext=(1.5,.91),arrowprops={'arrowstyle':'->'},fontsize=10)
axs[0].set(xlabel='Uniform radial loss (um)',ylabel='Force ratio, constant bridge strength',xlim=(0,a),ylim=(0,1.02),title='A. Fixed length; no cracking / delamination')
c=list(csv.DictReader((P/'side_coating.csv').open(encoding='utf-8')));axs[1].plot([float(x['thickness_um']) for x in c],[100*float(x['coat_to_bridge_mass']) for x in c],'o-',color=orange)
axs[1].set(xlabel='Assumed side-coat thickness (um)',ylabel='Additional coat mass / core bridge mass (%)',title='B. Side coating only; bond faces excluded')
for ax in axs:ax.grid(alpha=.18)
fig.supxlabel('Nominal a=6.155 um, length=10 um, core density=1830 and coat density=2000 kg/m^3.\nCoating is an untested design sensitivity; no barrier lifetime, adhesion or safety is inferred.',fontsize=10)
save(fig,'02_loss_and_coating')
fig,axs=plt.subplots(1,2,figsize=(12,5.8),layout='constrained');fig.suptitle('Off-site stabilization trades closure time for factory inventory',fontsize=17,weight='bold')
f=np.array([.01,.1,1]);day=49.41*f/.25*2
for hold,col in [(7,teal),(28,orange)]:axs[0].loglog(f*100,day*hold*10/1000,'o-',label=f'{hold} d test-duration scenario',color=col)
axs[0].set(xlabel='Contacts renewed per grooming (%)',ylabel='Occupied process bath (m^3)',title='A. 2 cycles/day; 10 L/kg feed; no spare tanks');axs[0].legend(fontsize=9);axs[0].grid(alpha=.18)
annual=day*180
for price,col in [(100,teal),(500,gray),(2000,orange)]:axs[1].loglog(f*100,annual*(1000+price)/1e6,'o-',color=col,label=f'processing {price} JPY/kg')
axs[1].set(xlabel='Contacts renewed per grooming (%)',ylabel='Partial recurring cost (million JPY/year)',title='B. Raw feed 1000 JPY/kg; assumed prices');axs[1].legend(fontsize=9);axs[1].grid(alpha=.18)
fig.supxlabel('7/28 days are published exposure durations, NOT required treatment time. No validated regeneration process.\nCost excludes tax, full carrier, equipment, civil works, energy/water unless included in a future verified quote.',fontsize=10)
save(fig,'03_factory_inventory')
print('3 PNG and 3 SVG created')
