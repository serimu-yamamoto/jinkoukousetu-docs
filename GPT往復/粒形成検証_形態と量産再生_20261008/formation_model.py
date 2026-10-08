"""Cycle 17: formation scales, prescribed profile and manufacturing budget.
No physical trials, snow-performance probability or manufacturing yield prediction.
Python 3 standard library. Geometry units: millimetres; thermal units: SI.
"""
import json, math, collections
from pathlib import Path
ROOT=Path(__file__).resolve().parent
I=json.loads((ROOT/'inputs.json').read_text(encoding='utf-8'))
T,S,O,B=(I[x] for x in ('thermal','shape','operation','budget'))

def simpson(f,a,b,n=512):
    if n%2: raise ValueError('even n required')
    h=(b-a)/n
    return h/3*(f(a)+f(b)+sum((4 if i%2 else 2)*f(a+i*h) for i in range(1,n)))

def thermal(r_um,ambient,nu,gamma,mu):
    r=r_um*1e-6
    if not T['Tin_C']>T['Tc_C']>ambient or r<=0 or min(nu,gamma,mu)<=0:
        raise ValueError('invalid scale input')
    factor=2*T['rho_kg_m3']*r*r/(3*nu*T['k_air_W_mK'])
    sensible=factor*T['cp_J_kgK']*math.log((T['Tin_C']-ambient)/(T['Tc_C']-ambient))
    latent=factor*T['latent_J_kg']/(T['Tc_C']-ambient)
    tv=mu*r/gamma
    ti=math.sqrt(T['rho_kg_m3']*r**3/gamma)
    return dict(radius_um=r_um,ambient_C=ambient,Nu=nu,gamma_N_m=gamma,
                illustrative_mu_Pa_s=mu,energy_to_Tc_s=sensible,
                energy_plus_prescribed_latent_s=sensible+latent,
                viscocapillary_scale_s=tv,inertiocapillary_scale_s=ti,
                Oh_radius_basis=tv/ti,
                mu_crossover_energy_proxy_Pa_s=gamma*(sensible+latent)/r,
                energy_time_over_viscous_scale=(sensible+latent)/tv,
                Bi_sphere=nu*T['k_air_W_mK']/(6*T['k_solid_W_mK']),
                applicability="No morphology, nucleation, crystallization-delay or viscoelastic nozzle model")

def outline(n):
    mean=S['outer_radius_mm']/(1+S['amplitude'])
    return [(mean*(1+S['amplitude']*math.cos(S['lobes']*2*math.pi*i/n))*math.cos(2*math.pi*i/n),
             mean*(1+S['amplitude']*math.cos(S['lobes']*2*math.pi*i/n))*math.sin(2*math.pi*i/n))
            for i in range(n)]

def area_exact():
    return math.pi*(S['outer_radius_mm']/(1+S['amplitude']))**2*(1+S['amplitude']**2/2)

def polygon_area(p):
    return sum(x*p[(i+1)%len(p)][1]-y*p[(i+1)%len(p)][0] for i,(x,y) in enumerate(p))/2

def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def dot(a,b): return sum(x*y for x,y in zip(a,b))

def mesh():
    p=outline(S['polygon_segments']); n=len(p); length=S['mesh_length_mm']
    v=[(x,y,-length/2) for x,y in p]+[(x,y,length/2) for x,y in p]+[(0,0,-length/2),(0,0,length/2)]
    f=[]
    for i in range(n):
        j=(i+1)%n
        f.extend([(2*n,j,i),(2*n+1,i+n,j+n),(i,j,j+n),(i,j+n,i+n)])
    return v,f

def write_mesh(v,f):
    with (ROOT/'X17_reference_mm.stl').open('w',encoding='ascii',newline='\n') as out:
        out.write('solid X17_reference_unrounded_cut_ends\n')
        for face in f:
            a,b,c=(v[i] for i in face)
            normal=cross(sub(b,a),sub(c,a)); size=math.sqrt(dot(normal,normal))
            normal=tuple(x/size for x in normal)
            out.write(' facet normal '+' '.join(f'{x:.12g}' for x in normal)+'\n  outer loop\n')
            for point in (a,b,c): out.write('   vertex '+' '.join(f'{x:.12g}' for x in point)+'\n')
            out.write('  endloop\n endfacet\n')
        out.write('endsolid X17_reference_unrounded_cut_ends\n')
    source=f"""// Units mm. Prescribed final geometry; NOT a production die.
// Cut ends are unrounded. No snow feel, safety, yield or manufacturability certification.
R={S['outer_radius_mm']}; amplitude={S['amplitude']}; lobes={S['lobes']};
length={S['mesh_length_mm']}; segments={S['polygon_segments']};
linear_extrude(height=length,center=true,convexity=10)
polygon(points=[for(i=[0:segments-1])
  let(theta=360*i/segments,r=R/(1+amplitude)*(1+amplitude*cos(lobes*theta)))
  [r*cos(theta),r*sin(theta)]]);
"""
    (ROOT/'X17_reference_mm.scad').write_text(source,encoding='utf-8')

def build():
    a=area_exact(); rho=S['solid_density_kg_m3']
    mass=O['area_m2']*O['depth_m']*O['bulk_density_kg_m3']
    crf=B['discount']/(1-(1+B['discount'])**(-B['years']))
    base=(mass*B['material_JPY_kg']+B['nonmaterial_capital_JPY'])*crf+B['annual_fixed_JPY']+mass*B['annual_material_replacement_fraction']*B['material_JPY_kg']
    headroom=B['annual_budget_JPY']-base
    geometry=[]
    for length in S['lengths_mm']:
        geometry.append(dict(length_mm=length,area_mm2=a,volume_mm3=a*length,
         mass_kg=rho*a*length*1e-9,
         outer_lobe_tip_radius_mm=S['outer_radius_mm']*(1+S['amplitude'])/(1+(S['lobes']**2+1)*S['amplitude']),
         area_fraction_of_bounding_circle=a/(math.pi*S['outer_radius_mm']**2),
         envelope_volume_ratio_needed_for_target_bulk_density=O['bulk_density_kg_m3']/(rho*a/(math.pi*S['outer_radius_mm']**2)),
         note="Envelope ratio is bookkeeping, not measured packing; bounding envelopes may overlap. No closed pore."))
    production=[]
    for length in S['lengths_mm']:
      for speed in S['solid_strand_speed_m_s']:
       for strands in S['strand_count']:
        production.append(dict(length_mm=length,solid_speed_m_s=speed,strands=strands,
         usable_kg_h=rho*a*1e-6*speed*strands*S['usable_yield']*3600,
         cuts_per_s_per_strand=speed/(length*1e-3),
         rotor_rpm_if_each_blade_cuts_each_strand=60*speed/(length*1e-3*S['blades'])))
    operations=[]
    for fraction in O['reform_fractions']:
        stock=mass*fraction; rate=stock/(O['processing_minutes']/60)
        annual=stock*O['closures_per_year']
        operations.append(dict(reform_fraction_per_closure=fraction,mass_per_closure_kg=stock,
         required_kg_h_in_processing_window=rate,annual_reforming_kg=annual,
         all_in_regeneration_fee_ceiling_JPY_kg=headroom/annual,
         holes_needed_at_1m_s_and_assumed_yield=math.ceil(rate/(rho*a*1e-6*S['usable_yield']*3600))))
    scales=[thermal(r,ta,nu,g,mu) for r in T['radius_um'] for ta in T['ambient_C'] for nu in T['Nu'] for g in T['surface_tension_N_m'] for mu in T['viscosity_Pa_s']]
    return dict(scope="Uncalibrated process/geometry/budget comparison; not performance trials",
                physical_tests=0,physical_success_probability=None,thermal_scales=scales,
                geometry=geometry,production=production,operation=operations,
                budget=dict(bed_mass_kg=mass,capital_recovery_factor=crf,inherited_base_EAC_JPY=base,additional_headroom_JPY_year=headroom))

def verify(result,v,f):
    checks=[]
    def require(condition,name):
        if not condition: raise AssertionError(name)
        checks.append(name)
    # Independent heat balance from mass and area, integrated over temperature.
    for r_um in (25,125,500):
        r=r_um*1e-6; rho=T['rho_kg_m3']
        mass=rho*4*math.pi*r**3/3; area=4*math.pi*r*r
        h=2*T['k_air_W_mK']/(2*r)
        sensible=simpson(lambda temp:mass*T['cp_J_kgK']/(h*area*(temp-30)),T['Tc_C'],T['Tin_C'])
        latent=mass*T['latent_J_kg']/(h*area*(T['Tc_C']-30))
        analytical=thermal(r_um,30,2,.03,100)
        require(math.isclose(sensible,analytical['energy_to_Tc_s'],rel_tol=1e-9),'heat balance sensible '+str(r_um))
        require(math.isclose(sensible+latent,analytical['energy_plus_prescribed_latent_s'],rel_tol=1e-9),'heat balance latent '+str(r_um))
    areas=[polygon_area(outline(n)) for n in (360,720)]
    errors=[abs(a-area_exact()) for a in areas]
    require(3.9<errors[0]/errors[1]<4.1,'outline refinement convergence')
    require(errors[1]/area_exact()<2e-4,'outline area accuracy')
    edge=collections.Counter(); directed=collections.Counter()
    for face in f:
        for i in range(3):
            a,b=face[i],face[(i+1)%3]; edge[tuple(sorted((a,b)))]+=1; directed[(a,b)]+=1
    require(all(count==2 for count in edge.values()),'closed mesh, two faces per edge')
    require(all(directed[(b,a)]==1 for a,b in directed),'mesh edge orientation')
    require(len(v)-len(edge)+len(f)==2,'mesh Euler characteristic')
    volume=sum(dot(v[a],cross(v[b],v[c]))/6 for a,b,c in f)
    require(volume>0,'outward mesh orientation')
    require(math.isclose(volume,areas[1]*S['mesh_length_mm'],rel_tol=1e-10),'signed tetrahedron volume vs cross section')
    for row in result['production']:
        m=S['solid_density_kg_m3']*area_exact()*row['length_mm']*1e-9
        from_pieces=m*row['cuts_per_s_per_strand']*row['strands']*S['usable_yield']*3600
        require(math.isclose(from_pieces,row['usable_kg_h'],rel_tol=1e-12),'piece count mass flow '+str(len(checks)))
    direct_crf=1/sum((1+B['discount'])**(-year) for year in range(1,B['years']+1))
    require(math.isclose(direct_crf,result['budget']['capital_recovery_factor'],rel_tol=1e-12),'discounted annuity identity')
    for row in result['operation']:
        require(math.isclose(row['annual_reforming_kg']*row['all_in_regeneration_fee_ceiling_JPY_kg'],result['budget']['additional_headroom_JPY_year'],rel_tol=1e-12),'budget identity '+str(row['reform_fraction_per_closure']))
    require(result['physical_tests']==0 and result['physical_success_probability'] is None,'evidence status remains unmeasured')
    return dict(passed_checks=len(checks),checks=checks,mesh_vertices=len(v),mesh_faces=len(f),
                polygon_area_relative_error=errors[1]/area_exact(),signed_volume_mm3=volume,
                physical_tests=0,physical_success_probability=None,
                limitations="Internal arithmetic and ideal mesh checks only, not independent physical performance tests")

if __name__=='__main__':
    result=build(); vertices,faces=mesh(); verification=verify(result,vertices,faces)
    write_mesh(vertices,faces)
    (ROOT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(checks=verification['passed_checks'],mesh_faces=len(faces),thermal_rows=len(result['thermal_scales']),production_rows=len(result['production']),budget=result['budget'],operation=result['operation']),ensure_ascii=False))
