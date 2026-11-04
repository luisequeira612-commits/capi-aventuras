from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import math
R=Path(__file__).resolve().parents[1]; O=R/"assets/generated"; P=R/"preview"
O.mkdir(parents=True,exist_ok=True); P.mkdir(parents=True,exist_ok=True)
W,H=720,1280
poses=["neutral","feliz","sorprendido","saludando","hablando_abierta","hablando_cerrada"]
bg={"mercado":("#F7DFA6","#D99A54","#77A66B"),"playa":("#BDEBFA","#E8D18C","#55B8D1"),"escuela":("#DDE8FF","#A9BCE8","#79B77A"),"granja":("#D8EDC2","#A9C47B","#8D6847"),"cocina":("#FFE2CF","#E8A98A","#C77D63"),"parque":("#D5F0D0","#8DC77D","#5A9B66")}
def background(n):
 a,b,c=bg[n]; im=Image.new("RGB",(W,H),a); d=ImageDraw.Draw(im); d.rectangle((0,850,W,H),fill=b); d.ellipse((-120,720,840,1380),fill=c)
 if n=="playa": d.ellipse((530,120,650,240),fill="#FFD36E")
 elif n=="mercado":
  for x in (70,280,490): d.polygon([(x,360),(x+95,360),(x+75,560),(x+20,560)],fill="#F4B45F")
 elif n=="escuela": d.polygon([(70,330),(360,150),(650,330)],fill="#D77E67"); d.rectangle((130,330,590,750),fill="#F6F1DE")
 elif n=="granja": d.polygon([(80,580),(360,340),(640,580)],fill="#C96F56"); d.rectangle((130,580,590,870),fill="#E8C38A")
 elif n=="cocina": d.rectangle((80,380,640,820),fill="#FFF5E8",outline="#C77D63",width=10); d.rectangle((130,460,590,650),fill="#A8D3D0")
 else: d.ellipse((80,260,280,470),fill="#76B96E"); d.ellipse((450,240,680,480),fill="#76B96E")
 return im
def draw(d,cx,cy,s,p):
 d.ellipse((cx-155*s,cy-90*s,cx+155*s,cy+105*s),fill="#A96E45",outline="#75472F",width=5)
 d.ellipse((cx-125*s,cy-155*s,cx+125*s,cy+55*s),fill="#B98053",outline="#75472F",width=5)
 for x in (-77,77): d.ellipse((cx+(x-28)*s,cy-174*s,cx+(x+28)*s,cy-116*s),fill="#B98053")
 d.ellipse((cx-75*s,cy-45*s,cx+75*s,cy+30*s),fill="#D7A47C")
 for x in (-40,40): d.ellipse((cx+(x-8)*s,cy-103*s,cx+(x+8)*s,cy-87*s),fill="#241B17")
 d.ellipse((cx-13*s,cy-25*s,cx+13*s,cy-7*s),fill="#39241D")
 if p in ("sorprendido","hablando_abierta"): d.ellipse((cx-18*s,cy+2*s,cx+18*s,cy+38*s),fill="#4A2525")
 elif p=="feliz": d.arc((cx-38*s,cy-5*s,cx+38*s,cy+48*s),10,170,fill="#5B3026",width=5)
 else: d.arc((cx-30*s,cy, cx+30*s,cy+34*s),5,175,fill="#5B3026",width=4)
 if p=="saludando": d.line((cx+100*s,cy+10*s,cx+155*s,cy-100*s,cx+190*s,cy-125*s),fill="#A96E45",width=25); d.ellipse((cx+172*s,cy-145*s,cx+208*s,cy-108*s),fill="#B98053")
 else:
  d.line((cx-110*s,cy+25*s,cx-165*s,cy+80*s),fill="#A96E45",width=24); d.line((cx+110*s,cy+25*s,cx+165*s,cy+80*s),fill="#A96E45",width=24)
 for x in (-90,75): d.rounded_rectangle((cx+x*s,cy+75*s,cx+(x+48)*s,cy+132*s),radius=12,fill="#75472F")
for p in poses:
 im=Image.new("RGBA",(W,H)); draw(ImageDraw.Draw(im),W//2,650,1.45,p); im.save(O/f"capi_{p}.png")
for n in bg: background(n).save(O/f"fondo_{n}.png")
sheet=Image.new("RGB",(720,1200),"#F8F6F0"); d=ImageDraw.Draw(sheet)
for i,p in enumerate(poses):
 x=i%3*240; y=i//3*300; b=background("parque").resize((240,300)); ch=Image.open(O/f"capi_{p}.png").resize((150,267)); sheet.paste(b,(x,y)); sheet.paste(ch,(x+45,y+5),ch); d.text((x+8,y+272),f"Capi · {p}",fill="#35251D")
for i,n in enumerate(bg):
 x=i%3*240; y=600+i//3*300; b=background(n).resize((240,300)); sheet.paste(b,(x,y)); d.text((x+8,y+272),f"Fondo · {n}",fill="#35251D")
sheet.save(P/"capi_poses.png")
print("6 poses, 6 fondos y preview listos")
