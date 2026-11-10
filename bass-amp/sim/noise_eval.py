"""Compare the A1 stage's output noise with the noise of the pickup alone.
Pickup model: 8k DCR + 3 H, 300 pF cable. Prints A-weighted EIN-equivalent
figures and the noise-figure-like penalty of the preamp (dB)."""
import subprocess, numpy as np, sys
def aw(f):
    f2=f*f
    ra=(12194**2*f2*f2)/((f2+20.6**2)*np.sqrt((f2+107.7**2)*(f2+737.9**2))*(f2+12194**2))
    return ra*10**(2.0/20)
def run(params):
    txt=open('t_noise.cir').read().replace("X1 INP INN OUT VP VN 0 HVOA","X1 INP INN OUT VP VN 0 HVOA "+params)
    txt=txt.replace(".control",".control\nac dec 50 20 20k\nwrdata gain.dat v(out)\n").replace("setplot noise2\nprint inoise_total onoise_total\nsetplot noise1","setplot noise1\nwrdata noise.dat onoise_spectrum")
    open('tmp.cir','w').write(txt); subprocess.run(['ngspice','-b','tmp.cir'],capture_output=True)
    g=np.loadtxt('gain.dat'); n=np.loadtxt('noise.dat')
    f=g[:,0]; H=np.hypot(g[:,1],g[:,2]); fn=n[:,0]; on=np.interp(f,fn,n[:,1])
    pu=np.sqrt(4*1.38e-23*300*8000)*H
    w=aw(f)**2
    tot=np.sqrt(np.trapezoid(on**2*w,f)); ref=np.sqrt(np.trapezoid(pu**2*w,f))
    print(f"{params:50s} out A-wtd: amp+pickup {tot*1e6:7.2f} uV, pickup alone {ref*1e6:7.2f} uV, penalty {20*np.log10(tot/ref):5.2f} dB")
for p in sys.argv[1:]: run(p)
