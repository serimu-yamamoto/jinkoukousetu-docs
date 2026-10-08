"""Reproduce Cycle 51 figures; needs matplotlib. No source images reused."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
local=ROOT.parents[1]/'.deps'
if local.exists(): sys.path.insert(0,str(local))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch
import csv
import math
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                     'figure.facecolor':'#fafafa','axes.facecolor':'#fafafa','svg.fonttype':'none'})

def rows(name):
    with (ROOT/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))
def save(fig,name):
    fig.savefig(ROOT/(name+'.png'),dpi=170,bbox_inches='tight')
    fig.savefig(ROOT/(name+'.svg'),bbox_inches='tight')
    svg=ROOT/(name+'.svg')
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(11.4,4.6),layout='constrained')
vals=rows('source_table.csv')[:5]
labels=['Crystallinity','Young modulus','Yield strength','Tensile strength','Break strain']
ratio=[float(x['ratio']) for x in vals]
axes[0].barh(labels,ratio,color=['#5267ad','#d76a43','#d76a43','#d76a43','#5267ad'])
axes[0].axvline(1,color='#454545',ls='--',lw=1)
for i,v in enumerate(ratio):axes[0].text(v+.035,i,f'{v:.3f}',va='center')
axes[0].set(xlim=(0,2.65),xlabel='PP + 1.5 wt% ER / PP (ratio of means)',title='S1: more crystallinity, less support')
axes[0].invert_yaxis()
for d,col in zip([1e-15,1e-14,1e-13],['#56876d','#5278b2','#bd6448']):
    hours=[10**(i/50-1) for i in range(250)]
    axes[1].loglog(hours,[math.sqrt(2*d*h*3600)*1e6 for h in hours],color=col,label=f'D = {d:.0e} m2/s')
axes[1].axvline(8,color='#777',lw=1,ls=':')
axes[1].axhline(30,color='#777',lw=1,ls='--')
axes[1].set(xlim=(.1,3000),ylim=(.5,2000),xlabel='Elapsed time (h)',ylabel='sqrt(2 D t) (um)',title='Migration scale, not a front or barrier')
axes[1].legend(fontsize=8,loc='upper left')
fig.suptitle('Other-system evidence: not a wet-50 C ski-material test',fontsize=14)
save(fig,'evidence')

fig,axes=plt.subplots(1,3,figsize=(13.5,4.4),layout='constrained')
f=[i/1000 for i in range(1,801)]
axes[0].plot(f,[1/(1+9*x**3) for x in f],label='Softened tip zone',color='#477e69')
axes[0].plot(f,[1/(1+9*(1-(1-x)**3)) for x in f],label='Softened root zone',color='#cc714e')
axes[0].set(xlabel='Softened fraction of length',ylabel='Remaining cantilever stiffness',title='Same amount, different location',ylim=(0,1.05))
axes[0].legend(fontsize=8)
a=[i/1000 for i in range(100,751)]
axes[1].plot(a,[1.5/x for x in a],color='#5267ad')
axes[1].axhline(5,color='#bb633f',ls='--',label='Assumed limit: 5 MPa')
axes[1].scatter([.2,.5],[7.5,3],color='#3c4147')
axes[1].set(xlabel='Projected crystal area fraction a',ylabel='Crystal pressure (MPa)',title='75% of load, mean pressure 2 MPa',ylim=(0,16))
axes[1].legend(fontsize=8)
axes[2].plot(a,[45*x for x in a],label='Same 0.5 um thickness',color='#5267ad')
axes[2].axhline(33.75,color='#cc714e',label='Equal wear life: 33.75')
axes[2].set(xlabel='Whole-surface coated fraction phi',ylabel='Initial coating purchase (million JPY)',title='Area reduction is not life-cost reduction',ylim=(0,47))
axes[2].legend(fontsize=8)
fig.suptitle('Conditional models: eta = 0.1 (left); equal specific wear and phi = a (middle/right)',fontsize=12)
save(fig,'tradeoffs')

fig,ax=plt.subplots(figsize=(11.4,6.2),layout='constrained')
ax.set(xlim=(-6,6),ylim=(-3.9,3.2));ax.axis('off')
# One schematic free grain: supported load seats and independent reset fingers.
ax.add_patch(Circle((0,0),.65,facecolor='#879b9a',edgecolor='#435956',lw=2))
for angle in [35,145,265]:
    th=math.radians(angle);x,y=2*math.cos(th),2*math.sin(th)
    ax.plot([0,x],[0,y],lw=15,color='#879b9a',solid_capstyle='round')
    ax.add_patch(Circle((x,y),.48,facecolor='#c8d7d3',edgecolor='#435956',lw=1.7))
    ax.plot([x-.32,x+.32],[y+.34,y+.34],color='#8265ae',lw=7,solid_capstyle='butt')
    ax.plot([x-.34,x+.34],[y+.17,y+.17],color='#a393bf',lw=3)
for sign in [-1,1]:
    ax.plot([sign*.5,sign*1.2,sign*2.0,sign*2.4],[-.15,-.4,-.5,-.22],lw=3,color='#477e69')
    ax.add_patch(Circle((sign*2.4,-.22),.07,facecolor='#477e69'))
ax.annotate('Broad load seat\nretained crystal face',xy=(1.75,1.48),xytext=(3.1,2.05),arrowprops=dict(arrowstyle='->',color='#555'),ha='left',fontsize=12)
ax.annotate('Unmodified root\nno mobile slip additive',xy=(-.35,.28),xytext=(-5.7,2.1),arrowprops=dict(arrowstyle='->',color='#555'),ha='left',fontsize=12)
ax.annotate('Separate elastic finger\nwet-contact recovery',xy=(2,-.49),xytext=(3.15,-.8),arrowprops=dict(arrowstyle='->',color='#555'),ha='left',fontsize=12)
ax.annotate('Open space for water\nand winter snow entry',xy=(-1.5,-1.35),xytext=(-5.7,-1.85),arrowprops=dict(arrowstyle='->',color='#555'),ha='left',fontsize=12)
ax.text(0,2.87,'H51: preserve roots, spread load, retain crystals',ha='center',fontsize=16,color='#293a45')
ax.text(0,-3.15,'Concept only: not a dimensioned CAD model, chosen material, or snow crystal.\nAll grains through usable bed depth require the same functions; random orientation remains unresolved.',ha='center',fontsize=10,color='#4a4a4a')
save(fig,'concept')
print('3 PNG + 3 SVG created')
