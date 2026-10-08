"""Original H48 diagrams. pip install matplotlib; python draw.py.
Figures describe hypotheses, not manufactured geometry or measured performance.
"""
import sys,json,math
from pathlib import Path
P=Path(__file__).resolve().parent
extra=P.parents[1]/'.deps'
if extra.is_dir(): sys.path.insert(0,str(extra))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle,FancyArrowPatch
r=json.loads((P/'results.json').read_text(encoding='utf8'))
plt.rcParams.update({'font.size':11,'svg.hashsalt':'H48-original','axes.spines.top':False,'axes.spines.right':False})
def save(fig,name):
 fig.savefig(P/(name+'.png'),dpi=170,bbox_inches='tight',metadata={'Software':'H48 original diagram'})
 fig.savefig(P/(name+'.svg'),bbox_inches='tight',metadata={'Date':None})
 s=(P/(name+'.svg')).read_text(encoding='utf8'); (P/(name+'.svg')).write_text('\n'.join(z.rstrip() for z in s.splitlines())+'\n',encoding='utf8',newline='\n'); plt.close(fig)
fig,axs=plt.subplots(2,2,figsize=(12,8.8),layout='constrained')
a=axs[0,0]
a.set_title('A | Summer: local sliding faces')
a.plot([.1,.35,.5,.65,.9],[.65,.45,.38,.45,.65],lw=15,color='#8faaa3',solid_capstyle='round')
a.plot([.5,.5],[.38,.13],lw=20,color='#8faaa3',solid_capstyle='round')
for px,py in [(.1,.65),(.9,.65)]: a.plot([px-.055,px+.055],[py+.035,py+.035],lw=6,color='#2989c9')
a.plot([.0,1],[.73,.73],color='#253b54',lw=8)
a.text(.5,.9,'Ski base / retained LL platelets',ha='center')
a.text(.5,.04,'Uncoated, open root seats',ha='center')
a.text(.5,.54,'Open access',ha='center',color='#405149')
a=axs[0,1];a.set_title('B | Winter: load enters near the root')
a.plot([.1,.35,.5,.65,.9],[.65,.45,.38,.45,.65],lw=15,color='#8faaa3',solid_capstyle='round')
a.plot([.5,.5],[.38,.13],lw=20,color='#8faaa3',solid_capstyle='round')
for px,py,rr in [(.3,.69,.10),(.52,.69,.09),(.53,.49,.065),(.74,.75,.1)]:a.add_patch(Circle((px,py),rr,facecolor='#d8edf9',edgecolor='#639fc2',lw=1.5))
a.annotate('',(.52,.38),(.52,.60),arrowprops={'arrowstyle':'->','lw':2,'color':'#d8643b'})
a.annotate('',(.86,.25),(.64,.39),arrowprops={'arrowstyle':'->','lw':2,'color':'#2689c9'})
a.text(.5,.92,'Snow access + grain withdrawal resistance',ha='center')
a.text(.74,.11,'Water must have\nan independent exit',ha='center',fontsize=10)
a=axs[1,0];a.set_title('C | Every load path must remain intact')
for y,lab,c in [(.81,'Snow cohesion / interface','#d6eafa'),(.57,'Artificial grain withdrawal','#d7e7d5'),(.33,'Bed shear and buried retention','#e9e5cd'),(.09,'Ground and drainage outlets','#ddd')]:
 a.add_patch(Rectangle((.08,y-.08),.84,.16,facecolor=c));a.text(.5,y,lab,ha='center',va='center',fontsize=10)
for y in [.73,.49,.25]:a.annotate('',(.5,y-.07),(.5,y),arrowprops={'arrowstyle':'->'})
a=axs[1,1];a.set_title('D | Seasonal change uses the same material')
a.add_patch(Rectangle((.05,.57),.9,.28,facecolor='#e5f4ff'));a.text(.5,.72,'Natural snow',ha='center')
a.add_patch(Rectangle((.05,.43),.9,.14,facecolor='#b2d4c3',hatch='..'));a.text(.5,.50,'5 / 15 / 30 mm mixing trials',ha='center',fontsize=10,bbox={'facecolor':'white','edgecolor':'none','alpha':0.9})
a.add_patch(Rectangle((.05,.1),.9,.33,facecolor='#dce6de'));a.text(.5,.29,'Same functional grain bed at depth',ha='center',fontsize=10)
a.plot([.05,.95],[.1,.1],lw=3,color='#777');a.text(.5,.035,'Retention below maximum gouge + margin',ha='center',fontsize=10)
for a in axs.flat:a.set(xlim=(-.03,1.03),ylim=(-.02,1.01));a.axis('off')
fig.suptitle('H48 | Seasonal interpenetration with root load transfer',fontsize=17)
fig.supxlabel('Concept only. Not to scale. No physical tests; winter adhesion and summer ski friction are unmeasured.',fontsize=10)
save(fig,'01_mechanism')
fig,axs=plt.subplots(2,2,figsize=(12,8.7),layout='constrained')
a=axs[0,0]
for p in [.1,.3,1]:
 v=[z for z in r['engagement'] if z['active_fraction']==p and z['neck_radius_m']==.00003]
 offsets=list(range(151)); F=v[0]['required_force_N']; A=math.pi*(30e-6)**2
 a.plot(offsets,[1e7*A/(1+4*(z*1e-6)/(30e-6))/F for z in offsets],label=f'Engaged fraction {p:g}')
 a.plot([z['eccentricity_m']*1e6 for z in v],[z['force_ratio'] for z in v],'o',color=a.lines[-1].get_color())
a.axhline(1,color='black',ls='--',lw=1);a.set(xlabel='Load eccentricity (um)',ylabel='Section limit / required force',title='A | Root loading, r = 30 um');a.legend(fontsize=9)
a=axs[0,1]
for d in [.002,.01,.03]:
 v=[z for z in r['drainage'] if z['skin_depth_m']==d and z['inflow_normal_m_h']==.02 and z['skin_K_ratio']>0]
 a.semilogx([z['skin_K_ratio'] for z in v],[1000*z['zero_head_capacity_m_h'] for z in v],'o-',label=f'Skin {d*1000:g} mm')
a.axhline(20,color='black',ls='--',lw=1,label='20 mm/h normal inflow');a.set(xlabel='Skin K / bulk K',ylabel='Zero-head capacity (mm/h)',title='B | Thin blocked layer controls drainage');a.legend(fontsize=8)
a=axs[1,0]
for T in [2,5,10]:
 v=[z for z in r['heat'] if z['initial_temperature_above_zero_K']==T]
 a.plot([100*z['water_volume_fraction'] for z in v],[z['potential_water_equivalent_mm'] for z in v],'o-',label=f'Initial +{T:g} C')
a.set(xlabel='Water volume / total bed volume (%)',ylabel='Sensible-heat melt allocation (mm WE)',title='C | Retained water adds initial heat');a.legend(fontsize=9)
a=axs[1,1];v=r['cost'];a.bar([1,3,6],[z['capital_plus_legacy_cap_JPY']/1e6 for z in v],width=.8,color=['#379082','#cc974e','#bc5e49']);a.axhline(200,color='black',ls='--');a.set(xlabel='Added tool capital, tax included (million JPY)',ylabel='Legacy cap + addition (million JPY)',title='D | 198 M JPY budget has only 2 M headroom',ylim=(195,206),xticks=[1,3,6])
fig.suptitle('H48 | Uncalibrated design boundaries, not performance predictions',fontsize=16)
fig.supxlabel('Bulk K = 0.3 m/h; bed depth = 0.45 m. Strength, engagement, thermal state and all costs are hypotheses.',fontsize=10)
save(fig,'02_boundaries')
print('Created 2 original figures, PNG and SVG.')
