"""Cycle 40: published-figure readings and arithmetic, never physical validation.
Run with Python 3.12 + Pillow + matplotlib; --no-plots only skips rendering.
"""
import csv, json, math, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
repo=ROOT.parents[1]
if (repo/'.deps').exists(): sys.path.insert(0,str(repo/'.deps'))
from PIL import Image
I=json.loads((ROOT/'inputs.json').read_text(encoding='utf-8'))
checks=[]
def check(name, condition):
    if not condition: raise AssertionError(name)
    checks.append(name)
def write_csv(name,rows):
    with (ROOT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
c=I['creep'];a=c['axis'];im=Image.open(ROOT/c['image']).convert('RGB')
check('source crop dimensions',im.size==(c['image_width'],c['image_height']))
check('time axis monotone',a['x_end']>a['x0'] and a['t_end_s']>0)
check('strain axis monotone',a['y_zero']>a['y_top'] and a['strain_top_percent']>0)
samples=[]
for t in c['time_s']:
    x=round(a['x0']+(a['x_end']-a['x0'])*t/a['t_end_s'])
    for name in ['PHBV','PHBV_TPU','PHBV_TPU_HMDI']:
        hits=[]
        for xx in range(x-c['reading_window_px'],x+c['reading_window_px']+1):
            for yy in range(100,570):
                r,g,b=im.getpixel((xx,yy))
                match=(r<100 and g<100 and b<100) if name=='PHBV' else (r>160 and g<140 and b<140) if name=='PHBV_TPU' else (b>160 and r<140 and g<140)
                if match: hits.append(yy)
        row={'material':name,'time_s':t,'image_x':x,'pixel_y_min':None,'pixel_y_max':None,'strain_percent':None,'reading_low_percent':None,'reading_high_percent':None,'apparent_secant_MPa':None,'status':'curve not present here; not evidence of failure'}
        if hits:
            lo,hi=min(hits),max(hits)
            convert=lambda y:(a['y_zero']-y)/(a['y_zero']-a['y_top'])*a['strain_top_percent']
            value=convert((lo+hi)/2)
            row.update(pixel_y_min=lo,pixel_y_max=hi,strain_percent=value,reading_low_percent=math.floor(convert(hi+c['reading_y_allowance_px'])*10)/10,reading_high_percent=math.ceil(convert(lo-c['reading_y_allowance_px'])*10)/10,apparent_secant_MPa=c['nominal_tensile_stress_MPa']/(value/100),status='figure digitization; allowance is not a confidence interval')
        samples.append(row)
check('11 readings and one absent curve',sum(r['strain_percent'] is not None for r in samples)==11)
check('TPU curve absent at 8 hours',[r['strain_percent'] for r in samples if r['material']=='PHBV_TPU' and r['time_s']==28800]==[None])
five={r['material']:r for r in samples if r['time_s']==18000}
check('5-hour order read from graph',five['PHBV']['strain_percent']<five['PHBV_TPU_HMDI']['strain_percent']<five['PHBV_TPU']['strain_percent'])
check('source reading intervals contain central readings',all(r['reading_low_percent']<=r['strain_percent']<=r['reading_high_percent'] for r in samples if r['strain_percent'] is not None))
write_csv('creep_readings.csv',samples)
fractions=[]
for name,weights in [('PHBV',[100,0,0]),('PHBV_TPU',[100,30,0]),('PHBV_TPU_HMDI',[100,30,1])]:
    values=[100*w/sum(weights) for w in weights]
    fractions.append(dict(material=name,PHBV_mass_percent=values[0],TPU_mass_percent=values[1],HMDI_feed_mass_percent=values[2]))
check('phr conversion conserves mass',all(abs(sum(list(r.values())[1:])-100)<1e-10 for r in fractions))
check('TPU phr is not 30 weight percent',abs(fractions[1]['TPU_mass_percent']-3000/130)<1e-10)
write_csv('composition.csv',fractions)
fibers=[]
for row in I['fibers']['rows']:
    r=dict(zip(I['fibers']['columns'],row))
    r['uts_retention_percent']=None if r['uts_initial_MPa'] is None else 100*r['uts_aged_MPa']/r['uts_initial_MPa']
    r['break_strain_retention_percent']=None if r['break_strain_initial_percent'] is None else 100*r['break_strain_aged_percent']/r['break_strain_initial_percent']
    fibers.append(r)
check('missing original sample remains missing',fibers[6]['uts_retention_percent'] is None and fibers[6]['break_strain_retention_percent'] is None)
check('largest initial UTS loses strength',next(r for r in fibers if r['id']=='1846-III')['uts_retention_percent']<100)
check('maximum retained elongation differs from maximum initial UTS',max(fibers,key=lambda r:r['break_strain_aged_percent'])['id']!=max(fibers,key=lambda r:r['uts_initial_MPa'] or -1)['id'])
write_csv('fiber_aging.csv',fibers)
b=I['cost']; rate=b['discount_rate'];n=b['years'];af=(1-(1+rate)**(-n))/rate
check('annuity formula matches annual discount sum',abs(af-sum((1+rate)**(-t) for t in range(1,n+1)))<1e-12)
M=b['mass_kg'];P=b['base_finished_price_JPY_kg'];old=b['lambda_old'];baseline=M*P*(1/af+old)
costs=[]
for q in b['conditioning_surcharge_JPY_kg']:
    lambda_max=P/(P+q)*(1/af+old)-1/af
    check('break-even reconstructed q='+str(q),abs(M*(P+q)*(1/af+lambda_max)-baseline)<1e-6)
    for lam in b['lambda_after_candidates']:
        treated=M*(P+q)*(1/af+lam)
        costs.append(dict(surcharge_JPY_kg=q,lambda_after=lam,lambda_max_break_even=lambda_max,required_reduction_percentage_points=100*(old-lambda_max),material_annual_JPY=treated,saving_annual_JPY=baseline-treated))
check('no lifetime benefit means extra cost',all(r['saving_annual_JPY']<0 for r in costs if r['lambda_after']==old))
qmax=P*(old-.1)/(1/af+.1)
check('price ceiling reconstruction',abs(M*(P+qmax)*(1/af+.1)-baseline)<1e-6)
write_csv('cost_sensitivity.csv',costs)
summary={'schema':'cycle40-results-v1','physical_tests':0,'physical_success_probability':None,'literature_graph_points':11,'literature_fiber_rows':9,'cost_assumption_cases':9,'five_hour_readings':five,'annual_factor':af,'baseline_material_annual_JPY':baseline,'conditioning_ceiling_JPY_kg_if_lambda_20_to_10_percent':qmax,'material_budget_example_JPY_year':10000000,'finished_price_ceiling_JPY_kg_for_10M_material_budget':{str(lam):10000000/(M*(1/af+lam)) for lam in [.1,.2]},'checks_passed':len(checks),'checks':checks,'scope':'External literature readings and arithmetic. No ski, wet, full-depth or 50 C branch experiment performed.'}
(ROOT/'results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
if '--no-plots' not in sys.argv:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
    colors={'PHBV':'#334155','PHBV_TPU':'#b91c1c','PHBV_TPU_HMDI':'#2563eb'}
    for name,color in colors.items():
        rows=[r for r in samples if r['material']==name and r['strain_percent'] is not None]
        y=[r['strain_percent'] for r in rows]
        axs[0].errorbar([r['time_s']/3600 for r in rows],y,yerr=[[r['strain_percent']-r['reading_low_percent'] for r in rows],[r['reading_high_percent']-r['strain_percent'] for r in rows]],fmt='o',capsize=3,label=name.replace('_','/'),color=color)
    axs[0].set(xlabel='Time under nominal 15 MPa tensile load (h)',ylabel='Total tensile strain (%)',title='50 C: readings from published Figure 10c',ylim=(0,5.6));axs[0].legend(fontsize=8);axs[0].grid(alpha=.2)
    fs=[r for r in fibers if r['uts_retention_percent'] is not None]
    xs=list(range(len(fs)))
    axs[1].scatter(xs,[r['uts_retention_percent'] for r in fs],label='Ultimate tensile strength',marker='o',color='#0f766e')
    axs[1].scatter(xs,[r['break_strain_retention_percent'] for r in fs],label='Elongation at break',marker='s',color='#a16207')
    axs[1].axhline(100,color='#94a3b8',lw=1,ls='--');axs[1].set_xticks(xs,[r['id'] for r in fs],rotation=40,ha='right')
    axs[1].set(ylabel='33-month / initial mean (%)',title='PHBH fibers: published Table 6');axs[1].legend(fontsize=8);axs[1].grid(alpha=.2)
    fig.suptitle('Literature evidence, not artificial-firn validation',fontsize=14)
    fig.supxlabel('Left: graphical reading allowances only; missing 8 h TPU curve is not a failure time. Right: not creep recovery.',fontsize=9)
    fig.savefig(ROOT/'literature_comparison.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4.8),layout='constrained')
    for q in b['conditioning_surcharge_JPY_kg']:
        rows=[r for r in costs if r['surcharge_JPY_kg']==q]
        ax.plot([r['lambda_after']*100 for r in rows],[r['saving_annual_JPY']/1e6 for r in rows],'o-',label=f'Assumed surcharge {q} JPY/kg')
    ax.axhline(0,color='#334155',lw=1);ax.set(xlabel='Assumed annual new replacement mass / bed inventory (%)',ylabel='Annualized material cost saving (million JPY/year)',title='Conditioning is economical only if replacement falls');ax.legend(fontsize=9);ax.grid(alpha=.2)
    fig.supxlabel('Assumptions: 108 t; base 1,000 JPY/kg; prior replacement 20%/year; 10 years at 8%. No quote or measured lifetime.',fontsize=8)
    fig.savefig(ROOT/'conditioning_cost.png',dpi=180);plt.close(fig)
print(json.dumps({'checks_passed':len(checks),'graph_points':11,'physical_tests':0,'five_hour_strain_percent':{k:round(v['strain_percent'],3) for k,v in five.items()},'qmax_JPY_kg':round(qmax,2)}))
