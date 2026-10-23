"""要件の理論スクリーニング用の共通部品（粒の密度・毛管粘着力・蒸発・流出負荷）。人工フィルン研究。"""
import math
def granule_density(solid_g, vsolid_cm3, water_g, air_frac=0.0):
    v=(vsolid_cm3+water_g)/(1-air_frac); return (solid_g+water_g)/v*1000
def capillary_tensile(d_m, porosity, gamma=0.072):
    F=2*math.pi*gamma*(d_m/2); return (1-porosity)/porosity*F/d_m**2   # Rumpf近似 [Pa]
def penman_open(Rs_MJ, albedo, T=28.0, RH=0.6, u2=2.0, Ln_MJ=5.0):
    es=0.6108*math.exp(17.27*T/(T+237.3)); ea=RH*es; D=4098*es/(T+237.3)**2; g=0.066
    Rn=(1-albedo)*Rs_MJ-Ln_MJ; fu=6.43*(1+0.536*u2)
    return max(0,(D*Rn+g*fu*(es-ea))/(D+g)/2.45)   # mm/day
