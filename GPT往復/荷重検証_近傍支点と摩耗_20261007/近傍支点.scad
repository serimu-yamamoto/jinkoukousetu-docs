// Units mm. Research review; texture, loads and production tolerances omitted.
$fn=128;
R=0.25; r=0.03; re=0.05; gap=0.02; theta=asin((2*re+gap)/(2*R));
offset=0.005; // provisional low-volume candidate, not a mechanical optimum
union(){
 rotate([0,0,theta]) rotate_extrude(angle=360-2*theta) translate([R,0]) circle(r=r);
 for(s=[-1,1]) translate([R*cos(theta),s*R*sin(theta),0]) sphere(r=re);
 translate([-0.22,0,0]) scale([0.04,0.035,0.02]) sphere(r=1);
 for(s=[-1,1]) translate([-0.22,0,s*offset]) sphere(r=0.03);
}
