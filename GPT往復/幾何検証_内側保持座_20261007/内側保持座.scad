// Units mm. Review geometry; no applied texture, load or manufacturing certification.
$fn=128;
candidate=1; // 0 = exposed thick seat, 1 = W1_one, 3 = W1_three
R=0.25; r=0.03; re=0.05; gap=0.02; theta=asin((2*re+gap)/(2*R));
module backbone(){ union(){
 rotate([0,0,theta]) rotate_extrude(angle=360-2*theta) translate([R,0]) circle(r=r);
 for(s=[-1,1]) translate([R*cos(theta),s*R*sin(theta),0]) sphere(r=re);
}}
module seat(a){ rotate([0,0,a]) translate([0.22,0,0]) scale([0.04,0.035,candidate==0?0.045:0.02]) sphere(r=1); }
union(){backbone(); if(candidate==3){ for(a=[60,180,300]) seat(a); } else seat(180); }
