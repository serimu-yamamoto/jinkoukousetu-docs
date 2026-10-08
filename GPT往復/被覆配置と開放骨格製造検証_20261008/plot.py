from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parent
local=P.parents[1]/'.deps'
if local.exists():sys.path.insert(0,str(local))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=json.loads((P/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':10,'axes.grid':True,'grid.alpha':.22})
fig,ax=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
x=O['bed_inventory'][:4]
labels=['5 um spheres','0.2 um patches','1 um patches','5 um patches']
ax[0].bar(labels,[r['guest_kg']/1000 for r in x],color=['#b65b48','#579b91','#167f78','#579b91'])
ax[0].set_ylabel('Additional coating inventory (tonnes)')
ax[0].set_title('2,000 m2 bed: 108 t uncoated host; C = 0.70')
ax[0].tick_params(axis='x',rotation=15)
for i,r in enumerate(x):ax[0].text(i,r['guest_kg']/1000+.3,f"{r['guest_kg']/1000:.2f}",ha='center')
b=[r['volume_ratio'] for r in O['expansion']]
ax[1].plot(b,[r['fixed_guest_coverage'] for r in O['expansion']],'o-',label='Fixed-size discrete guests')
ax[1].plot(b,[r['affine_film_coverage'] for r in O['expansion']],'s--',label='Ideal bonded/stretching patches')
ax[1].plot(b,[r['film_thickness_ratio'] for r in O['expansion']],'^:',label='Stretching patch: thickness / initial')
ax[1].set(xlabel='Host volume expansion B (hypothetical)',ylabel='Coverage or thickness ratio',ylim=(0,1.08))
ax[1].legend(fontsize=9)
fig.suptitle('H34 | Conditional geometry and mass balance; no physical performance prediction')
fig.savefig(P/'figure1_mass_and_expansion.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
f=O['flattening']; vals=[f['lateral_semiaxis_um'],f['diagnostic_contact_radius_um'],1.5*f['diagnostic_contact_radius_um']]
ax[0].bar(['Flattened guest\nfootprint radius','Contact radius\n4 mN, E* = 0.5 GPa','Footprint target\n1.5 x margin'],vals,color=['#b65b48','#607da0','#167f78'])
for i,v in enumerate(vals):ax[0].text(i,v+.4,f'{v:.2f}',ha='center')
ax[0].set(ylabel='Radius (um)',ylim=(0,26),title='R = 500 um curvature does not ensure sufficient width')
cycles=[r['cycles'] for r in O['wear_budget']]
ax[1].bar([str(r['thickness_um'])+' um' for r in O['wear_budget']],[r['allowable_mean_removal_nm_per_cycle'] for r in O['wear_budget']],color='#167f78')
ax[1].set(ylabel='Allowed mean removal (nm / cycle)',xlabel='Initial partial-film thickness',title='500 hypothetical cycles; keep half the thickness')
fig.suptitle('H34 | Geometry screening and inverse wear allowance; not a measured service life')
fig.savefig(P/'figure2_footprint_and_wear.png',dpi=180);plt.close(fig)
print('Two diagnostic figures saved')
