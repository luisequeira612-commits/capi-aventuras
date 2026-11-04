import argparse,json,re,shutil,subprocess
from pathlib import Path
from PIL import Image,ImageDraw

def main():
 p=argparse.ArgumentParser();p.add_argument("video");p.add_argument("--out",default="output/verification");a=p.parse_args()
 video=Path(a.video);out=Path(a.out);frames=out/"frames";frames.mkdir(parents=True,exist_ok=True)
 duration=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(video)],text=True).strip())
 if not 60<=duration<=75:raise SystemExit(f"Duración fuera del objetivo: {duration:.3f}s (60–75s)")
 sampled=[]
 for sec in range(0,int(duration)+1,3):
  fp=frames/f"frame_{sec:04d}.jpg";subprocess.run(["ffmpeg","-y","-ss",str(sec),"-i",str(video),"-frames:v","1","-q:v","3",str(fp)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  if fp.exists() and fp.stat().st_size:sampled.append((sec,fp))
 meta=json.loads(subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height","-of","json",str(video)],text=True))["streams"][0]
 if (meta["width"],meta["height"])!=(1080,1920):raise SystemExit("Resolución distinta de 1080x1920")
 lp=Path("output/layout.json")
 if not lp.exists():raise SystemExit("Falta output/layout.json")
 layout=json.loads(lp.read_text(encoding="utf-8"))
 layout_duration=layout[-1]["end"] if layout else 0
 delta=abs(layout_duration-duration)
 if not layout or delta>1.0:raise SystemExit(f"Manifiesto y MP4 difieren demasiado: manifiesto={layout_duration:.3f}s, MP4={duration:.3f}s, diferencia={delta:.3f}s")
 empty=[s for s in layout if s["type"] in ("word","caption") and (not s["has_text"] or not s["box"])]
 if empty:raise SystemExit(f"Cajas vacías: {len(empty)}")
 lower=1080*960;small=[]
 for s in layout:
  if s["type"] not in ("word","caption"):continue
  x1,y1,x2,y2=s["box"]
  if y1<960 or (x2-x1)*(y2-y1)/lower<.25:small.append(s)
 if small:raise SystemExit(f"Tarjetas dejan zonas inferiores grandes: {len(small)}")
 checks=0;fail=[]
 for sec,fp in sampled:
  s=next((v for v in layout if v["start"]<=sec+.01<v["end"] and v["type"] in ("word","caption")),None)
  if not s:continue
  x1,y1,x2,y2=s["box"];im=Image.open(fp).convert("RGB").crop((x1+12,y1+12,x2-12,y2-12)).resize((48,32))
  px=list(im.getdata());ratio=sum(1 for r,g,b in px if r>235 and g>225 and b>205)/len(px);checks+=1
  if ratio<.30:fail.append((sec,round(ratio,3)))
 if fail:raise SystemExit(f"Tarjetas vacías/no visibles en muestras: {fail}")
 ocr=edges=0
 if shutil.which("tesseract"):
  for _,fp in sampled:
   res=subprocess.run(["tesseract",str(fp),"stdout","tsv"],text=True,capture_output=True,check=True)
   for row in res.stdout.splitlines()[1:]:
    cols=row.split("\t")
    if len(cols)<12 or not cols[11].strip():continue
    x,y,w,h=map(int,cols[6:10]);ocr+=1
    if x<2 or y<2 or x+w>1078 or y+h>1918:edges+=1
 if edges:raise SystemExit(f"OCR detectó {edges} textos tocando el borde")
 proc=subprocess.run(["ffmpeg","-i",str(video),"-af","silencedetect=noise=-45dB:d=0.8","-f","null","-"],text=True,capture_output=True)
 starts=[];silences=[]
 for line in proc.stderr.splitlines():
  m=re.search(r"silence_start: ([0-9.]+)",line)
  if m:starts.append(float(m.group(1)))
  e=re.search(r"silence_end: ([0-9.]+)",line);d=re.search(r"silence_duration: ([0-9.]+)",line)
  if e and d and starts:silences.append((starts.pop(0),float(e.group(1)),float(d.group(1))))
 longest=max((x[2] for x in silences),default=0)
 contact=Image.new("RGB",(720,((len(sampled)+3)//4)*348),"#F4F0E7");draw=ImageDraw.Draw(contact)
 for i,(sec,fp) in enumerate(sampled):
  thumb=Image.open(fp).convert("RGB").resize((180,320));x=i%4*180;y=i//4*348
  contact.paste(thumb,(x,y));draw.text((x+8,y+324),f"{sec:03d}s",fill="#30231F")
 contact.save(out/"contact_sheet.jpg",quality=90)
 report=[f"Video: {video.name}",f"Duración exacta (ffprobe): {duration:.3f} s",f"Duración planificada (manifiesto): {layout_duration:.3f} s",f"Diferencia de muxing: {delta:.3f} s",f"Resolución: {meta['width']}x{meta['height']}",f"Fotogramas extraídos cada 3 s: {len(sampled)}","Hoja de contacto: contact_sheet.jpg",f"OCR palabras detectadas: {ocr}",f"OCR textos tocando el borde: {edges}",f"Cajas vacías: {len(empty)}",f"Tarjetas revisadas por ocupación de píxeles: {checks}",f"Tarjetas no visibles en muestras: {len(fail)}",f"Tarjetas con área insuficiente: {len(small)}",f"Silencios >=0.8 s detectados: {len(silences)}",f"Silencio más largo detectado: {longest:.3f} s","Intervalos: "+"; ".join(f"{s:.3f}-{e:.3f}s ({d:.3f}s)" for s,e,d in silences),"Texto: medición Pillow + OCR de bordes.","Tarjetas: manifiesto geométrico + proporción de píxeles claros en muestras.","Limitación: las métricas no juzgan por completo la estética, anatomía de Capi ni la percepción humana de espacios vacíos; revisar la hoja de contacto."]
 (out/"verification.txt").write_text("\n".join(report)+"\n",encoding="utf-8");print("\n".join(report))
 if longest>3.2:raise SystemExit(f"Silencio demasiado largo: {longest:.3f}s")
if __name__=="__main__":main()
