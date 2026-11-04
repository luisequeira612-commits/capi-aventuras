import argparse, asyncio, json, os, re, shutil, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

ROOT=Path(__file__).resolve().parents[1]
W,H,FPS=1080,1920,24
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def run(args, capture=False):
    return subprocess.run(args,check=True,text=capture,capture_output=capture,stdout=None if capture else subprocess.DEVNULL,stderr=subprocess.PIPE)

def font(size): return ImageFont.truetype(FONT,size)

def measure(draw,text,f):
    return draw.textbbox((0,0),text,font=f)[2]

def wrap_text(draw,text,f,max_width):
    words=str(text).split()
    if not words: return []
    lines=[]; current=""
    for word in words:
        candidate=word if not current else current+" "+word
        if measure(draw,candidate,f)<=max_width:
            current=candidate
        else:
            if current: lines.append(current)
            # Long unbreakable token: split it by measured character width.
            if measure(draw,word,f)>max_width:
                part=""
                for ch in word:
                    if part and measure(draw,part+ch,f)>max_width:
                        lines.append(part); part=ch
                    else: part+=ch
                current=part
            else: current=word
    if current: lines.append(current)
    return lines

def fit_lines(draw,text,max_width,max_height,start=52,minimum=30,line_gap=12):
    for size in range(start,minimum-1,-1):
        f=font(size); lines=wrap_text(draw,text,f,max_width)
        line_h=f.getbbox("Ag")[3]-f.getbbox("Ag")[1]
        total=len(lines)*line_h+max(0,len(lines)-1)*line_gap
        if total<=max_height and all(measure(draw,line,f)<=max_width for line in lines):
            return f,lines,line_h,total
    raise ValueError(f"Texto no cabe ni con fuente {minimum}: {text!r}")

def draw_text_box(draw,text,box,fill,outline,text_color,start=52,minimum=30,pad=32,radius=34):
    if not str(text).strip(): return None
    x1,y1,x2,y2=box; max_w=x2-x1-2*pad; max_h=y2-y1-2*pad
    f,lines,line_h,total=fit_lines(draw,text,max_w,max_h,start,minimum)
    actual_h=total+2*pad
    y2=y1+actual_h
    if y2>H-20: raise ValueError("Caja de texto excede el lienzo")
    draw.rounded_rectangle((x1,y1,x2,y2),radius=radius,fill=fill,outline=outline,width=6)
    y=y1+pad
    for line in lines:
        bbox=draw.textbbox((0,0),line,font=f)
        draw.text((x1+pad,y-bbox[1]),line,font=f,fill=text_color)
        assert measure(draw,line,f)<=max_w, "Texto desbordado"
        y+=line_h+12
    return y2

async def edge(text,voice,path):
    await edge_tts.Communicate(text,voice=voice,rate="-5%").save(str(path))

def make_voice(text,lang,path):
    voice="pt-BR-FranciscaNeural" if lang=="pt" else "es-MX-DaliaNeural"
    try: asyncio.run(edge(text,voice,path))
    except Exception as exc:
        model=os.getenv("PIPER_MODEL_PT" if lang=="pt" else "PIPER_MODEL_ES")
        if not model or not shutil.which("piper"):
            raise RuntimeError(f"Falló TTS {lang}; Piper no disponible: {exc}")
        subprocess.run(["piper","--model",model,"--output_file",str(path)],input=text,text=True,check=True)

def audio_duration(path):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(path)],text=True).strip())

def make_frame(data,pose,word=None,translation=None,message=None):
    bg=Image.open(ROOT/"assets/generated"/f"fondo_{data['fondo']}.png").convert("RGB").resize((W,H))
    ch=Image.open(ROOT/"assets/generated"/f"capi_{pose}.png").convert("RGBA")
    alpha=ch.getchannel("A").getbbox()
    if alpha: ch=ch.crop(alpha)
    ch.thumbnail((600,900),Image.Resampling.LANCZOS)
    # Character fills ~50-55% video width and sits centrally with minimal dead space.
    bg.paste(ch,((W-ch.width)//2,390),ch)
    draw=ImageDraw.Draw(bg)
    draw_text_box(draw,data["titulo_pt"],(42,38,1038,360),"#FFF8E8","#9A6748","#543624",52,34,34,38)
    if word:
        draw_text_box(draw,word,(65,1390,1015,1660),"#FFF9EB","#9A6748","#245A54",104,72,28,38)
        if translation:
            f=font(54); txt=str(translation)
            if measure(draw,txt,f)>850:
                f,lines,lh,total=fit_lines(draw,txt,850,100,54,36,5)
            else: lines=[txt]; lh=60
            yy=1670
            for line in lines:
                draw.text(((W-measure(draw,line,f))//2,yy),line,font=f,fill="#704C39"); yy+=lh+5
        draw.text((W//2-150,1780),"Repita comigo!",font=font(40),fill="#FFFFFF",stroke_width=3,stroke_fill="#345C55")
    elif message and str(message).strip():
        draw_text_box(draw,message,(65,1450,1015,1850),"#FFF9EB","#9A6748","#543624",58,34,34,38)
    return bg

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("episode"); ap.add_argument("--out",default="output")
    a=ap.parse_args(); data=json.loads(Path(a.episode).read_text(encoding="utf-8"))
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix="capi-render-")); clips=[]; subtitles=[]; elapsed=0.0
    def add(text="",lang="pt",pose="hablando_abierta",word=None,translation=None,message=None,silence=0):
        nonlocal elapsed
        index=len(clips); audio=work/f"a{index}.wav"
        if text:
            raw=work/f"voice{index}.mp3"; make_voice(text,lang,raw)
            subprocess.run(["ffmpeg","-y","-i",str(raw),"-af","silenceremove=start_periods=1:start_duration=0.15:start_threshold=-45dB:start_silence=0.12:stop_periods=1:stop_duration=0.15:stop_threshold=-45dB:stop_silence=0.12","-ac","1","-ar","24000",str(audio)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            duration=audio_duration(audio)
            subtitles.append((elapsed,elapsed+duration,text))
        else:
            duration=float(silence)
            subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=24000:cl=mono","-t",str(duration),str(audio)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        frame=make_frame(data,pose,word,translation,message)
        image=work/f"i{index}.png"; frame.save(image)
        video=work/f"v{index}.mp4"
        subprocess.run(["ffmpeg","-y","-loop","1","-i",str(image),"-i",str(audio),"-t",f"{duration:.3f}","-r",str(FPS),"-vf",f"scale={W}:{H},format=yuv420p","-c:v","libx264","-preset","ultrafast","-c:a","aac","-b:a","128k","-shortest",str(video)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        clips.append(video); elapsed+=duration
    add(data["titulo_pt"],"pt","saludando")
    add(data["lugar"],"pt","neutral")
    for scene in data["escenas"]:
        item=scene["palabras_es"][0]
        add(scene["texto_pt"],"pt",scene["pose"])
        add(item["es"],"es",scene["pose"],item["es"],item["pt"])
        # Keep the same word card on screen during a clean 2.5-second pause.
        add("",pose=scene["pose"],word=item["es"],translation=item["pt"],silence=2.5)
    add("Vamos revisar!","pt","feliz")
    add(data.get("cierre_pt","Muito bem! Até a próxima aventura!"),"pt","saludando",message=data.get("cierre_pt","Muito bem! Até a próxima aventura!"))
    listing=work/"concat.txt"
    listing.write_text("\n".join(f"file '{p.as_posix()}'" for p in clips),encoding="utf-8")
    eid=Path(a.episode).stem; mp4=out/f"{eid}.mp4"
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(listing),"-c","copy","-movflags","+faststart",str(mp4)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    def stamp(t):
        ms=round(t*1000); hh,ms=divmod(ms,3600000); mm,ms=divmod(ms,60000); ss,ms=divmod(ms,1000)
        return f"{hh:02}:{mm:02}:{ss:02},{ms:03}"
    lines=[]
    for i,(start,end,text) in enumerate(subtitles,1):
        lines.extend([str(i),f"{stamp(start)} --> {stamp(end)}",text,""])
    (out/f"{eid}.srt").write_text("\n".join(lines),encoding="utf-8")
    (out/"metadata.txt").write_text(f"{data['titulo_pt']}\n\n{data['descripcion_pt']}\n\n{' '.join(data['hashtags'])}\n\nConteúdo criado com assistência de IA. Revise o conteúdo, a pronúncia e as legendas antes de publicar.\n",encoding="utf-8")
    shutil.rmtree(work,ignore_errors=True)
    print(f"RENDER_OK id={eid} expected_duration={elapsed:.3f} resolution={W}x{H}")
if __name__=="__main__": main()
