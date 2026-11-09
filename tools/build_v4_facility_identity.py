"""Owned facility lettering/pictograms and measured panorama/light alignment.

Face artwork is made with image_gen separately. This packs finished 64px heads;
lettering and geometric wayfinding symbols use the existing Korean typeface.
"""
from pathlib import Path
import json, hashlib, math
R=Path(__file__).resolve().parents[1]
O=R/'art/space_v4/facility_identity_v1';O.mkdir(exist_ok=True)
CAST=['mio','rin','ken','nana','taiga','ai','rei','sora','haruka','sho','koto','akari','riku','satsuki','yuu','kaede']
FONT='C:/Windows/Fonts/malgunbd.ttf'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def family(ident):
    if ident=='clinic':return 'medical'
    if ident in ['dining_room','kitchen','refreshment_store']:return 'dining'
    if ident in ['hotel_lobby','hotel_corridor','guest_room','hotel_multiuse','service_lounge']:return 'hotel'
    if ident in ['performance_stage','screening_room','dream_lobby','theatre_preparation']:return 'theatre'
    if ident in ['mirror_maze','mirror_workbay','mirror_waiting']:return 'mirror'
    if ident in ['reading_room','archive_room','record_room','exhibition_room','operating_archive']:return 'archive'
    if ident in ['electrical_room','central_control','maintenance_workshop','inspection_hall_normal','inspection_hall_changed','cold_store','supply_store','laundry_room','staff_passage']:return 'utility'
    if ident in ['management_office','shelter_reception','shelter_inner','lower_stairway','lower_corridor','trial_elevator']:return 'civic'
    return 'park'
PALETTE={'medical':'#77d0bd','dining':'#e8b269','hotel':'#be94c5','theatre':'#df8093','mirror':'#80c9dd','archive':'#c7b582','utility':'#e8bf59','civic':'#9badcb','park':'#9fc588'}
def pictogram(d,kind,x,y,c):
    # Shared original wayfinding geometry, not downloaded original-game icons.
    if kind=='washer':
        d.rounded_rectangle((x-32,y-36,x+32,y+36),radius=5,outline=c,width=5);d.ellipse((x-23,y-18,x+23,y+28),outline=c,width=5);d.line((x-24,y-25,x-2,y-25),fill=c,width=4);d.ellipse((x+17,y-29,x+23,y-23),fill=c)
    elif kind=='snowflake':
        for i in range(6):
            a=i*math.tau/6;dx,dz=math.cos(a),math.sin(a);d.line((x,y,x+dx*35,y+dz*35),fill=c,width=4)
            for sign in [-1,1]:
                aa=a+sign*2.4;xx=x+dx*24;yy=y+dz*24;d.line((xx,yy,xx+math.cos(aa)*12,yy+math.sin(aa)*12),fill=c,width=3)
    elif kind=='gear':
        d.ellipse((x-25,y-25,x+25,y+25),outline=c,width=9);d.ellipse((x-8,y-8,x+8,y+8),outline=c,width=4)
        for i in range(8):
            a=i*math.tau/8;d.line((x+math.cos(a)*24,y+math.sin(a)*24,x+math.cos(a)*36,y+math.sin(a)*36),fill=c,width=10)
    elif kind=='crate':
        d.rectangle((x-34,y-30,x+34,y+30),outline=c,width=5);d.line((x-30,y-25,x+30,y+25),fill=c,width=4);d.line((x+30,y-25,x-30,y+25),fill=c,width=4)
    elif kind=='monitor':
        d.rectangle((x-36,y-30,x+36,y+15),outline=c,width=5);d.line((x,y+15,x,y+32),fill=c,width=5);d.line((x-20,y+32,x+20,y+32),fill=c,width=5)
    elif kind=='passage':
        d.line((x-34,y,x+30,y),fill=c,width=7);d.line((x+10,y-22,x+32,y,x+10,y+22),fill=c,width=7)
    elif kind=='medical':d.polygon([(x-10,y-34),(x+10,y-34),(x+10,y-10),(x+34,y-10),(x+34,y+10),(x+10,y+10),(x+10,y+34),(x-10,y+34),(x-10,y+10),(x-34,y+10),(x-34,y-10),(x-10,y-10)],fill=c)
    elif kind=='dining':
        d.ellipse((x-23,y-23,x+23,y+23),outline=c,width=5);d.line((x-38,y-31,x-38,y+34),fill=c,width=5);d.line((x+38,y-31,x+38,y+34),fill=c,width=5)
        for dx in [-7,0,7]:d.line((x-38+dx,y-32,x-38+dx,y-12),fill=c,width=3)
    elif kind=='hotel':
        d.rectangle((x-35,y-9,x+35,y+20),outline=c,width=5);d.line((x-35,y-31,x-35,y+32),fill=c,width=5);d.line((x+35,y+17,x+35,y+32),fill=c,width=5);d.rectangle((x-26,y-5,x-6,y+6),fill=c)
    elif kind=='archive':
        d.polygon([(x-35,y-28),(x-5,y-22),(x,y-15),(x+5,y-22),(x+35,y-28),(x+35,y+25),(x+5,y+30),(x,y+35),(x-5,y+30),(x-35,y+25)],outline=c,width=4);d.line((x,y-15,x,y+29),fill=c,width=4)
    elif kind=='theatre':
        d.rectangle((x-37,y-28,x+37,y+28),outline=c,width=5);d.polygon([(x-11,y-19),(x+23,y),(x-11,y+19)],fill=c)
    elif kind=='utility':d.polygon([(x+9,y-36),(x-26,y+7),(x-3,y+7),(x-9,y+36),(x+27,y-9),(x+5,y-9)],fill=c)
    elif kind=='mirror':
        d.polygon([(x,y-36),(x+30,y),(x,y+36),(x-30,y)],outline=c,width=5);d.line((x-12,y+15,x+12,y-15),fill=c,width=4)
    elif kind=='civic':
        d.polygon([(x-39,y-19),(x,y-37),(x+39,y-19)],outline=c,width=5)
        for dx in [-26,0,26]:d.line((x+dx,y-14,x+dx,y+26),fill=c,width=6)
        d.line((x-39,y+32,x+39,y+32),fill=c,width=6)
    else:
        d.ellipse((x-31,y-31,x+31,y+31),outline=c,width=5);d.line((x-27,y+27,x+27,y-27),fill=c,width=4);d.line((x-27,y-27,x+27,y+27),fill=c,width=4)
def main():
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    world=json.loads((R/'art/space_v4/runtime_v1/world.json').read_text(encoding='utf8'))
    names={k:v['label']for k,v in world['spaces'].items()};names['guest_room']='개인 객실'
    # Square atlas cells carry a 4:1 printed sign with explicit blank gutters.
    atlas=Image.new('RGBA',(2048,512),(21,25,33,255));rows={}
    for i,(ident,name)in enumerate(names.items()):
        x=(i%8)*256;y=(i//8)*72;c=PALETTE[family(ident)];tile=Image.new('RGBA',(512,128),(21,25,33,255));d=ImageDraw.Draw(tile)
        symbol={'laundry_room':'washer','cold_store':'snowflake','maintenance_workshop':'gear','inspection_hall_normal':'gear','inspection_hall_changed':'gear','supply_store':'crate','refreshment_store':'crate','central_control':'monitor','staff_passage':'passage'}.get(ident,family(ident))
        d.rounded_rectangle((3,3,508,124),radius=12,outline=c,width=4);pictogram(d,symbol,61,64,c)
        size=44
        while d.textbbox((0,0),name,font=ImageFont.truetype(FONT,size))[2]>372:size-=1
        font=ImageFont.truetype(FONT,size);d.text((119,64),name,font=font,anchor='lm',fill='#f5eee1')
        tile=tile.resize((248,62),Image.Resampling.LANCZOS);atlas.alpha_composite(tile,(x+4,y+5))
        rows[ident]={'label':name,'family':family(ident),'symbol':symbol,'rectPixels':[x+4,y+5,248,62]}
    atlas.save(O/'facility-signs.png')
    owners={f'guest_{i+1:02d}':slug for i,slug in enumerate(CAST)}
    manifest={'scope':'Own cast door badges and facility identities; room allocation introduced for art consistency, no story event changed','facilityAtlas':'art/space_v4/facility_identity_v1/facility-signs.png','atlasSize':[2048,512],'facilities':rows,'roomOwners':owners}
    faces=O/'faces'
    if all((faces/(s+'.png')).exists()for s in CAST):
        sheet=Image.new('RGBA',(288,288),(21,25,33,255));rects={}
        for i,s in enumerate(CAST):
            im=Image.open(faces/(s+'.png')).convert('RGBA');assert im.size==(64,64)
            x=(i%4)*72+4;y=(i//4)*72+4;sheet.alpha_composite(im,(x,y));rects[s]=[x,y,64,64]
        sheet.save(O/'room-faces.png');manifest.update(faceAtlas='art/space_v4/facility_identity_v1/room-faces.png',faceAtlasSize=[288,288],faceRects=rects,faceSampler='NEAREST; no mipmaps, no smoothing')
    (O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    # The exported dome's vertical UV fit is 1.35, not a conventional equirect dome.
    align={}
    for phase,box in {'day':(875,351,906,383),'evening':(876,426,897,447),'night':(913,315,974,375)}.items():
        file=R/'art/environment_v4'/(phase+'.png');im=np.array(Image.open(file).convert('RGB'));l,t,r,b=box;a=im[t:b,l:r].astype(float);luma=a.mean(axis=2);mask=luma>=luma.max()-6;yy,xx=np.where(mask);assert len(xx)>0
        x=float(np.mean(xx)+l);y=float(np.mean(yy)+t);h,w=im.shape[:2];u=x/w;v=.5+(y/h-.5)/1.35;az=(u-.5)*math.tau;el=(.5-v)*math.pi;direction=[-math.cos(el)*math.sin(az),math.sin(el),-math.cos(el)*math.cos(az)]
        # Euler XYZ: rotate +Z onto the measured light direction.
        dx,dy,dz=direction;rx=math.atan2(-dy,dz);ry=math.asin(dx)
        align[phase]={'image':file.relative_to(R).as_posix(),'sourceSHA256':digest(file),'discPixel':[x,y],'direction':direction,'rotationDegrees':[math.degrees(rx),math.degrees(ry),0],'elevationDegrees':math.degrees(el),'projectionVerticalFit':1.35}
    (R/'art/environment_v4/celestial-alignment.json').write_text(json.dumps(align,indent=2)+'\n')
    print(json.dumps({'facilities':len(rows),'roomOwners':len(owners),'facesPacked':'faceAtlas'in manifest,'celestialElevations':{k:v['elevationDegrees']for k,v in align.items()}}))
if __name__=='__main__':main()
