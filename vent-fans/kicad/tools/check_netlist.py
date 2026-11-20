#!/usr/bin/env python3
"""Export the schematic netlist with kicad-cli and verify it against PARTS."""
import re, subprocess, sys, os, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import gen_schematic as g
net_file = os.path.join(tempfile.gettempdir(), "vent_fans.net")
subprocess.run(["kicad-cli", "sch", "export", "netlist", "-o", net_file,
                os.path.join(g.PROJ, "vent_fans.kicad_sch")], check=True, capture_output=True)
nets = {}
for blk in open(net_file).read().split("(net (code")[1:]:
    name = re.search(r'\(name "([^"]*)"\)', blk).group(1).lstrip("/")
    nets[name] = set(re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', blk))
want = {}
for ref, (lib, val, fp, pos, rot, pn, desc) in g.PARTS.items():
    for p, n in pn.items():
        want.setdefault(n, set()).add((ref, str(p)))
bad = 0
for n, nodes in sorted(want.items()):
    if nets.get(n) != nodes:
        bad += 1; print(f"MISMATCH {n}: want {sorted(nodes)} got {sorted(nets.get(n, []))}")
    else:
        print(f"ok  {n:8s} {len(nodes)} pins")
extra = [n for n in nets if n not in want and not n.startswith("unconnected")]
if extra: bad += 1; print("unexpected nets:", extra)
print("NETLIST OK" if not bad else f"{bad} PROBLEM(S)"); sys.exit(1 if bad else 0)
