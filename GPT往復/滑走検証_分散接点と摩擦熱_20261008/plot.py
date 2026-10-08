"""Plots are calculated scenarios, never measured performance."""
from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parent
# Optional workspace-only dependencies; ordinary installed matplotlib also works.
sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
R=json.loads((P/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
for radius,n,label in [(150,1,'R150, one contact'),(300,1,'R300, one contact'),(150,4,'R150, four equal contacts')]:
    rows=[x for x in R['thermal_cases'] if x['radius_um']==radius and x['contacts']==n and x['support_fraction']==.3 and x['mu']==.1]
    rows.sort(key=lambda x:x['speed_m_s'])
    axs[0].plot([x['speed_m_s'] for x in rows],[x['delta_average_K'] for x in rows],'o-',label=label)
axs[0].set(xlabel='Sliding speed (m/s)',ylabel='Isolated contact mean temperature rise (K)',title='Same total load; imposed load sharing')
axs[0].legend(fontsize=9);axs[0].grid(alpha=.2)
labels=['One large\ncontact','One of four\nisolated','Square: two\nin one track','Row: four\nin one track']
keys=['large_isolated','small_isolated','square_aligned_two','row_aligned_four']
vals=[R['layout'][k]['pulse_peak_rise_K'] for k in keys]
axs[1].bar(labels,vals,color=['#426c98','#519c9b','#72b6a1','#bd7160'])
for j,value in enumerate(vals): axs[1].text(j,value+.25,f'{value:.2f}',ha='center')
axs[1].set(ylabel='Centreline pulse temperature rise (K)',ylim=(0,22),title='Same area & pressure; heat left in the track')
fig.suptitle('Dry-contact thermal screening: initial 50 C, mu = 0.10 (assumed)',fontsize=13)
fig.text(.5,-.025,'Left: two-body area mean. Right: all heat to base, 1-D pulse peak. Do not compare as the same temperature.',ha='center',fontsize=9)
fig.savefig(P/'thermal_comparison.png',dpi=180,bbox_inches='tight');plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(12,4.6),layout='constrained')
a=R['layout']['small_four']['a_um'];big=R['layout']['large_one']['a_um']
layouts=[[(0,0)], [(-40,-40),(40,-40),(-40,40),(40,40)], [(-120,0),(-40,0),(40,0),(120,0)]]
for j,(ax,pts) in enumerate(zip(axs,layouts)):
    for x,y in pts:
        if j>0: ax.add_patch(Circle((x,y),30,fill=False,edgecolor='#999',linestyle='--'))
        ax.add_patch(Circle((x,y),big if j==0 else a,color='#3c8291'))
    ax.set_aspect('equal');ax.set(xlim=(-165,165),ylim=(-90,90),xlabel='micrometres',ylabel='micrometres')
    ax.annotate('',xy=(140,75),xytext=(-140,75),arrowprops=dict(arrowstyle='->',color='#b65d42'))
    ax.text(0,82,'Sliding direction',ha='center',fontsize=9)
    ax.grid(alpha=.15)
axs[0].set_title('One R300 contact\ncontact radius 16.94 um')
axs[1].set_title('Four R150 contacts, square\n80 um centre spacing')
axs[2].set_title('Counterexample: straight row\nthermal wakes overlap')
fig.suptitle('H21 local cap layout: equal total calculated contact area, not a full grain',fontsize=13)
fig.text(.5,-.025,'Blue = Hertz contact patch. Dashed = proposed 60 um cap aperture. Support frame, branches and height tolerances are unresolved.',ha='center',fontsize=9)
fig.savefig(P/'contact_layout.png',dpi=180,bbox_inches='tight');plt.close(fig)
print('Two calculated figures written.')
