# VT10 20°の山肌に直接1.5m敷く場合の安定と水
import numpy as np
b=np.radians(20); g_s=20.2; g_d=16.4; gw=9.81; t=1.5
print("[1] 床と山肌の境目（すべり面）の安全率：境目の強さ＝山肌の土の強さ")
print("   土φ/c  →  乾燥 / 境目まで半分水 / 境目まで全部水（m=0, 0.5, 1）")
for phi in [25,30,35]:
    for c in [0,5,10]:
        out=[]
        for m in [0,0.5,1]:
            gam=g_d if m==0 else g_d+(g_s-g_d)*m
            sn=gam*t*np.cos(b)**2; u=m*gw*t*np.cos(b)**2; tau=gam*t*np.sin(b)*np.cos(b)
            out.append((c+(sn-u)*np.tan(np.radians(phi)))/tau)
        print(f"   φ{phi}° c{c:>2}kPa → "+" / ".join(f"{x:.2f}" for x in out))
print("\n[2] 雨の水が境目の上を流れる量と、床が流せる量（床の透水1e-3m/s、厚さ1.5m、20°）")
cap=1e-3*np.sin(b)*t
for rain in [5,10,30,50]:
    Lsat=cap/(rain/1000/3600)
    print(f"   雨{rain:>2}mm/h：斜面の上端から {Lsat:6.0f}m より下では、床が底から頂まで水で満ちる（地山の透水を1e-6m/s以下と仮定）")
print("   → 1kmのコースでは、強い雨のとき中腹から下が全層水浸しになる。表面から水が湧き出す")
for rain in [30,50,100]:
    for drain_cap_spacing in [30,50,100]:
        pass
print("\n[3] 横断排水（斜面を横切る暗渠）の間隔：雨の間も床の下半分だけが水で満ちる（m≦0.5）条件")
for rain in [30,50,100]:
    s=0.5*cap/(rain/1000/3600)
    print(f"   雨{rain:>3}mm/h → 間隔 {s:4.0f}m 以下")
print("\n[4] 山への重さ：1.5mの床＋水 ≈ %.0f〜%.0fkN/m²（＝%.1f〜%.1ft/m²）が山肌に加わる。山の深い所の地すべりは地盤調査なしに判断できない" % (g_d*t,g_s*t,g_d*t/9.81,g_s*t/9.81))
print("\n[5] 床そのもの（石灰水焼結 c≧10kPa）の安全率（全層水浸し、φ35°）:")
for c in [5,10,68]:
    sn=g_s*t*np.cos(b)**2; u=gw*t*np.cos(b)**2; tau=g_s*t*np.sin(b)*np.cos(b)
    print(f"   c={c}kPa → {(c+(sn-u)*np.tan(np.radians(35)))/tau:.2f}")
print("\n[6] 山肌の細かい土が床に入り込むか（Terzaghiのフィルター条件：床のD15≦5×土のd85）")
for d85 in [0.05,0.1,0.3,1.0]:
    print(f"   土のd85={d85}mm：床のD15 0.6mm {'≦' if 0.6<=5*d85 else '＞'} {5*d85:.2f}mm → {'入り込まない' if 0.6<=5*d85 else '泥が床に入り込み、目詰まりする'}")
