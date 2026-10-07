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
module c3(){union(){
 carc();
 multmatrix([[0,0,1,0],[1,0,0,0],[0,1,0,0],[0,0,0,1]]) carc();
 multmatrix([[0,1,0,0],[0,0,1,0],[1,0,0,0],[0,0,0,1]]) carc();
}}
// Uncompiled concept. Internal member diameter 28 micrometre.
b=0.014;
module tie(p,q){hull(){translate(p)sphere(r=b);translate(q)sphere(r=b);}}
union(){c3();
tie([0.06211657082460498,0.2318221983093764,0],[-0.24,0,0]);
tie([0.06211657082460507,-0.23182219830937636,0],[-0.24,0,0]);
tie([0,0.06211657082460498,0.2318221983093764],[0,-0.24,0]);
tie([0,0.06211657082460507,-0.23182219830937636],[0,-0.24,0]);
tie([0.2318221983093764,0,0.06211657082460498],[0,0,-0.24]);
tie([-0.23182219830937636,0,0.06211657082460507],[0,0,-0.24]);
}
