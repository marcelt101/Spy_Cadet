import sys; sys.path.insert(0,'.')
from cc import *
def step(mode,R,g1=0.0,g2=-15.0,**kw):
    P=40; f0=2*FC/P; T=0.62; n=int(round(T*FC))*SPC; t=np.arange(n)*DT
    s=np.where((np.arange(n)%SPC)<SPC//2,1.0,-1.0)
    vc=np.where((t>=0.30)&(t<0.46),vb_for(g2),vb_for(g1))
    p=params(mode,R,n=n,**kw)
    y,c=run(0.3*np.sqrt(2)*np.sin(2*np.pi*f0*t)*s,vc,**p)
    yy=demod(y); m=len(yy)//P; tt=(np.arange(m)+1.0)*P/(2*FC)
    ref=np.exp(-2j*np.pi*f0*np.arange(P)/(2*FC))
    A=np.array([abs(np.sum(yy[k*P:(k+1)*P]*ref)) for k in range(m)])
    gdb=20*np.log10(A)
    hi=gdb[np.argmin(abs(tt-0.295))]; lo=gdb[np.argmin(abs(tt-0.455))]; hi2=gdb[np.argmin(abs(tt-0.615))]
    span=hi-lo
    a90=(tt[np.flatnonzero((tt>0.30)&(gdb<=hi-0.9*span))[0]]-0.30)*1e3
    r90=(tt[np.flatnonzero((tt>0.46)&(gdb>=lo+0.9*span))[0]]-0.46)*1e3
    def settle(t0,final,tol):
        idx=np.flatnonzero((tt>t0)&(tt<t0+0.15)&(np.abs(gdb-final)>tol))
        return (tt[idx[-1]]-t0)*1e3 if len(idx) else 0.0
    e5=gdb[np.argmin(abs(tt-0.305))]-lo; e20=gdb[np.argmin(abs(tt-0.32))]-lo; e60=gdb[np.argmin(abs(tt-0.36))]-lo
    return span,a90,r90,settle(0.30,lo,0.1),settle(0.46,hi2,0.1),e5,e20,e60,hi2-hi
print("gain step (5.12 kHz tone, 0.2 ms resolution), measured against the settled gain")
for R in [10e6,3.3e6,1e6]:
    for mode,name in [(0,"plain R feed     "),(1,"bootstrap+replica")]:
        span,a,r,sa,sr,e5,e20,e60,drift=step(mode,R)
        print(f"  R={R/1e6:4.1f}M {name}: step {span:5.1f} dB | attack90 {a:5.2f} ms, release90 {r:5.2f} ms | within 0.1 dB after {sa:5.1f} / {sr:5.1f} ms | error at +5/+20/+60 ms: {e5:+.2f} {e20:+.3f} {e60:+.3f} dB")
