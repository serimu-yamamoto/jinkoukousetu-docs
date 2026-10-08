"""Branch retention diagnostics. No ski/material success probability is computed."""
from pathlib import Path
import json, math, random, statistics, csv, itertools
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
b=I['beam']; n=I['network']; c=I['cost']; checks=[]
def check(name,ok,details=None):
    checks.append({'name':name,'passed':bool(ok),'details':details})
    if not ok: raise AssertionError(name)
def near(name,a,z,tol=1e-9): check(name,math.isclose(a,z,rel_tol=tol,abs_tol=tol),{'actual':a,'expected':z})
def avg_factor(a): return 1+2*a/3+a*a/5
def radius(s,a): return b['reference_min_radius_m']*math.sqrt(avg_factor(b['reference_taper_a'])/avg_factor(a))*(1+a*(2*s-1)**2)
def volume_fraction(s,a):
    u=2*s-1; den=avg_factor(a)
    return (u+2*a*u**3/3+a*a*u**5/5+den)/(2*den)
beam=[]; curves=[]
for a in b['taper_a_values']:
    for ratio in b['axial_to_shear_force_ratios']:
        V=b['shear_force_N']; N=V*ratio; vals=[]
        for k in range(b['sample_points']):
            s=k/(b['sample_points']-1); r=radius(s,a); M=V*b['length_m']*(0.5-s)
            sa=abs(N)/(math.pi*r*r); sb=4*abs(M)/(math.pi*r**3)
            # These two stresses occur at different cross-section positions; do not combine them into a fabricated failure index.
            tau=4*abs(V)/(3*math.pi*r*r)
            vals.append((s,sa+sb,tau,sb,sa,r))
        peak=max(vals,key=lambda t:t[1]); center=vals[(b['sample_points']-1)//2]
        ustar=1 if a<=0.2 else 1/math.sqrt(5*a)
        beam.append({'a':a,'N_over_V':ratio,'r_mid_um':radius(0.5,a)*1e6,'r_node_um':radius(0,a)*1e6,'peak_surface_normal_MPa':peak[1]/1e6,'first_peak_x_over_L':peak[0],'symmetric_peak_x_over_L':1-peak[0],'center_normal_MPa':center[1]/1e6,'center_shear_max_MPa':center[2]/1e6,'pure_bending_analytic_first_peak':(1-ustar)/2,'peak_in_middle_20_percent':abs(peak[0]-.5)<=.10001,'L_over_max_diameter':b['length_m']/(2*radius(0,a))})
        if ratio in [0,20]:
            for s,sn,tau,sb,sa,r in vals[::20]: curves.append({'a':a,'N_over_V':ratio,'x_over_L':s,'r_um':r*1e6,'surface_normal_MPa':sn/1e6,'bending_MPa':sb/1e6,'centerline_shear_MPa':tau/1e6})
        if ratio==0:
            near('beam_analytic_peak_a'+str(a),min(peak[0],1-peak[0]),(1-ustar)/2,0.00026)
            near('zero_midpoint_bending_a'+str(a),center[3],0)
            near('constant_strut_volume_a'+str(a),radius(.5,a)**2*avg_factor(a),b['reference_min_radius_m']**2*avg_factor(b['reference_taper_a']),1e-18)
# Diamond topology: four tetrahedral neighbors, periodic in all directions.
def network_graph(ncell):
    bases=[(0,0,0),(0,2,2),(2,0,2),(2,2,0)]; period=4*ncell
    A=[(4*i+x,4*j+y,4*k+z) for i in range(ncell) for j in range(ncell) for k in range(ncell) for x,y,z in bases]
    B=[((x+1)%period,(y+1)%period,(z+1)%period) for x,y,z in A]
    nodes=A+B; lookup={t:i for i,t in enumerate(nodes)}
    offsets=[(1,1,1),(1,-1,-1),(-1,1,-1),(-1,-1,1)]
    edges=[(idx,lookup[((x+dx)%period,(y+dy)%period,(z+dz)%period)]) for idx,(x,y,z) in enumerate(A) for dx,dy,dz in offsets]
    return nodes,edges
nodes,edges=network_graph(n['diamond_cells_each_axis']); nv=len(nodes); ne=len(edges)
deg=[0]*nv
for i,j in edges: deg[i]+=1;deg[j]+=1
check('fourfold_connectivity',set(deg)=={4});near('node_count',nv,8*n['diamond_cells_each_axis']**3);near('edge_count',ne,2*nv)
check('unique_edges',len(set(tuple(sorted(e)) for e in edges))==ne)
def run_case(p,mode,kerf,seed,a=1):
    rnd=random.Random(seed); flags=[rnd.random()<p for _ in edges]; uniforms=[rnd.random() for _ in edges]
    parent=list(range(nv)); size=[1]*nv
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]];x=parent[x]
        return x
    def union(x,y):
        x=find(x);y=find(y)
        if x==y:return
        if size[x]<size[y]:x,y=y,x
        parent[y]=x;size[x]+=size[y]
    for (i,j),cut in zip(edges,flags):
        if not cut:union(i,j)
    roots=[find(i) for i in range(nv)]; counts={}
    for r in roots:counts[r]=counts.get(r,0)+1
    mass={r:0.0 for r in counts}; arms=[[] for _ in nodes]; removed=0.0
    lo,hi=n['cut_position_modes'][mode]
    for (i,j),cut,u in zip(edges,flags,uniforms):
        if not cut: mass[roots[i]]+=1;continue
        x=lo+(hi-lo)*u; left=max(0,x-kerf/2);right=min(1,x+kerf/2)
        ml=volume_fraction(left,a);mr=1-volume_fraction(right,a)
        mass[roots[i]]+=ml;mass[roots[j]]+=mr;removed+=1-ml-mr
        arms[i].append(left);arms[j].append(1-right)
    isolated=[i for i in range(nv) if counts[roots[i]]==1]
    acceptable=[i for i in isolated if len(arms[i])==4 and max(arms[i])<=n['max_arm_fraction'] and sum(x>=n['min_long_arm_fraction'] for x in arms[i])>=n['min_long_arms']]
    good=sum(mass[roots[i]] for i in acceptable);single=sum(mass[roots[i]] for i in isolated);multi=sum(v for k,v in mass.items() if counts[k]>1)
    total=good+(single-good)+multi+removed
    if not math.isclose(total,ne,rel_tol=1e-11):raise AssertionError('mass conservation')
    return {'mass_profile_a':a,'p_input':p,'mode':mode,'removed_length_fraction':kerf,'seed':seed,'cut_edges_fraction':sum(flags)/ne,'isolated_node_fraction':len(isolated)/nv,'geometry_only_node_fraction':len(acceptable)/nv,'geometry_only_mass_fraction':good/ne,'single_reject_mass_fraction':(single-good)/ne,'cluster_mass_fraction':multi/ne,'removed_mass_fraction':removed/ne,'component_count':len(counts),'largest_component_nodes':max(counts.values()),'mass_balance_error':abs(total/ne-1)}
runs=[run_case(p,mode,gap,seed,a) for a in n['mass_profile_taper_a_values'] for p in n['cut_edge_probabilities'] for mode in n['cut_position_modes'] for gap in n['removed_length_fractions'] for seed in n['seeds']]
summary=[]
keys=['cut_edges_fraction','isolated_node_fraction','geometry_only_node_fraction','geometry_only_mass_fraction','single_reject_mass_fraction','cluster_mass_fraction','removed_mass_fraction']
for a,p,mode,gap in itertools.product(n['mass_profile_taper_a_values'],n['cut_edge_probabilities'],n['cut_position_modes'],n['removed_length_fractions']):
    rows=[r for r in runs if r['mass_profile_a']==a and r['p_input']==p and r['mode']==mode and r['removed_length_fraction']==gap]
    out={'mass_profile_a':a,'p_input':p,'mode':mode,'removed_length_fraction':gap,'n_seeds':len(rows),'independent_cut_isolated_node_expectation':p**4}
    for key in keys:
        vv=[r[key] for r in rows];out[key+'_mean']=statistics.mean(vv);out[key+'_min']=min(vv);out[key+'_max']=max(vv)
    if gap==0:out['geometry_only_node_expectation']=p**4*(0.3024 if mode=='uniform' else 1)
    summary.append(out)
# Repeat-processing ledger, intentionally ideal: same one-pass yield each pass, full restoration before each pass.
cost=[]
for row in summary:
    if row['p_input'] not in [.9,1] or row['removed_length_fraction']!=.05:continue
    y=row['geometry_only_mass_fraction_mean']; recover=c['recovery_fraction_of_rejects']; feed_factor=1.0; gross=0.0; good=0.0
    for k in range(1,c['max_passes']+1):
        gross+=feed_factor;good+=feed_factor*y
        feed_factor*=recover*(1-y)
        initial=c['fixed_good_mass_kg']/good; grossmass=initial*gross
        raw=initial*c['raw_feed_price_JPY_kg'];process=grossmass*c['processing_JPY_kg_gross_feed']
        cost.append({'mass_profile_a':row['mass_profile_a'],'p_input':row['p_input'],'mode':row['mode'],'passes':k,'one_pass_geometric_mass_fraction':y,'good_mass_per_initial_kg':good,'gross_processed_per_initial_kg':gross,'remaining_recoverable_per_initial_kg':feed_factor,'initial_feed_kg_for_target':initial,'gross_processed_kg_for_target':grossmass,'raw_plus_assumed_processing_JPY':raw+process,'JPY_per_good_kg':(raw+process)/c['fixed_good_mass_kg'],'gross_per_good_kg':gross/good,'is_real_manufacturing_yield':False})
# Validation: structural identities, limiting cases, independently integrated volumes, seed and lattice checks.
for a in [0,1,5]:
    near('volume_start_a'+str(a),volume_fraction(0,a),0);near('volume_end_a'+str(a),volume_fraction(1,a),1)
    near('volume_symmetry_a'+str(a),volume_fraction(.27,a)+volume_fraction(.73,a),1)
for mode in ['uniform','central_band']:
    r0=run_case(0,mode,0,3800);near('uncut_component_'+mode,r0['component_count'],1)
    r1=run_case(1,mode,0,3800);near('allcut_components_'+mode,r1['component_count'],nv)
near('ideal_center_band_all_nodes_pass',run_case(1,'central_band',0,3800)['geometry_only_node_fraction'],1)
near('independent_cut_p90_isolation',.9**4,.6561)
near('uniform_arm_gate',.6**4+4*.2*.6**3,.3024)
check('mass_balance_all_runs',max(r['mass_balance_error'] for r in runs)<1e-11)
check('seed_reproducibility',run_case(.9,'uniform',.05,3800)==run_case(.9,'uniform',.05,3800))
check('probability_unassigned',I['physical_tests']==0 and I['physical_success_probability'] is None)
for a in [0,1,5]:
    h=1/20000; integ=h*(sum((1+a*(2*k*h-1)**2)**2 for k in range(1,20000))+.5*((1+a)**2+(1+a)**2))
    near('profile_volume_quadrature_a'+str(a),integ,avg_factor(a),3e-8)
for row in cost:
    if row['passes']==1:near('one_pass_gross_a'+str(row['mass_profile_a'])+'_'+str(row['p_input'])+'_'+row['mode'],row['gross_per_good_kg'],1/row['one_pass_geometric_mass_fraction'])
check('reprocessing_gross_invariant',all(math.isclose(z['gross_per_good_kg'],1/z['one_pass_geometric_mass_fraction'],rel_tol=1e-12) for z in cost))
check('mass_bounds',all(0<=r['geometry_only_mass_fraction']<=1 and 0<=r['removed_mass_fraction']<=1 for r in runs))
R={'physical_tests':0,'physical_success_probability':None,'beam':beam,'network':{'nodes':nv,'edges':ne,'synthetic_runs':len(runs),'summary':summary,'runs':runs},'cost':cost,'numerical_checks':len(checks),'analytic':{'shape_gate_uniform_fraction':.3024,'isolated_node_fraction_p90':.6561,'p_for_90percent_isolated_nodes_only':.9**.25,'midpoint_star_max_tip_distance_um':b['length_m']*math.sqrt(2/3)*1e6,'fixed_min_radius_mass_ratio_a5_to_a1':avg_factor(5)/avg_factor(1)}}
(P/'results.json').write_text(json.dumps(R,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(P/'validation.json').write_text(json.dumps({'passed':True,'count':len(checks),'physical_tests':0,'checks':checks},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
for filename,data in [('beam_profiles.csv',curves),('fragment_ledger.csv',runs)]:
    with (P/filename).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
print('Completed '+str(len(runs))+' synthetic graph cases and '+str(len(checks))+' numerical checks; physical tests = 0.')
