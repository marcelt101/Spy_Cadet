import copy, os
from sexp import parse, find, Sym
LIBDIR='/usr/share/kicad/symbols'
_cache={}
def lib(name):
    if name not in _cache:
        _cache[name]=parse(open(os.path.join(LIBDIR,name+'.kicad_sym')).read())[0]
    return _cache[name]
def get_symbol(libname, symname):
    """Return a flattened copy of the symbol (resolves 'extends')."""
    L=lib(libname)
    syms={s[1]:s for s in find(L,'symbol')}
    s=copy.deepcopy(syms[symname])
    ext=find(s,'extends')
    if ext:
        parent=copy.deepcopy(get_symbol(libname, ext[0][1]))
        # keep child's properties, parent's graphics/pins
        props={p[1]:p for p in find(s,'property')}
        out=[Sym('symbol'), symname]
        for e in parent[2:]:
            if isinstance(e,list) and e[0]=='property' and e[1] in props:
                out.append(props.pop(e[1]))
            elif isinstance(e,list) and e[0]=='symbol':
                sub=copy.deepcopy(e); sub[1]=sub[1].replace(ext[0][1]+'_',symname+'_',1); out.append(sub)
            else:
                out.append(e)
        for p in props.values(): out.insert(2,p)
        s=out
    return s
def pins(sym):
    """[(number,name,unit,x,y,angle,type)] for all units (unit 0 = common)."""
    res=[]
    for sub in find(sym,'symbol'):
        unit=int(sub[1].rsplit('_',2)[-2])
        for p in find(sub,'pin'):
            at=find(p,'at')[0]; num=find(p,'number')[0][1]; name=find(p,'name')[0][1]
            res.append((num,name,unit,float(at[1]),float(at[2]),float(at[3]) if len(at)>3 else 0.0,str(p[1])))
    return res
if __name__=='__main__':
    import sys
    for spec in sys.argv[1:]:
        l,s=spec.split(':'); sym=get_symbol(l,s)
        fp=[p[2] for p in find(sym,'property') if p[1]=='Footprint']
        print(spec, 'fp=',fp, sorted(pins(sym),key=lambda t:(t[2],t[0])))
