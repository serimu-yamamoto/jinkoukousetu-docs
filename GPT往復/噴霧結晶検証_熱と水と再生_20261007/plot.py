import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parent
r=json.loads((ROOT/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})
fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
for ta,col in [(30,'#197a86'),(40,'#d18b16'),(50,'#ab4261')]:
    rows=[x for x in r['cooling'] if x['ambient_C']==ta and x['Nu']==2]
    ax[0].loglog([x['diameter_um'] for x in rows],[x['total_s'] for x in rows],'-o',color=col,
                 label=f'Air {ta} C; exit {rows[0]["exit_C"]} C')
ax[0].set(xlabel='Sphere diameter (micrometres)',ylabel='Energy-removal time (s)',title='Thermal model, not crystallization kinetics')
ax[0].legend(fontsize=9);ax[0].grid(alpha=.25,which='both')
rows=[x for x in r['reforming'] if x['area_m2']==2000 and x['depth_m']==.45]
ax[1].loglog([100*x['fraction'] for x in rows],[x['rate_kg_h']/1000 for x in rows],'-o',color='#197a86')
for x in rows:ax[1].annotate(f'{x["rate_kg_h"]/1000:g} t/h',(100*x['fraction'],x['rate_kg_h']/1000),xytext=(7,7),textcoords='offset points',fontsize=9)
ax[1].set(xlabel='Mass reformed per closure (%)',ylabel='Required production (tonnes/hour)',
          title='2,000 m2 x 0.45 m; assumed 120 kg/m3')
ax[1].set_xlim(.8,170);ax[1].grid(alpha=.25,which='both')
fig.suptitle('Cycle 16 | 40-minute processing window within a 60-minute closure',fontsize=14)
fig.savefig(ROOT/'01_thermal_throughput.png');plt.close(fig)

fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
rows=[x for x in r['bridges'] if x['area_m2']==2000 and x['depth_m']==.45 and
      x['product_fraction']==.001 and x['treated_fraction']==1]
values=[r['saturated_solution']['water_kg_per_kg_gypsum']]+[x['free_water_kg']/x['product_kg'] for x in rows]
labels=['Saturated\nsolution','20 wt%\nslurry','50 wt%\nslurry','80 wt%\nslurry']
ax[0].bar(labels,values,color=['#ab4261','#197a86','#429ba3','#89bcc1'])
ax[0].set_yscale('log');ax[0].set_ylim(.02,1200)
for i,v in enumerate(values):ax[0].text(i,v*1.25,f'{v:.3g}',ha='center')
ax[0].set(ylabel='Free water to evaporate (kg/kg gypsum)',title='Hydration avoids the dilute-feed penalty')
ax[0].text(.98,.96,'80 wt% sprayability is unverified',transform=ax[0].transAxes,ha='right',va='top',fontsize=9)
for f,col in [(.0001,'#ab4261'),(.001,'#197a86'),(.005,'#d18b16')]:
    rows=[x for x in r['rain'] if x['area_m2']==2000 and x['depth_m']==.45 and
          x['product_fraction']==f and x['effective_saturation']==1]
    ax[1].plot([x['rain_mm'] for x in rows],[x['capped_loss_kg']/x['inventory_kg']*100 for x in rows],'-o',color=col,label=f'Bridge stock {f*100:g} wt%')
ax[1].set_xscale('log');ax[1].set(xlabel='Equivalent water depth / bed area (mm)',ylabel='Inventory-equivalent dissolution capacity (%)',
    ylim=(0,110),title='25 C equilibrium capacity; not erosion rate')
ax[1].legend(fontsize=9);ax[1].grid(alpha=.25)
fig.suptitle('Water carried into manufacture and water carried away by rain',fontsize=14)
ax[1].text(.98,.03,'All supplied water effective; kinetics unknown',transform=ax[1].transAxes,ha='right',va='bottom',fontsize=8,color='#555555')
# Render the capped-linear capacity law in water depth, not chords in log-depth.
# Original model markers are retained; this is not an erosion-rate model.
for line in list(ax[1].lines):
    px=[float(v) for v in line.get_xdata()]
    py=[float(v) for v in line.get_ydata()]
    first=min(range(len(px)),key=px.__getitem__)
    if not (px[first]>0 and 0<py[first]<100):
        raise ValueError('Need an uncapped positive capacity point')
    coefficient=py[first]/px[first]
    if max(abs(y-min(100,coefficient*x)) for x,y in zip(px,py))>1e-7:
        raise ValueError('Capacity law disagrees with model markers')
    lo,hi=min(px),max(px)
    dense=[lo*(hi/lo)**(i/199) for i in range(200)]
    knee=100/coefficient
    if lo<knee<hi:
        dense.append(knee)
    dense=sorted(set(dense+px))
    line.set_data(dense,[min(100,coefficient*x) for x in dense])
    line.set_marker('')
    ax[1].plot(px,py,'o',color=line.get_color(),label='_nolegend_')
ax[1].legend(loc='upper center',bbox_to_anchor=(.5,-.18),ncol=3,fontsize=8)
fig.set_size_inches(12,5.4)

fig.savefig(ROOT/'02_water_rain.png');plt.close(fig)

fig,ax=plt.subplots(figsize=(12,6.5));ax.set_xlim(0,12);ax.set_ylim(0,6.5);ax.axis('off')
def box(x,y,w,h,text,color='#e3f1f3'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.08',facecolor=color,edgecolor='#286572'))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10)
def arrow(a,b,label=None):
    ax.annotate('',b,a,arrowprops=dict(arrowstyle='->',color='#455565',lw=1.4))
    if label:ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+.13,label,ha='center',fontsize=9)
ax.text(.1,6.12,'Two research branches | manufacture shape and renew selected contacts',fontsize=16,weight='bold')
box(.2,4.6,2.3,1.0,'P16: polymer melt\nFeed heating + shaping')
box(3,4.6,2.5,1.0,'Enclosed gas process\nShort attached branches\nNo continuous fibre mat')
box(6,4.6,2.5,1.0,'Retained porous grains\nRounded outer contacts\nDSC + shape inspection')
arrow((2.6,5.1),(2.9,5.1));arrow((5.6,5.1),(5.9,5.1))
box(.2,2.65,2.3,1.15,'G16: hemihydrate\nConcentrated suspension\nNo soluble-salt lubricant','#fbecd8')
box(3,2.65,2.5,1.15,'Localized crystal necks\nInner contact pockets\nHydration + water removal','#fbecd8')
box(6,2.65,2.5,1.15,'Candidate composite bed\nSupport / edge release\nWet stability both required','#fbecd8')
arrow((2.6,3.2),(2.9,3.2));arrow((5.6,3.2),(5.9,3.2));arrow((7.25,4.5),(7.25,3.95),'Hypothesis')
box(9.2,2.65,2.4,1.15,'Skiing + rain\nMeasure wear, runoff,\nedge force and grooves','#ede7f4')
arrow((8.6,3.2),(9.1,3.2))
box(6,.8,5.6,1.0,'Groomer: recover / separate / return sound grains\nDamaged stock to enclosed regeneration + reserve stock')
arrow((10.4,2.55),(10.4,1.9));arrow((5.9,1.3),(1.35,1.3));arrow((1.35,1.3),(1.35,2.5))
ax.text(2.0,1.6,'Fresh feed / regeneration requires validation',fontsize=9)
ax.text(.2,.22,'Concept only. No verified 30-50 C formulation, 60-minute cure, snow feel, or physical success probability.',fontsize=10,color='#9b2846')
fig.savefig(ROOT/'03_process_concept.png',bbox_inches='tight');plt.close(fig)
print('3 figures saved; concept is not a built machine or validated material')
