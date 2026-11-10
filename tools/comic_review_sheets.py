"""QA contact sheets only. Never publish thumbnails or alter original art."""
import json,hashlib,textwrap
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from v4_comic_presentation import build_comic,ROOT
def main():
    out=ROOT/'Game/Saved/comic-current-visual-review-20261104';out.mkdir(exist_ok=True)
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
    receipts=[]
    for task,metadata in build_comic()['tasks'].items():
        slots=metadata['slots'];sheet=Image.new('RGB',(1440,len(slots)*358),'#25202c');draw=ImageDraw.Draw(sheet)
        for row,slot in enumerate(slots):
            for column,option in enumerate(slot['options']):
                p=ROOT/option['image'];before=hashlib.sha256(p.read_bytes()).hexdigest();image=Image.open(p).convert('RGB');image.thumbnail((472,266))
                x=column*480+(480-image.width)//2;y=row*358+(270-image.height)//2;sheet.paste(image,(x,y))
                label=task+' S'+str(row+1)+' '+option['id']+(' [current replacement]' if option.get('reviewedReplacement') else '')
                draw.text((column*480+8,row*358+272),label,font=font,fill='#f7e9bf')
                for line,text in enumerate(textwrap.wrap(option['caption'],width=31)[:3]):draw.text((column*480+8,row*358+294+line*19),text,font=font,fill='white')
                assert hashlib.sha256(p.read_bytes()).hexdigest()==before
                receipts.append({'task':task,'slot':slot['id'],'option':option['id'],'image':option['image'],'sha256':before,'caption':option['caption'],'source':option['source']})
        sheet.save(out/(task+'.jpg'),quality=93)
    (out/'source-receipt.json').write_text(json.dumps({'scope':'QA-only contact sheets, not game asset edits or final visual acceptance','sourceBytesUnchanged':True,'rows':receipts},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'chapters':6,'sourceImages':len(receipts),'originalBytesChanged':False}))
if __name__=='__main__':main()
