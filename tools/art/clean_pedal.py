import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os
HERE=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(HERE,'..','out','src_')

M=52                      # side margin (jacks stick out)
im=Image.open(os.path.join(HERE,'new.png')).convert('RGB')
orig=np.array(im).astype(np.float32)
a=orig.copy()
H,W,_=a.shape
yy,xx=np.mgrid[:H,:W]

def inpaint(mask,rad=5):
    global a
    u=np.clip(a,0,255).astype(np.uint8)
    r=cv2.inpaint(u,(mask>0).astype(np.uint8)*255,rad,cv2.INPAINT_TELEA)
    a=r.astype(np.float32)

def erase_circle(cx,cy,r,m=3):
    for y in range(int(cy-r),int(cy+r)+1):
        dy=y-cy
        if abs(dy)>r: continue
        dx=(r*r-dy*dy)**0.5
        xl=int(round(cx-dx))-m; xr=int(round(cx+dx))+m
        L=a[y,xl-2:xl+1].mean(0); R=a[y,xr:xr+3].mean(0); n=xr-xl
        for i,x in enumerate(range(xl,xr+1)):
            t=i/max(n,1); a[y,x]=L*(1-t)+R*t

def circ_sprite(src,cx,cy,r,feather=2.0,name=None):
    """RGBA circular crop of src around the integer centre; returns (img,(cx,cy))"""
    cx=int(round(cx)); cy=int(round(cy)); s=2*r+1
    crop=np.zeros((s,s,4),np.float32)
    crop[...,:3]=src[cy-r:cy+r+1,cx-r:cx+r+1]
    d=np.hypot(xx[cy-r:cy+r+1,cx-r:cx+r+1]-cx,yy[cy-r:cy+r+1,cx-r:cx+r+1]-cy)
    crop[...,3]=np.clip((r-d)/feather,0,1)*255
    img=Image.fromarray(crop.astype(np.uint8),'RGBA')
    if name: img.save(OUT+name)
    return img,(cx,cy)

# ---------------------------------------------------------------- 1. clean the old half jacks on the rails
ref=a[543,1100:1136].copy()
for y in list(range(255,520))+list(range(568,672)): a[y,1100:1136]=ref
refl=a[722,0:16].copy()
for y in range(110,672): a[y,0:16]=refl

# ---------------------------------------------------------------- 2. LEDs
ladder=[(738.0,350.9),(738.0,390.4),(738.0,428.2),(738.0,467.2),(738.0,506.3),(738.0,543.9),(737.8,582.9),(737.8,621.2),(737.8,660.4)]
modeled={'rm':(956.7,318.4),'ub':(1003.1,348.1),'lb':(1051.2,317.3)}
presetled=(405.5,758.6); statusled=(713.5,758.7)

def make_led_sprites(c,r_s,r_bead,tag,hue_off):
    on,_=circ_sprite(orig,c[0],c[1],r_s,feather=3.0)
    on.save(OUT+f'led_{tag}_on.png')
    # synthetic switched-off bead: black bezel, dark glassy dome, tiny specular
    s=2*r_s+1; k=4
    big=Image.new('RGBA',(s*k,s*k),(0,0,0,0)); d=ImageDraw.Draw(big)
    cxy=r_s*k+k//2
    def disc(rad,col): d.ellipse((cxy-rad*k,cxy-rad*k,cxy+rad*k,cxy+rad*k),fill=col)
    disc(r_bead+3.0,(5,4,4,255))
    disc(r_bead+0.6,(24,20,18,255))
    # dome: stacked discs shifting up-left give a gradient
    steps=26
    for i in range(steps):
        t=i/(steps-1)
        rad=(r_bead)*(1-0.78*t)
        ox=-0.30*(r_bead)*t*k; oy=-0.34*(r_bead)*t*k
        col=tuple(int(v) for v in (hue_off[0]*(0.35+0.65*t),hue_off[1]*(0.35+0.65*t),hue_off[2]*(0.35+0.65*t)))+(255,)
        d.ellipse((cxy+ox-rad*k,cxy+oy-rad*k,cxy+ox+rad*k,cxy+oy+rad*k),fill=col)
    # specular
    sp=Image.new('RGBA',big.size,(0,0,0,0)); ds=ImageDraw.Draw(sp)
    sx=cxy-0.36*r_bead*k; sy=cxy-0.42*r_bead*k; rr=0.30*r_bead*k
    ds.ellipse((sx-rr,sy-rr*0.7,sx+rr,sy+rr*0.7),fill=(255,235,215,120))
    sp=sp.filter(ImageFilter.GaussianBlur(1.6*k)); big=Image.alpha_composite(big,sp)
    # outer fade
    big=big.resize((s,s),Image.LANCZOS)
    big.save(OUT+f'led_{tag}_off.png')

make_led_sprites(ladder[0],17,10.6,'s',(150,58,16))        # small amber LED (ladder, mode, phaser)
make_led_sprites(presetled,26,16.4,'p',(150,58,16))        # preset LED (amber)
make_led_sprites(statusled,26,16.4,'r',(120,12,10))        # status LED (red)
# erase from background
for c in ladder: erase_circle(c[0],c[1],21)
erase_circle(*presetled,25,m=1); erase_circle(*statusled,25,m=1)
for c in (presetled,statusled):
    d=np.hypot(xx-c[0],yy-c[1])
    red=np.clip((a[...,0]-a[...,2]-3)/6,0,1)                     # reste de lueur rouge de l'ancienne LED
    w=np.clip((64-d)/22,0,1)*red                                  # desaturation en fondu (plus de cercle net)
    g=a[...,1:].mean(2)
    for ch in range(3): a[...,ch]=a[...,ch]*(1-w)+g*w

# ---------------------------------------------------------------- 3. mode buttons
BX={'rm':934,'ub':982,'lb':1030}; BY=287; BW=44; BH=98
def white_mask(x0,y0,w,h,thr=150):
    sub=orig[y0:y0+h,x0:x0+w]; return (sub.min(2)>thr)
labels={}
for k,(lx,ly) in modeled.items():
    x0=BX[k]; m=white_mask(x0,BY,BW,BH)
    dd=np.hypot(xx[BY:BY+BH,x0:x0+BW]-lx,yy[BY:BY+BH,x0:x0+BW]-ly)
    m&=(dd>21)
    # keep only the text (largest area below/above the LED)
    ys,xs=np.where(m)
    labels[k]=(xs.min()+x0-2,ys.min()+BY-2,xs.max()+x0+3,ys.max()+BY+3)
print('labels',labels)
# label sprites (white, alpha from "whiteness")
for k,(x0,y0,x1,y1) in labels.items():
    sub=orig[y0:y1,x0:x1]
    al=np.clip((sub.min(2)-45)/(215-45),0,1)
    arr=np.zeros(sub.shape[:2]+(4,),np.uint8); arr[...,:3]=255; arr[...,3]=(al*255).astype(np.uint8)
    Image.fromarray(arr,'RGBA').save(OUT+f'label_{k}.png')
LABPOS={k:(v[0],v[1]) for k,v in labels.items()}
# clean faces: remove LED + label from the three faces (in the working copy a)
rng=np.random.default_rng(3)
def clean_face(k,orange=False):
    """rebuild the face interior from its own per-row colour (no LED, no label)"""
    x0=BX[k]; reg=a[BY:BY+BH,x0:x0+BW]
    out=reg.copy()
    vals=np.full((BH,3),np.nan,np.float32)
    for y in range(BH):
        row=reg[y,4:BW-4]
        if orange: ok=(row[:,0]>200)&(row[:,1]<120)
        else:      ok=(np.abs(row[:,0]-row[:,2])<9)&(row.mean(1)>20)&(row.mean(1)<85)
        if ok.sum()>12: vals[y]=np.median(row[ok],axis=0)
    idx=np.arange(BH); good=~np.isnan(vals[:,0])
    for c in range(3): vals[:,c]=np.interp(idx,idx[good],vals[good,c])
    for y in range(BH): out[y,3:BW-3]=vals[y]
    out[3:BH-3,3:BW-3]+=rng.normal(0,1.1,(BH-6,BW-6,1))
    a[BY:BY+BH,x0:x0+BW]=out
x0=BX['rm']; save_a=a.copy()
clean_face('rm',orange=True)
face_on=np.clip(a[BY:BY+BH,x0:x0+BW],0,255).astype(np.uint8)
Image.fromarray(face_on,'RGB').save(OUT+'face_on.png')
a=save_a
clean_face('ub'); clean_face('lb')
ub_face=a[BY:BY+BH,BX['ub']-1:BX['ub']+BW+1].copy()
a[BY:BY+BH,BX['rm']-1:BX['rm']+BW+1]=ub_face            # RM now has the grey (off) face
FACE=(BX,BY,BW,BH)

# ---------------------------------------------------------------- 4. PITCH-SHIFT label -> sprites
px0,py0,px1,py1=934,398,1076,428
reg=orig[py0:py1,px0:px1].mean(2)
ys,xs=np.where(reg>70); bx0,bx1=xs.min()+px0-2,xs.max()+px0+3; by0,by1=ys.min()+py0-2,ys.max()+py0+3
reg=orig[by0:by1,bx0:bx1].mean(2); al=np.clip((reg-10)/(235-10),0,1)
for nm,rgb in (('white',(255,255,255)),('yellow',(255,214,0))):
    arr=np.zeros(al.shape+(4,),np.uint8); arr[...,0],arr[...,1],arr[...,2]=rgb; arr[...,3]=(al*255).astype(np.uint8)
    Image.fromarray(arr,'RGBA').save(OUT+f'pitchshift_{nm}.png')
PSPOS=(bx0,by0); print('pitchshift',PSPOS,al.shape)
m=np.zeros((H,W),np.uint8); m[by0-3:by1+3,bx0-3:bx1+3]=1; m=(m&(orig.mean(2)>25).astype(np.uint8))
inpaint(cv2.dilate(m,np.ones((5,5),np.uint8)),4)

# ---------------------------------------------------------------- 5. knobs: remove the white pointer
KN=[(114.0,203.0),(292.0,203.0),(472.5,203.0),(652.0,203.0),(829.0,203.0)]
mask=np.zeros((H,W),np.uint8)
for kx,ky in KN:
    sub=(orig[148:194,int(kx)-9:int(kx)+10].min(2)>110)
    mm=np.zeros((H,W),np.uint8); mm[148:194,int(kx)-9:int(kx)+10]=sub
    mask|=cv2.dilate(mm,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(11,11)))
inpaint(mask,6)

# ---------------------------------------------------------------- 6. big cap + foot caps -> sprites, dark seat in the background
cap_big,cb=circ_sprite(orig,1004.7,203.5,69,feather=2.5,name='cap_big.png')
capL,cl=circ_sprite(orig,204.0,782.0,40,feather=2.0,name='cap_fsL.png')
capR,cr=circ_sprite(orig,915.0,782.5,40,feather=2.0,name='cap_fsR.png')
print('caps',cb,cl,cr)
def seat(cx,cy,r,col):
    d=np.hypot(xx-cx,yy-cy); m=np.clip((r-d)/1.5,0,1)[...,None]
    a[:]=a*(1-m)+np.array(col,np.float32)*m
# big cap seat: erase cap + its shadow with row interpolation then darken the gap
erase_circle(1004.7,203.5,76)
seat(204.0,782.0,41.5,(4,4,4)); seat(915.0,782.5,41.5,(4,4,4))

# ---------------------------------------------------------------- 6b. remove the 9V symbol and the "MADE BY STUDIO WIGA" text
def erase_text(x0,x1,y0,y1,thr,grow=5):
    m=np.zeros((H,W),np.uint8)
    sub=(a[y0:y1,x0:x1].mean(2)>thr)
    m[y0:y1,x0:x1]=sub
    inpaint(cv2.dilate(m,np.ones((grow,grow),np.uint8)),5)
erase_text(523,606,41,75,75)
erase_text(436,730,857,892,75)


np.save(os.path.join(HERE,'..','out','pedal_clean.npy'),a)
