import re, sys, io, contextlib, importlib.util
# expected = verified v2 netlist (../kicad/gen.py) + deliberate drawing changes
spec=importlib.util.spec_from_file_location("g","../kicad/gen.py"); g=importlib.util.module_from_spec(spec)
import os, tempfile
_cwd=os.getcwd(); _gen=os.path.abspath("../kicad/gen.py"); _t=tempfile.mkdtemp(); os.chdir(_t)
spec=importlib.util.spec_from_file_location("g",_gen); g=importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()): spec.loader.exec_module(g)
os.chdir(_cwd)
exp={}
for p in g.parts:
    if p['ref'].startswith('#'): continue
    for u,mp in p['units'].items():
        for pin,net in mp.items(): exp[(p['ref'],pin)]=net
# deliberate changes: connector pin orders, NAND input swap (equivalent)
exp[("J1","1")]="-15V"; exp[("J1","3")]="+15V"
exp[("J2","1")]="GND"; exp[("J2","2")]="AUD_IN"
exp[("U12","9")]="+5V"; exp[("U12","10")]="GATE_N"
for k in [k for k in exp if k[0] in ("JP2","RB2","RB1")]: del exp[k]
exp.update({("RB1","1"):"VB_DRIVE",("RB1","2"):"CB",
 ("U16","3"):"CB",("U16","2"):"BSENSE",("U16","1"):"BSENSE",("U16","5"):"CR",("U16","6"):"RSENSE",("U16","7"):"RSENSE",("U16","8"):"+15V",("U16","4"):"-15V",
 ("U17","3"):"BSENSE",("U17","2"):"RSENSE",("U17","5"):"GND",("U17","6"):"ERR",("U17","7"):"+15V",("U17","4"):"-15V",
 ("C41","1"):"ERR",("C41","2"):"HPX",("R34","1"):"HPX",("R34","2"):"ERRHP",("R33","1"):"ERRHP",("R33","2"):"GND",
 ("U18","3"):"ERRHP",("U18","2"):"GND",("U18","5"):"VB",("U18","6"):"VB_DRIVE",("U18","7"):"+15V",("U18","4"):"-15V",
 ("RV5","1"):"VB",("RV5","2"):"REPR",("RV5","3"):"REPR",("R35","1"):"REPR",("R35","2"):"CR",
 ("D3","1"):"CR",("D3","2"):"GND",("D4","1"):"CR",("D4","2"):"GND",("TP10","1"):"VB_DRIVE",("TP11","1"):"ERR",
 ("C42","1"):"+15V",("C42","2"):"GND",("C43","1"):"-15V",("C43","2"):"GND",("C44","1"):"+15V",("C44","2"):"GND",("C45","1"):"-15V",("C45","2"):"GND",("C46","1"):"+15V",("C46","2"):"GND",("C47","1"):"-15V",("C47","2"):"GND"})
t=open(sys.argv[1]).read()
got={}; names={}
for m in re.finditer(r'\(net \(code "?(\d+)"?\) \(name "([^"]*)"\)(.*?)(?=\(net \(code|\Z)',t,re.S):
    nodes=re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)',m.group(3))
    for r,pn in nodes:
        if not r.startswith('#'): got[(r,pn)]=m.group(2)
# compare partitions
from collections import defaultdict
E=defaultdict(set); G=defaultdict(set)
for k,v in exp.items(): E[v].add(k)
for k,v in got.items():
    if k in exp: G[v].add(k)
bad=0
for en,s in E.items():
    gn={got.get(k) for k in s}
    if len(gn)!=1: bad+=1; print("SPLIT  expected net",en,"->",sorted(gn,key=str))
    else:
        gname=gn.pop()
        if G[gname]!=s: bad+=1; print("MERGED expected",en,"with",sorted(G[gname]-s)[:6],"in",gname)
missing=[k for k in exp if k not in got]
extra=[k for k in got if k not in exp and not got[k].startswith('unconnected')]
print(f"expected nets {len(E)}, mismatched {bad}, missing pins {missing[:8]}, unexpected pins {extra[:8]}")
uncon=sorted(k for k,v in got.items() if v.startswith('unconnected'))
print("unconnected (should be only NC pins):",uncon)
print("net names:",sorted(n for n in G if not n.startswith('unconnected') and not n.startswith('Net-')))
