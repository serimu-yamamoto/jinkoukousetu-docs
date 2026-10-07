// Millimetres. R4 comparison concept; material and manufacture unvalidated.
$fn=128; R=0.24; a=0.022; opening=150;
module C(){rotate([0,0,opening/2]) rotate_extrude(angle=360-opening) translate([R,0,0]) circle(r=a); for(p=[opening/2,360-opening/2])translate([R*cos(p),R*sin(p),0])sphere(r=a);}
union(){C(); rotate([90,0,0])C();rotate([0,90,0])rotate_extrude()translate([R,0,0])circle(r=a);}
