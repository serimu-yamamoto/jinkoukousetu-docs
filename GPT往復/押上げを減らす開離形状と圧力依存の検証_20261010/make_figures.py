from pathlib import Path
import sys,json,math
D=Path(__file__).resolve().parent
local=D.parents[1]/'.git'/'research98-deps'
if local.exists():sys.path.insert(0,str(local))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
R=json.loads((D/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,3,figsize=(15,4.9),layout='constrained')
x=np.linspace(0,0.5,401)
for h,color in [(0.02,'#006d77'),(0.2,'#c05027')]:
 d=np.pi*h*np.sin(np.pi*x/.5)/(2*.5)
 tau=20*(.2+d)/(1-.2*d)+3*(1-x/.5)
 axes[0].plot(x,tau,label=f'Rise {h:.2f} mm',color=color,lw=2)
axes[0].set(xlabel='Horizontal release travel (mm)',ylabel='Resistance / patch area (kPa)',title='A  Same contact friction, different climb')
axes[0].legend();axes[0].text(.02,.97,'Cosine path; p = 20 kPa; particle mu = 0.2',transform=axes[0].transAxes,va='top',fontsize=8)
cases=R['single_pressure_match']['cases']
for key,label,color in [('deep_kPa','Deep path / weak latch','#c05027'),('shallow_kPa','Shallow path / stronger latch','#006d77')]:
 axes[1].plot([r['p_kPa'] for r in cases],[r[key] for r in cases],'o-',label=label,color=color)
axes[1].set(xlabel='Confining patch pressure (kPa)',ylabel='Initial release resistance (kPa)',title='B  One pressure cannot identify geometry')
axes[1].legend(fontsize=8);axes[1].axvline(20,color='gray',ls=':',lw=1)
for mu,color in [(0.1,'#457b9d'),(0.2,'#006d77'),(0.4,'#c05027')]:
 d=np.linspace(0,.7,300);axes[2].plot(d,(mu+d)/(1-mu*d),label=f'Particle mu = {mu}',color=color)
axes[2].axhline(.3,color='gray',ls='--',label='Diagnostic B = 0.3')
axes[2].set(xlabel='Local climb slope dh/dx',ylabel='Ramp resistance / normal pressure',title='C  Low lift has a friction floor',ylim=(0,1.4))
axes[2].legend(fontsize=8)
for ax in axes:ax.grid(alpha=.18)
fig.suptitle('Cycle 98 | Assumed contact model, not ski or snow measurements',fontsize=14)
fig.savefig(D/'pressure_and_release.png',dpi=160)
plt.close(fig)
# Independent functional diagram, not production CAD. Section and plan are distinct views.
fig,ax=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
for a in ax:a.set_aspect('equal');a.axis('off')
ax[0].plot([0,1,3,4],[0,0,1.2,1.2],lw=6,color='#c05027')
ax[0].plot([0,1,3,4],[-1,-1,-.88,-.88],lw=6,color='#006d77')
ax[0].annotate('',(2.6,1.8),(2.6,2.4),arrowprops={'arrowstyle':'->','lw':2})
ax[0].text(2.8,2,'Normal load',fontsize=10)
ax[0].text(0,.6,'Deep rising escape',fontsize=10);ax[0].text(0,-1.65,'Shallow escape: retain vertical support separately',fontsize=10)
ax[0].set(xlim=(-.3,5.1),ylim=(-2.1,2.7),title='Section: reduce rise along the escape path')
# Top view: open radial windows; no guaranteed motion in random packing.
for angle in [0,120,240]:
 t=math.radians(angle);u=np.array([math.cos(t),math.sin(t)]);v=np.array([-u[1],u[0]])
 for sign in [-1,1]:
  p0=.35*u+sign*.18*v;p1=1.5*u+sign*.3*v
  ax[1].plot([p0[0],p1[0]],[p0[1],p1[1]],color='#006d77',lw=6,solid_capstyle='round')
 ax[1].annotate('',1.9*u,.8*u,arrowprops={'arrowstyle':'->','color':'#c05027','lw':2})
ax[1].add_patch(plt.Circle((0,0),.3,color='#457b9d'))
ax[1].text(-2.1,-2,'Rounded open seats / multiple release directions\nNo closed ring; dimensional feasibility unverified',fontsize=9)
ax[1].set(xlim=(-2.3,2.4),ylim=(-2.3,2.2),title='Plan: H98-O functional candidate')
fig.suptitle('Schematic only | Local horizontal escape does not ensure low lift in a tilted grain',fontsize=12)
fig.savefig(D/'concept.png',dpi=160)
print('Two original figures generated; no source figure reproduced')
