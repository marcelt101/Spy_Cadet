import sys; sys.path.insert(0,'.')
from real import *
from scipy.signal import resample_poly, butter, sosfilt
from scipy.io import wavfile
import time
SR_A=48000; DUR=8.0; rng=np.random.default_rng(3)
t=np.arange(int(SR_A*DUR))/SR_A; mix=np.zeros_like(t)
def env(t0,dec,att=0.002):
    tt=t-t0; e=np.where(tt<0,0,np.minimum(tt/att,1)*np.exp(-np.maximum(tt,0)/dec)); return e,tt
beat=0.5
for k in range(16):                                   # kick
    e,tt=env(k*beat,0.18); f=48+62*np.exp(-np.maximum(tt,0)/0.03)
    ph=2*np.pi*np.cumsum(np.where(tt>=0,f,0))/SR_A; mix+=1.0*e*np.sin(ph)
    e2,_=env(k*beat,0.004,0.0005); mix+=0.3*e2*rng.normal(0,1,len(t))
hp=butter(2,[1500,7000],btype='band',fs=SR_A,output='sos'); noise=sosfilt(hp,rng.normal(0,1,len(t)))
for k in range(16):                                   # snare on 2 & 4
    if k%4 in (1,3):
        e,tt=env(k*beat,0.12); mix+=0.55*e*noise*2.5+0.35*e*np.sin(2*np.pi*185*np.maximum(tt,0))
hh=sosfilt(butter(2,8000,btype='high',fs=SR_A,output='sos'),rng.normal(0,1,len(t)))
for k in range(32):                                   # hats
    e,_=env(k*beat/2,0.03); mix+=0.25*e*hh*(1.3 if k%2 else 0.8)
roots=[55.0,43.65,65.41,49.0]                        # A1 F1 C2 G1
chords=[[220,261.6,329.6],[174.6,220,261.6],[261.6,329.6,392],[196,246.9,293.7]]
for bar in range(4):
    for k in range(8):                                # bass 8ths
        t0=bar*2+k*0.25; e,tt=env(t0,0.22,0.004); f=roots[bar]*(2 if k%4==3 else 1)
        saw=2*((f*np.maximum(tt,0))%1)-1; mix+=0.45*e*saw
    for hlf in range(2):                              # chords
        t0=bar*2+hlf*1.0
        for f in chords[bar]:
            for h in range(1,9):
                e,tt=env(t0,1.2/(1+0.6*h),0.004); mix+=0.11*e*np.sin(2*np.pi*f*h*np.maximum(tt,0))/h**1.2
lp=butter(2,9000,fs=SR_A,output='sos'); mix=sosfilt(lp,mix)
x48=mix/np.max(np.abs(mix))*3.5                       # volts at the cell input (peaks 3.5 V ~ +9 dBu)

def compressor(x,thr,ratio,att,rel,knee=6.0):
    a_rms=np.exp(-1/(0.005*SR_A)); p=0.0; L=np.empty_like(x)
    for i,v in enumerate(x):
        p=a_rms*p+(1-a_rms)*v*v; L[i]=10*np.log10(p+1e-12)
    over=L-thr
    gr=np.where(over<=-knee/2,0,np.where(over>=knee/2,(1-1/ratio)*over,(1-1/ratio)*(over+knee/2)**2/(2*knee)))
    aA=1-np.exp(-1/(att*SR_A)); aR=1-np.exp(-1/(rel*SR_A)); R=0.0; Rs=np.empty_like(gr)
    for i,g in enumerate(gr):
        R+=(g-R)*(aA if g>R else aR); Rs[i]=R
    return 10**(-Rs/20),Rs

diodes=make_diodes(); calibrate(diodes)
UP=FS/SR_A                                              # 4 MHz / 48 kHz
def render(name,thr,ratio,att,rel):
    t0=time.time()
    g48,R=compressor(x48,thr,ratio,att,rel)
    xs=resample_poly(x48,250,3); n=len(xs)
    gs=np.interp(np.arange(n)/FS,np.arange(len(g48))/SR_A,g48)
    y=simulate(xs,gs,diodes)                            # 200 kHz
    # reference: perfect gain element through the same 30 kHz output filter
    xi=resample_poly(x48,25,6); gi=np.interp(np.arange(len(xi))/(2*FC),np.arange(len(g48))/SR_A,g48)
    ideal=lowpass(xi*gi)
    m=min(len(y),len(ideal)); y=y[:m]; ideal=ideal[:m]
    # align: fractional delay + scale by least squares (gain calibration / latency are not artifacts)
    Y=np.fft.rfft(y); I=np.fft.rfft(ideal); fr=np.fft.rfftfreq(m,1/(2*FC))
    best=None
    for d in np.linspace(-10e-6,10e-6,401):
        Is=I*np.exp(-2j*np.pi*fr*d); c=np.real(np.vdot(Is,Y))/np.real(np.vdot(Is,Is))
        r=np.sum(np.abs(Y-c*Is)**2)
        if best is None or r<best[0]: best=(r,d,c)
    _,d,c=best; ideal=np.fft.irfft(I*np.exp(-2j*np.pi*fr*d)*c,m)
    y48=resample_poly(y,6,25); i48=resample_poly(ideal,6,25); diff=y48-i48
    band=lambda v: sosfilt(butter(4,[20,20000],btype='band',fs=SR_A,output='sos'),v)
    res_db=20*np.log10(np.std(band(diff))/np.std(band(i48)))
    scale=10**(-1/20)/np.max(np.abs(i48))
    for tag,v in [("ideal",i48),("varactor",y48),("difference_x100",diff*100)]:
        wavfile.write(f"audio/{name}_{tag}.wav",SR_A,np.clip(v*scale,-1,1).astype(np.float32))
    print(f"{name}: GR max {R.max():.1f} dB, mean {R.mean():.1f} dB | cell latency {d*1e6:+.2f} us | "
          f"everything the cell adds (noise+distortion+errors) = {res_db:.1f} dB re music | {time.time()-t0:.0f}s")
wavfile.write("audio/dry_input.wav",SR_A,(x48/np.max(np.abs(x48))*10**(-1/20)).astype(np.float32))
render("glue",thr=-7.0,ratio=3.0,att=0.010,rel=0.150)
render("squash",thr=-16.0,ratio=10.0,att=0.001,rel=0.080)
