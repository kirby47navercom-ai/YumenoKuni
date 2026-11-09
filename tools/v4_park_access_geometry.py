"""Walkable upper landing and collision for the authored observatory railing."""
import math
def observatory(collision,walk):
    # The railing defines the circular boundary; its supporting floor must cover
    # that entire boundary instead of ending at the corners of a coarse grid.
    walk[:]=[r for r in walk if r[4]<5.84]+[[20.4,-4.55,20.7,-2.45,5.85],[7.3,-10.2,20.5,3.2,5.85]]
    for k in range(2,47):
        a=k*math.tau/48;b=(k+1)*math.tau/48
        x0,z0=14+6.45*math.cos(a),-3.5-6.45*math.sin(a);x1,z1=14+6.45*math.cos(b),-3.5-6.45*math.sin(b)
        collision.append([min(x0,x1)-.04,min(z0,z1)-.04,max(x0,x1)+.04,max(z0,z1)+.04,5.8,7.1])
    for angle,z in [(2*math.tau/48,-4.55),(47*math.tau/48,-2.45)]:
        x0,z0=14+6.45*math.cos(angle),-3.5-6.45*math.sin(angle)
        collision.append([min(x0,20.4)-.05,min(z0,z)-.05,max(x0,20.4)+.05,max(z0,z)+.05,5.8,7.1])
    for i in range(32):
        lo=(i+1)*5.85/32
        for z in [-4.55,-2.45]:collision.append([30-(i+1)*.3,z-.045,30-i*.3,z+.045,lo+.35,lo+1.2])
