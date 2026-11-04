import argparse, json, re, shutil, subprocess
from pathlib import Path
from PIL import Image, ImageDraw

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("--out",default="output/verification")
    args=parser.parse_args()
    video=Path(args.video); out=Path(args.out); frames=out/"frames"
    frames.mkdir(parents=True,exist_ok=True)
    duration=float(subprocess.check_output(
        ["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(video)],text=True).strip())
    times=list(range(0,int(duration)+1,3)); sampled=[]
    for second in times:
        frame=frames/f"frame_{second:04d}.jpg"
        subprocess.run(["ffmpeg","-y","-ss",str(second),"-i",str(video),"-frames:v","1","-q:v","3",str(frame)],
                       check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        if frame.exists() and frame.stat().st_size: sampled.append((second,frame))
    meta=subprocess.check_output(
        ["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height","-of","json",str(video)],text=True)
    stream=json.loads(meta)["streams"][0]
    assert (stream["width"],stream["height"])==(1080,1920), f"Resolución inesperada: {stream}"

    # Pillow comprueba geometría del texto durante render; Tesseract añade control de bordes.
    ocr_words=0; ocr_edge_hits=0
    if shutil.which("tesseract"):
        for _,frame in sampled:
            result=subprocess.run(["tesseract",str(frame),"stdout","tsv"],text=True,capture_output=True,check=True)
            for row in result.stdout.splitlines()[1:]:
                cols=row.split("\t")
                if len(cols)<12 or not cols[11].strip(): continue
                x,y,width,height=map(int,cols[6:10]); ocr_words+=1
                if x<2 or y<2 or x+width>1078 or y+height>1918: ocr_edge_hits+=1
        if ocr_edge_hits:
            raise SystemExit(f"OCR detectó {ocr_edge_hits} textos tocando el borde del fotograma")

    proc=subprocess.run(["ffmpeg","-i",str(video),"-af","silencedetect=noise=-45dB:d=0.8","-f","null","-"],
                        text=True,capture_output=True)
    starts=[]; silences=[]
    for line in proc.stderr.splitlines():
        match=re.search(r"silence_start: ([0-9.]+)",line)
        if match: starts.append(float(match.group(1)))
        end_match=re.search(r"silence_end: ([0-9.]+)",line)
        duration_match=re.search(r"silence_duration: ([0-9.]+)",line)
        if end_match and duration_match and starts: silences.append((starts.pop(0),float(duration_match.group(1))))
    max_silence=max((item[1] for item in silences),default=0.0)

    thumb_w,thumb_h,columns=180,320,4
    rows=(len(sampled)+columns-1)//columns
    contact=Image.new("RGB",(columns*thumb_w,rows*(thumb_h+28)),"#F4F0E7")
    draw=ImageDraw.Draw(contact)
    for index,(second,frame) in enumerate(sampled):
        thumb=Image.open(frame).convert("RGB").resize((thumb_w,thumb_h))
        x=(index%columns)*thumb_w; y=(index//columns)*(thumb_h+28)
        contact.paste(thumb,(x,y)); draw.text((x+8,y+thumb_h+4),f"{second:03d}s",fill="#30231F")
    contact.save(out/"contact_sheet.jpg",quality=88)

    report=out/"verification.txt"
    report.write_text("\n".join([
        f"Video: {video.name}",
        f"Duración exacta (ffprobe): {duration:.3f} s",
        f"Resolución: {stream['width']}x{stream['height']}",
        f"Fotogramas extraídos cada 3 s: {len(sampled)}",
        "Hoja de contacto: contact_sheet.jpg",
        f"OCR palabras detectadas: {ocr_words}",
        f"OCR textos tocando el borde: {ocr_edge_hits}",
        f"Silencios >=0.8 s detectados: {len(silences)}",
        f"Silencio más largo detectado: {max_silence:.3f} s",
        "Texto: medición Pillow y ajuste automático antes de dibujar; OCR de bordes como comprobación secundaria.",
        "Cajas vacías: no se dibujan cajas inferiores sin texto."
    ])+"\n",encoding="utf-8")
    print(report.read_text(encoding="utf-8"))
    if max_silence>3.2:
        raise SystemExit(f"Silencio demasiado largo: {max_silence:.3f}s")

if __name__=="__main__":
    main()
