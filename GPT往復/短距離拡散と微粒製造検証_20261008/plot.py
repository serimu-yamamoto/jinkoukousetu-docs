"""Cycle 31 diagnostic figures; hypothetical geometries, not measured artificial snow."""
import json,sys,math
from pathlib import Path
P=Path(__file__).resolve().parent
local=P.parents[1]/'.deps'
if local.exists():sys.path.insert(0,str(local))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator,FixedFormatter,NullFormatter
R=json.loads((P/'results.json').read_text(encoding='utf8'))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})
fig,ax=plt.subplots(1,2,figsize=(12,5.7),layout='constrained')
for dcoef,col in [(1e-10,'#9c4c23'),(1e-9,'#2878a4'),(1e-8,'#43815c')]:
 rows=[r for r in R['diffusion'] if r['D_m2_s']==dcoef]
 ax[0].plot([r['precursor_diameter_mm'] for r in rows],[r['t95_s'] for r in rows],'o-',color=col,label=f'Assumed D = {dcoef:.0e} m2/s')
ax[0].set(xscale='log',yscale='log',xlabel='UNEXPANDED spherical precursor diameter (mm)',ylabel='Time to 95% uptake (s)',title='A. Short paths reduce diffusion time')
ax[0].legend(fontsize=9);ax[0].grid(alpha=.2)
for ratio,col in [(.1,'#43815c'),(1,'#2878a4'),(10,'#9c4c23')]:
 rows=[r for r in R['retention'] if r['Ddes_to_Ds']==ratio]
 ax[1].plot([r['delay_s'] for r in rows],[100*r['remaining_fraction'] for r in rows],'o-',color=col,label=f'D release / D uptake = {ratio:g}')
ax[1].set(xscale='log',xlabel='Delay after ideal surface concentration drops to zero (s)',ylabel='Gas remaining (%)',ylim=(-3,103),title='B. Small precursors also lose gas quickly')
ax[1].legend(fontsize=9);ax[1].grid(alpha=.2)
ax[1].set_xlabel('Delay after ideal surface concentration drops to zero (s)\nPrecursor 0.273 mm; D uptake = 1e-9 m2/s\nNo expansion, nucleation, heating or pressure ramp',fontsize=9)
fig.suptitle('Cycle 31 | Diffusion-only limits, not production cycle predictions',fontsize=14)
fig.savefig(P/'figure1_diffusion_and_release.png');plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,5.7),layout='constrained')
for rho,col in [(100,'#43815c'),(200,'#2878a4'),(400,'#9c4c23')]:
 rows=[r for r in R['particle_manufacture'] if r['area_m2']==2000 and r['envelope_density_kg_m3']==rho]
 ax[0].plot([r['finished_diameter_mm'] for r in rows],[r['particles_per_s']/1e6 for r in rows],'o-',color=col,label=f'Envelope density {rho} kg/m3')
ax[0].axvspan(3,5,alpha=.1,color='#2878a4',label='S2 brochure size: 3-5 mm')
ax[0].axvspan(.3,.6,alpha=.12,color='#c79924',label='Research comparison: 0.3-0.6 mm')
ax[0].set(xscale='log',yscale='log',xlabel='FINISHED equivalent sphere diameter (mm)',ylabel='Required particles (million / s)',title='A. Feed 281.25 kg/h: particle count matters')
ax[0].legend(fontsize=8,loc='upper right');ax[0].grid(alpha=.2)
for t in [0,2,5,10,15]:
 rows=[r for r in R['skin'] if r['shell_um']==t]
 ax[1].plot([r['diameter_mm'] for r in rows],[r['envelope_density_kg_m3'] for r in rows],'o-',label=f'Assumed shell {t} um')
ax[1].set(xscale='log',xlabel='Finished equivalent sphere diameter (mm)',ylabel='Envelope density (kg/m3)',title='B. A dense skin can erase low core density')
ax[1].legend(fontsize=9,loc='upper right');ax[1].grid(alpha=.2)
ax[1].set_xlabel('Finished equivalent sphere diameter (mm)\nHypothetical core 60 / shell 900 kg/m3\nNot measured shell thickness or support strength',fontsize=9)
for a in ax:
 a.xaxis.set_major_locator(FixedLocator([.3,.45,.6,1,3,5]));a.xaxis.set_major_formatter(FixedFormatter(['0.3','0.45','0.6','1','3','5']));a.xaxis.set_minor_formatter(NullFormatter())
fig.suptitle('Cycle 31 | Fine grain production and surface-to-volume trade-offs',fontsize=14)
fig.savefig(P/'figure2_particle_count_and_skin.png');plt.close(fig)
print('Rendered 2 diagnostic figures; physical tests = 0')
