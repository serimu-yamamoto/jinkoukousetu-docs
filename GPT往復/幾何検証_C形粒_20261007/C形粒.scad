// Units mm. Capped circular-tube model; no manufacturing/force validation.
$fn=128;
module grain(D=0.6,d=0.06,De=0.10,g=0.02){
 R=(D-De)/2; t=asin((De+g)/(2*R));
 union(){ rotate([0,0,t]) rotate_extrude(angle=360-2*t) translate([R,0]) circle(r=d/2);
 for(s=[-1,1]) translate([R*cos(t),s*R*sin(t),0]) sphere(r=De/2); } }
// candidate: 1=G1, 2=G2, 3=G3. pair=true shows checked facing-gap pose.
candidate=3; pair=false; separation=0.5;
 De=candidate==3?0.10:0.06; g=candidate==1?0.04:0.02;
 grain(De=De,g=g);
 if(pair) multmatrix([[-1,0,0,separation],[0,0,1,0],[0,1,0,0],[0,0,0,1]]) grain(De=De,g=g);
