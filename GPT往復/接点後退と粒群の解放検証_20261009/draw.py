from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=json.loads((P/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none'})
def save(fig,name):
 for ext in ['png','svg']:fig.savefig(P/(name+'.'+ext),dpi=180,bbox_inches='tight',facecolor='white')
 plt.close(fig)
fig,(ax,bx)=plt.subplots(1,2,figsize=(11,4.8))
f=R['fold'];ax.plot([r['axial_compression']*100 for r in f],[r['one_side_retreat_um'] for r in f],'o-',color='#247c87');ax.set_xlabel('Assumed axial compression [%]');ax.set_ylabel('Retreat on one side [µm]');ax.set_title('Re-entrant unit-cell kinematics');ax.grid(alpha=.2)
for q,color in [(1.01,'#315b92'),(1.04,'#247c87'),(1.09,'#c68b2a'),(1.25,'#b7465f')]:
 rows=[r for r in R['clearance'] if r['geometry_spacing_ratio']==q];bx.plot([r['axial_compression']*100 for r in rows],[r['post_retreat_gap_um'] for r in rows],'o-',label=f'q = {q}',color=color)
bx.axhline(0,color='black',ls='--',lw=1);bx.set_xlabel('Assumed axial compression [%]');bx.set_ylabel('Side gap at fixed grain centers [µm]');bx.set_title('Retreat may open a lateral contact');bx.legend(fontsize=9);bx.grid(alpha=.2)
fig.text(.02,.01,'500 µm cell span; geometric model only. q sets initial center spacing. No force, 3D packing or ski validation.',fontsize=9);fig.tight_layout(rect=(0,.05,1,1));save(fig,'figure1_retreat')
fig,ax=plt.subplots(figsize=(9.5,4.8))
for mu,c in [(.1,'#315b92'),(.3,'#247c87'),(.6,'#b7465f')]:
 rows=[r for r in R['ring'] if r['reference_diameter_um']==500 and r['friction_coefficient']==mu];ax.plot([r['density_ratio_phi_over_hexagonal'] for r in rows],[r['release_distance_um'] for r in rows],'o-',label=f'Contact friction µ = {mu}',color=c)
ax.set_xlabel('2D nominal density ratio Φ / Φh');ax.set_ylabel('Attractive-to-repulsive distance [µm]');ax.set_title('Published ring-pair geometry: friction and contact extent');ax.legend();ax.grid(alpha=.2)
fig.text(.02,.01,'Illustrative 500 µm scaling of the 2D formula; not measured ski release or a 3D stability boundary.',fontsize=9);fig.tight_layout(rect=(0,.05,1,1));save(fig,'figure2_release')
fig,(ax,bx)=plt.subplots(1,2,figsize=(11,4.8))
rows=R['tolerance'];ax.bar([str(r['actual_thickness_um']) for r in rows],[r['ideal_bending_stiffness_ratio'] for r in rows],color=['#e4aa51','#247c87','#b7465f']);ax.axhline(1,color='gray',ls='--');ax.set_xlabel('Hinge thickness [µm]');ax.set_ylabel('Bending stiffness / nominal');ax.set_title('20 ± 5 µm thickness tolerance')
rows=[r for r in R['cost'] if r['auxetic_body_mass_fraction']==.25];bx.bar([str(r['assumed_auxetic_yen_kg']) for r in rows],[r['required_whole_bed_life_ratio_for_equal_annual_material_cost'] for r in rows],color=['#e4aa51','#247c87','#b7465f']);bx.set_xlabel('Assumed auxetic grain price [JPY/kg]');bx.set_ylabel('Required whole-bed functional life ratio');bx.set_title('25% mass mix: material cost break-even')
fig.text(.02,.01,'Beam estimate and assumed prices only. Same mass; base body price 1,000 JPY/kg. Manufacturing and service costs excluded.',fontsize=9);fig.tight_layout(rect=(0,.05,1,1));save(fig,'figure3_tolerance_cost')
print('3 figures saved as PNG and SVG')
