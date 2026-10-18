import sys
from PIL import Image, ImageDraw, ImageFont
src,outdir=sys.argv[1],sys.argv[2]
base=Image.open(src).convert("RGBA").resize((2048,2048),Image.LANCZOS)
K=4; cx=cy=432*K; r=50*K
lay=Image.new("RGBA",base.size,(0,0,0,0)); d=ImageDraw.Draw(lay)
d.ellipse((cx-r-7*K,cy-r-7*K,cx+r+7*K,cy+r+7*K),fill="white")
d.ellipse((cx-r,cy-r,cx+r,cy+r),fill="#1F2937")
f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",37*K)
b=d.textbbox((0,0),"PMc",font=f); w,h=b[2]-b[0],b[3]-b[1]
d.text((cx-w/2-b[0],cy-h/2-b[1]),"PMc",font=f,fill="white")
im=Image.alpha_composite(base,lay)
for n,s in [("icon-512.png",512),("icon-192.png",192),("apple-touch-icon.png",180),("favicon.png",64)]:
    out=im.resize((s,s),Image.LANCZOS)
    if n=="apple-touch-icon.png": 
        bg=Image.new("RGBA",out.size,(255,255,255,255)); out=Image.alpha_composite(bg,out)
    out.convert("RGB" if n=="apple-touch-icon.png" else "RGBA").save(f"{outdir}/{n}")
