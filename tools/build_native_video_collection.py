"""Validate actual recordings and make a seekable, silent native preview reel."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,html
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'연출 영상'

def probe(p):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)],text=True,encoding='utf8'))

def main():
    partial='--partial' in sys.argv
    for i in range(10):
        try:m=json.loads((OUT/'manifest.json').read_text(encoding='utf8'));break
        except ValueError:time.sleep(.02)
    rows=sorted(m['clips'],key=lambda r:Path(r['video']).name)
    if not partial:
        assert len(rows)==18 and not m['failures'],(len(rows),m['failures'])
    checks=[];total=0
    for r in rows:
        video=ROOT/r['video'];gif=ROOT/r['gif'];v=probe(video)
        streams=[s for s in v['streams'] if s['codec_type']=='video'];assert len(streams)==1
        s=streams[0];assert s['codec_name']=='h264' and (s['width'],s['height'])==(640,360),r['name']
        assert not any(s['codec_type']=='audio' for s in v['streams'])
        record=json.loads(Path(r['recording']).read_text(encoding='utf8'));frames=record['frames']
        assert len(frames)>=8 and all(b['elapsed']>a['elapsed'] for a,b in zip(frames,frames[1:]))
        # Distinct captured pixels, not a static screenshot held for the clip.
        directory=Path(r['recording']).parent
        distinct={hashlib.sha256((directory/f['file']).read_bytes()).digest() for f in frames}
        assert len(distinct)>=5,r['name']
        im=Image.open(gif);assert im.n_frames>1
        duration=float(v['format']['duration']);total+=duration
        checks.append({'name':r['name'],'frames':len(frames),'distinctCapturedFrames':len(distinct),'gifFrames':im.n_frames,'width':s['width'],'height':s['height'],'duration':duration,'captureFPS':r['captureFPS'],'audio':False})
    text=['# 실제 움직임 · 연출 재생목록','',f"현재 빌드 `{m['build']}`의 재판 15종 및 일상·자유행동·탐색 미리보기예요.",'','새 대본 수정 전의 게임 화면이에요. 실제 연속 프레임이며, 640×360 무음 미리보기예요. 종류별 짧은 동작을 담았으며 전편의 모든 이벤트·분기 영상을 뜻하지 않아요.','']
    if not partial:text+=['[전체 영상 재생](전체-연출-모아보기.mp4)','']
    text+=['|종류|영상|움직이는 GIF|','|---|---|---|']
    for r in rows:
        v=Path(r['video']).name;g=Path(r['gif']).name
        text.append(f"|{r['label']}|[MP4]({v})|[GIF]({g})|")
    (OUT/'재생목록.md').write_text('\n'.join(text)+'\n',encoding='utf8')
    choices=''.join('<button data-index="'+str(i)+'">'+html.escape(r['label'])+'</button>' for i,r in enumerate(rows))
    payload=json.dumps([{'label':r['label'],'video':Path(r['video']).name,'gif':Path(r['gif']).name} for r in rows],ensure_ascii=False).replace('<','\\u003c')
    page='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>실제 연출 · 동영상</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{background:#111218;color:#eee;font-family:'Malgun Gothic',sans-serif;margin:24px}h1{font-size:26px}p{color:#bbb;line-height:1.7}video{width:min(100%,1100px);max-height:76vh;background:#000}button,a{font:inherit;color:#fff1a2;background:#282a36;border:1px solid #555;padding:10px;display:inline-block;margin:5px;cursor:pointer}nav{max-width:1200px}#title{font-size:20px}</style><h1>유메노쿠니 · 실제 움직임</h1><p>현재 게임의 종류별 짧은 실제 녹화예요. 새 대본 적용 전 / 640×360 / 무음. 재생 버튼을 누르면 움직여요.</p><h2 id="title"></h2><video id="player" controls preload="metadata" playsinline></video><div><a id="gif" target="_blank">GIF 열기</a><a href="전체-연출-모아보기.mp4">전체 모음 영상</a></div><nav>'''+choices+'''</nav><script>const clips='''+payload+''';function select(i){const c=clips[i];document.getElementById('title').textContent=c.label;document.getElementById('player').src=c.video;document.getElementById('gif').href=c.gif;}document.querySelectorAll('button').forEach(b=>b.onclick=()=>{select(+b.dataset.index);document.getElementById('player').play()});select(0);</script></html>'''
    (OUT/'재생.html').write_text(page,encoding='utf8')
    if not partial:
        concat=['ffconcat version 1.0'];metadata=[';FFMETADATA1'];at=0
        for r,c in zip(rows,checks):
            concat.append("file '"+Path(r['video']).name+"'")
            end=at+round(c['duration']*1000);metadata+=['[CHAPTER]','TIMEBASE=1/1000','START='+str(at),'END='+str(end),'title='+r['label']];at=end
        (OUT/'playlist.ffconcat').write_text('\n'.join(concat)+'\n',encoding='utf8');(OUT/'chapters.ffmetadata').write_text('\n'.join(metadata)+'\n',encoding='utf8')
        combined=OUT/'전체-연출-모아보기.mp4'
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-safe','0','-i',str(OUT/'playlist.ffconcat'),'-i',str(OUT/'chapters.ffmetadata'),'-map','0:v:0','-map_metadata','1','-map_chapters','1','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-fps_mode','vfr','-enc_time_base','1:1000','-video_track_timescale','1000','-an','-movflags','+faststart',str(combined)],check=True)
        merged=probe(combined);assert abs(float(merged['format']['duration'])-total)<2
    result={'build':m['build'],'clips':len(rows),'totalSeconds':total,'partial':partial,'checks':checks,'audio':False,'source':'actual sequential native captures; no interpolation or static-slide reconstruction'}
    (OUT/'검증.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'clips':len(rows),'seconds':round(total,2),'partial':partial},ensure_ascii=False))

if __name__=='__main__':main()
