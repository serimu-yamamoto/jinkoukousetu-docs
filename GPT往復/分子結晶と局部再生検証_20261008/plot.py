from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent
if (P.parents[1]/'.deps').exists():sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=json.loads((P/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':10,'axes.grid':True,'grid.alpha':.2})
fig,ax=plt.subplots(1,2,figsize=(12,4.7),layout='constrained')
a=O['neck_network'][:5]
ax[0].plot([x['seeded_surface_fraction'] for x in a],[x['neck_radius_um'] for x in a],'o-',color='#167f78')
ax[0].axhline(20,linestyle='--',color='#b35949',label='Assumed local width limit')
ax[0].set(xlabel='Seeded fraction at random contact locations',ylabel='Required neck radius (um)',title='Same 3 kPa ideal isotropic normal-force budget')
ax[0].legend(fontsize=8)
ax[0].text(.43,35,'Fewer connected pairs require larger bonds.\nA connected load-bearing network is NOT proven.',fontsize=9)
g=[x for x in O['growth_kinematics'] if x['gap_um']==2 and x['growth_time_min']==20]
ax[1].plot([x['terrace_spacing_nm'] for x in g],[x['geometric_closure_um'] for x in g],'s-',color='#607da0')
ax[1].axhline(2,linestyle='--',color='#b35949',label='Assumed 2 um gap')
ax[1].set(xlabel='Assumed terrace spacing (nm)',ylabel='Two-front closure in 20 min (um)',title='Step motion is not face-normal growth')
ax[1].legend(fontsize=8)
fig.suptitle('H35 | Geometry and growth conditions; not measured bed strength or a 50 C result')
fig.savefig(P/'figure1_contacts_and_growth.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,4.7),layout='constrained')
for name,label,col in [('tyrosine_reported_feed','Tyr feed: inventory comparison only','#b35949'),('cystine_reported_feed','Cystine feed: conditional comparison','#167f78')]:
 rows=[x for x in O['solution_and_material_balance'] if x['area_m2']==2000 and x['repaired_fraction']==.1 and x['new_fraction']==.1 and x['solution']==name]
 ax[0].plot([x['useful_fraction'] for x in rows],[x['solution_volume_m3']*1000 for x in rows],'o-',label=label,color=col)
 rows=[x for x in O['rain_capacity'] if x['solution']==name and x['rainfall_mm']==50]
 ax[1].loglog([x['contact_water_fraction'] for x in rows],[x['ratio_to_bridge_inventory'] for x in rows],'o-',label=label,color=col)
ax[0].set(xlabel='Useful fraction of precipitated mass',ylabel='Solution volume per hypothetical repair (L)',title='Renew 10% of bonds; regrow 10% of each bond')
ax[0].legend(fontsize=8)
ax[1].axhline(1,linestyle='--',color='#666',label='Capacity equals total bridge inventory')
ax[1].set(xlabel='Fraction of 50 mm rainfall contacting bonds',ylabel='Dissolution capacity / 5.22 kg bridge inventory',title='Water capacity, NOT an actual dissolution rate')
ax[1].legend(fontsize=7)
fig.suptitle('H35 | Common hypothetical bridge geometry; neither material is validated for this application')
fig.savefig(P/'figure2_regrowth_and_rain.png',dpi=180);plt.close(fig)
print('2 figures generated')
