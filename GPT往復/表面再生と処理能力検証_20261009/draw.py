from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
R=json.loads((P/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none'})
def save(fig,name):
    fig.savefig(P/(name+'.png'),dpi=180,bbox_inches='tight',facecolor='white')
    fig.savefig(P/(name+'.svg'),bbox_inches='tight',facecolor='white')
    plt.close(fig)
fig,ax=plt.subplots(figsize=(10,5))
x=[v['daily_damage_fraction']*100 for v in R['capacity']]
y=[v['incoming_body_kg_day'] for v in R['capacity']]
ax.bar(range(3),y,color=['#3c9c8e','#e5aa48','#cf5962'])
ax.axhline(R['ideal_processing_body_kg_day'],color='#25485f',ls='--',label='20 m² service: 269 kg/day (assumed schedule)')
ax.set_xticks(range(3),[str(v)+'%' for v in x]);ax.set_xlabel('Assumed daily damaged fraction of body mass');ax.set_ylabel('Body mass [kg/day]')
for i,v in enumerate(y):ax.text(i,v+25,f'{v:,.1f}',ha='center')
ax.legend(loc='upper left');ax.set_ylim(0,1680);ax.set_title('Material arriving for renewal versus processing capacity')
fig.text(.02,.01,'Reference exposure only: 6 faces × 30 s; 16 h/day × 75% availability. No handling time or proof of cure.',fontsize=9)
fig.tight_layout(rect=(0,.05,1,1));save(fig,'figure1_capacity')
fig,ax=plt.subplots(figsize=(10,5))
rows=[v for v in R['classification'] if v['damage_fraction']==.001]
tp=[v['true_positive_fraction']*140025.26867296622 for v in rows];fp=[v['false_positive_fraction']*140025.26867296622 for v in rows]
ax.bar(range(3),tp,label='Damaged bodies correctly selected',color='#3c9c8e');ax.bar(range(3),fp,bottom=tp,label='Healthy bodies selected by mistake',color='#e5aa48')
ax.axhline(R['ideal_processing_body_kg_day'],color='#25485f',ls='--',label='20 m² service capacity')
ax.set_xticks(range(3),['99%','99.9%','99.99%']);ax.set_xlabel('Assumed specificity (correctly reject healthy bodies)');ax.set_ylabel('Selected body mass [kg/day]');ax.set_title('Small sorting errors can dominate rare surface damage')
ax.legend(loc='upper right');ax.set_ylim(0,1840)
for i,r in enumerate(rows):ax.text(i,r['processed_body_kg_day']+25,f"{r['processed_body_kg_day']:,.1f} kg",ha='center')
fig.text(.02,.01,'Assumed: 0.1% daily damage, 90% detection sensitivity. 14.0 kg damaged bodies/day remain missed in all cases.',fontsize=9)
fig.tight_layout(rect=(0,.05,1,1));save(fig,'figure2_sorting')
fig,ax=plt.subplots(figsize=(11,5.5));ax.axis('off');ax.set_xlim(-.35,11);ax.set_ylim(0,5.5)
boxes=[(.15,3.6,3.2,1.25,'1 | On slope\nRedistribute + drain\nAdd qualified reserve grains'),(3.9,3.6,3.2,1.25,'2 | Removed batch\nCheck shape + wet friction\nDo not assume perfect sorting'),(7.65,3.6,3.2,1.25,'3 | Off-slope factory\nRenew contact material\nReject broken skeletons'),(7.65,1.1,3.2,1.25,'4 | Re-qualification\n50°C + rain + repeat wear\nEdge force and short release'),(3.9,1.1,3.2,1.25,'5 | Qualified reserve\nReturn within usable depth\nTrack mass and actual cost'),(.15,1.1,3.2,1.25,'Concept H55\nMass loss needs material\nLight alone does not refill grooves')]
for j,(x,y,w,h,t) in enumerate(boxes):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.08',facecolor='#e8f2f1' if j!=5 else '#fff1d6',edgecolor='#315c68'));ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=11)
for a,b in [((3.4,4.2),(3.75,4.2)),((7.15,4.2),(7.5,4.2)),((9.25,3.5),(9.25,2.5)),((7.5,1.7),(7.15,1.7)),((5.5,1),(-.15,.55)),((-.15,.55),(-.15,4.2)),((-.15,4.2),(.02,4.2))]:ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',lw=1.6,color='#315c68'))
ax.text(5.5,5.25,'H55: recover structure, renew lost surface, verify function',ha='center',fontsize=15,weight='bold')
fig.text(.02,.01,'Concept only. Shape recovery, wear resistance and ski glide are separate acceptance tests.',fontsize=10)
fig.tight_layout();save(fig,'figure3_process')
print('3 PNG + 3 SVG figures generated')
