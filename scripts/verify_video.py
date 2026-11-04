import argparse, json, re, subprocess
from pathlib import Path

def main():
    p=argparse.ArgumentParser(); p.add_argument("video"); p.add_argument("--out",default="output/verification"); a=p.parse_args()
    video=Path(a.video); out=Path(a.out); frames=out/"frames"; frames.mkdir(parents=True,exist_ok=True)
    duration=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(video)],text=True).strip())
    times=list(range(0,int(duration)+1,3))
    for t in times:
        subprocess.run(["ffmpeg","-y","-ss",str(t),"-i",str(video),"-frames:v","1","-q:v","3",str(frames/f"frame_{t:04d}.jpg")],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    meta=subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height","-of","json",str(video)],text=True)
    stream=json.loads(meta)["streams"][0]
    assert stream["width"]==1080 and stream["height"]==1920, f"Resolución inesperada: {stream}"
    proc=subprocess.run(["ffmpeg","-i",str(video),"-af","silencedetect=noise=-45dB:d=0.8","-f","null","-"],text=True,capture_output=True)
    starts=[]; silences=[]
    for line in proc.stderr.splitlines():
        m=re.search(r"silence_start: ([0-9.]+)",line)
        if m: starts.append(float(m.group(1)))
        m=re.search(r"silence_end: ([0-9.]+) \| silence_duration: ([0-9.]+)",line)
        if m and starts: silences.append((starts.pop(0),float(m.group(2))))
    max_silence=max((s[1] for s in silences),default=0.0)
    report=out/"verification.txt"
    report.write_text(f"Video: {video.name}\nDuración exacta (ffprobe): {duration:.3f} s\nResolución: {stream['width']}x{stream['height']}\nFotogramas extraídos cada 3 s: {len(times)}\nSilencios >=0.8 s detectados: {len(silences)}\nSilencio más largo detectado: {max_silence:.3f} s\nTexto: medido con Pillow y ajustado antes de dibujar; no se usó OCR independiente.\nCajas vacías: no se dibujan cajas inferiores sin texto.\n",encoding="utf-8")
    print(report.read_text(encoding="utf-8"))
    if max_silence>3.2: raise SystemExit(f"Silencio demasiado largo: {max_silence:.3f}s")
if __name__=="__main__": main()
