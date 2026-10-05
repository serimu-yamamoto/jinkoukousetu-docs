# VT12 造成の数量拾い（1km×40m）と、地震・凍結の確認
import numpy as np
Lc,Wc=1000.,40.; Az=10.   # 集中ゾーン幅10m
for ang in [30,20]:
    b=np.radians(ang); A=Lc*Wc   # 斜面に沿った面積
    hz=Lc*np.sin(b)
    zone=Lc*Az; other=A-zone
    bed_z=0.8 if ang==30 else 0.6; bed_o=0.3
    Vbed=zone*bed_z+other*bed_o
    Vfil=A*0.1; Vdr=A*0.2
    step_h=0.5 if ang==30 else 0.0
    nstep=int(Lc*np.sin(b)/step_h) if step_h else 0
    # 横断排水：排水層あり→間隔は排水層の能力で決まる（100mm/hで余裕1.5倍）
    cap=0.1*np.sin(b)*0.2; s=cap/(100/1000/3600)/1.5
    ncross=int(np.ceil(Lc/s)); Lcross=ncross*Wc; Llong=2*Lc
    pond=A*np.cos(b)*0.05      # 50mm分の初期雨水＋散水回収
    print(f"[{ang}°] 斜面長1km・幅40m（水平投影{Lc*np.cos(b):.0f}m、高低差{hz:.0f}m）、斜面面積{A:,.0f}m²")
    print(f"  床材 {Vbed:,.0f}m³（{Vbed*1.674:,.0f}t）＝集中ゾーン{bed_z}m×{zone:,.0f}m²＋その他0.3m×{other:,.0f}m²")
    print(f"  フィルター層 {Vfil:,.0f}m³（{Vfil*1.6:,.0f}t）／排水層 {Vdr:,.0f}m³（{Vdr*1.6:,.0f}t）")
    print(f"  段切り {'高さ'+str(step_h)+'m×'+str(nstep)+'段（各40m）＝延長'+f'{nstep*Wc:,.0f}m' if nstep else '原則不要（地盤調査で判断）'}")
    print(f"  横断暗渠 間隔{s:.0f}m以下→{ncross}本×40m＝{Lcross:,.0f}m、縦断の集水管（両端）{Llong:,.0f}m")
    print(f"  回収池 約{pond:,.0f}m³（雨50mm分＋散水の回収）")
    # 地震（無限斜面・震度法）
    for kh in [0.15,0.25]:
        for c in [10,30]:
            g=20.2; z=bed_z; phi=np.radians(35)
            num=c+g*z*(np.cos(b)**2-kh*np.sin(b)*np.cos(b))*np.tan(phi) - 0
            den=g*z*(np.sin(b)*np.cos(b)+kh*np.cos(b)**2)
            print(f"  地震 kh={kh} 床c={c}kPa（飽和でない）: 床内の安全率 {num/den:.2f}", end=";")
        print()
    # 境目（排水層＝角ばった砕石φ42°、c=0）の地震時
    for kh in [0.15,0.25]:
        phi=np.radians(42); print(f"  地震 kh={kh}: 排水層（φ42°・粘着なし）の層すべり安全率 {(np.cos(b)-kh*np.sin(b))*np.tan(phi)/(np.sin(b)+kh*np.cos(b)):.2f}")
print("\n[凍結] Stefan式 Z=sqrt(2kF/L)。乾いた方解石床・砕石は凍上しにくい。凍上が問題になるのは細かい地山")
for F in [300,600,1000]:
    for k,Lh,lab in [(0.6,1674*0.03*334e3,'含水3%の床'),(1.2,1674*0.10*334e3,'含水10%の床')]:
        Z=np.sqrt(2*k*F*86400/Lh); print(f"  凍結指数{F}℃・日 {lab}: 凍結深さ{Z:.2f}m（積雪がない場合。積雪30cm以上でほぼ半減以下）")
