import subprocess, numpy as np, re, itertools, sys
base=open('t_eq.cir').read()
def resp(RI,RL,RG,POT,cs,cg,pm=0.0,pb=0.5,pt=0.5,out='o2'):
    t=base
    t=re.sub(r"^RI O1 P2 .*$",f"RI O1 P2 {RI}",t,flags=re.M)
    t=re.sub(r"^RFB O2 M2 .*$",f"RFB O2 M2 {RI}",t,flags=re.M)
    t=re.sub(r"^RLY GO X .*$",f"RLY GO X {RL}",t,flags=re.M)
    t=re.sub(r"^RGY GP 0 .*$",f"RGY GP 0 {RG}",t,flags=re.M)
    t=t.replace("{10k*(1-pm)+1}",f"{{{POT}*(1-pm)+1}}").replace("{10k*pm+1}",f"{{{POT}*pm+1}}")
    t=re.sub(r"^\.param pb=.*$",f".param pb={pb} pt={pt} pm={pm} cs={cs} cg={cg}",t,flags=re.M)
    t=t[:t.index(".control")]+f".control\nac dec 200 10 40k\nwrdata eq.dat v({out})\n.endc\n.end\n"
    open('tmp_mid.cir','w').write(t); subprocess.run(['ngspice','-b','tmp_mid.cir'],capture_output=True)
    d=np.loadtxt('eq.dat'); return d[:,0], 20*np.log10(np.hypot(d[:,1],d[:,2]))
def pk(*a):
    f,g=resp(*a); i=np.argmax(g); half=g[i]/2
    lo=f[:i][g[:i]<half][-1]; hi=f[i:][g[i:]<half][0]
    return g[i], f[i], f[i]/(hi-lo)
if __name__=="__main__":
    for RL in ['560','680','820']:
        print(RL, ["%.1fdB %.0fHz Q%.2f"%pk('3.3k',RL,'100k','10k','150n','22n')])
