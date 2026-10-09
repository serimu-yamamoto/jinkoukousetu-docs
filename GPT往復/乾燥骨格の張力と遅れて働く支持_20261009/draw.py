from pathlib import Path
import sys,json,csv,math
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=json.loads((D/'results.json').read_text(encoding='utf-8'))
with (D/'support_curve.csv').open(encoding='utf-8') as f: rows=list(csv.DictReader(f))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white'})
fig,ax=plt.subplots(1,2,figsize=(11.5,4.4),gridspec_kw={'width_ratios':[1.45,1]})
labels={'slack_inverse_spec':'Delayed tautness: inverse specification','just_taut':'Initially just taut','pretension_1_5_assumed':'Pretension 1.5: linear extrapolation'}
colors=['#176B87','#DC7C22','#995495']
for (key,label),col in zip(labels.items(),colors):
 q=[x for x in rows if x['configuration']==key]
 ax[0].plot([float(x['displacement_um']) for x in q],[float(x['pressure_kPa']) for x in q],label=label,color=col,lw=2,ls='--' if 'pretension' in key else '-')
ax[0].scatter([48.15,R['basis']['x2_um']],[5,100],c='black',zorder=8)
ax[0].axvline(R['inverse_spec']['engagement_displacement_um'],color='#176B87',ls=':',alpha=.5)
ax[0].set(xlabel='Cell displacement (micrometres)',ylabel='Nominal cell pressure (kPa)',title='Same high-load endpoint does not match low-load support',xlim=(0,90),ylim=(0,110))
ax[0].legend(fontsize=8,loc='upper left');ax[0].grid(alpha=.15)
for y,color,label in [(0,'#999999','Initial chord = 200 um'),(48.15,'#DC7C22','x = 48.15 um'),(86.60254,'#176B87','x = 86.60 um')]:
 ax[1].plot([-100,0,100],[0,-y,0],color=color,lw=2,label=label)
ax[1].scatter([-100,100],[0,0],c='black',s=35)
ax[1].text(0,18,'Fixed anchors; ideal central loading',ha='center',fontsize=9)
ax[1].text(0,-145,'Natural half-band length = 109.25 um\nSlack ends at x = 44.00 um\nOrange: 48.15 um; blue: 86.60 um\nAnchors, contact and drainage not modeled',ha='center',fontsize=9)
ax[1].set(xlim=(-125,125),ylim=(-180,35),aspect='equal');ax[1].axis('off')
fig.suptitle('H69 support counterexample | uncalibrated material law, no physical test',fontsize=13)
fig.text(.5,.012,'The 1.5 pretension example reaches 98.4% band strain; it is not a validated material design.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.055,1,.93));fig.savefig(D/'figure1_support.png',dpi=170);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(11.5,4.4))
m=R['band_material_budget'];bars=ax[0].bar([str(x['E_MPa_assumed_or_proxy']) for x in m],[x['band_mass_kg_for_reference_bed']/1000 for x in m],color=['#DC7C22','#4CA1A3','#176B87'])
for b,x in zip(bars,m):ax[0].text(b.get_x()+b.get_width()/2,b.get_height()+.7,f"{x['band_mass_kg_for_reference_bed']/1000:.2f}",ha='center')
ax[0].set(xlabel='Band modulus (MPa): 1.35 reference, 5/20 assumed',ylabel='Band material alone (tonnes)',title='Supporting elements can dominate material mass',ylim=(0,65));ax[0].grid(axis='y',alpha=.15)
a=R['factory_basis']['case_factor2_yield80']['patterned_area_m2'];rates=[1,10,100];costs=[a*x/1e6 for x in rates]
bars=ax[1].bar([str(x) for x in rates],costs,color='#176B87')
for b,y in zip(bars,costs):ax[1].text(b.get_x()+b.get_width()/2,y+3,f'{y:.2f}',ha='center')
ax[1].set(xlabel='Assumed processing unit cost (JPY per square metre)',ylabel='Area processing cost only (million JPY)',title='1.95 million square metres of precursor pattern',ylim=(0,230));ax[1].grid(axis='y',alpha=.15)
fig.suptitle('Reference bed: 2,000 m2, depth 0.45 m | assumptions, not quotations',fontsize=13)
fig.text(.5,.018,'Film footprint = 2x grain footprint; layout yield = 80%. No machine, feedstock or QA cost included.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.055,1,.93));fig.savefig(D/'figure2_material_and_area.png',dpi=170);plt.close(fig)
print('Rendered 2 figures from results.json and support_curve.csv')
