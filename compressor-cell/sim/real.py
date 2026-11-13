"""Varactor-bridge gain cell with datasheet-class real components (behavioural, charge-domain).
Unknowns per step: centre A, centre B, virtual-ground vg; op-amp output via backward-Euler integrator + slew limit."""
import numpy as np
from numba import njit
KB=1.380649e-23; TK=300.0; QE=1.602e-19
# --- varactor: MV2109-class abrupt, 2 in parallel per position
NPAR=2; CJ1=78e-12; VJ=0.7; MG=0.45
CJO=CJ1*NPAR
VA=4.0; VBMAX=28.0
def cdi(V,M=MG,cj=CJO): return cj/(1+V/VJ)**M
DC=(cdi(VA)-cdi(VBMAX))/2; CF=DC/2                    # 0 dB at max imbalance (small-signal)
# --- op-amp OPA1656-class
GBW=53e6; SR=24e6; EN=2.9e-9; CIN=10e-12; RFB=100e6; VRAIL=13.0
# --- carrier / modulator / demod
FC=100e3; SPC=40; FS=FC*SPC; DT=1/FS; RSER=1e3
TAU_EDGE=RSER*(cdi(VA)/2+cdi(VA)/2)                   # ~ series R x node capacitance
WIN=(0.40,0.95)                                       # demod gate within each half period
# --- bias: servo (1 Hz) modelled as equivalent R; leakage per diode
RSERVO=1/(2*np.pi*1.0*(2*cdi(VA))); RLEAK=100e9; FFK=0.9   # leakage feed-forward accuracy

@njit(cache=True)
def Qd(V,p): return p[0]*p[2]/(1-p[1])*((1+V/p[2])**(1-p[1])-1)+p[3]*V
@njit(cache=True)
def Cd(V,p): return p[0]/(1+V/p[2])**p[1]+p[3]

@njit(cache=True)
def engine(a_in, QAt, QBt, A1,A2,B1,B2, noise_vg, noise_qa, noise_qb):
    n=len(a_in); vout_arr=np.empty(n)
    k=2*np.pi*GBW*DT
    # initial state from targets (zero signal): centres at bias, vg=0
    ca=VA; cb=VA
    QA=QAt[0]; QB=QBt[0]
    # solve centres for initial charges
    for _ in range(50):
        f=Qd(ca,A1)+Qd(ca,A2)-QA; ca-=f/(Cd(ca,A1)+Cd(ca,A2))
        f=Qd(cb,B1)+Qd(cb,B2)-QB; cb-=f/(Cd(cb,B1)+Cd(cb,B2))
    vg=0.0; vout=0.0
    Qvg=-Qd(ca,A2)-Qd(cb,B2)            # vg-node charge invariant (Cf,Cin at 0 V)
    dA=0.0; dB=0.0; iA=0.0; iB=0.0       # deviations from target charge; servo integrators
    w0=2*np.pi*1.0; kp=2*w0; ki=w0*w0    # PI servo, critically damped, 1 Hz
    for i in range(n):
        a=0.5*a_in[i]; b=-0.5*a_in[i]
        # bias charge = target (feed-forward current source) + deviation (leakage, noise, servo)
        iLa=-((ca-a)+(ca-vg))/RLEAK; iLb=-((cb-b)+(cb-vg))/RLEAK
        dA+=(iLa*(1-FFK) - kp*dA - iA)*DT + noise_qa[i]; iA+=ki*dA*DT
        dB+=(iLb*(1-FFK) - kp*dB - iB)*DT + noise_qb[i]; iB+=ki*dB*DT
        QA=QAt[i]+dA; QB=QBt[i]+dB
        Qvg+=(vout-vg)/RFB*DT
        en=noise_vg[i]; vprev=vout
        for it in range(2):
            fixed = it==1
            for _ in range(30):
                vo = vout if fixed else vprev-k*(vg-en)
                dvo = 0.0 if fixed else -k
                F1=Qd(ca-a,A1)+Qd(ca-vg,A2)-QA
                F2=Qd(cb-b,B1)+Qd(cb-vg,B2)-QB
                F3=-Qd(ca-vg,A2)-Qd(cb-vg,B2)+CF*(vg-vo)+CIN*vg-Qvg
                c1a=Cd(ca-a,A1); c2a=Cd(ca-vg,A2); c1b=Cd(cb-b,B1); c2b=Cd(cb-vg,B2)
                J11=c1a+c2a; J22=c1b+c2b
                J33=c2a+c2b+CF*(1-dvo)+CIN
                # arrow system: rows 1,2 couple to vg via -c2
                # dca = (-F1 + c2a*dvg)/J11 ; dcb = (-F2 + c2b*dvg)/J22
                # row3: -c2a*dca - c2b*dcb + J33*dvg = -F3
                num=-F3 + c2a*(-F1)/J11 + c2b*(-F2)/J22
                den=J33 - c2a*c2a/J11 - c2b*c2b/J22
                dvg=num/den
                dca=(-F1+c2a*dvg)/J11; dcb=(-F2+c2b*dvg)/J22
                ca+=dca; cb+=dcb; vg+=dvg
                if abs(dvg)<1e-13 and abs(dca)<1e-13 and abs(dcb)<1e-13: break
            if not fixed:
                vtry=vprev-k*(vg-en)
                lim=SR*DT
                if vtry>vprev+lim: vout=vprev+lim
                elif vtry<vprev-lim: vout=vprev-lim
                else:
                    vout=vtry; break
                if vout>VRAIL: vout=VRAIL
                if vout<-VRAIL: vout=-VRAIL
        vout_arr[i]=vout
    return vout_arr

def diode(scale=1.0,ct=0.0,M=MG): return np.array([CJO*scale,M,VJ,ct])
def make_diodes(misA=0.01,misB=-0.008,trim=True,M=MG):
    """D1 of each stack has mismatch; trimmer (70% rule) on the smaller diode"""
    A1=diode(1+misA); B1=diode(1+misB)
    if trim:
        tA=0.7*misA*cdi(VA); tB=0.7*misB*cdi(VA+0.05)
        A2=diode(ct=max(tA,0)); B2=diode(ct=max(tB,0))
        if tA<0: A1=diode(1+misA,ct=-tA)
        if tB<0: B1=diode(1+misB,ct=-tB)
    else:
        A2=diode(); B2=diode()
    return A1,A2,B1,B2

def vb_for_gain(g):
    tgt=g*2*CF*2; lo,hi=VA,VBMAX
    for _ in range(80):
        mid=(lo+hi)/2
        if cdi(VA)-cdi(mid)<tgt: lo=mid
        else: hi=mid
    return (lo+hi)/2
def qtarget(vb,p1,p2):
    return Qd_np(vb,p1)+Qd_np(vb,p2)
def Qd_np(V,p): return p[0]*p[2]/(1-p[1])*((1+V/p[2])**(1-p[1])-1)+p[3]*V

def carrier_sign(n):
    ph=(np.arange(n)%SPC)/SPC; return np.where(ph<0.5,1.0,-1.0), ph
def modulate(x):
    """SPDT switch selects +x / -x each half period; 1k series R into capacitive node (RC edge) + resistor noise"""
    n=len(x); s,ph=carrier_sign(n); v=x*s
    al=np.exp(-DT/TAU_EDGE); y=np.empty(n); acc=v[0]
    rn=np.random.default_rng(7).normal(0,np.sqrt(4*KB*TK*RSER*FS/2),n)
    from scipy.signal import lfilter
    y=lfilter([1-al],[1,-al],v+rn,zi=[v[0]*al])[0]
    return y,s,ph
def demod(vout,s,ph):
    """gated synchronous demod: average vout*s over WIN of each half period -> 2*FC samples/s"""
    half=SPC//2; m=len(vout)//half
    v=vout[:m*half].reshape(m,half); ss=s[:m*half].reshape(m,half)[:,0]
    i0,i1=int(WIN[0]*half),int(WIN[1]*half)
    return v[:,i0:i1].mean(1)*ss
def lowpass(y):
    from scipy.signal import butter, sosfilt
    sos=butter(4,30e3,fs=2*FC,output='sos'); return sosfilt(sos,y)

def simulate(x, gain, diodes, seed=1):
    """x: input volts at FS; gain: linear target gain at FS. Returns demodulated, filtered output at 2*FC."""
    A1,A2,B1,B2=diodes; n=len(x)
    rng=np.random.default_rng(seed)
    vbs=np.array([vb_for_gain(g) for g in np.unique(np.round(gain,5))])
    lut_g=np.unique(np.round(gain,5)); vb=np.interp(gain,lut_g,vbs)
    QBt=Qd_np(vb,B1)+Qd_np(vb,B2); QAt=np.full(n,Qd_np(VA,A1)+Qd_np(VA,A2))
    a,s,ph=modulate(x)
    nvg=rng.normal(0,EN*np.sqrt(FS/2),n)
    iq=np.sqrt(4*KB*TK/RSERVO + 2*QE*1e-10)*np.sqrt(FS/2)*DT
    out=engine(a,QAt,QBt,A1,A2,B1,B2,nvg,rng.normal(0,iq,n),rng.normal(0,iq,n))
    return lowpass(demod(out,s,ph))

# ---- calibration against bias voltage (signed gain), as a real unit's sidechain LUT would store
def simulate_vb(x, vb, diodes, seed=1):
    A1,A2,B1,B2=diodes; n=len(x); rng=np.random.default_rng(seed)
    QBt=Qd_np(vb,B1)+Qd_np(vb,B2); QAt=np.full(n,Qd_np(VA,A1)+Qd_np(VA,A2))
    a,s,ph=modulate(x)
    nvg=rng.normal(0,EN*np.sqrt(FS/2),n)
    iq=np.sqrt(4*KB*TK/RSERVO + 2*QE*1e-10)*np.sqrt(FS/2)*DT
    out=engine(a,QAt,QBt,A1,A2,B1,B2,nvg,rng.normal(0,iq,n),rng.normal(0,iq,n))
    return lowpass(demod(out,s,ph))
_CAL=None
def calibrate(diodes):
    global _CAL
    f0=1000.0; n=int(6/f0*FS); t=np.arange(n)/FS; x=0.1*np.sqrt(2)*np.sin(2*np.pi*f0*t)
    d=np.r_[-np.logspace(-3,0,30)[::-1],0,np.logspace(-4,np.log10(VBMAX-VA),300)]
    vbs=VA+d; gs=[]
    m=int(round(4*2*FC/f0)); ref=None
    for vb in vbs:
        y=simulate_vb(x,np.full(n,vb),diodes); Y=np.fft.rfft(y[-m:])[4]
        if ref is None: ref=np.exp(-1j*np.angle(Y))   # sign reference taken at most-negative-side point
        gs.append(Y)
    gs=np.array(gs); ph=np.exp(-1j*np.angle(gs[-1])); sg=np.real(gs*ph)*2/m/(0.1*np.sqrt(2))
    sg/=sg[-1]                                   # normalise: max-imbalance = 0 dB
    k=np.argmax(sg>0) if np.any(sg>0) else 0
    # monotonic positive branch from the zero crossing upward
    i0=np.flatnonzero(np.diff(np.sign(sg))>0)
    i0=i0[-1]+1 if len(i0) else 0
    gpos=sg[i0:]; vpos=vbs[i0:]
    _CAL=(np.log(np.maximum(gpos,1e-6)),vpos); return vbs,sg
def vb_cal(g):
    from scipy.interpolate import PchipInterpolator
    lg,vb=_CAL; o=np.argsort(lg); lg=lg[o]; vb=vb[o]; keep=np.r_[True,np.diff(lg)>1e-9]
    return PchipInterpolator(lg[keep],vb[keep])(np.log(np.maximum(g,1e-6)))
def simulate(x,gain,diodes,seed=1): return simulate_vb(x,vb_cal(gain),diodes,seed)
