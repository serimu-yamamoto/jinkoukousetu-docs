"""Replace collision-prone straight bracing by a continuous equatorial hoop.
Analytical distance to a circle plus an angular grid covering bound certifies
ONLY the registered nominal rigid path. No random capture or strength claim.
"""
import copy,json,math
from calculate import H,frame,cost,np

def distance(inp):
    g=inp['geometry'];R=g['R_mm'];q=g['q_mm'];p=np.linspace(math.radians(g['opening_deg']/2),2*math.pi-math.radians(g['opening_deg']/2),g['distance_samples']);x=R*np.cos(p);y=R*np.sin(p)
    best=None
    for side in ['A_hoop_B_arc','B_hoop_A_arc']:
        s=np.clip(-x if side=='A_hoop_B_arc' else x,g['s_min_mm'],g['s_max_mm'])
        dx=s+x if side=='A_hoop_B_arc' else x-s
        rho=np.sqrt((y+q)**2+q*q) if side=='A_hoop_B_arc' else np.sqrt((y-q)**2+q*q)
        d=np.sqrt(dx*dx+(rho-R)**2);k=int(np.argmin(d))
        if best is None or d[k]<best['upper_mm']:best=dict(upper_mm=float(d[k]),side=side,phi_deg=float(math.degrees(p[k])),s_mm=float(s[k]))
    err=2*R*math.sin((p[1]-p[0])/4);best.update(lower_mm=max(0,best['upper_mm']-err),grid_cover_bound_mm=err)
    return best

def hoopcost(inp,radius):
    c=inp['cost'];R=inp['geometry']['R_mm'];base=cost(inp,None,0);V=base['volume_upper_mm3']+2*math.pi*R*math.pi*radius**2
    rho=V*1e-9*c['number_density_m3']*c['matrix_density_kg_m3'];mass=c['area_m2']*c['depth_m']*rho;crf=c['discount']*(1+c['discount'])**c['years']/((1+c['discount'])**c['years']-1);fixed=c['initial_other_JPY']*crf+c['annual_other_JPY'];factor=crf+c['replacement']
    return dict(volume_upper_mm3=V,bulk_kg_m3=rho,pilot_mass_kg=mass,annual_equivalent_JPY=fixed+mass*c['assumed_price_JPY_kg']*factor,finished_price_cap_JPY_kg=(c['annual_budget_JPY']-fixed)/(mass*factor))

def main():
    inp=json.loads((H/'inputs.json').read_text(encoding='utf-8'));models=[]
    for opening in [64,90,120,150]:
        cur=copy.deepcopy(inp);cur['geometry']['opening_deg']=opening;dg=distance(cur);unbraced=frame(cur)
        for radius_um in [3,6,12,18,22]:
            b=radius_um/1000;model=frame(cur,brace_a=b,closed_hoop=True)
            a=cur['geometry']['wire_radius_mm'];q=cur['geometry']['q_mm'];R=cur['geometry']['R_mm'];s=cur['geometry']['s_min_mm'];theta=math.radians(opening/2)
            assert 2*q<=R*math.sin(theta) and s-R*(1-math.cos(theta))>q
            arcgap=q-2*a;hoopgap=dg['lower_mm']-a-b;parallelgap=s-2*b
            models.append(dict(opening_deg=opening,hoop_radius_um=radius_um,distance=dg,nominal_rigid_surface_gap_lower_um=1000*min(arcgap,hoopgap,parallelgap),hoop_arc_surface_gap_lower_um=1000*hoopgap,cost=hoopcost(cur,b),mechanics=model,unbraced_same_opening=unbraced,comparison='registered nominal pose; internal joints treated rigid; no physical pass'))
    balanced_models=[]
    for opening in [64,120,150]:
        cur=copy.deepcopy(inp);cur['geometry']['opening_deg']=opening
        balanced_models.append(dict(opening_deg=opening,hoop_radius_um=22,hoop=frame(cur,brace_a=.022,closed_hoop=True,balanced=True),unbraced=frame(cur,balanced=True)))
    out=dict(metadata=inp['probability'],models=models,balanced_models=balanced_models,geometry_scope='All arc/arc pairs use prior analytic bound; hoop/arc distances use analytic closest circle and continuous-parameter covering bound; hoop/hoop pairs have plane separation at least s_min. No orientation or manufacturing tolerance extension.')
    assert all(x['nominal_rigid_surface_gap_lower_um']>0 for x in models)
    (H/'hoop_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'models':len(models),'physical_tests':0,'success_probability':None,'minimum_nominal_gap_um':min(x['nominal_rigid_surface_gap_lower_um'] for x in models)},indent=2))
if __name__=='__main__':main()
