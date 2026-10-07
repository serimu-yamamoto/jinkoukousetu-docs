// Enlarged FREE strip only; units mm. No snow performance is demonstrated.
// BVP contact uses a centreline idealization; this finite CAD is NOT its exact contact solution.
scale_factor=100;
Rs=0.05*scale_factor;
t=0.005*scale_factor;
b=0.1*scale_factor;
phi=2.1;
N=256;
function pt(r,i)=[r*sin((-phi+2*phi*i/N)*180/PI),r*cos((-phi+2*phi*i/N)*180/PI)];
points=concat([for(i=[0:N]) pt(Rs+t/2,i)],[for(i=[N:-1:0]) pt(Rs-t/2,i)]);
linear_extrude(height=b,center=true,convexity=10) polygon(points);
