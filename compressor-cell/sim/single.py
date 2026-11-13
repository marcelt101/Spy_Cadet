"""Single-varactor variants, carrier-fed, ideal charge amp & gated sync demod."""
import numpy as np
from numba import njit
FC=100e3; SPC=200; FS=FC*SPC; DT=1/FS
@njit(cache=True)
def Qd(V,cj,M,vj): return cj*vj/(1-M)*((1+V/vj)**(1-M)-1)
@njit(cache=True)
def Cd(V,cj,M,vj): return cj/(1+V/vj)**M
@njit(cache=True)
def run(mode, xs, VB, cj, M, vj, cfix, Qc0):
    """mode 0: single diode, reverse V = VB - a (a = x*s), charge out = -Qd(VB-a)
       mode 1: anti-series pair, floating centre with fixed charge Qc0; out = charge of D2 (centre->VG)
       mode 2: mode 1 + fixed cap fed with -a (half-bridge)"""
    n=len(xs); out=np.empty(n); c=VB
    for i in range(n):
        a=xs[i]
        if mode==0:
            out[i]=-Qd(VB-a,cj,M,vj)
        else:
            for _ in range(40):
                f=Qd(c-a,cj,M,vj)+Qd(c,cj,M,vj)-Qc0
                d=f/(Cd(c-a,cj,M,vj)+Cd(c,cj,M,vj)); c-=d
                if abs(d)<1e-14: break
            q=Qd(c,cj,M,vj)
            if mode==2: q+=cfix*(-a)
            out[i]=q
    return out
def demod(y):
    half=SPC//2; m=len(y)//half; v=y[:m*half].reshape(m,half)
    s=np.where(np.arange(m)%2==0,1.0,-1.0)
    return v[:,int(0.5*half):int(0.94*half)].mean(1)*s
def measure(mode,VB,vrms,dio,cfix=0.0,f0=1000.0):
    cj,M,vj=dio; n=int(4/f0*FS); t=np.arange(n)/FS
    s=np.where((np.arange(n)%SPC)<SPC//2,1.0,-1.0)
    x=vrms*np.sqrt(2)*np.sin(2*np.pi*f0*t)*s
    Qc0=2*Qd(VB,cj,M,vj)
    y=demod(run(mode,x,VB,cj,M,vj,cfix,Qc0)); m=len(y)
    Y=np.fft.rfft(y); h=np.abs(Y[[4*k for k in range(1,10)]])
    return h[0]*2/m/(vrms*np.sqrt(2)), np.sqrt(np.sum(h[1:]**2))/h[0], h[1]/h[0], h[2]/h[0]
ABRUPT=(156e-12,0.45,0.7)          # MV2109-class x2 in parallel
HYPER=(560e-12,1.5,1.2)            # hyperabrupt AM-tuning class (illustrative): ~500 pF @1 V -> ~30 pF @9 V
if __name__=="__main__":
    for dname,dio,vbs in [("ABRUPT (MV2109-class)",ABRUPT,(1.0,13.0)),("HYPERABRUPT (AM-tuning class)",HYPER,(1.0,9.0))]:
        cj,M,vj=dio
        print(f"\n=== {dname}: C({vbs[0]}V)={Cd(vbs[0],*dio)*1e12:.0f} pF, C({vbs[1]}V)={Cd(vbs[1],*dio)*1e12:.0f} pF, ratio {Cd(vbs[0],*dio)/Cd(vbs[1],*dio):.1f} = {20*np.log10(Cd(vbs[0],*dio)/Cd(vbs[1],*dio)):.1f} dB")
        for mode,name in [(0,"A single diode"),(1,"B one anti-series pair")]:
            g0=None
            for VB in np.linspace(vbs[0]+ (1.0 if mode==0 else 0.5),vbs[1],5):
                r=[]
                for v in (0.25,0.5,1.0):
                    g,thd,h2,h3=measure(mode,VB,v,dio)
                    if g0 is None: g0=g
                    r.append(f"{v}V: {thd*100:.3f}% (H3 {h3*100:.3f})")
                print(f"  {name:24} VB={VB:5.2f} gain {20*np.log10(g/g0):6.1f} dB | "+" | ".join(r))
        # half-bridge: fixed cap equal to pair capacitance at VB_null, choose null near the top bias
        VBn=vbs[1]; Cn=Cd(VBn,*dio)/2
        g0=None
        print(f"  C half-bridge: fixed C0G = {Cn*1e12:.1f} pF (pair value at {VBn} V -> null there)")
        for VB in [vbs[0]+0.5, vbs[0]+1.5, vbs[0]+3, VBn-1.5, VBn-0.6]:
            r=[]
            for v in (0.25,0.5,1.0):
                g,thd,h2,h3=measure(2,VB,v,dio,cfix=Cn)
                if g0 is None: g0=g
                r.append(f"{v}V: {thd*100:.3f}%")
            print(f"  {'C pair + fixed cap':24} VB={VB:5.2f} gain {20*np.log10(g/g0):6.1f} dB | "+" | ".join(r))
