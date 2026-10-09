// H105-C: comparison coupon geometry only; units mm.
// Not a snow crystal, validated material, or manufacturing-ready product.
$fn=120;
R=1; r=0.7; h=0.6; rim=0.1; n=6; web_angle=20;
module sector(angle,zheight) {
  linear_extrude(height=zheight)
    polygon(concat([[0,0]],[for(i=[0:40]) [R*cos(-angle/2+i*angle/40),R*sin(-angle/2+i*angle/40)]]));
}
module annulus(zheight) { difference(){cylinder(h=zheight,r=R);translate([0,0,-0.01])cylinder(h=zheight+0.02,r=r);} }
union() {
 annulus(rim);
 translate([0,0,h-rim])annulus(rim);
 difference() {
  union() {for(j=[0:n-1])rotate([0,0,j*360/n])sector(web_angle,h);}
  translate([0,0,-0.01])cylinder(h=h+0.02,r=r);
 }
}
