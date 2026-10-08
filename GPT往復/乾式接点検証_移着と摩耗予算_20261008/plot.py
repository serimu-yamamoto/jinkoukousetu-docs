from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
R=json.loads((P/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,2,figsize=(13,5.2),layout='constrained')
qs=[j/500 for j in range(501)]
a=math.exp(-1.6/10);b=1-a
before=[(1-q)*b/(q+(1-q)*b) for q in qs]
mean=[1-(1-c)*10/1.6*b for c in before]
ax[0].plot(qs,[.22-.14*c for c in before],label='Steady start / peak',color='#c45525')
ax[0].plot(qs,[.22-.14*c for c in mean],label='Steady pass average',color='#217b91')
ax[0].axhline(.22,ls=':',color='#555',label='Fresh first point')
ax[0].axhline(.1,ls='--',color='black',label='Diagnostic target (assumed)')
ax[0].set(xlabel='Fraction of load paths reset between passes',ylabel='Total friction coefficient (hypothetical)',ylim=(.06,.24),title='A low steady coefficient does not establish cold-start glide')
ax[0].legend(fontsize=9)
for depth,col in [(10,'#217b91'),(20,'#d99400'),(40,'#8658a5')]:
    ns=[10**(2+j*2/200) for j in range(201)]
    ax[1].loglog(ns,[depth*1e-6/(5e6*n*1.6) for n in ns],label=f'{depth} um usable wear depth',color=col)
ax[1].set(xlabel='Loaded passes on the same contact region',ylabel='Maximum local wear coefficient k (m2/N)',title='Required wear resistance; no measured PEI cap k')
ax[1].text(.03,.06,'Mean pressure 5 MPa; slip 1.6 m/pass\nConstant geometry only',transform=ax[1].transAxes,fontsize=9)
ax[1].legend(fontsize=9,loc='upper right');ax[1].grid(which='both',alpha=.15)
fig.suptitle('Cycle 23 | Conditional requirements, not experimental performance',fontsize=13)
fig.savefig(P/'runin_and_wear_limits.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(13,5.4),layout='constrained')
ax[0].add_patch(Rectangle((-60,-45),120,45,facecolor='#d9e3df',edgecolor='#63796e'))
ax[0].add_patch(Rectangle((-30,-30),60,30,facecolor='#eac786',edgecolor='#95692c',lw=2))
xs=[-30+j*.3 for j in range(201)]
ys=[math.sqrt(150**2-x*x)-math.sqrt(150**2-30**2) for x in xs]
ax[0].fill_between(xs,0,ys,color='#eac786');ax[0].plot(xs,ys,color='#95692c',lw=2)
a0=next(x['a_um'] for x in R['contact_cases'] if x['effective_E_MPa']==300 and x['R_um']==150 and x['group_force_mN']==6.48)
ax[0].plot([-a0,a0],[3.7,3.7],color='#245d86',lw=5)
ax[0].annotate('Model contact radius a = 8.47 um\nunder the assumed Hertz pair',xy=(0,4),xytext=(0,24),ha='center',arrowprops={'arrowstyle':'->'})
ax[0].text(0,-15,'Hard contact region\n30 um reference depth',ha='center',va='center',fontsize=10)
ax[0].text(0,-39,'Semicrystalline particle support',ha='center',fontsize=10)
ax[0].annotate('',xy=(-30,-49),xytext=(30,-49),arrowprops={'arrowstyle':'<->'})
ax[0].text(0,-54,'Region diameter 60 um',ha='center')
ax[0].text(0,-67,'Section only; not a validated joint or grain.\nAdded shape volume allowance = 20% (assumed).',ha='center',fontsize=9)
ax[0].set(xlim=(-76,76),ylim=(-74,44),aspect='equal',title='Local contact, with snow/holding paths left elsewhere')
ax[0].axis('off')
rads=[20,30,50]
for alpha,col in [(0,'#217b91'),(.1,'#c45525')]:
    vals=[next(x['annual_added_material_JPY']/1e6 for x in R['cost_cases'] if x['radius_um']==r and x['depth_um']==30 and x['shape_factor']==1.2 and x['price_JPY_kg']==10000 and x['extra_contact_replacement_fraction_year']==alpha) for r in rads]
    offs=-2 if alpha==0 else 2
    ax[1].bar([r+offs for r in rads],vals,width=3.5,color=col,label=f'Additional renewal {alpha*100:g}% / year')
ax[1].axhline(R['remaining_annual_JPY']/1e6,color='black',ls='--',label='Shared annual margin')
ax[1].set(xlabel='Contact-region radius (um)',ylabel='Added material cost (million JPY/year)',xticks=rads,title='Material alone can use the entire annual margin')
ax[1].text(.03,.72,'Hypothetical price 10,000 JPY/kg\nDepth 30 um; shape factor 1.2\nAll 108 t of particles; processing cost extra',transform=ax[1].transAxes,fontsize=9)
ax[1].legend(fontsize=9,loc='upper left');ax[1].grid(axis='y',alpha=.15)
fig.suptitle('Cycle 23 | Localizing expensive material has contact and durability limits',fontsize=13)
fig.savefig(P/'contact_and_cost.png',dpi=180);plt.close(fig)
print('Wrote2 figures')
