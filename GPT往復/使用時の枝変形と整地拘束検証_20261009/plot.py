from pathlib import Path
import sys,json,csv
P=Path(__file__).resolve().parent
D=P.parents[1]/'.deps'
if D.exists():sys.path.insert(0,str(D))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=json.loads((P/'results.json').read_text(encoding='utf-8'))
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
profiles=I['beam']['profiles'];labels=['Uniform','H38 a=1','H38 a=5','Clipped taper']
colors=['#556577','#147d92','#cb6a36','#7562a8'];B=R['optimized_taper_B'];s=np.linspace(0,1,500)
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','savefig.facecolor':'white'})
fig,axs=plt.subplots(2,2,figsize=(13,8),layout='constrained')
for p,label,col in zip(profiles,labels,colors):
    if p=='uniform':r=s*0+10*np.sqrt(28/15)
    elif p=='volume_optimal_clipped':r=10*np.maximum(1,B*(1-s))**(1/3)
    else:
        a=1 if p=='quadratic_a1' else 5;r=10*np.sqrt((28/15)/(1+2*a/3+a*a/5))*(1+a*(1-s)**2)
    axs[0,0].plot(s,r,label=label,color=col,lw=2)
axs[0,0].set(xlabel='Arc coordinate from root / full arm length',ylabel='Radius (micrometres)',title='A. Equal volume; different distribution of material')
axs[0,0].legend(fontsize=9,ncols=2);axs[0,0].grid(alpha=.2)
curves=list(csv.DictReader((P/'beam_shapes.csv').open(encoding='utf-8')))
for p,label,col in zip(profiles,labels,colors):
    rr=[r for r in curves if r['profile']==p];axs[0,1].plot([float(r['X_um']) for r in rr],[float(r['Y_um']) for r in rr],color=col,lw=2,label=label)
axs[0,1].set(xlabel='Horizontal coordinate (micrometres)',ylabel='Displacement (micrometres)',title='B. Free arm after separation; fixed root diagnostic')
axs[0,1].set_aspect('equal',adjustable='box');axs[0,1].grid(alpha=.2)
ref=[next(r for r in R['beam_cases'] if r['profile']==p and r['E_Pa']==3e8 and r['F_N']==1e-4 and r['contact_fraction']==1) for p in profiles]
x=np.arange(4);w=.34
axs[1,0].bar(x-w/2,[r['linear_contact_y_um'] for r in ref],w,label='Small-deflection formula',color='#bac5cf')
axs[1,0].bar(x+w/2,[r['contact_y_um'] for r in ref],w,label='Large-rotation elastica',color=colors)
axs[1,0].set_xticks(x,labels);axs[1,0].set(ylabel='Loaded-point displacement (micrometres)',title='C. Linear extrapolation can substantially overestimate bending')
axs[1,0].legend(fontsize=8);axs[1,0].grid(axis='y',alpha=.2)
half=[next(r for r in R['beam_cases'] if r['profile']==p and r['E_Pa']==3e8 and r['F_N']==1e-4 and r['contact_fraction']==.5) for p in profiles]
axs[1,1].bar(x-w/2,[r['max_surface_normal_MPa'] for r in half],w,label='Force applied halfway',color='#bac5cf')
axs[1,1].bar(x+w/2,[r['max_surface_normal_MPa'] for r in ref],w,label='Force applied at tip',color=colors)
axs[1,1].set_xticks(x,labels);axs[1,1].set(ylabel='Peak surface normal stress (MPa)',title='D. Contact position changes the design ranking')
axs[1,1].legend(fontsize=8);axs[1,1].grid(axis='y',alpha=.2)
fig.suptitle('H39 service-load diagnostics: length 300 micrometres, E = 300 MPa, force = 100 micronewtons\nAssumed inputs; elastic model only; no 50 C material qualification or snow validation',fontsize=13)
fig.savefig(P/'figure1_service_arm_profiles.png',dpi=170);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(13,5),layout='constrained')
lengths=np.linspace(.1,7,200)
for width,col in zip([10,20,40],['#556577','#147d92','#cb6a36']):
    speed=50*(40/width)/2400
    ax[0].plot(lengths,30*lengths/speed,label=str(width)+' m working width',color=col,lw=2)
ax[0].axhline(10000,ls='--',color='#7562a8',label='10,000 cycles: reference only')
ax[0].scatter([.4,1,2],[576,1440,2880],color='#cb6a36',zorder=3)
ax[0].set(xlabel='Total active footprint in travel direction (m)',ylabel='Nominal vibration cycles at one surface point',title='A. 2,000 m2 covered in 40 min; 30 Hz')
ax[0].legend(fontsize=8,loc='upper left');ax[0].grid(alpha=.2)
sc=np.array([z['scale'] for z in R['similarity']]);counts=np.array([z['number_ratio_same_mass'] for z in R['similarity']])
ax[1].plot(sc,counts,'o-',label='Particle count at the same total mass',color='#147d92',lw=2)
ax[1].plot(sc,np.ones(len(sc)),'s--',label='Stress and relative deflection at same applied stress',color='#cb6a36',lw=2)
ax[1].set(xscale='log',yscale='log',xlabel='Geometric scale relative to the reference particle',ylabel='Ratio to reference',title='B. Smaller particles do not automatically reduce branch strain')
from matplotlib.ticker import NullFormatter
ax[1].xaxis.set_minor_formatter(NullFormatter())
ax[1].yaxis.set_minor_formatter(NullFormatter())
ax[1].set_xticks(sc,['0.25','0.5','1','2']);ax[1].set_yticks([.125,1,8,64],['0.125','1','8','64'])
ax[1].legend(fontsize=8,loc='upper right');ax[1].grid(alpha=.2,which='both')
fig.suptitle('Residence and scale constraints: ideal coverage, no lane-change losses; scale-invariant contact topology\nCycle count is not compaction success; the same acceleration does not ensure the same grain motion',fontsize=12)
fig.savefig(P/'figure2_residence_and_scaling.png',dpi=170);plt.close(fig)
print('Rendered two diagnostic figures. Matplotlib '+matplotlib.__version__)
