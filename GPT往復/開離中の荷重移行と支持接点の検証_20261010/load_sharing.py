"""Dimensionless elastic beam on unilateral point springs; static surrogate only."""
from reproduce import *
def beam(pattern,lam,mesh=1):
    ns=25;ne=(ns-1)*mesh;nd=2*(ne+1);dx=1/mesh
    Ke=lam/dx**3*np.array([[12,6*dx,-12,6*dx],[6*dx,4*dx**2,-6*dx,2*dx**2],[-12,-6*dx,12,-6*dx],[6*dx,2*dx**2,-6*dx,4*dx**2]])
    K=np.zeros((nd,nd));f=np.zeros(nd)
    # Consistent nodal vector for uniform transverse load q=1.
    fe=np.array([dx/2,dx**2/12,dx/2,-dx**2/12])
    for e in range(ne):
        ids=np.arange(2*e,2*e+4);K[np.ix_(ids,ids)]+=Ke;f[ids]+=fe
    support_dofs=np.arange(ns)*2*mesh
    missing={'intact':[],'dispersed':[3,6,9,12,15,18],'central_block':list(range(9,15)),'edge_block':list(range(6))}[pattern]
    allowed=np.array([j not in missing for j in range(ns)])
    active=allowed.copy();states=[]
    for iteration in range(100):
        H=K.copy();ids=support_dofs[active];H[ids,ids]+=1
        u=np.linalg.solve(H,f);w=u[support_dofs]
        update=allowed & (w>0)
        if np.array_equal(update,active):break
        key=tuple(update.tolist())
        if key in states:raise RuntimeError('Active-set cycle')
        states.append(key);active=update
    else:raise RuntimeError('Active set did not converge')
    reactions=np.where(active,w,0);balance=H@u-f
    return dict(pattern=pattern,lam=lam,mesh_per_support=mesh,missing=missing,available_supports=int(allowed.sum()),active_supports=int(active.sum()),displacement=w.tolist(),rotation=u[support_dofs+1].tolist(),reactions=reactions.tolist(),max_support_force=float(reactions.max()),max_support_node_displacement=float(w.max()),mean_displacement=float(w.mean()),sum_reactions=float(reactions.sum()),reaction_moment=float(reactions@np.arange(ns)),max_residual=float(np.max(np.abs(balance))),minimum_candidate_displacement=float(w[allowed].min()),bending_energy=float(.5*u@K@u),spring_energy=float(.5*reactions@reactions),external_work=float(f@u),active_set_iterations=iteration+1)
def main():
    rows=[];checks=[]
    for pattern,lam in itertools.product(['intact','dispersed','central_block','edge_block'],[.01,.1,1,10,100]):
        r=beam(pattern,lam);rows.append(r)
        for name,ok in [('force',abs(r['sum_reactions']-24)<1e-7),('moment',abs(r['reaction_moment']-288)<1e-6),('equilibrium',r['max_residual']<1e-7),('energy',abs(2*(r['bending_energy']+r['spring_energy'])-r['external_work'])<1e-5),('unilateral',min(r['reactions'])>=0)]:
            assert ok,(name,pattern,lam);checks.append(name+'-'+pattern+'-'+str(lam))
    convergence=[]
    for pattern in ['intact','dispersed','central_block','edge_block']:
        base=next(r for r in rows if r['pattern']==pattern and r['lam']==1)
        refined=beam(pattern,1,mesh=2)
        # Exact EB point-spring support-node response should be unchanged by extra unloaded support-free nodes.
        err=max(abs(x-y) for x,y in zip(base['displacement'],refined['displacement']))
        assert err<1e-7,(pattern,err);checks.append('mesh-'+pattern)
        convergence.append(dict(pattern=pattern,max_support_node_difference=err,refined=refined))
    # Independent overhang deflection benchmark: fixed root, uniform load, no springs.
    # Evaluated via one exact cubic element with the consistent load vector.
    lam=3.;L=2.;ke=lam/L**3*np.array([[12,6*L,-12,6*L],[6*L,4*L**2,-6*L,2*L**2],[-12,-6*L,12,-6*L],[6*L,2*L**2,-6*L,4*L**2]])
    u=np.linalg.solve(ke[2:,2:],np.array([L/2,-L**2/12]));exact=L**4/(8*lam)
    assert abs(u[0]-exact)<1e-12;checks.append('cantilever-uniform-load-analytic')
    out=dict(physical_tests=0,success_probability=None,scope='Dimensionless static uniform-load beam, 25 support locations; not actual ski/bed or dynamic comfort.',definitions={'lambda':'EI/(k*d^3)','force_unit':'q*d','deflection_unit':'q*d/k','missing_contacts_per_damaged_pattern':6,'material_parameters_measured':False,'all_supports_are_compressive':True},cases=rows,mesh_checks=convergence,analytic_tip_deflection=float(u[0]),checks=len(checks))
    (D/'load_sharing_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(cases=len(rows),checks=len(checks),lambda1=[dict(pattern=r['pattern'],active=r['active_supports'],peak_force=r['max_support_force'],max_displacement=r['max_support_node_displacement']) for r in rows if r['lam']==1])))
if __name__=='__main__':main()
