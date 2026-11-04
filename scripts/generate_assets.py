from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/generated"
PREVIEW = ROOT / "preview"
OUT.mkdir(parents=True, exist_ok=True)
PREVIEW.mkdir(parents=True, exist_ok=True)
W, H = 900, 900
POSES = ["neutral", "feliz", "sorprendido", "saludando", "hablando_abierta", "hablando_cerrada"]
PALETTE = {"fur":"#A96F45","fur_light":"#C18A5D","fur_dark":"#75472F","muzzle":"#D9AD86","nose":"#30231F","eye":"#211916","cream":"#FFF6E7","green":"#6D9D63","red":"#D96F5F","yellow":"#F2C45E","blue":"#78B7C8"}

def font(size):
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)

def capybara(draw, pose):
    p=PALETTE
    # Broad barrel-shaped body, short legs, no tail.
    draw.ellipse((115,390,785,790), fill=p["fur"], outline=p["fur_dark"], width=9)
    draw.ellipse((150,435,750,755), fill=p["fur_light"])
    # Four compact feet, mostly tucked under the barrel.
    for x in (245, 575):
        draw.rounded_rectangle((x,700,x+105,825), radius=34, fill=p["fur_dark"])
        draw.rounded_rectangle((x+10,700,x+95,790), radius=28, fill=p["fur"])
    # Large sloping head, attached to the front of the body.
    draw.ellipse((275,170,700,610), fill=p["fur"], outline=p["fur_dark"], width=9)
    # Tiny low-set ears, not bear-like.
    draw.ellipse((325,160,385,220), fill=p["fur_dark"])
    draw.ellipse((333,168,377,210), fill=p["fur_light"])
    draw.ellipse((600,160,660,220), fill=p["fur_dark"])
    draw.ellipse((608,168,652,210), fill=p["fur_light"])
    # Wide, squared muzzle and broad dark nose.
    draw.rounded_rectangle((350,365,690,570), radius=68, fill=p["muzzle"], outline=p["fur_dark"], width=6)
    draw.rounded_rectangle((445,365,605,435), radius=25, fill=p["nose"])
    # Small eyes set high and wide.
    for x in (390,625):
        draw.ellipse((x-12,305,x+12,329), fill=p["eye"])
        draw.ellipse((x-5,308,x+2,315), fill="#FFF4DD")
    # Mouth changes by pose; keep the silhouette/palette identical.
    if pose in ("sorprendido","hablando_abierta"):
        draw.ellipse((485,475,555,545), fill="#5A3028", outline="#75472F", width=4)
        draw.ellipse((503,485,537,515), fill="#D98779")
    elif pose == "feliz":
        draw.arc((465,465,575,555), 5, 175, fill="#63392C", width=9)
    elif pose == "hablando_cerrada":
        draw.line((475,515,565,515), fill="#63392C", width=8)
    else:
        draw.arc((475,480,565,545), 5, 175, fill="#63392C", width=7)
    # One short raised foreleg for greeting; otherwise tucked short forelegs.
    if pose == "saludando":
        draw.line((680,520,755,410,780,345), fill=p["fur_dark"], width=48)
        draw.ellipse((750,310,810,370), fill=p["fur_light"], outline=p["fur_dark"], width=5)
    else:
        draw.rounded_rectangle((210,535,300,680), radius=38, fill=p["fur_dark"])
        draw.rounded_rectangle((650,535,735,680), radius=38, fill=p["fur_dark"])

def draw_background(name):
    palettes = {
      "mercado":("#9ED8ED","#EBCB8B","#D9B36D"),
      "playa":("#8ED4ED","#F2D38A","#3CA9C5"),
      "escuela":("#B9D5F0","#E9D7B7","#77A86E"),
      "granja":("#A9D9EF","#91BC72","#8D6847"),
      "cocina":("#F4D9C5","#E8B99D","#B9D5CB"),
      "parque":("#A8D9E7","#8EC77D","#559A61")
    }
    sky, ground, green = palettes[name]
    im=Image.new("RGB",(720,1280),sky); d=ImageDraw.Draw(im)
    d.rectangle((0,850,720,1280),fill=ground)
    if name=="mercado":
        # Readable outdoor market: sky, striped awnings, stalls, produce crates, ground.
        d.rectangle((0,790,720,850),fill="#B58B57")
        for x in (35,270,505):
            d.rectangle((x,440,x+185,805),fill="#F5E7C9",outline="#80573B",width=7)
            d.rectangle((x+12,570,x+173,785),fill="#B77C48",outline="#80573B",width=5)
            d.rectangle((x-12,365,x+197,465),fill="#F7E8C9",outline="#80573B",width=6)
            stripe=26
            for sx in range(x-8,x+200,stripe*2):
                d.polygon([(sx,368),(min(sx+stripe, x+197),368),(min(sx+stripe,x+197),463),(sx,463)],fill="#D96858")
            # Visible produce
            for j,col in enumerate(("#D94E43","#E9B83F","#6DAD57","#E58A37")):
                cx=x+35+(j%2)*65; cy=630+(j//2)*65
                d.ellipse((cx,cy,cx+48,cy+48),fill=col,outline="#704B34",width=3)
                d.line((cx+24,cy-3,cx+29,cy-14),fill="#557A43",width=4)
        d.ellipse((575,90,650,165),fill="#FFE08A")
    elif name=="playa":
        d.ellipse((550,100,650,200),fill="#FFE08A")
        d.polygon([(0,830),(720,760),(720,900),(0,930)],fill="#F7E2A7")
        d.polygon([(0,940),(720,875),(720,1060),(0,1080)],fill="#46B6CC")
        d.polygon([(0,1110),(720,1060),(720,1280),(0,1280)],fill="#EBCB8B")
        d.line((30,980,190,965,340,980,500,950,690,965),fill="#E9FAF8",width=10)
        d.line((60,1030,230,1010,410,1025,650,1000),fill="#E9FAF8",width=8)
        d.ellipse((70,560,210,700),fill="#6DAD57")
        d.line((140,700,140,870),fill="#8A613B",width=22)
    elif name=="escuela":
        d.polygon([(95,465),(360,255),(625,465)],fill="#C96D59",outline="#744C42")
        d.rectangle((145,460,575,835),fill="#F6EEDB",outline="#805F4D",width=8)
        for x in (205,420):
            d.rectangle((x,540,x+105,655),fill="#83C5D8",outline="#805F4D",width=7)
            d.line((x+52,540,x+52,655),fill="#805F4D",width=5)
        d.rectangle((300,680,410,835),fill="#9B674B",outline="#805F4D",width=7)
        d.rectangle((265,420,455,485),fill="#4F826E")
        d.text((295,435),"ESCOLA",font=font(27),fill="white")
    elif name=="granja":
        d.ellipse((60,100,145,185),fill="#FFE08A")
        for x in (90,440):
            d.polygon([(x,590),(x+125,430),(x+250,590)],fill="#B9654E",outline="#754B3D")
            d.rectangle((x+25,585,x+225,850),fill="#E6C18B",outline="#754B3D",width=7)
            d.rectangle((x+95,690,x+155,850),fill="#8D6847")
        d.line((0,900,720,900),fill="#F5E5C7",width=8)
        for x in range(20,720,95):
            d.line((x,855,x,1000),fill="#8A623E",width=8)
        d.line((0,875,720,875),fill="#8A623E",width=8)
    elif name=="cocina":
        d.rectangle((60,340,660,825),fill="#FFF5E8",outline="#A87963",width=9)
        d.rectangle((90,460,630,610),fill="#9BC8C5",outline="#A87963",width=7)
        d.rectangle((110,650,610,810),fill="#D4A47C",outline="#A87963",width=7)
        d.ellipse((230,390,370,450),fill="#E8B94F",outline="#A87963",width=5)
        d.rectangle((470,230,580,340),fill="#B6D5E7",outline="#A87963",width=6)
        d.line((0,850,720,850),fill="#9A745C",width=10)
    elif name=="parque":
        d.ellipse((35,250,255,500),fill="#62A65F")
        d.ellipse((465,210,700,490),fill="#62A65F")
        d.rectangle((130,500,160,790),fill="#8D6847")
        d.rectangle((555,485,585,790),fill="#8D6847")
        d.line((250,825,470,825),fill="#E9E0C8",width=22)
        d.ellipse((330,120,420,210),fill="#FFE08A")
    return im

for pose in POSES:
    canvas=Image.new("RGBA",(W,H),(0,0,0,0))
    capybara(ImageDraw.Draw(canvas),pose)
    canvas.save(OUT/f"capi_{pose}.png")
for name in ("mercado","playa","escuela","granja","cocina","parque"):
    draw_background(name).save(OUT/f"fondo_{name}.png")

# Contact sheet: character poses and all six recognizable locations.
sheet=Image.new("RGB",(900,1200),"#F8F4E9"); d=ImageDraw.Draw(sheet)
for i,pose in enumerate(POSES):
    x=(i%3)*300; y=(i//3)*300
    d.rounded_rectangle((x+8,y+8,x+292,y+292),radius=18,fill="#E8E2D6")
    ch=Image.open(OUT/f"capi_{pose}.png").resize((260,260))
    sheet.paste(ch,(x+20,y+12),ch)
    d.text((x+15,y+268),f"Capi · {pose}",font=font(18),fill="#35251D")
for i,name in enumerate(("mercado","playa","escuela","granja","cocina","parque")):
    x=(i%3)*300; y=600+(i//3)*225
    bg=draw_background(name).resize((284,185))
    sheet.paste(bg,(x+8,y+5))
    d.text((x+15,y+192),f"Fondo · {name}",font=font(18),fill="#35251D")
sheet.save(PREVIEW/"capi_poses.png")
print("OK: 6 poses de capibara, 6 fondos y preview generados")
