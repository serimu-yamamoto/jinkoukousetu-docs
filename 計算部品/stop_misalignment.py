"""Nominal planar overlap and ideal beam ratios. No adhesion model."""
import math
def pos(*xs):
    if not all(math.isfinite(x) and x>0 for x in xs):raise ValueError("finite positive values required")
def circle_overlap(r,R,d):
    pos(r,R)
    if not math.isfinite(d) or d<0:raise ValueError("invalid centre offset")
    if d>=r+R:return 0.0
    if d<=abs(r-R):return math.pi*min(r,R)**2
    a=max(-1.0,min(1.0,(d*d+r*r-R*R)/(2*d*r)))
    b=max(-1.0,min(1.0,(d*d+R*R-r*r)/(2*d*R)))
    rad=(-d+r+R)*(d+r-R)*(d-r+R)*(d+r+R)
    return r*r*math.acos(a)+R*R*math.acos(b)-.5*math.sqrt(max(0.0,rad))
def nominal_pressure_multiplier(patch_area,contact_area,active_contacts):
    pos(patch_area)
    if not math.isfinite(contact_area) or contact_area<0:raise ValueError("invalid area")
    if type(active_contacts) is not int or active_contacts<1:raise ValueError("invalid count")
    if contact_area==0:return None
    return patch_area/(contact_area*active_contacts)
def rearrangement(height_each,radius,number_pairs):
    pos(height_each,radius)
    if type(number_pairs) is not int or number_pairs<1:raise ValueError("invalid count")
    V=number_pairs*math.pi*radius**2*2*height_each
    return dict(paired_volume_m3=V,single_sided_volume_m3=V,
      paired_lateral_compliance_times_EI=2*height_each**3/3,
      single_lateral_compliance_times_EI=(2*height_each)**3/3,
      lateral_compliance_ratio_single_to_pair=4.0,
      axial_compliance_times_EA=2*height_each,
      assumptions="same radius; two independent equal cantilevers in series versus one twice as long; rigid plates; no slip at lateral force application")

def beam_compliance(segments,poisson,shear_factor):
    """Piecewise circular straight beam, values multiplied by E; not a 3D stub model."""
    if not math.isfinite(poisson) or not -1<poisson<.5:raise ValueError("invalid Poisson ratio")
    pos(shear_factor)
    if not segments:raise ValueError("empty beam")
    for length,radius in segments:pos(length,radius)
    L=sum(x[0] for x in segments);x=0.;bend=shear=axial=volume=0.
    for length,radius in segments:
        A=math.pi*radius**2;I=math.pi*radius**4/4
        bend+=((L-x)**3-(L-x-length)**3)/(3*I)
        shear+=2*(1+poisson)*length/(shear_factor*A)
        axial+=length/A;volume+=A*length;x+=length
    return dict(bending_times_E=bend,shear_times_E=shear,lateral_times_E=bend+shear,
                axial_times_E=axial,volume_m3=volume)
