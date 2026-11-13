import sys; sys.path.insert(0,'.')
exec(open('run_step2.py').read().split('print("gain step')[0])
for gc,lab in [(1.0,"INA REF exact"),(1.0002,"INA REF gain error 0.02%"),(1.0005,"INA REF gain error 0.05%")]:
    kw=dict(Cs=1e-12,fhp=1.0,kboot=0.99,gcmd=gc,grep=1.0,mis_rep=0.002,rep_rmis=0.001)
    r=[f'{f0} Hz {max(thd(f0,1.0,g,1,3.3e6,settle=1.0,**kw) for g in [0,-12,-25])*100:.3f}%' for f0 in [50,200,1000]]
    span,a,rl,sa,sr,e5,e20,e60,drift=step(1,3.3e6,**kw)
    print(f"{lab:26}: THD "+" | ".join(r)+f" || attack90 {a:.2f}, release90 {rl:.2f} ms, settle 0.1 dB {sa:.1f}/{sr:.1f} ms, err +5/+20/+60 ms {e5:+.3f}/{e20:+.3f}/{e60:+.3f} dB")
