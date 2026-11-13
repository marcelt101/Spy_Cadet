"""v3 bias: bootstrapped resistor feed with replica varactor pair (charge-control from real parts)."""
import numpy as np
from numba import njit
from single import Qd, Cd
FC=102.4e3; SPC=100; FS=FC*SPC; DT=1/FS
KB=1.380649e-23; T=300.0
cj=78e-12; M=0.45; vj=0.7
Cfix=Cd(12.0,cj,M,vj)/2
G=lambda VB: Cd(VB,cj,M,vj)/2-Cfix
from scipy.optimize import brentq
vb_for=lambda gdb: 1.5 if gdb==0 else brentq(lambda u: 20*np.log10(G(u)/G(1.5))-gdb,1.5,11.99)

@njit(cache=True)
def solve(Q,a,cj1,cj2,Cs,g):
    c=g
    for _ in range(40):
        f=Qd(c-a,cj1,M,vj)+Qd(c,cj2,M,vj)+Cs*c-Q
        d=f/(Cd(c-a,cj1,M,vj)+Cd(c,cj2,M,vj)+Cs); c-=d
        if abs(d)<1e-14: break
    return c

@njit(cache=True)
def run(xs,vcmd,mode,R,Rrep,fhp,kboot,Cs,mis_pair,mis_rep,Ib,Rleak,nmain,nrep,gcmd=1.0,grep=1.0,share=False,inj=False,delta=0.0099,Rinj=0.0):
    """mode 0: plain resistor feed; mode 1: bootstrapped with replica pair"""
    n=len(xs); out=np.empty(n); cmain=np.empty(n)
    c=vcmd[0]; r=vcmd[0]
    Q=Qd(c,cj*(1+mis_pair),M,vj)+Qd(c,cj,M,vj)+Cs*c
    Qr=Qd(r,cj*(1+mis_rep),M,vj)+Qd(r,cj*(1+mis_rep),M,vj)+Cs*r
    hp=0.0; xprev=0.0; ahp=np.exp(-2*np.pi*fhp*DT)
    for i in range(n):
        a=xs[i]; vc=vcmd[i]
        if mode==1:
            d=c-r
            hp=ahp*(hp+d-xprev); xprev=d          # 1st-order high-pass of (main - replica)
            vdrive=gcmd*vc+kboot*hp
        else:
            vdrive=vc
        if vdrive>14.0: vdrive=14.0
        if vdrive<-14.0: vdrive=-14.0
        leak=((c-a)+c)/Rleak
        if inj:
            vinj=(1.0+delta)*c+kboot*hp
            if vinj>14.0: vinj=14.0
            if vinj<-14.0: vinj=-14.0
            Q+=((vc-c)/R + (vinj-c)/Rinj - leak + Ib)*DT + nmain[i]
        else:
            Q+=((vdrive-c)/R - leak + Ib)*DT + nmain[i]
        vr=vdrive if share else grep*vc
        Qr+=((vr-r)/Rrep - 2*r/Rleak + Ib)*DT + nrep[i]
        c=solve(Q,a,cj*(1+mis_pair),cj,Cs,c)
        r=solve(Qr,0.0,cj*(1+mis_rep),cj*(1+mis_rep),Cs,r)
        out[i]=Qd(c,cj,M,vj)-Cfix*a; cmain[i]=c
    return out,cmain

def demod(y):
    half=SPC//2; m=len(y)//half
    return y[:m*half].reshape(m,half)[:,int(0.5*half):int(0.94*half)].mean(1)*np.where(np.arange(m)%2==0,1.0,-1.0)

def params(mode,R,fhp=5.0,kboot=0.999,gcmd=1.0,grep=1.0,share=False,inj=False,delta=0.0099,Rinj=0.0,Cs=5e-12,mis_pair=0.01,mis_rep=0.01,rep_rmis=0.01,Ib=0.5e-12,Rleak=100e9,seed=1,n=1):
    rng=np.random.default_rng(seed)
    nm=rng.normal(0,np.sqrt(4*KB*T/R*FS/2),n)*DT
    nr=rng.normal(0,np.sqrt(4*KB*T/(R*(1+rep_rmis))*FS/2),n)*DT
    return dict(inj=inj,delta=delta,Rinj=(Rinj if Rinj else R),share=share,gcmd=gcmd,grep=grep,mode=mode,R=R,Rrep=R*(1+rep_rmis),fhp=fhp,kboot=kboot,Cs=Cs,mis_pair=mis_pair,mis_rep=mis_rep,Ib=Ib,Rleak=Rleak,nmain=nm,nrep=nr)

def thd(f0,v,gdb,mode,R,settle=0.05,**kw):
    ncyc=max(16,int(np.ceil(16)));
    P=int(round(2*FC/f0)); f0=2*FC/P                      # exact-cycle frequency
    tmeas=16/f0; T=settle+tmeas; n=int(round(T*FC))*SPC; t=np.arange(n)*DT
    s=np.where((np.arange(n)%SPC)<SPC//2,1.0,-1.0)
    vc=np.full(n,vb_for(gdb))
    p=params(mode,R,n=n,**kw)
    y,_=run(v*np.sqrt(2)*np.sin(2*np.pi*f0*t)*s,vc,**p)
    yy=demod(y); seg=yy[-16*P:]; Y=np.abs(np.fft.rfft(seg)); h=[Y[16*k] for k in range(1,8)]
    return np.sqrt(sum(x*x for x in h[1:]))/h[0]
