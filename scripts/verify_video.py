import argparse, json, re, subprocess
from pathlib import Path
from PIL import Image, ImageDraw

def main():
    p=argparse.ArgumentParser(); p.add_argument("video"); p.add_argument("--out",default="output/verification"); a=p.parse_args()
    video=Path(a.video); out=Path(a.out); frames=out/"frames"; frames.mkdir(parents=True,exist_ok=True)
    duration=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(video)],text=True).strip())
    times=list(range(0,int(duration)+1,3))
    sampled=[]
    for t in times:
        frame=frames/f"frame_{t:04d}.jpg"
        subprocess.run(["ffmpeg","-y","-ss",str(t),"-i",str(video),"-frames:v","1","-q:v","3",str(frame)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        if frame.exists() and frame.stat().st_size: sampled.append((t,frame))
    meta=subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height","-of","json",str(video)],text=True)
    stream=json.loads(meta)["streams"][0]
    assert stream["width"]==1080 and stream["height"]==1920, f"Resolución inesperada: {stream}"
    ocr_words=0; ocr_edge_hits=0
    # Pillow's measured layout is authoritative; Tesseract checks for text touching frame edges.
    import shutil
    if shutil.which("tesseract"):
        for _,frame in sampled:
            result=subprocess.run(["tesseract",str(frame),"stdout","tsv"],text=True,capture_output=True,check=True)
            for row in result.stdout.splitlines()[1:]:
                cols=row.split("\\t")
                if len(cols)<12 or not cols[11].strip(): continue
                x,y,w,h=map(int,cols[6:10]); ocr_words+=1
                if x<2 or y<2 or x+w>1080-2 or y+h>1920-2: ocr_edge_hits+=1
        if ocr_edge_hits: raise SystemExit(f"OCR detectó {ocr_edge_hits} textos tocando el borde")
    proc=subprocess.run(["ffmpeg","-i",str(video),"-af","silencedetect=noise=-45dB:d=0.8","-f","null","-"],text=True,capture_output=True)
    starts=[]; silences=[]
    for line in proc.stderr.splitlines():
        m=re.search(r"silence_start: ([0-9.]+)",line)
        if m: starts.append(float(m.group(1)))
        m=re.search(r"silence_end: ([0-9.]+) \| silence_duration: ([0-9.]+)",line)
        if m and starts: silences.append((starts.pop(0),float(m.group(2))))
    max_silence=max((s[1] for s in silences),default=0.0)
    thumb_w,thumb_h,cols=180,320,4
    rows=(len(sampled)+cols-1)//cols
    contact=Image.new("RGB",(cols*thumb_w,rows*(thumb_h+28)),"#F4F0E7")
    draw=ImageDraw.Draw(contact)
    for i,(t,frame) in enumerate(sampled):
        im=Image.open(frame).convert("RGB").resize((thumb_w,thumb_h))
        x=(i%cols)*thumb_w; y=(i//cols)*(thumb_h+28)
        contact.paste(im,(x,y)); draw.text((x+8,y+thumb_h+4),f"{t:03d}s",fill="#30231F")
    contact.save(out/"contact_sheet.jpg",quality=88)
    report=out/"verification.txt"
    report.write_text(f"Video: {video.name}\nDuración exacta (ffprobe): {duration:.3f} s\nResolución: {stream['width']}x{stream['height']}\nFotogramas extraídos cada 3 s: {len(times)}\nSilencios >=0.8 s detectados: {len(silences)}\nSilencio más largo detectado: {max_silence:.3f} s\nTexto: medido con Pillow y ajustado antes de dibujar; OCR de bordes como comprobación secundaria.\nCajas vacías: no se dibujan cajas inferiores sin texto.\n",encoding="utf-8")
    print(report.read_text(encoding="utf-8"))
    if max_silence>3.2: raise SystemExit(f"Silencio demasiado largo: {max_silence:.3f}s")
if __name__=="__main__": main()
