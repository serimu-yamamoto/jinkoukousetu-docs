"""Original diagnostic plots; literature panel labelled separately."""
from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=json.loads((P/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':135})
fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
for d in [1,3,10]:
 a=[r for r in R['reference_cases'] if r['diameter_um']==d]
 ax[0].semilogx([r['transfer_factor'] for r in a],[r['stiffness_ratio_proxy'] for r in a],'o-',label=f'Fibril diameter {d} um')
ax[0].axhline(1,color='black',ls='--',label='Unreinforced host')
ax[0].set_xlabel('Assumed transfer-spring factor chi')
ax[0].set_ylabel('Axial stiffness proxy / host modulus')
ax[0].set_title('Short embedded fibrils require load transfer')
ax[0].legend(fontsize=9);ax[0].grid(alpha=.2)
for o,label in [(1,'Aligned'),(.375,'Planar random proxy'),(.2,'3D random proxy')]:
 rows=[r for r in R['geometry_cases'] if r['diameter_um']==1 and r['transfer_factor']==.1 and r['orientation_factor']==o]
 ax[1].plot([r['length_um'] for r in rows],[r['stiffness_ratio_proxy'] for r in rows],'o-',label=label)
ax[1].axhline(1,color='black',ls='--')
ax[1].set_xlabel('Embedded fibril length [um]')
ax[1].set_ylabel('Directional stiffness proxy / host modulus')
ax[1].set_title('Orientation benefit is not available in every direction')
ax[1].legend(fontsize=9);ax[1].grid(alpha=.2)
fig.suptitle('Cycle25 | Assumed Ehost=300 MPa; Efiber=3000 MPa; 15 wt% fiber; 5 um skin',fontsize=12)
fig.savefig(P/'01_load_transfer.png');plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
for price in [500,1000,3000]:
 rows=[r for r in R['same_shape_cost_cases'] if r['fiber_JPY_kg']==price and r['forming_JPY_kg']==100]
 ax[0].plot([r['w']*100 for r in rows],[r['annual_remaining_JPY']/1e6 for r in rows],'o-',label=f'Fiber {price:,} JPY/kg')
ax[0].axhline(0,color='black',ls='--')
ax[0].set_xlabel('Fiber mass fraction [%]')
ax[0].set_ylabel('Annual budget remaining [million JPY]')
ax[0].set_title('Same grain geometry: density and forming cost included')
ax[0].legend(fontsize=9);ax[0].grid(alpha=.2)
ax[0].text(.02,.03,'Hypothetical prices; forming=100 JPY/kg\nNo extra regeneration plant cost included',transform=ax[0].transAxes,fontsize=9)
bars=ax[1].bar(['Before isotropization','188C / 6 min'],[8,3],color=['#37758e','#aa6d49'],width=.55)
for b in bars:ax[1].text(b.get_x()+b.get_width()/2,b.get_height()+.2,str(int(b.get_height()))+' GPa',ha='center')
ax[1].set_ylim(0,10);ax[1].set_ylabel('Reported filament modulus [GPa]')
ax[1].set_title('S3: PET survival does not preserve oriented PP stiffness')
ax[1].text(.03,.93,'Literature: PP / 22 wt% PET\nNot a 50C wet test or our candidate result',transform=ax[1].transAxes,va='top',fontsize=9)
ax[1].grid(axis='y',alpha=.2)
fig.suptitle('Cycle25 | Shared budget and a measured reprocessing counterexample',fontsize=12)
fig.savefig(P/'02_cost_and_history.png');plt.close(fig)
print('Generated2figures; matplotlib '+matplotlib.__version__)
