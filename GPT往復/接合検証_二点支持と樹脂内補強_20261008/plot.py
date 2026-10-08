"""Rebuild original schematic and diagnostic plots from results.json; requires matplotlib."""
import os,sys,json
from pathlib import Path
D=Path(__file__).resolve().parent
deps=D.parents[1]/'.deps'
sys.path.insert(0,str(deps))
os.environ.setdefault('MPLCONFIGDIR',str(deps/'.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
R=json.loads((D/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
for ax,E in zip(axs,[.3,3]):
    base=next(x for x in R['rows'] if x['pad_E_MPa']==E and x['a_um']==5 and x['h_um']==1 and x['half_separation_um']==0)
    ax.axhline(base['total_deflection_to_fixed_ratio'],color='#666',ls='--',label='Single disk on rigid local seat')
    for t,col in [(2,'#d95f02'),(5,'#1b9e77'),(10,'#7570b3')]:
        rr=[x for x in R['rows'] if x['pad_E_MPa']==E and x['a_um']==5 and x['h_um']==1 and x['carrier_t_um']==t]
        rr.sort(key=lambda x:x['half_separation_um'])
        ax.plot([x['half_separation_um'] for x in rr],[x['total_deflection_to_fixed_ratio'] for x in rr],'o-',color=col,label=f'Arm thickness {t} um')
    ax.axhline(1.1,color='black',lw=.8,ls=':',label='1.10 diagnostic reference')
    ax.set(xlabel='Half spacing s (um)',ylabel='Deflection / ideally fixed-branch deflection',title=f'Assumed wet pad modulus: {E} MPa',xticks=[5,10,20])
    ax.legend(fontsize=8)
    ax.grid(alpha=.15)
fig.suptitle('Same pad volume; flexible arms can erase the spacing benefit\nLocal linear model, a = 5 um, h = 1 um; NOT measured ski performance',fontsize=11)
fig.savefig(D/'support_comparison.png',dpi=170);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(11,5),layout='constrained')
for ax,pair in zip(axs,[False,True]):
    ax.set_xlim(-22,22);ax.set_ylim(-6,33);ax.set_aspect('equal');ax.axis('off')
    if pair:
        rp=5/(2**.5)
        for cx in [-10,10]:
            ax.add_patch(Rectangle((cx-rp,-3),2*rp,3,facecolor='#999',edgecolor='#555'))
            ax.add_patch(Rectangle((cx-rp,0),2*rp,1,facecolor='#d95f02'))
        ax.add_patch(Rectangle((-10,1),20,5,facecolor='#58a',alpha=.8))
        ax.plot([0,0],[6,26],color='#134',lw=4)
        ax.annotate('',(-10,-4),(10,-4),arrowprops={'arrowstyle':'<->'})
        ax.text(0,-5,'2s = 20 um',ha='center',va='top')
        ax.text(13,3.5,'Arms\nt = 5 um',va='center',fontsize=9)
        ax.set_title('Two pads + two deformable arms')
    else:
        ax.add_patch(Rectangle((-7,-3),14,3,facecolor='#999',edgecolor='#555'))
        ax.add_patch(Rectangle((-5,0),10,1,facecolor='#d95f02'))
        ax.plot([0,0],[1,21],color='#134',lw=4)
        ax.annotate('',(-5,-4),(5,-4),arrowprops={'arrowstyle':'<->'})
        ax.text(0,-5,'2a = 10 um',ha='center',va='top')
        ax.set_title('Single pad on rigid local seat')
    ax.annotate('Branch reaction',xy=(0,15),xytext=(-20,29),arrowprops={'arrowstyle':'->'},fontsize=9)
    ax.text(0,-8,'Grey anchors: assumed rigid INTERNAL frame',ha='center',fontsize=8)
fig.suptitle('H20 local support topology (section, not a manufacturing drawing)\nOrange pads have equal total area and volume; their radius differs',fontsize=11)
fig.savefig(D/'joint_topology.png',dpi=170);plt.close(fig)
print('Two original figures written; matplotlib '+matplotlib.__version__)
