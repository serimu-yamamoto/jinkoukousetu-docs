"""Reproducible scenario figures. Not experimental data."""
from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
R=json.loads((P/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,3,figsize=(12,4.6),layout='constrained')
A=4*math.pi*(20e-6)**2
wet_loaded=1000*(1-.00648/(A*10e6))
for ax,height,title,board in zip(axs,[wet_loaded,820,100],['Fully wet, under load','Partly dry (assumed theta=0.8)','Fully dry'],[wet_loaded,850,850]):
    ax.add_patch(Rectangle((-34,-150),68,150,color='#657782'))
    for x in [-30,20]: ax.add_patch(Rectangle((x,0),10,850,color='#657782'))
    ax.add_patch(Rectangle((-20,0),40,height,color='#62b6cb',alpha=.8))
    ax.plot([-33,33],[board,board],color='#242424',linewidth=4)
    ax.axhline(850,color='#b46050',linestyle=':',linewidth=1)
    ax.text(0,height/2,f'Layer height\n{height:.0f} nm',ha='center')
    ax.set(xlim=(-35,35),ylim=(-160,1150),xlabel='Lateral coordinate (um)',ylabel='Height (nm)',title=title)
    ax.grid(alpha=.15)
axs[1].annotate('Only 30 nm gap;\nliquid bridging unresolved',xy=(0,835),xytext=(0,1030),ha='center',fontsize=9,arrowprops={'arrowstyle':'->'})
fig.suptitle('H22 recessed-layer concept: hard rim at 850 nm; vertical scale enlarged',fontsize=13)
fig.text(.5,-.025,'Ideal rigid rim and plate; M = 10 MPa is assumed. No claim of zero adhesion, ice bonding or a manufactured particle.',ha='center',fontsize=9)
fig.savefig(P/'recess_concept.png',dpi=180,bbox_inches='tight');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(12,4.6),layout='constrained')
for clearance,color in [(0,'#3e8195'),(30,'#b88737'),(100,'#bb6452')]:
    moduli=[8+j*.1 for j in range(421)]
    pressure=R['reference_switch_windows'][0]['pressure_MPa']
    widths=[1000*(1-pressure/m)-10-(820+10+clearance) for m in moduli]
    axs[0].plot(moduli,widths,label=f'Required clearance {clearance} nm',color=color)
axs[0].axhline(0,color='black',linewidth=1)
axs[0].set(xlabel='Assumed effective compression modulus M (MPa)',ylabel='Allowable recess interval width (nm)',title='Positive interval is only a geometric requirement')
axs[0].legend(fontsize=9);axs[0].grid(alpha=.2)
refs=R['reference_inventories']
axs[1].bar([f'{x["pocket_depth_um"]} um\npocket depth' for x in refs],[x['maximum_loss_for_4h_g_m2_h'] for x in refs],color=['#5d9dad','#72b4b6','#99c4b7'])
for j,x in enumerate(refs):axs[1].text(j,x['maximum_loss_for_4h_g_m2_h']+.003,f'{x["maximum_loss_for_4h_g_m2_h"]:.4f}',ha='center')
axs[1].set(ylabel='Maximum net water loss for 4 h (g/m2/h)',ylim=(0,.19),title='Top 1 mm only; all stored water assumed usable')
fig.suptitle('H22 design requirements: contact switching and surface water inventory',fontsize=13)
fig.text(.5,-.025,'100 nm dry layer, swelling ratio 10, four r20 um patches per hypothetical 500 um grain. Evaporation is not predicted.',ha='center',fontsize=9)
fig.savefig(P/'switch_and_water_limits.png',dpi=180,bbox_inches='tight');plt.close(fig)
print('Two scenario figures written.')
