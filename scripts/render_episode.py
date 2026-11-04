import argparse,asyncio,json,os,shutil,subprocess,tempfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import edge_tts
R=Path(__file__).resolve().parents[1]; W,H,FPS=1080,1920,24
def cmd(a): subprocess.run(a,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
def ft(n): return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",n)
async def edge(t,v,p): await edge_tts.Communicate(t,voice=v,rate="-5%").save(str(p))
def voice(t,v,p):
 try: asyncio.run(edge(t,v,p))
 except Exception as e:
  model=os.getenv("PIPER_MODEL_PT" if v.startswith("pt-") else "PIPER_MODEL_ES")
  if not model or not shutil.which("piper"): raise RuntimeError(f"edge-tts falló y Piper no está listo para {v}: {e}")
  subprocess.run(["piper","--model",model,"--output_file",str(p)],input=t,text=True,check=True)
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("episode"); ap.add_argument("--out",default="output"); a=ap.parse_args()
 d=json.loads(Path(a.episode).read_text(encoding="utf-8")); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
 w=Path(tempfile.mkdtemp()); clips=[]; subs=[]; tm=0
 def scene(text,lang,word=None,pt=None,pose="hablando_abierta",silence=0):
  nonlocal tm
  idx=len(clips); au=w/f"a{idx}.mp3"
  if text:
   v="pt-BR-FranciscaNeural" if lang=="pt" else "es-MX-DaliaNeural"; voice(text,v,au)
   dur=max(4.5,float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(au)],text=True).strip()))
   subs.append((tm,tm+dur,text))
  else:
   cmd(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=24000:cl=mono","-t",str(silence),str(au)]); dur=silence
  bg=Image.open(R/"assets/generated"/f"fondo_{d['fondo']}.png").convert("RGB").resize((W,H))
  ch=Image.open(R/"assets/generated"/f"capi_{pose}.png").convert("RGBA"); ch.thumbnail((760,980)); bg.paste(ch,((W-ch.width)//2,440),ch)
  dr=ImageDraw.Draw(bg); dr.rounded_rectangle((55,65,1025,245),radius=45,fill="#FFF8E8",outline="#9A6748",width=7); dr.text((95,112),d["titulo_pt"][:40],font=ft(48),fill="#543624")
  if word:
   dr.rounded_rectangle((75,1430,1005,1740),radius=50,fill="#FFF9EB",outline="#9A6748",width=8); dr.text((125,1480),word,font=ft(100),fill="#245A54"); dr.text((130,1630),pt or "",font=ft(58),fill="#704C39"); dr.text((130,1810),"Repita comigo!",font=ft(42),fill="#FFFFFF",stroke_width=3,stroke_fill="#345C55")
  else:
   dr.rounded_rectangle((85,1510,995,1735),radius=50,fill="#FFF9EB",outline="#9A6748",width=7); dr.text((130,1580),text[:50],font=ft(54),fill="#543624")
  im=w/f"i{idx}.png"; bg.save(im); clips.append((im,au,dur)); tm+=dur
 scene(d["titulo_pt"],"pt","",None,"saludando")
 scene(d["lugar"],"pt",pose="neutral")
 for s in d["escenas"]:
  x=s["palabras_es"][0]
  scene(s["texto_pt"],"pt",pose=s["pose"])
  scene(x["es"],"es",x["es"],x["pt"],s["pose"])
  scene("","",silence=2)
 scene("Vamos revisar!","pt",pose="feliz")
 scene("Muito bem! Até a próxima aventura!","pt",pose="saludando")
 parts=[]
 for i,(im,au,dur) in enumerate(clips):
  v=w/f"v{i}.mp4"; cmd(["ffmpeg","-y","-loop","1","-i",str(im),"-i",str(au),"-t",str(dur),"-r",str(FPS),"-vf",f"scale={W}:{H},format=yuv420p","-c:v","libx264","-preset","ultrafast","-af","apad","-c:a","aac","-t",str(dur),str(v)]); parts.append(v)
 lst=w/"list.txt"; lst.write_text("\n".join(f"file '{p.resolve()}'" for p in parts))
 eid=Path(a.episode).stem; mp4=out/f"{eid}.mp4"; cmd(["ffmpeg","-y","-f","concat","-safe","0","-i",str(lst),"-c","copy","-movflags","+faststart",str(mp4)])
 def stamp(t):
  ms=round(t*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000); return f"{h:02}:{m:02}:{s:02},{ms:03}"
 lines=[]
 for i,(st,en,t) in enumerate(subs,1): lines += [str(i),f"{stamp(st)} --> {stamp(en)}",t,""]
 (out/f"{eid}.srt").write_text("\n".join(lines),encoding="utf-8")
 (out/"metadata.txt").write_text(f"{d['titulo_pt']}\n\n{d['descripcion_pt']}\n\n{' '.join(d['hashtags'])}\n\nConteúdo criado com assistência de IA. Revise o conteúdo, a pronúncia e as legendas antes de publicar.\n",encoding="utf-8")
 shutil.rmtree(w,ignore_errors=True); print(f"{mp4}: {tm:.1f} segundos")
if __name__=="__main__": main()
