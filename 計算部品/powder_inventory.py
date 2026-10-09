"""Mass, count and coating balances; geometry assumptions, not measured performance."""
from math import isfinite
def distribution(diameters_um,counts,mass_exponent=3):
    if len(diameters_um)!=len(counts) or not diameters_um:raise ValueError('invalid bins')
    bins=sorted(zip(diameters_um,counts))
    if not all(isfinite(d) and d>0 and isfinite(n) and n>0 for d,n in bins):raise ValueError('positive finite bins required')
    if mass_exponent not in (2,3):raise ValueError('2: constant-thickness plates, 3: similar shapes')
    total_n=sum(n for d,n in bins);total_v=sum(n*d**mass_exponent for d,n in bins)
    def quantile(q,exponent):
        total=sum(n*d**exponent for d,n in bins);run=0.
        for d,n in bins:
            run+=n*d**exponent
            if run>=q*total-1e-12*total:return d
        return bins[-1][0]
    return dict(mass_exponent=mass_exponent,number_D90_um=quantile(.9,0),
      volume_D50_um=quantile(.5,mass_exponent),volume_D90_um=quantile(.9,mass_exponent),
      bins=[dict(d_um=d,count=n,number_fraction=n/total_n,
        equal_density_mass_fraction=n*d**mass_exponent/total_v) for d,n in bins])
def retention(dist,ideal_cutoff_um):
    keep=[b for b in dist['bins'] if b['d_um']>=ideal_cutoff_um]
    return dict(ideal_cutoff_um=ideal_cutoff_um,retained_number_fraction=sum(b['number_fraction'] for b in keep),
      retained_mass_fraction=sum(b['equal_density_mass_fraction'] for b in keep),
      boundary='ideal diameter classification only; not real filtration efficiency')
def coating(finished_mass_kg,weight_fraction,coatable_area_m2_per_kg_core,
            coating_density_kg_m3=1200.,target_area_fraction=1.):
    if not (finished_mass_kg>0 and 0<weight_fraction<1 and coatable_area_m2_per_kg_core>0 and coating_density_kg_m3>0 and 0<target_area_fraction<=1):raise ValueError('invalid mass/area')
    coat=finished_mass_kg*weight_fraction;core=finished_mass_kg-coat
    area=core*coatable_area_m2_per_kg_core*target_area_fraction
    return dict(finished_mass_kg=finished_mass_kg,weight_fraction=weight_fraction,core_kg=core,
      coating_kg=coat,coatable_area_m2_per_kg_core=coatable_area_m2_per_kg_core,
      target_area_fraction=target_area_fraction,coating_density_kg_m3=coating_density_kg_m3,
      equivalent_solid_thickness_um=coat/coating_density_kg_m3/area*1e6)
def loss_budget(coating_kg,annual_detached_fraction,capture_fraction,assumed_price_JPY_kg):
    if not (coating_kg>0 and 0<=annual_detached_fraction<=1 and 0<=capture_fraction<=1 and assumed_price_JPY_kg>=0):raise ValueError('invalid loss budget')
    detached=coating_kg*annual_detached_fraction
    return dict(coating_kg=coating_kg,annual_detached_fraction=annual_detached_fraction,
      capture_fraction=capture_fraction,detached_kg=detached,captured_kg=detached*capture_fraction,
      uncaptured_kg=detached*(1-capture_fraction),
      replacement_material_JPY_if_all_detached_unusable=detached*assumed_price_JPY_kg,
      status='assumed inventory loss; not measured wear, permitted release, or quotation')
