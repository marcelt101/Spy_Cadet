"""Minimal S-expression reader/writer for KiCad files."""
import re
class Sym(str):
    pass
_tok = re.compile(r'\s*(\(|\)|"(?:\\.|[^"\\])*"|[^\s()"]+)', re.S)
def parse(text):
    stack=[[]]
    for m in _tok.finditer(text):
        t=m.group(1)
        if t=='(':
            stack.append([])
        elif t==')':
            x=stack.pop(); stack[-1].append(x)
        elif t.startswith('"'):
            stack[-1].append(t[1:-1].replace('\\"','"').replace('\\\\','\\'))
        else:
            stack[-1].append(Sym(t))
    return stack[0]
def q(s):
    return '"'+str(s).replace('\\','\\\\').replace('"','\\"')+'"'
def dump(x, ind=0):
    """Serialise, preserving element order (KiCad's parser is order-sensitive)."""
    if isinstance(x,list):
        if not x: return '()'
        if all(not isinstance(e,list) for e in x):
            return '('+' '.join(dump(e) for e in x)+')'
        i=0
        while i<len(x) and not isinstance(x[i],list): i+=1
        s='('+' '.join(dump(e) for e in x[:i])
        for e in x[i:]:
            s+='\n'+'  '*(ind+1)+dump(e,ind+1)
        return s+'\n'+'  '*ind+')'
    if isinstance(x,Sym): return str(x)
    if isinstance(x,bool): return 'yes' if x else 'no'
    if isinstance(x,float):
        return ('%.4f'%x).rstrip('0').rstrip('.')
    if isinstance(x,int): return str(x)
    return q(x)
def find(x,key):
    return [e for e in x if isinstance(e,list) and e and e[0]==key]
