"""Generate KiCad 7 schematics (.kicad_sch) from a netlist description.

Every pin is tied to its net with a local net label placed exactly on the pin
end, so the netlist is unambiguous and passes ERC. Parts are grouped into
titled blocks on a grid. It reads like a "net-label" schematic: correct, but you
may want to tidy the drawing in KiCad.
"""
import uuid, json, os, math, copy, collections
from sexp import Sym, dump, find
from libs import get_symbol, pins as sympins

G = 2.54
def snap(v): return round(v / 1.27) * 1.27
def uid(seed):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))

class Part:
    def __init__(self, ref, libid, value, footprint, conn, unit=1, fields=None, dnp=False):
        self.ref, self.libid, self.value, self.fp = ref, libid, value, footprint
        self.conn = {str(k): v for k, v in conn.items()}   # pin number -> net name (None = no-connect)
        self.unit = unit
        self.fields = fields or {}
        self.dnp = dnp

class Sheet:
    def __init__(self, project, title, rev='1', company='', comments=()):
        self.project, self.title, self.rev, self.company = project, title, rev, company
        self.comments = list(comments)
        self.blocks = []          # (title, [parts], note)
        self.flags = []           # nets that get a PWR_FLAG
        self.root = uid('root/' + project)

    def block(self, title, note=''):
        b = (title, [], note)
        self.blocks.append(b)
        return b[1]

    # ------------------------------------------------------------------
    def all_parts(self):
        return [p for _, ps, _ in self.blocks for p in ps]

    def nets(self):
        n = collections.defaultdict(list)
        for p in self.all_parts():
            for pin, net in p.conn.items():
                if net is not None:
                    n[net].append((p.ref, pin))
        for f in self.flags:
            n[f].append(('#FLG', '1'))
        return n

    def check(self):
        errs = []
        # every pin of every placed unit must be mentioned
        for p in self.all_parts():
            lib, name = p.libid.split(':')
            sp = [x for x in sympins(get_symbol(lib, name)) if x[2] in (0, p.unit)]
            have = set(p.conn)
            want = set(x[0] for x in sp)
            if have != want:
                errs.append(f'{p.ref} unit {p.unit}: pins given {sorted(have)} expected {sorted(want)}')
        for net, members in self.nets().items():
            if len(members) < 2:
                errs.append(f'net {net} has a single connection {members}')
        refs = collections.Counter((p.ref, p.unit) for p in self.all_parts())
        for k, v in refs.items():
            if v > 1: errs.append(f'duplicate {k}')
        if errs:
            raise SystemExit('\n'.join(errs))

    # ------------------------------------------------------------------
    def write(self, path, cols=6, cellw=14 * G, cellh=11 * G, blockcols=2):
        self.check()
        libsyms = {}
        items = []
        texts = []
        # --- layout -------------------------------------------------------
        x0, y0 = 20 * G, 20 * G
        colx = [x0, x0]
        blockw = cols * cellw + 4 * G
        # simple 2-column masonry of blocks
        heights = [y0] * blockcols
        placed = []
        for bi, (title, parts, note) in enumerate(self.blocks):
            k = heights.index(min(heights))
            bx = x0 + k * (blockw + 6 * G)
            by = heights[k]
            nrows = math.ceil(len(parts) / cols) if parts else 0
            bh = 6 * G + nrows * cellh + (3 * G if note else 0)
            placed.append((bx, by, blockw, bh, title, parts, note))
            heights[k] = by + bh + 4 * G
        width = x0 + blockcols * (blockw + 6 * G) + 10 * G
        height = max(heights) + 10 * G
        paper = None
        for name, w, h in (('A3', 420, 297), ('A2', 594, 420), ('A1', 841, 594), ('A0', 1189, 841)):
            if width <= w and height <= h:
                paper = name; break
        if paper is None:
            paper = ('User', math.ceil(width / 10) * 10, math.ceil(height / 10) * 10)

        for (bx, by, bw, bh, title, parts, note) in placed:
            items.append([Sym('rectangle'), [Sym('start'), bx, by], [Sym('end'), bx + bw, by + bh],
                          [Sym('stroke'), [Sym('width'), 0], [Sym('type'), Sym('dash')]],
                          [Sym('fill'), [Sym('type'), Sym('none')]], [Sym('uuid'), uid(self.project + title + 'rect')]])
            texts.append((title, bx + 2 * G, by + 2.5 * G, 2.0, True))
            if note:
                texts.append((note, bx + 2 * G, by + bh - 1.5 * G, 1.27, False))
            for i, p in enumerate(parts):
                cx = bx + 4 * G + (i % cols) * cellw + cellw / 2 - 2 * G
                cy = by + 6 * G + (i // cols) * cellh + cellh / 2
                cx, cy = snap(cx), snap(cy)
                self._place(p, cx, cy, items, libsyms)
        # PWR_FLAGs in a strip under the title of the first block area
        fx = x0 + 4 * G
        fy = 10 * G
        for i, net in enumerate(self.flags):
            p = Part(f'#FLG{i+1:02d}', 'power:PWR_FLAG', 'PWR_FLAG', '', {'1': net})
            self._place(p, snap(fx + i * 12 * G), snap(fy), items, libsyms, power=True)
        texts.append(('Power flags (ERC drivers for rails that enter through connectors)', fx, 6 * G, 1.27, False))

        for (t, x, y, size, bold) in texts:
            eff = [Sym('effects'), [Sym('font'), [Sym('size'), size, size]] + ([Sym('bold')] if bold else []),
                   [Sym('justify'), Sym('left'), Sym('bottom')]]
            items.append([Sym('text'), t, [Sym('at'), snap(x), snap(y), 0], eff, [Sym('uuid'), uid(self.project + t + str(x) + str(y))]])

        tb = [Sym('title_block'), [Sym('title'), self.title], [Sym('rev'), self.rev]]
        if self.company: tb.append([Sym('company'), self.company])
        for i, c in enumerate(self.comments[:9]):
            tb.append([Sym('comment'), i + 1, c])
        doc = [Sym('kicad_sch'), [Sym('version'), 20230121], [Sym('generator'), Sym('eeschema')],
               [Sym('uuid'), self.root],
               [Sym('paper')] + ([paper] if isinstance(paper, str) else [paper[0], paper[1], paper[2]]),
               tb,
               [Sym('lib_symbols')] + list(libsyms.values())]
        doc += items
        doc.append([Sym('sheet_instances'), [Sym('path'), '/', [Sym('page'), '1']]])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(dump(doc) + '\n')
        self._write_project(path)

    def _place(self, p, cx, cy, items, libsyms, power=False):
        lib, name = p.libid.split(':')
        if p.libid not in libsyms:
            s = copy.deepcopy(get_symbol(lib, name))
            s[1] = p.libid
            libsyms[p.libid] = s
        sym = libsyms[p.libid]
        props = {pp[1]: pp for pp in find(sym, 'property')}
        su = uid(f'{self.project}/{p.ref}/{p.unit}')
        body = [Sym('symbol'), [Sym('lib_id'), p.libid], [Sym('at'), cx, cy, 0], [Sym('unit'), p.unit],
                [Sym('in_bom'), Sym('no') if power else Sym('yes')],
                [Sym('on_board'), Sym('no') if power else Sym('yes')], [Sym('dnp'), Sym('yes') if p.dnp else Sym('no')],
                [Sym('uuid'), su]]
        def prop(k, v, dx, dy, hide=False, size=1.27):
            eff = [Sym('effects'), [Sym('font'), [Sym('size'), size, size]], [Sym('justify'), Sym('left')]]
            if hide: eff.append(Sym('hide'))
            return [Sym('property'), k, v, [Sym('at'), snap(cx + dx), snap(cy + dy), 0], eff]
        if power:
            body.append(prop('Reference', p.ref, 0, 5 * G, hide=True))
            body.append(prop('Value', 'PWR_FLAG', 0, 5 * G, hide=True))
            body.append(prop('Footprint', '', 0, 0, hide=True))
            body.append(prop('Datasheet', '', 0, 0, hide=True))
        else:
            # put ref/value to the right of the body, clear of the pin labels
            bx = 2 * G if 'Q_' in p.libid or 'MPSA' in p.libid or 'BD1' in p.libid else 1.5 * G
            by = 0
            if p.libid in ('Device:D', 'Device:D_Zener', 'Device:LED'):
                bx, by = -2 * G, -2.5 * G      # horizontal parts: text above the body
            body.append(prop('Reference', p.ref, bx, by - 0.5 * G))
            body.append(prop('Value', p.value, bx, by + 0.5 * G))
            body.append(prop('Footprint', p.fp, 0, 0, hide=True))
            body.append(prop('Datasheet', '~', 0, 0, hide=True))
            for i, (k, v) in enumerate(p.fields.items()):
                body.append(prop(k, v, bx, (1.5 + i) * G, hide=True))
        for pin in sympins(sym):
            if pin[2] in (0, p.unit):
                body.append([Sym('pin'), pin[0], [Sym('uuid'), uid(su + '/pin/' + pin[0])]])
        body.append([Sym('instances'), [Sym('project'), self.project,
                     [Sym('path'), '/' + self.root, [Sym('reference'), p.ref], [Sym('unit'), p.unit]]]])
        items.append(body)
        # labels / no-connects on every pin end
        for (num, pname, unit, px, py, ang, ptype) in sympins(sym):
            if unit not in (0, p.unit):
                continue
            x, y = snap(cx + px), snap(cy - py)
            net = p.conn.get(num)
            if net is None:
                items.append([Sym('no_connect'), [Sym('at'), x, y], [Sym('uuid'), uid(su + 'nc' + num)]])
                continue
            out = (ang + 180) % 360
            just = 'right' if out == 180 else 'left'
            items.append([Sym('label'), net, [Sym('at'), x, y, int(out)], [Sym('fields_autoplaced')],
                          [Sym('effects'), [Sym('font'), [Sym('size'), 1.0, 1.0]], [Sym('justify'), Sym(just), Sym('bottom')]],
                          [Sym('uuid'), uid(su + 'lbl' + num)]])

    def _write_project(self, schpath):
        base = os.path.splitext(schpath)[0]
        pro = {
            "board": {"design_settings": {"defaults": {}, "rules": {}}},
            "meta": {"filename": os.path.basename(base) + ".kicad_pro", "version": 1},
            "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
            "sheets": [[self.root, ""]],
            "text_variables": {},
        }
        if not os.path.exists(base + '.kicad_pro'):
            json.dump(pro, open(base + '.kicad_pro', 'w'), indent=2)
