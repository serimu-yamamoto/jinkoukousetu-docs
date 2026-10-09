from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent
R=P.parents[1]
dep=R/'.research95/deps'
if dep.exists():sys.path.insert(0,str(dep))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
d=json.loads((P/'results.json').read_text(encoding='utf-8'))
fig,axs=plt.subplots(1,2,figsize=(12,5),layout='constrained')
t=d['source_table_recalculation'];x=np.arange(3)
axs[0].bar(x-.18,[a['virgin_mm'] for a in t],.36,label='Uncrosslinked')
axs[0].bar(x+.18,[a['crosslinked_mm'] for a in t],.36,label='Crosslinked (gamma)')
axs[0].set_xticks(x,['Room temperature','50 C','60 C'])
axs[0].set_ylabel('Terminal displacement (mm)')
axs[0].set_title('S1 Table 7.1: compression, 8 MPa')
axs[0].legend(loc='upper left');axs[0].set_ylim(0,2.05)
for i,a in enumerate(t):axs[0].text(i,max(a['virgin_mm'],a['crosslinked_mm'])+.1,f"-{a['reduction_from_virgin_percent']:.1f}%",ha='center')
for q in [50,150,500]:
    rows=[a for a in d['manufacturing_cases'] if a['pre_crosslink_recovery']==.95 and a['charge_JPY_kg']==q]
    axs[1].plot([a['yield']*100 for a in rows],[a['combined_saving_before_extra_handling_JPY']/1e6 for a in rows],'o-',label=f'Charge {q} JPY/kg')
axs[1].set_xlabel('Assumed cutting yield (%)')
axs[1].set_ylabel('Difference before extra handling (million JPY)')
axs[1].set_title('Cut / recover offcuts BEFORE crosslinking')
axs[1].legend();axs[1].grid(alpha=.2)
fig.suptitle('Cycle 95 | Literature values and conditional manufacturing arithmetic',fontsize=13)
fig.text(.5,-.045,'Left: reported terminal values; duration inconsistency noted. Right: assumed 135 t, recovery 95%, raw 500 JPY/kg.\nNo measurements of the proposed ski material. No success probability.',ha='center',fontsize=9)
fig.savefig(P/'evidence_and_process.png',dpi=160,bbox_inches='tight',metadata={'Software':'Cycle95 reproduceable figure'})
plt.close(fig)
print(json.dumps({'figure':'evidence_and_process.png','matplotlib':matplotlib.__version__}))
