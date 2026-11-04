import argparse, asyncio, json, os, re, shutil, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

ROOT=Path(__file__).resolve().parents[1]
W,H,FPS=1080,1920,24
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def run(args):
    return subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)

def font(size): return ImageFont.truetype(FONT,size)
def measure(draw,text,f): return draw.textbbox((0,0),text,font=f)[2]

def wrap_text(draw,text,f,max_width):
    words=str(text).split()
    lines=[]; current=""
    for word in words:
        candidate=word if not current else current+" "+word
        if measure(draw,candidate,f)<=max_width: current=candidate
        else:
            if current: lines.append(current)
            part=""
            for ch in word:
                if part and measure(draw,part+ch,f)>max_width:
                    lines.append(part); part=ch
                else: part+=ch
            current=part
    if current: lines.append(current)
    return lines

def fit_lines(draw,text,max_width,max_height,start=54,minimum=30,line_gap=10):
    for size in range(start,minimum-1,-1):
        f=font(size); lines=wrap_text(draw,text,f,max_width)
        line_h=f.getbbox("Ag")[3]-f.getbbox("Ag")[1]
        total=len(lines)*line_h+max(0,len(lines)-1)*line_gap
        if total<=max_height and all(measure(draw,line,f)<=max_width for line in lines):
            return f,lines,line_h,total
    raise ValueError(f"Texto no cabe: {text!r}")

def draw_centered(draw,text,center_y,f,color):
    bbox=draw.textbbox((0,0),text,font=f)
    x=(W-(bbox[2]-bbox[0]))//2
    draw.text((x,center_y-bbox[1]),text,font=f,fill=color)

async def edge(text,voice,path):
    await edge_tts.Communicate(text,voice=voice,rate="-5%").save(str(path))

def make_voice(text,lang,path):
    voice="pt-BR-FranciscaNeural" if lang=="pt" else "es-MX-DaliaNeural"
    try: asyncio.run(edge(text,voice,path))
    except Exception as exc:
        model=os.getenv("PIPER_MODEL_PT" if lang=="pt" else "PIPER_MODEL_ES")
        if not model or not shutil.which("piper"): raise RuntimeError(f"Falló TTS {lang}; Piper no disponible: {exc}")
        subprocess.run(["piper","--model",model,"--output_file",str(path)],input=text,text=True,check=True)

def audio_duration(path):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(path)],text=True).strip())

def draw_box(draw,box,fill="#FFF9EB",outline="#9A6748",radius=42):
    draw.rounded_rectangle(box,radius=radius,fill=fill,outline=outline,width=7)

def draw_narration(draw,message):
    if not message or not str(message).strip(): return None
    box=(58,1480,1022,1830); draw_box(draw,box)
    x1,y1,x2,y2=box
    f,lines,line_h,total=fit_lines(draw,message,x2-x1-72,y2-y1-56,54,34,12)
    y=y1+(y2-y1-total)//2
    for line in lines:
        bbox=draw.textbbox((0,0),line,font=f)
        draw.text(((W-measure(draw,line,f))//2,y-bbox[1]),line,font=f,fill="#543624")
        y+=line_h+12
    return box

def draw_word_card(draw,word,translation):
    box=(58,1120,1022,1800); draw_box(draw,box)
    x1,y1,x2,y2=box
    f,lines,line_h,total=fit_lines(draw,word,x2-x1-100,210,116,76,8)
    y=1210
    for line in lines:
        bbox=draw.textbbox((0,0),line,font=f)
        draw.text(((W-measure(draw,line,f))//2,y-bbox[1]),line,font=f,fill="#245A54")
        y+=line_h+8
    tf,tl,th,tt=fit_lines(draw,translation,x2-x1-120,100,58,40,6)
    y=1490
    for line in tl:
        bbox=draw.textbbox((0,0),line,font=tf)
        draw.text(((W-measure(draw,line,tf))//2,y-bbox[1]),line,font=tf,fill="#704C39")
        y+=th+6
    draw_centered(draw,"Repita comigo!",1650,font(46),"#9A553B")
    return box

def make_frame(data,pose,word=None,translation=None,message=None):
    bg=Image.open(ROOT/"assets/generated"/f"fondo_{data['fondo']}.png").convert("RGB").resize((W,H))
    ch=Image.open(ROOT/"assets/generated"/f"capi_{pose}.png").convert("RGBA")
    alpha=ch.getchannel("A").getbbox()
    if alpha: ch=ch.crop(alpha)
    ch.thumbnail((500,760),Image.Resampling.LANCZOS)
    x=555 if data["fondo"]=="mercado" else (W-ch.width)//2
    y=380 if not word else 340
    bg.paste(ch,(x,y),ch)
    draw=ImageDraw.Draw(bg)
    if message: draw_narration(draw,message)
    elif word: draw_word_card(draw,word,translation or "")
    return bg

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("episode"); ap.add_argument("--out",default="output")
    a=ap.parse_args(); data=json.loads(Path(a.episode).read_text(encoding="utf-8"))
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix="capi-render-")); clips=[]; subtitles=[]; elapsed=0.0; layout=[]
    def add(text="",lang="pt",pose="hablando_abierta",word=None,translation=None,message=None,silence=0,min_duration=0):
        nonlocal elapsed
        index=len(clips); audio=work/f"a{index}.wav"
        if text:
            raw=work/f"voice{index}.mp3"; make_voice(text,lang,raw)
            run(["ffmpeg","-y","-i",str(raw),"-af","silenceremove=start_periods=1:start_duration=0.15:start_threshold=-45dB:start_silence=0.12,areverse,silenceremove=start_periods=1:start_duration=0.15:start_threshold=-45dB:start_silence=0.12,areverse","-ac","1","-ar","24000",str(audio)])
            spoken=audio_duration(audio)
            if min_duration and spoken+0.35<float(min_duration):
                raise RuntimeError(f"Locución demasiado corta: {spoken:.2f}s; se necesitan al menos {float(min_duration):.2f}s. Amplía el texto, no añadas silencio.")
            duration=spoken
            subtitles.append((elapsed,elapsed+spoken,text))
        else:
            spoken=0.0; duration=float(silence)
            run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=24000:cl=mono","-t",str(duration),str(audio)])
        frame=make_frame(data,pose,word,translation,message)
        image=work/f"i{index}.png"; frame.save(image)
        video=work/f"v{index}.mp4"
        run(["ffmpeg","-y","-loop","1","-i",str(image),"-i",str(audio),"-t",f"{duration:.3f}","-r",str(FPS),"-vf",f"scale={W}:{H},format=yuv420p","-af","apad","-c:v","libx264","-preset","ultrafast","-c:a","aac","-b:a","128k",str(video)])
        clips.append(video)
        kind="word" if word else ("caption" if message and message.strip() else "scene")
        box=[58,1120,1022,1800] if kind=="word" else ([58,1480,1022,1830] if kind=="caption" else None)
        layout.append({"start":round(elapsed,3),"end":round(elapsed+duration,3),"type":kind,"has_text":bool(word or (message and message.strip())),"box":box,"duration":round(duration,3),"spoken":round(spoken,3)})
        elapsed+=duration
    # The spoken content itself fills each scene; min_duration is a guard, never silent padding.
    add(data["titulo_pt"],"pt","saludando",message=data["titulo_pt"],min_duration=5.0)
    add(data["lugar"],"pt","neutral",message=data["lugar"],min_duration=5.5)
    for scene in data["escenas"]:
        item=scene["palabras_es"][0]
        add(scene["texto_pt"],"pt",scene["pose"],message=scene["texto_pt"],min_duration=4.6)
        add(item["es"],"es",scene["pose"],item["es"],item["pt"])
        add("",pose=scene["pose"],word=item["es"],translation=item["pt"],silence=2.5)
    add("Vamos revisar! Repita as palavras comigo.","pt","feliz",message="Vamos revisar! Repita as palavras comigo.",min_duration=4.5)
    for scene in data["escenas"]:
        item=scene["palabras_es"][0]
        add(item["es"],"es","feliz",item["es"],item["pt"])
        add("",pose="feliz",word=item["es"],translation=item["pt"],silence=0.8)
    closing=data.get("cierre_pt","Muito bem! Até a próxima aventura!")
    add(closing,"pt","saludando",message=closing,min_duration=6.5)
    listing=work/"concat.txt"; listing.write_text("\n".join(f"file '{p.as_posix()}'" for p in clips),encoding="utf-8")
    eid=Path(a.episode).stem; mp4=out/f"{eid}.mp4"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(listing),"-c","copy","-movflags","+faststart",str(mp4)])
    def stamp(t):
        ms=round(t*1000); hh,ms=divmod(ms,3600000); mm,ms=divmod(ms,60000); ss,ms=divmod(ms,1000)
        return f"{hh:02}:{mm:02}:{ss:02},{ms:03}"
    lines=[]
    for i,(start,end,text) in enumerate(subtitles,1):
        lines.extend([str(i),f"{stamp(start)} --> {stamp(end)}",text,""])
    (out/f"{eid}.srt").write_text("\n".join(lines),encoding="utf-8")
    (out/"layout.json").write_text(json.dumps(layout,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"metadata.txt").write_text(f"{data['titulo_pt']}\n\n{data['descripcion_pt']}\n\n{' '.join(data['hashtags'])}\n\nConteúdo criado com assistência de IA. Revise o conteúdo, a pronúncia e as legendas antes de publicar.\n",encoding="utf-8")
    shutil.rmtree(work,ignore_errors=True)
    print(f"RENDER_OK id={eid} expected_duration={elapsed:.3f} resolution={W}x{H}")
if __name__=="__main__": main()
