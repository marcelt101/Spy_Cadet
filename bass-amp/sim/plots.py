"""Regenerate the response plots in ../docs from the SPICE netlists."""
import subprocess, numpy as np, re, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mid_tune import resp
plt.rcParams.update({'figure.dpi':110,'axes.grid':True,'grid.alpha':.3})
# --- EQ ---------------------------------------------------------------
fig,ax=plt.subplots(1,3,figsize=(14,4.2),sharey=True)
for p in [0,.25,.5,.75,1]:
    f,g=resp('3.3k','680','100k','10k','100n','15n',pm=.5,pb=p,pt=.5); ax[0].semilogx(f,g,label=f"bass {p*10:.0f}")
    f,g=resp('3.3k','680','100k','10k','100n','15n',pm=.5,pb=.5,pt=p); ax[2].semilogx(f,g,label=f"treble {p*10:.0f}")
for cg,cs,lab in [('27n','220n','250 Hz'),('15n','100n','500 Hz'),('8.2n','68n','800 Hz'),('4.7n','33n','1.5 kHz'),('2.2n','18n','3 kHz')]:
    for pm in (0,1):
        f,g=resp('3.3k','680','100k','10k',cs,cg,pm=pm)
        ax[1].semilogx(f,g,color='C%d'%['250 Hz','500 Hz','800 Hz','1.5 kHz','3 kHz'].index(lab),label=lab if pm==0 else None)
for a,t in zip(ax,['BASS (0..10)','MID full boost/cut, 5 positions','TREBLE (0..10)']):
    a.set_title(t); a.set_xlabel('Hz'); a.set_xlim(10,40e3); a.legend(fontsize=8)
ax[0].set_ylabel('dB'); fig.tight_layout(); fig.savefig('../docs/eq_response.png')
# --- A1 input stage: response vs gain + input impedance ---------------
def a1(rf):
    t=open('t_final.cir').read().split('* ---- A2')[0]
    t=t.replace('.param amp=1 f=1k rf=47k',f'.param amp=1 f=1k rf={rf}').replace('VIN JACK 0 DC 0 SIN(0 {amp} {f})','VIN SRC 0 DC 0 AC 1\nRSRC SRC JACK 1')
    t=t.replace(".nodeset v(x1.tail)=1 v(x2.tail)=1 v(out)=0 v(out2)=0","")
    t+=".nodeset v(x1.tail)=1 v(out)=0 v(inp)=0 v(inn)=0 v(bs)=0 v(x1.m2)=-38.3 v(x1.vasl)=-0.7 v(x1.vash)=0.8 v(x1.casb)=-4.7 v(x1.v7)=-38.9 v(x1.v8)=-36.6\n.control\nac dec 50 0.5 1Meg\nwrdata a1.dat v(out) i(VIN)\n.endc\n.end\n"
    open('tmp_a1.cir','w').write(t); subprocess.run(['ngspice','-b','tmp_a1.cir'],capture_output=True)
    d=np.loadtxt('a1.dat'); f=d[:,0]; H=np.hypot(d[:,1],d[:,2]); I=np.hypot(d[:,4],d[:,5]); return f,20*np.log10(H),1/I
fig,ax=plt.subplots(1,2,figsize=(12,4))
for rf,lab in [(0,'gain min (+1.7 dB)'),('4.7k','gain mid'),('47k','gain max (+27 dB)')]:
    f,g,z=a1(rf); ax[0].semilogx(f,g,label=lab)
ax[1].loglog(f,z); ax[1].set_title('A1 input impedance (incl. 100 pF RF cap)'); ax[1].set_ylabel('ohm')
ax[0].set_title('A1 bootstrapped input/gain stage'); ax[0].set_ylabel('dB'); ax[0].legend()
for a in ax: a.set_xlabel('Hz')
fig.tight_layout(); fig.savefig('../docs/a1_response.png')
# --- subsonic filter ----------------------------------------------------
def sk(r1,r2,c):
    w=2*np.pi*np.logspace(0,3,400); s=1j*w
    H=s**2/(s**2+s*(2/(r2*c))+1/(r1*r2*c*c)); return w/2/np.pi,20*np.log10(abs(H))
fig,ax=plt.subplots(figsize=(6,4))
for r1,r2,lab in [(22e3,47e3,'DEEP  (22k/47k, 220n)'),(22e3*27e3/49e3,47e3*56e3/103e3,'TIGHT (22k||27k / 47k||56k, 220n)')]:
    f,g=sk(r1,r2,220e-9); ax.semilogx(f,g,label=lab)
    print(lab, 'f(-3dB)=%.1f Hz'%f[np.argmin(abs(g+3))], 'at 31Hz %.2f dB'%np.interp(31,f,g), 'at 41Hz %.2f dB'%np.interp(41,f,g))
ax.axvline(30.9,ls=':',c='k'); ax.text(31.5,-30,'low B 30.9 Hz',fontsize=8); ax.axvline(41.2,ls=':',c='k'); ax.text(42,-35,'low E 41.2 Hz',fontsize=8)
ax.set_ylim(-40,3); ax.set_title('Subsonic filter (2nd order, unity-gain Sallen-Key)'); ax.legend(); ax.set_xlabel('Hz'); ax.set_ylabel('dB')
fig.tight_layout(); fig.savefig('../docs/subsonic.png')
