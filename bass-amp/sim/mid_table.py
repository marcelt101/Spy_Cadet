from mid_tune import pk
import numpy as np
E6=[1.0,1.2,1.5,1.8,2.2,2.7,3.3,3.9,4.7,5.6,6.8,8.2]
caps=[m*10**e for e in range(-10,-5) for m in E6]
def fmt(c):
    return f"{c*1e9:g}n" if c<1e-6 else f"{c*1e6:g}u"
for ft in [250,500,800,1500,3000]:
    best=None
    for cg in caps:
        for cs in caps:
            r=cs/cg
            if not (6<=r<=8.5): continue
            f=1/(2*np.pi*np.sqrt(680*100e3*cg*cs))
            err=abs(np.log(f/ft))
            if best is None or err<best[0]: best=(err,cg,cs,f)
    _,cg,cs,f=best
    g,fp,q=pk('3.3k','680','100k','10k',fmt(cs),fmt(cg))
    print(f"target {ft:5d}: Cg={fmt(cg):6s} Cs={fmt(cs):6s} calc {f:6.0f} Hz | sim peak {g:.1f} dB @ {fp:.0f} Hz, Q={q:.2f}")
