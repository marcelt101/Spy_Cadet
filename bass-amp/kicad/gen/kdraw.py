"""Draw "human" KiCad 7 schematics: hand-placed parts, real wires, power symbols.

Workflow per board:
  s = Drawing(project, title, ...)
  b = s.block('Title', x, y, w, h)            # block frame, grid units (2.54 mm)
  b.add(part, x, y, rot=0, mirror=None)       # position relative to the block origin
  s.rails = {'GND': 'power:GND', '+15V': 'power:+15V', ...}
  s.write(path)

Signal nets are wired inside each block by an orthogonal router that refuses
any path touching another net, crossing a part body, or ending on another
net's wire. A net that leaves a block gets one net label in that block. Pins
the router cannot reach get a label (reported in the summary), so the result
is always electrically exact; build_all.py checks it against the netlist."""
import math, copy, json, os, collections, itertools, uuid
from sexp import Sym, dump, find
from libs import get_symbol, pins as sympins

U = 2.54
def uid(seed): return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))
LIBDIR_LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib', 'bassamp.kicad_sym')

# ---------------------------------------------------------------- symbols
def local_power_symbols():
    """+40V, -40V, -28V cloned from the stock +36V / -36V power symbols."""
    out = {}
    for new, base in (('+40V', '+36V'), ('-40V', '-36V'), ('-28V', '-36V')):
        s = copy.deepcopy(get_symbol('power', base))
        txt = dump(s).replace(base, new)
        from sexp import parse
        out[new] = parse(txt)[0]
    return out
_LOCAL = None
def symbol(libid):
    global _LOCAL
    lib, name = libid.split(':')
    if lib == 'bassamp':
        if _LOCAL is None: _LOCAL = local_power_symbols()
        return copy.deepcopy(_LOCAL[name])
    return get_symbol(lib, name)

def write_local_lib():
    syms = local_power_symbols()
    doc = [Sym('kicad_symbol_lib'), [Sym('version'), 20220914], [Sym('generator'), Sym('kicad_symbol_editor')]] + list(syms.values())
    os.makedirs(os.path.dirname(LIBDIR_LOCAL), exist_ok=True)
    open(LIBDIR_LOCAL, 'w').write(dump(doc) + '\n')

def body_box(sym):
    xs, ys = [], []
    def walk(e):
        if not isinstance(e, list) or not e: return
        if e[0] == 'pin': return
        if e[0] in ('xy', 'start', 'end', 'center', 'mid'):
            xs.append(float(e[1])); ys.append(float(e[2]))
        if e[0] == 'circle':
            c = find(e, 'center')[0]; r = float(find(e, 'radius')[0][1])
            xs.extend([float(c[1]) - r, float(c[1]) + r]); ys.extend([float(c[2]) - r, float(c[2]) + r])
        if e[0] == 'property': return
        for x in e[1:]: walk(x)
    for sub in find(sym, 'symbol'): walk(sub)
    if not xs: return None
    return min(xs), min(ys), max(xs), max(ys)   # library coords (mm, y up)

# ---------------------------------------------------------------- geometry
def xform(px, py, rot, mirror):
    """library (mm, y up) -> screen offset (grid units, y down). KiCad rotates, then mirrors."""
    r = math.radians(rot)
    x = px * math.cos(r) - py * math.sin(r)
    y = px * math.sin(r) + py * math.cos(r)
    if mirror == 'x': y = -y
    if mirror == 'y': x = -x
    return round(x / U * 2) / 2, round(-y / U * 2) / 2
def dirvec(angle_lib, rot, mirror):
    a = (angle_lib + rot) % 360
    if mirror == 'x': a = (360 - a) % 360
    if mirror == 'y': a = (180 - a) % 360
    return {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}[int(round(a)) % 360]

class Placed:
    def __init__(self, part, x, y, rot, mirror, block):
        self.part, self.x, self.y, self.rot, self.mirror, self.block = part, x, y, rot, mirror, block

class Block:
    def __init__(self, sheet, title, x, y, w, h, note=''):
        self.sheet, self.title, self.x, self.y, self.w, self.h, self.note = sheet, title, x, y, w, h, note
        self.items = []
        self.texts = []
    def add(self, part, x, y, rot=0, mirror=None):
        self.items.append(Placed(part, self.x + x, self.y + y, rot, mirror, self))
        return part
    def text(self, t, x, y, size=1.27):
        self.texts.append((t, self.x + x, self.y + y, size))

class Drawing:
    def __init__(self, project, title, rev='1', comments=(), paper='A2'):
        self.project, self.title, self.rev, self.comments, self.paper = project, title, rev, list(comments), paper
        self.blocks = []
        self.rails = {}
        self.root = uid('root/' + project)
        self.flags = []          # (net, x, y) PWR_FLAG positions (grid)
        self.report = []
        self.named = set()       # nets that always carry a visible label
        self.label_pins = set()  # (ref, pin) drawn with a net label instead of a wire
        self.stubs = {}          # (ref, pin) -> [(dx, dy), ...] wire path before a rail symbol
    def block(self, title, x, y, w, h, note=''):
        b = Block(self, title, x, y, w, h, note); self.blocks.append(b); return b
    def all_parts(self):
        return [p.part for b in self.blocks for p in b.items]
    def nets(self):
        n = collections.defaultdict(list)
        for p in self.all_parts():
            for pin, net in p.conn.items():
                if net is not None: n[net].append((p.ref, pin))
        return n

    # ------------------------------------------------------------ write
    def write(self, path):
        libsyms = {}
        items = []
        pinpts = []            # (x, y, net, ref) grid units
        boxes = []             # (x0, y0, x1, y1, ref) grid units
        placed_pins = collections.defaultdict(list)   # (block, net) -> [(x, y, dir)]
        allp = [p for b in self.blocks for p in b.items]
        # sanity: every pin named, no duplicate (ref, unit)
        seen = set()
        for pl in allp:
            p = pl.part
            k = (p.ref, p.unit)
            assert k not in seen, f'duplicate {k}'; seen.add(k)
            want = {x[0] for x in sympins(symbol(p.libid)) if x[2] in (0, p.unit) and x[6] != 'no_connect'}
            assert want <= set(p.conn), f'{p.ref}: missing pins {want - set(p.conn)}'
        for pl in allp:
            p = pl.part
            sym = symbol(p.libid)
            if p.libid not in libsyms:
                s2 = copy.deepcopy(sym); s2[1] = p.libid; libsyms[p.libid] = s2
            bb = body_box(sym)
            if bb:
                pts = [xform(x, y, pl.rot, pl.mirror) for x in (bb[0], bb[2]) for y in (bb[1], bb[3])]
                xs = [pl.x + a for a, _ in pts]; ys = [pl.y + b for _, b in pts]
                boxes.append((min(xs), min(ys), max(xs), max(ys), p.ref))
            for (num, name, unit, px, py, ang, ptype) in sympins(sym):
                if unit not in (0, p.unit): continue
                dx, dy = xform(px, py, pl.rot, pl.mirror)
                x, y = pl.x + dx, pl.y + dy
                net = p.conn.get(num)
                d = dirvec(ang, pl.rot, pl.mirror)
                out = (-d[0], -d[1])
                pinpts.append((x, y, net, p.ref))
                if net is not None:
                    if not any((q[0], q[1]) == (x, y) for q in placed_pins[(pl.block, net)]):
                        placed_pins[(pl.block, net)].append((x, y, out, p.ref, num))
                elif ptype != 'no_connect':
                    items.append([Sym('no_connect'), [Sym('at'), x * U, y * U], [Sym('uuid'), uid(f'{self.project}nc{p.ref}{num}')]])
            items.append(self._symbol(pl, sym))
        self.R = Router(pinpts, boxes)
        nblocks = collections.defaultdict(set)
        for (b, net) in placed_pins: nblocks[net].add(b)
        pwr_n = 0
        labels = []
        # rails -> power symbols at each pin
        for (b, net), pts in placed_pins.items():
            if net in self.rails:
                for (x, y, out, ref, num) in pts:
                    pwr_n += 1
                    if (ref, num) in self.stubs:
                        cx, cy = x, y
                        for (dx, dy) in self.stubs[(ref, num)]:
                            nx, ny = x + dx, y + dy
                            self.R.add_segment((cx, cy), (nx, ny), net)
                            out = ((nx > cx) - (nx < cx), (ny > cy) - (ny < cy))
                            cx, cy = nx, ny
                        x, y = cx, cy
                    items.append(self._power(self.rails[net], net, x, y, out, pwr_n, libsyms))
                    self.R.claim_point(x, y, net)
                    ex, ey = x + out[0] * 2.5, y + out[1] * 2.5
                    self.R.boxes.append((min(x, ex) - (1 if out[0] == 0 else 0) - 0.01 + (0.4 if out[0] > 0 else 0),
                                         min(y, ey) - (1 if out[1] == 0 else 0) - 0.01 + (0.4 if out[1] > 0 else 0),
                                         max(x, ex) + (1 if out[0] == 0 else 0) + 0.01 - (0.4 if out[0] < 0 else 0),
                                         max(y, ey) + (1 if out[1] == 0 else 0) + 0.01 - (0.4 if out[1] < 0 else 0)))
        # signal nets: route inside each block
        order = sorted(((b, net) for (b, net) in placed_pins if net not in self.rails),
                       key=lambda k: -len(placed_pins[k]))
        for (b, net) in order:
            allpts = placed_pins[(b, net)]
            lab = [q for q in allpts if (q[3], q[4]) in self.label_pins]
            pts = [q for q in allpts if (q[3], q[4]) not in self.label_pins]
            for q in lab:
                x, y, o, _ = self._label_spot(net, [q[:4]])
                labels.append(self._label_at(net, x, y, o))
            if not pts: continue
            if lab: nblocks[net] = nblocks[net] | {None}
            unrouted = self.R.route_net(net, [(x, y) for x, y, *_ in pts])
            need_label = len(nblocks[net]) > 1 or any(n == net for n, *_ in self.flags) or net in self.named
            if unrouted:
                self.report.append(f'{self.project}: {b.title[:30]}: net {net} labelled at {len(unrouted)} pin(s)')
                for (x, y) in unrouted:
                    o = next(o for (px, py, o, *_) in pts if (px, py) == (x, y))
                    labels.append(self._label_at(net, x, y, o))
                need_label = need_label or True
                # also label the routed tree once so the pieces meet
                rest = [(x, y, o) for (x, y, o, *_) in pts if (x, y) not in unrouted]
                if rest:
                    x, y, o = rest[0]; labels.append(self._label_at(net, x, y, o))
            elif need_label:
                x, y, o, _ = self._label_spot(net, [q[:4] for q in pts])
                labels.append(self._label_at(net, x, y, o))
        for (net, fx, fy) in self.flags:
            pwr_n += 1
            items.append(self._flag(net, fx, fy, pwr_n, libsyms))
            if net in self.rails:
                items.append(self._power(self.rails[net], net, fx, fy, (0, 1), 900 + pwr_n, libsyms))
            else:
                labels.append(self._label_at(net, fx, fy, (0, 1)))
        # wires and junctions (split wires wherever something of the same net tees in)
        self.R.split_tees()
        for (a, b2, net) in self.R.segments:
            items.append([Sym('wire'), [Sym('pts'), [Sym('xy'), a[0] * U, a[1] * U], [Sym('xy'), b2[0] * U, b2[1] * U]],
                          [Sym('stroke'), [Sym('width'), 0], [Sym('type'), Sym('default')]], [Sym('uuid'), uid(f'{self.project}w{a}{b2}{net}')]])
        for (x, y) in self.R.junctions():
            items.append([Sym('junction'), [Sym('at'), x * U, y * U], [Sym('diameter'), 0], [Sym('color'), 0, 0, 0, 0],
                          [Sym('uuid'), uid(f'{self.project}j{x},{y}')]])
        items += labels
        # frames and texts
        for b in self.blocks:
            items.append([Sym('rectangle'), [Sym('start'), b.x * U, b.y * U], [Sym('end'), (b.x + b.w) * U, (b.y + b.h) * U],
                          [Sym('stroke'), [Sym('width'), 0], [Sym('type'), Sym('dash')]], [Sym('fill'), [Sym('type'), Sym('none')]],
                          [Sym('uuid'), uid(self.project + b.title)]])
            items.append(self._text(b.title, b.x + 1, b.y + 1.5, 2.0, True))
            if b.note:
                for i, line in enumerate(b.note.split('\n')):
                    items.append(self._text(line, b.x + 1, b.y + b.h - 1 - (len(b.note.split('\n')) - 1 - i) * 1.2, 1.27, False))
            for (t, x, y, size) in b.texts:
                items.append(self._text(t, x, y, size, False))
        tb = [Sym('title_block'), [Sym('title'), self.title], [Sym('rev'), self.rev]]
        for i, c in enumerate(self.comments[:9]): tb.append([Sym('comment'), i + 1, c])
        doc = [Sym('kicad_sch'), [Sym('version'), 20230121], [Sym('generator'), Sym('eeschema')], [Sym('uuid'), self.root],
               [Sym('paper'), self.paper], tb, [Sym('lib_symbols')] + list(libsyms.values())] + items
        doc.append([Sym('sheet_instances'), [Sym('path'), '/', [Sym('page'), '1']]])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'w').write(dump(doc) + '\n')
        d = os.path.dirname(path)
        open(os.path.join(d, 'sym-lib-table'), 'w').write(
            '(sym_lib_table\n  (lib (name "bassamp")(type "KiCad")(uri "${KIPRJMOD}/../lib/bassamp.kicad_sym")(options "")(descr "Bass amp power symbols +40V -40V -28V"))\n)\n')
        base = os.path.splitext(path)[0]
        if not os.path.exists(base + '.kicad_pro'):
            json.dump({"meta": {"filename": os.path.basename(base) + ".kicad_pro", "version": 1},
                       "sheets": [[self.root, ""]], "text_variables": {}}, open(base + '.kicad_pro', 'w'), indent=2)
        return self.report

    # ------------------------------------------------------------ pieces
    def _text(self, t, x, y, size, bold):
        font = [Sym('font'), [Sym('size'), size, size]] + ([Sym('bold')] if bold else [])
        return [Sym('text'), t, [Sym('at'), x * U, y * U, 0], [Sym('effects'), font, [Sym('justify'), Sym('left'), Sym('bottom')]],
                [Sym('uuid'), uid(f'{self.project}t{t}{x}{y}')]]

    def _symbol(self, pl, sym):
        p = pl.part
        su = uid(f'{self.project}/{p.ref}/{p.unit}')
        at = [Sym('at'), pl.x * U, pl.y * U, pl.rot]
        body = [Sym('symbol'), [Sym('lib_id'), p.libid], at]
        if pl.mirror: body.append([Sym('mirror'), Sym(pl.mirror)])
        body += [[Sym('unit'), p.unit], [Sym('in_bom'), Sym('yes')], [Sym('on_board'), Sym('yes')],
                 [Sym('dnp'), Sym('yes') if p.dnp else Sym('no')], [Sym('uuid'), su]]
        # field placement: beside the body, horizontal text, centred
        bb = body_box(sym) or (-2, -2, 2, 2)
        pts = [xform(x, y, pl.rot, pl.mirror) for x in (bb[0], bb[2]) for y in (bb[1], bb[3])]
        x0 = min(a for a, _ in pts); x1 = max(a for a, _ in pts); y0 = min(b for _, b in pts); y1 = max(b for _, b in pts)
        horiz = (x1 - x0) > (y1 - y0) * 1.4
        pp = [xform(q[3], q[4], pl.rot, pl.mirror) for q in sympins(sym) if q[2] in (0, p.unit)]
        if len(pp) == 2:
            horiz = pp[0][1] == pp[1][1]
        is_q = p.libid.split(':')[1].startswith(('Q_', 'MPSA', 'BD1'))
        fang = pl.rot if pl.rot in (90, 270) else 0
        def prop(k, v, dx, dy, hide=False, just='left'):
            eff = [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]]]
            if just != 'center': eff.append([Sym('justify'), Sym(just)])
            if hide: eff.append(Sym('hide'))
            return [Sym('property'), k, v, [Sym('at'), (pl.x + dx) * U, (pl.y + dy) * U, fang], eff]
        conn_like = p.libid.startswith('Connector_Generic')
        if is_q:
            if pl.mirror == 'y' or pl.rot == 180:
                fx, just = x0 - 0.5, 'right'
            else:
                fx, just = x1 + 0.5, 'left'
            r1, r2 = (fx, -0.5), (fx, 0.5)
        elif horiz:
            r1, r2, just = ((x0 + x1) / 2, y0 - 1.6), ((x0 + x1) / 2, y1 + 1.6), 'center'
        else:
            r1, r2, just = (x1 + 0.8, -0.5), (x1 + 0.8, 0.5), 'left'
            if conn_like:
                r1, r2, just = ((x0 + x1) / 2, y0 - 1.0), ((x0 + x1) / 2, y1 + 1.0), 'center'
            if p.libid.startswith('Relay:'):
                r1, r2, just = (x1 + 1, y0 - 1.0), (x1 + 1, y0 - 2.0), 'left'
            if p.libid.startswith('Amplifier_'):
                r1, r2, just = (x1 + 1.5, y1 + 0.3), (x1 + 1.5, y1 + 1.3), 'left'
        # KiCad mirrors justification for rotated/mirrored symbols; keep text centred there to stay predictable
        if pl.rot in (90, 180, 270) or pl.mirror:
            if just != 'center':
                w = max(len(p.ref), len(p.value)) * 0.45
                r1 = (r1[0] + (w if just == 'left' else -w), r1[1]); r2 = (r2[0] + (w if just == 'left' else -w), r2[1])
                just = 'center'
        body.append(prop('Reference', p.ref, r1[0], r1[1], just=just))
        body.append(prop('Value', p.value, r2[0], r2[1], just=just))
        body.append(prop('Footprint', p.fp, 0, 0, hide=True))
        body.append(prop('Datasheet', '~', 0, 0, hide=True))
        for k, v in (p.fields or {}).items():
            body.append(prop(k, v, 0, 0, hide=True))
        for pin in sympins(sym):
            if pin[2] in (0, p.unit):
                body.append([Sym('pin'), pin[0], [Sym('uuid'), uid(su + '/pin/' + pin[0])]])
        body.append([Sym('instances'), [Sym('project'), self.project, [Sym('path'), '/' + self.root, [Sym('reference'), p.ref], [Sym('unit'), p.unit]]]])
        return body

    def _power(self, libid, net, x, y, out, n, libsyms):
        sym = symbol(libid)
        if libid not in libsyms:
            s2 = copy.deepcopy(sym); s2[1] = libid; libsyms[libid] = s2
        ang = sympins(sym)[0][5]          # direction from connection point into the symbol body
        body_dir = {90: (0, -1), 270: (0, 1)}[int(ang)]
        # rotate so the body points along 'out'
        rot = None
        for r in (0, 90, 180, 270):
            if dirvec(ang, r, None) == out: rot = r
        su = uid(f'{self.project}/pwr/{n}/{net}/{x}/{y}')
        ref = f'#PWR{n:03d}'
        name = libid.split(':')[1]
        if out[1] == -1: tx, ty = x, y - 1.6
        elif out[1] == 1: tx, ty = x, y + (2.3 if 'GND' in name else 2.2)
        else: tx, ty = x + out[0] * (2.6 + 0.32 * len(name)), y
        return [Sym('symbol'), [Sym('lib_id'), libid], [Sym('at'), x * U, y * U, rot], [Sym('unit'), 1],
                [Sym('in_bom'), Sym('yes')], [Sym('on_board'), Sym('yes')], [Sym('dnp'), Sym('no')], [Sym('uuid'), su],
                [Sym('property'), 'Reference', ref, [Sym('at'), x * U, y * U, 0], [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]], Sym('hide')]],
                [Sym('property'), 'Value', libid.split(':')[1], [Sym('at'), tx * U, ty * U, rot if rot in (90, 270) else 0], [Sym('effects'), [Sym('font'), [Sym('size'), 1.0, 1.0]]]],
                [Sym('property'), 'Footprint', '', [Sym('at'), x * U, y * U, 0], [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]], Sym('hide')]],
                [Sym('property'), 'Datasheet', '', [Sym('at'), x * U, y * U, 0], [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]], Sym('hide')]],
                [Sym('pin'), '1', [Sym('uuid'), uid(su + 'p')]],
                [Sym('instances'), [Sym('project'), self.project, [Sym('path'), '/' + self.root, [Sym('reference'), ref], [Sym('unit'), 1]]]]]

    def _flag(self, net, x, y, n, libsyms):
        libid = 'power:PWR_FLAG'
        sym = symbol(libid)
        if libid not in libsyms:
            s2 = copy.deepcopy(sym); s2[1] = libid; libsyms[libid] = s2
        su = uid(f'{self.project}/flag/{net}')
        ref = f'#FLG{n:02d}'
        return [Sym('symbol'), [Sym('lib_id'), libid], [Sym('at'), x * U, y * U, 0], [Sym('unit'), 1],
                [Sym('in_bom'), Sym('yes')], [Sym('on_board'), Sym('yes')], [Sym('dnp'), Sym('no')], [Sym('uuid'), su],
                [Sym('property'), 'Reference', ref, [Sym('at'), x * U, (y - 3) * U, 0], [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]], Sym('hide')]],
                [Sym('property'), 'Value', 'PWR_FLAG', [Sym('at'), x * U, (y - 3.5) * U, 0], [Sym('effects'), [Sym('font'), [Sym('size'), 1.0, 1.0]]]],
                [Sym('property'), 'Footprint', '', [Sym('at'), x * U, y * U, 0], [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]], Sym('hide')]],
                [Sym('property'), 'Datasheet', '', [Sym('at'), x * U, y * U, 0], [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]], Sym('hide')]],
                [Sym('pin'), '1', [Sym('uuid'), uid(su + 'p')]],
                [Sym('instances'), [Sym('project'), self.project, [Sym('path'), '/' + self.root, [Sym('reference'), ref], [Sym('unit'), 1]]]]]

    def _label_spot(self, net, pts):
        """Prefer a pin whose outward stub of 2 units is free; return (x, y, out, ref) for the label."""
        for (x, y, o, r) in pts:
            for L in (2, 1):
                ex, ey = x + o[0] * L, y + o[1] * L
                own = set()
                for sg in self.R.segments:
                    if sg[2] == net: own.update(self.R._cells(sg[0], sg[1]))
                if any(c in own for c in self.R._cells((x, y), (ex, ey))[1:]): continue
                if self.R.free_segment((x, y), (ex, ey), net):
                    self.R.add_segment((x, y), (ex, ey), net)
                    return ex, ey, o, r
        x, y, o, r = pts[0]
        return x, y, o, r

    def _label_at(self, net, x, y, o):
        ang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[o]
        just = 'right' if ang == 180 else 'left'
        return [Sym('label'), net, [Sym('at'), x * U, y * U, ang], [Sym('fields_autoplaced')],
                [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]], [Sym('justify'), Sym(just), Sym('bottom')]],
                [Sym('uuid'), uid(f'{self.project}l{net}{x}{y}')]]


class Router:
    def __init__(self, pinpts, boxes):
        self.pins = collections.defaultdict(set)      # (x,y) -> nets ('' for no-connect pins)
        for (x, y, net, ref) in pinpts:
            self.pins[(x, y)].add(net if net is not None else '#nc')
        self.boxes = [(x0 + 0.05, y0 + 0.05, x1 - 0.05, y1 - 0.05) for (x0, y0, x1, y1, r) in boxes]
        self.segments = []          # ((x,y),(x,y),net)
        self.claimed = {}           # extra points owned by a net (power symbol anchors)

    def claim_point(self, x, y, net): self.claimed[(x, y)] = net

    @staticmethod
    def _cells(a, b):
        (x1, y1), (x2, y2) = a, b
        if x1 == x2:
            s = 1 if y2 >= y1 else -1
            n = int(round(abs(y2 - y1) * 2))
            return [(x1, y1 + s * i / 2) for i in range(n + 1)]
        s = 1 if x2 >= x1 else -1
        n = int(round(abs(x2 - x1) * 2))
        return [(x1 + s * i / 2, y1) for i in range(n + 1)]

    def _on_seg(self, p, seg):
        (x1, y1), (x2, y2), _ = seg
        if x1 == x2 == p[0]: return min(y1, y2) <= p[1] <= max(y1, y2)
        if y1 == y2 == p[1]: return min(x1, x2) <= p[0] <= max(x1, x2)
        return False

    def free_segment(self, a, b, net):
        if a == b: return True
        cells = self._cells(a, b)
        for i, c in enumerate(cells):
            nets = self.pins.get(c)
            if nets and (nets - {net}): return False
            if c in self.claimed and self.claimed[c] != net: return False
            if 0 < i < len(cells) - 1:
                # passing over a same-net pin is fine (it connects); passing over a body is not
                pass
        # bodies (allow the very ends: pins sit on body edges for some symbols)
        for (x0, y0, x1, y1) in self.boxes:
            for c in cells[1:-1] if len(cells) > 2 else []:
                if x0 < c[0] < x1 and y0 < c[1] < y1: return False
            # segment fully crossing a box without a grid cell inside (thin bodies)
            if a[0] == b[0] and x0 < a[0] < x1 and min(a[1], b[1]) < y0 and max(a[1], b[1]) > y1: return False
            if a[1] == b[1] and y0 < a[1] < y1 and min(a[0], b[0]) < x0 and max(a[0], b[0]) > x1: return False
        horiz = a[1] == b[1]
        for seg in self.segments:
            if seg[2] == net: continue
            s_h = seg[0][1] == seg[1][1]
            # our endpoints must not lie on foreign wires, and theirs not on ours
            if self._on_seg(a, seg) or self._on_seg(b, seg): return False
            if self._on_seg(seg[0], (a, b, net)) or self._on_seg(seg[1], (a, b, net)): return False
            # collinear overlap
            if horiz == s_h:
                if horiz and seg[0][1] == a[1]:
                    lo, hi = sorted((a[0], b[0])); slo, shi = sorted((seg[0][0], seg[1][0]))
                    if max(lo, slo) <= min(hi, shi): return False
                if not horiz and seg[0][0] == a[0]:
                    lo, hi = sorted((a[1], b[1])); slo, shi = sorted((seg[0][1], seg[1][1]))
                    if max(lo, slo) <= min(hi, shi): return False
        return True

    def add_segment(self, a, b, net):
        if a != b: self.segments.append((a, b, net))

    def _tree_points(self, net, tree_pins):
        pts = set(tree_pins)
        for seg in self.segments[self._start:]:
            if seg[2] == net:
                pts.update(self._cells(seg[0], seg[1]))
        return pts

    def _try(self, p, targets, net):
        """Return the best list of segments from p to one of the targets, or None."""
        best = None
        tl = sorted(targets, key=lambda t: abs(t[0] - p[0]) + abs(t[1] - p[1]))[:40]
        for t in tl:
            cands = []
            if p[0] == t[0] or p[1] == t[1]:
                cands.append([p, t])
            cands.append([p, (t[0], p[1]), t])
            cands.append([p, (p[0], t[1]), t])
            for k in range(1, 12):
                for s in (k, -k):
                    xm = (p[0] + t[0]) / 2 + s * 0.5
                    xm = round(xm * 2) / 2
                    cands.append([p, (xm, p[1]), (xm, t[1]), t])
                    ym = round(((p[1] + t[1]) / 2 + s * 0.5) * 2) / 2
                    cands.append([p, (p[0], ym), (t[0], ym), t])
            for c in cands:
                c = [c[0]] + [q for i, q in enumerate(c[1:], 1) if q != c[i - 1]]
                segs = list(zip(c, c[1:]))
                if any(a[0] != b[0] and a[1] != b[1] for a, b in segs): continue
                if not all(self.free_segment(a, b, net) for a, b in segs): continue
                # a bend point must not sit on another net's pin (checked) - and bends on same-net wire are ok
                length = sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in segs)
                score = length + 3 * (len(segs) - 1)
                if best is None or score < best[0]:
                    best = (score, segs)
            if best and best[0] < abs(t[0] - p[0]) + abs(t[1] - p[1]) + 3.5:
                break
        return best[1] if best else None

    def route_net(self, net, pts):
        pts = list(dict.fromkeys(pts))
        self._start = len(self.segments)
        if len(pts) < 2: return []
        # start from the left-most pin
        pts.sort()
        tree = [pts[0]]
        todo = pts[1:]
        failed = []
        while todo:
            tp = self._tree_points(net, tree)
            todo.sort(key=lambda p: min(abs(p[0] - t[0]) + abs(p[1] - t[1]) for t in tp))
            p = todo.pop(0)
            if p in tp:
                tree.append(p); continue
            segs = self._try(p, tp, net)
            if segs is None:
                failed.append(p)
                continue
            for a, b in segs: self.add_segment(a, b, net)
            tree.append(p)
        if failed:
            failed.append(None)
        return [f for f in failed if f is not None]

    def split_tees(self):
        changed = True
        while changed:
            changed = False
            pts = collections.defaultdict(set)
            for (a, b, net) in self.segments:
                pts[net].add(a); pts[net].add(b)
            for pt, nets in self.pins.items():
                for n in nets: pts[n].add(pt)
            for pt, n in self.claimed.items(): pts[n].add(pt)
            out = []
            for (a, b, net) in self.segments:
                inner = [c for c in self._cells(a, b)[1:-1] if c in pts[net]]
                if inner:
                    changed = True
                    chain = [a] + inner + [b]
                    out += [(p, q, net) for p, q in zip(chain, chain[1:])]
                else:
                    out.append((a, b, net))
            self.segments = out

    def junctions(self):
        deg = collections.Counter()
        nets_at = collections.defaultdict(set)
        for (a, b, net) in self.segments:
            for c in self._cells(a, b):
                nets_at[c].add(net)
            deg[(a, net)] += 1; deg[(b, net)] += 1
            for c in self._cells(a, b)[1:-1]:
                deg[(c, net)] += 2
        for (pt, nets) in self.pins.items():
            for n in nets:
                if (pt, n) in deg: deg[(pt, n)] += 1
        for (pt, n) in self.claimed.items():
            if (pt, n) in deg: deg[(pt, n)] += 1
        return sorted({pt for (pt, n), d in deg.items() if d >= 3})
