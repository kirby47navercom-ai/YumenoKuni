"""Comic sheet geometry calibrated against hCqejpi6Hps at 5550.847s.

These are measured screen correspondences, not a recovered camera/FOV.
The original DAT confirms perspective (17,25,-4.7 degrees); the old fixed
2D rotation did not reproduce it. All panels below belong to our own story.
"""
import numpy as np

SIZE = (1100, 650)
MAIN = [(556, 143), (1220, 128), (1180, 568), (487, 491)]
PREVIOUS = [(276, 267), (526, 285), (492, 516), (232, 488)]
REPLAY = [(38, 30), (1242, 30), (1242, 688), (38, 688)]

def homography(quad):
    a, b = [], []
    for (x,y),(u,v) in zip([(0,0),(1100,0),(1100,650),(0,650)],quad):
        a += [[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]
        b += [u,v]
    return np.r_[np.linalg.solve(a,b),1].reshape(3,3)

def project(points, quad=MAIN):
    h=homography(quad)
    out=[]
    for x,y in points:
        p=h@np.array([x,y,1]);out.append([round(float(p[0]/p[2]),4),round(float(p[1]/p[2]),4)])
    return out

def panels(count):
    # A continuous black-gutter comic sheet, rather than detached cards.
    if count==3:
        return [(14,14,516,290),(14,316,516,320),(542,14,544,622)]
    return [(14,14,516,290),(542,14,544,290),(14,316,410,320),(436,316,650,320)]

def thumb(page):
    x=560+page*142;y=117-page*15
    return [(x,y),(x+136,y-15),(x+128,y+50),(x-8,y+65)]

def slot_quad(slot_list, index, context_count):
    r=panels(len(slot_list)+context_count)[slot_list.index(index)]
    x,y,w,h=r
    return project([(x,y),(x+w,y),(x+w,y+h),(x,y+h)])
