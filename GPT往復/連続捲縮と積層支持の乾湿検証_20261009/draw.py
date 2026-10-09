from pathlib import Path
import sys,csv,json
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=json.loads((D/'results.json').read_text(encoding='utf-8'))
rows=list(csv.DictReader((D/'support_curves.csv').open(encoding='utf-8')))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
colors=['#157f94','#cd743b','#7c579c']
for n,c in zip([1,8,64],colors):
    rr=[x for x in rows if int(x['layers'])==n]
    axs[0].plot([float(x['x_um']) for x in rr],[float(x['pressure_kPa']) for x in rr],label=f'{n} free layer(s)',color=c,lw=2)
axs[0].scatter([48.15,86.60254],[5,100],marker='x',s=65,c='black',label='Design points (not snow data)',zorder=5)
axs[0].set(xlabel='Central displacement (micrometres)',ylabel='Pressure (kPa)',title='Axial compliance lowers the fitted response')
axs[0].legend(fontsize=8,loc='upper left');axs[0].grid(alpha=.2)
ls=r['layer_results'];axs[1].bar(['1','8','64'],[x['high_tensile_surface_strain_estimate']*100 for x in ls],color=colors)
axs[1].set(xlabel='Number of freely sliding layers',ylabel='Estimated maximum surface strain (%)',title='Thinner layers reduce bending strain')
for i,x in enumerate(ls):axs[1].text(i,x['high_tensile_surface_strain_estimate']*100+.25,f"{x['material_multiplier']:.0f}x material",ha='center')
axs[1].set_ylim(0,11)
fig.suptitle('H70 one-mode curved ribbon: E = 1 GPa assumed; no material validation',fontsize=13)
fig.savefig(D/'figure1_support.png',dpi=160);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
axs[0].bar(['1','8','64'],[x['material_kg']/1000 for x in ls],color=colors)
axs[0].set(xlabel='Number of free layers',ylabel='Ribbon-only mass (tonnes)',title='Reference bed: 2000 square metres, 450 mm')
for i,x in enumerate(ls):axs[0].text(i,x['material_kg']/1000+.3,f"{x['material_kg']/1000:.2f} t",ha='center')
fr=list(csv.DictReader((D/'factory.csv').open(encoding='utf-8')))
selected=[x for x in fr if float(x['layout_yield_assumed'])==.8]
axs[1].bar(['1','8','64'],[float(x['web_area_m2'])/1e6 for x in selected],color=colors)
axs[1].set(xlabel='Number of separate processing layers',ylabel='Web area (million square metres)',title='500 micrometre cell pitch; layout yield 80%')
for i,x in enumerate(selected):axs[1].text(i,float(x['web_area_m2'])/1e6+1,f"{float(x['one_meter_web_speed_m_min']):.1f} m/min",ha='center')
axs[1].set_ylim(0,72)
fig.suptitle('Layer multiplication has a production cost: no vendor quotation',fontsize=13)
fig.savefig(D/'figure2_production.png',dpi=160);plt.close(fig)
print('Two conceptual calculation figures saved')
