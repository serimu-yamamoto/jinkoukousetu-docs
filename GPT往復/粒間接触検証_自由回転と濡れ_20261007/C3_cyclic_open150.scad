// Concept geometry; dimensions mm. Not a manufacturing or performance approval.
R=0.24; a=0.022; opening=150; $fn=96;
module carc(){
  union(){
    rotate([0,0,opening/2]) rotate_extrude(angle=360-opening,convexity=8) translate([R,0,0]) circle(r=a);
    for(t=[opening/2,360-opening/2]) translate([R*cos(t),R*sin(t),0]) sphere(r=a);
  }
}
module hoop(){rotate_extrude(convexity=8) translate([R,0,0]) circle(r=a);}
// C3: openings point along +x in XY, +y in YZ, and +z in ZX.
union(){
 carc();
 multmatrix([[0,0,1,0],[1,0,0,0],[0,1,0,0],[0,0,0,1]]) carc();
 multmatrix([[0,1,0,0],[0,0,1,0],[1,0,0,0],[0,0,0,1]]) carc();
}
