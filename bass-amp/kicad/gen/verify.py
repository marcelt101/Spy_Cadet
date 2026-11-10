"""Check a KiCad-exported netlist against the generator's intended netlist,
and (for the HVOA module) against the SPICE subcircuit in sim/hvoa.sub."""
import subprocess, sys, os, re, collections
from sexp import parse, find

def kicad_nets(sch):
    out = '/tmp/claude-0/verify.net'
    r = subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '-o', out, sch], capture_output=True, text=True)
    if r.returncode: raise SystemExit(f'kicad-cli failed on {sch}: {r.stdout}{r.stderr}')
    doc = parse(open(out).read())[0]
    nets = {}
    for n in find(find(doc, 'nets')[0], 'net'):
        name = find(n, 'name')[0][1].lstrip('/')
        nodes = frozenset((find(x, 'ref')[0][1], find(x, 'pin')[0][1]) for x in find(n, 'node'))
        nets[name] = nodes
    comps = {find(c, 'ref')[0][1]: (find(c, 'value')[0][1], (find(c, 'footprint') or [[0, '']])[0][1]) for c in find(find(doc, 'components')[0], 'comp')}
    return nets, comps

def check_against_sheet(sheet, sch):
    nets, comps = kicad_nets(sch)
    want = {}
    for net, members in sheet.nets().items():
        want[net] = frozenset(m for m in members if not m[0].startswith('#'))
    got = {k: frozenset(m for m in v if not m[0].startswith('#')) for k, v in nets.items()}
    got = {k: v for k, v in got.items() if v}
    # unconnected pins come out as single-node nets named unconnected-...
    got_conn = {k: v for k, v in got.items() if not k.startswith('unconnected-')}
    errs = []
    if set(got_conn.values()) != set(want.values()):
        missing = [k for k, v in want.items() if v not in set(got_conn.values())]
        extra = [k for k, v in got_conn.items() if v not in set(want.values())]
        errs.append(f'net mismatch: missing {missing[:10]} extra {extra[:10]}')
    for p in sheet.all_parts():
        if p.ref not in comps: errs.append(f'{p.ref} missing from netlist')
        elif not comps[p.ref][1]: errs.append(f'{p.ref} has no footprint')
    nfp = set(c[1] for c in comps.values())
    for fp in nfp:
        lib, name = fp.split(':')
        if not os.path.exists(f'/usr/share/kicad/footprints/{lib}.pretty/{name}.kicad_mod'):
            errs.append(f'footprint not in library: {fp}')
    print(f'{os.path.basename(sch)}: {len(comps)} parts, {len(want)} nets ->', 'OK' if not errs else 'FAIL')
    for e in errs: print('   ', e)
    return not errs

def spice_partition(path):
    role = {'Q': ['C', 'B', 'E'], 'D': ['A', 'K'], 'R': ['1', '2'], 'C': ['1', '2']}
    nets = collections.defaultdict(set)
    for line in open(path):
        t = line.split()
        if not t or t[0][0] not in 'QDRC' or line.startswith('*'): continue
        ref = t[0]; kind = ref[0]
        for r, n in zip(role[kind], t[1:1 + len(role[kind])]):
            nets[n].add((ref, r))
    return nets

def check_hvoa(sch, spice):
    nets, comps = kicad_nets(sch)
    pinrole = {'1': 'E', '2': 'B', '3': 'C'}   # all module transistors are E-B-C TO-92
    k = collections.defaultdict(set)
    rename = {'CC1': 'CC'}
    for name, nodes in nets.items():
        for ref, pin in nodes:
            if ref.startswith('#') or ref in ('J1', 'R1', 'R2', 'C1', 'C2', 'C3', 'C4'): continue
            r = rename.get(ref, ref)
            if r[0] == 'Q': role = pinrole[pin]
            elif r[0] == 'D': role = {'1': 'K', '2': 'A'}[pin]
            else: role = None
            k[name].add((r, role))
    s = spice_partition(spice)
    # resistors/caps: pin order irrelevant -> compare as unordered
    def canon(part):
        out = set()
        for net in part.values():
            out.add(frozenset((r, (role if r[0] in 'QD' else '*')) for r, role in net))
        return out
    a, b = canon(k), canon(s)
    a = {n for n in a if n}
    ok = a == b
    print('HVOA KiCad vs SPICE topology:', 'IDENTICAL' if ok else 'DIFFERENT')
    if not ok:
        for n in a - b: print('  only in KiCad:', sorted(n))
        for n in b - a: print('  only in SPICE:', sorted(n))
    return ok
