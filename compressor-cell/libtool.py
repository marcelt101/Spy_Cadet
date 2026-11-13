import re, os
LIBDIR="/usr/share/kicad/symbols"
def blocks(text,start):
    """return balanced (...) block starting at index start"""
    d=0
    for i in range(start,len(text)):
        if text[i]=='(': d+=1
        elif text[i]==')':
            d-=1
            if d==0: return text[start:i+1]
_cache={}
def libtext(lib):
    if lib not in _cache: _cache[lib]=open(f"{LIBDIR}/{lib}.kicad_sym").read()
    return _cache[lib]
def raw_symbol(lib,name):
    t=libtext(lib); m=re.search(r'\n\s*\(symbol "%s"'%re.escape(name),t)
    if not m: raise KeyError(f"{lib}:{name}")
    return blocks(t,t.index('(',m.start()))
def flat_symbol(lib,name):
    """flattened symbol text named 'lib:name' (resolves extends)"""
    s=raw_symbol(lib,name)
    m=re.search(r'\(extends "([^"]+)"\)',s)
    if m:
        base=raw_symbol(lib,m.group(1))
        # properties from derived, units from base (renamed)
        props=re.findall(r'\(property "[^"]*".*?\n\s*\)\s*(?=\n\s*\((?:property|symbol|extends)|\n\s*\)$)',s,re.S)
        # simpler: take everything of base, then replace its properties with derived's
        units=[]; i=0
        for mm in re.finditer(r'\n\s*\(symbol "%s_(\d+)_(\d+)"'%re.escape(m.group(1)),base):
            u=blocks(base,base.index('(',mm.start()))
            units.append(u.replace(f'(symbol "{m.group(1)}_',f'(symbol "{name}_',1))
        head=base[:base.index('(property')]
        head=head.replace(f'(symbol "{m.group(1)}"',f'(symbol "{name}"',1)
        dprops=[]
        for mm in re.finditer(r'\(property "',s):
            dprops.append(blocks(s,mm.start()))
        s=head+"\n".join(dprops)+"\n"+"\n".join(units)+"\n)"
    s=s.replace(f'(symbol "{name}"',f'(symbol "{lib}:{name}"',1)
    return s
def pins(lib,name):
    """{unit: [(number,name,type,x,y,angle)]} ; unit 0 = all units"""
    s=raw_symbol(lib,name); m=re.search(r'\(extends "([^"]+)"\)',s)
    base=raw_symbol(lib,m.group(1)) if m else s; bname=m.group(1) if m else name
    out={}
    for mm in re.finditer(r'\(symbol "%s_(\d+)_(\d+)"'%re.escape(bname),base):
        u=int(mm.group(1)); blk=blocks(base,mm.start())
        if mm.group(2)=="2": continue
        for p in re.finditer(r'\(pin (\w+) \w+\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\).*?\(name "([^"]*)".*?\(number "([^"]*)"',blk,re.S):
            out.setdefault(u,[]).append((p.group(6),p.group(5),p.group(1),float(p.group(2)),float(p.group(3)),float(p.group(4))))
    return out
if __name__=="__main__":
    import sys
    for spec in sys.argv[1:]:
        lib,name=spec.split(":")
        P=pins(lib,name); print(spec, {u:[(n,nm,t) for n,nm,t,*_ in v] for u,v in P.items()})
