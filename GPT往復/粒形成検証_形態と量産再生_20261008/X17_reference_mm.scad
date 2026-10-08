// Units mm. Prescribed final geometry; NOT a production die.
// Cut ends are unrounded. No snow feel, safety, yield or manufacturability certification.
R=0.3; amplitude=0.45; lobes=6;
length=0.3; segments=720;
linear_extrude(height=length,center=true,convexity=10)
polygon(points=[for(i=[0:segments-1])
  let(theta=360*i/segments,r=R/(1+amplitude)*(1+amplitude*cos(lobes*theta)))
  [r*cos(theta),r*sin(theta)]]);
