#!/usr/bin/env python3
"""Generate the KiCad 7 project for the vent-fan controller.

Writes, next to this tools/ folder:
  vent_fans.kicad_pro, vent_fans.kicad_sch, sym-lib-table, fp-lib-table,
  lib/vent_fans.kicad_sym, lib/vent_fans.pretty/RaspberryPi_PicoW_THT.kicad_mod

Every part is defined once in PARTS below (symbol, footprint, value and the
net on each pin). gen_pcb.py reads the same table, so schematic and board
cannot drift apart. Re-run both after editing PARTS.
"""
import os, re, uuid, json

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
SYMDIR = "/usr/share/kicad/symbols"
NAME = "vent_fans"

# --------------------------------------------------------------------------
# Pico W pinout (pin number -> name). Physical pins 1-20 down the left side
# (USB at the top), 21-40 up the right side.
PICO = {1: "GP0", 2: "GP1", 3: "GND", 4: "GP2", 5: "GP3", 6: "GP4", 7: "GP5",
        8: "GND", 9: "GP6", 10: "GP7", 11: "GP8", 12: "GP9", 13: "GND",
        14: "GP10", 15: "GP11", 16: "GP12", 17: "GP13", 18: "GND", 19: "GP14",
        20: "GP15", 21: "GP16", 22: "GP17", 23: "GND", 24: "GP18", 25: "GP19",
        26: "GP20", 27: "GP21", 28: "GND", 29: "GP22", 30: "RUN", 31: "GP26",
        32: "GP27", 33: "AGND", 34: "GP28", 35: "ADC_VREF", 36: "3V3",
        37: "3V3_EN", 38: "GND", 39: "VSYS", 40: "VBUS"}

PICO_NETS = {n: "GND" for n, nm in PICO.items() if nm in ("GND", "AGND")}
PICO_NETS.update({40: "+5V", 36: "+3V3", 20: "FAN_PWM", 21: "ONEWIRE"})

# ref: (lib_id, value, footprint, (x, y) on schematic, rotation, {pin: net}, description)
PARTS = {
    "U1": (f"{NAME}:RaspberryPi_PicoW", "Pico W", f"{NAME}:RaspberryPi_PicoW_THT",
           (63.5, 101.6), 0, PICO_NETS,
           "Raspberry Pi Pico W on 2x20 female headers. Powered by its own micro-USB."),
    "C1": ("Device:C_Polarized", "100uF 10V", "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
           (127.0, 55.88), 0, {1: "+5V", 2: "GND"},
           "Input bulk, 5 V rail. Low-ESR electrolytic."),
    "C2": ("Device:C", "10uF 16V X7R", "Capacitor_SMD:C_1206_3216Metric",
           (139.7, 55.88), 0, {1: "+5V", 2: "GND"},
           "Input ceramic, right next to Q1/D1."),
    "C3": ("Device:C_Polarized", "100uF 10V", "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
           (190.5, 83.82), 0, {1: "+5V", 2: "FAN-"},
           "Output cap ACROSS the fans (buck output)."),
    "L1": ("Device:L", "100uH >=1A", "Inductor_SMD:L_Bourns_SRR1260",
           (205.74, 96.52), 0, {1: "FAN-", 2: "SW"},
           "Buck inductor, shielded, Isat >= 1 A, DCR <= 0.4 ohm (e.g. Bourns SRR1260-101M)."),
    "D1": ("Device:D_Schottky", "SS14", "Diode_SMD:D_SMA",
           (220.98, 96.52), 90, {1: "+5V", 2: "SW"},
           "Freewheel diode, 1 A 40 V Schottky (SMD 1N5819). Cathode stripe to +5V."),
    "Q1": ("Device:Q_NMOS_GSD", "AO3400A", "Package_TO_SOT_SMD:SOT-23",
           (203.2, 119.38), 0, {1: "GATE", 2: "GND", 3: "SW"},
           "Logic-level N-MOSFET, 30 V 5.7 A, Rds(on) ~32 mOhm at 3.3 V gate."),
    "R1": ("Device:R", "100", "Resistor_SMD:R_0805_2012Metric",
           (182.88, 119.38), 90, {1: "FAN_PWM", 2: "GATE"},
           "Gate series resistor."),
    "R2": ("Device:R", "10k", "Resistor_SMD:R_0805_2012Metric",
           (193.04, 127.0), 0, {1: "GATE", 2: "GND"},
           "Gate pull-down: fans stay off while the Pico boots or is unplugged."),
    "J1": ("Connector_Generic:Conn_01x03", "Fan 1", "Connector:FanPinHeader_1x03_P2.54mm_Vertical",
           (170.18, 76.2), 0, {1: "FAN-", 2: "+5V"},
           "Fan header. Pin 1 = black (FAN-), pin 2 = red (+5V), pin 3 = tach (unused)."),
    "J2": ("Connector_Generic:Conn_01x03", "Fan 2", "Connector:FanPinHeader_1x03_P2.54mm_Vertical",
           (170.18, 91.44), 0, {1: "FAN-", 2: "+5V"}, "Fan header."),
    "J3": ("Connector_Generic:Conn_01x03", "Fan 3", "Connector:FanPinHeader_1x03_P2.54mm_Vertical",
           (170.18, 106.68), 0, {1: "FAN-", 2: "+5V"}, "Fan header."),
    "J4": ("Connector_Generic:Conn_01x03", "DS18B20 (optional)",
           "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
           (129.54, 147.32), 0, {1: "GND", 2: "ONEWIRE", 3: "+3V3"},
           "Optional duct probe: 1 = GND (black), 2 = DQ (yellow), 3 = 3V3 (red)."),
    "R3": ("Device:R", "4.7k", "Resistor_SMD:R_0805_2012Metric",
           (104.14, 134.62), 0, {1: "+3V3", 2: "ONEWIRE"},
           "1-Wire pull-up (only needed with the DS18B20)."),
    "H1": ("Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3",
           (40.64, 160.02), 0, {}, "Mounting hole."),
    "H2": ("Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3",
           (50.8, 160.02), 0, {}, "Mounting hole."),
}
POWER_NETS = {"+5V": "power:+5V", "GND": "power:GND", "+3V3": "power:+3V3"}

# --------------------------------------------------------------------------
# tiny s-expression reader / writer
def parse(s):
    tok = re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', s)
    stack, cur = [], []
    for t in tok:
        if t == "(":
            stack.append(cur); cur = []
        elif t == ")":
            done = cur; cur = stack.pop(); cur.append(done)
        else:
            cur.append(t)
    return cur

def dump(e, ind=0):
    if not isinstance(e, list):
        return e
    if all(not isinstance(x, list) for x in e):
        return "(" + " ".join(e) + ")"
    out, pad = "(", "  " * (ind + 1)
    seen_list = False
    for i, x in enumerate(e):
        if isinstance(x, list):
            out += "\n" + pad + dump(x, ind + 1); seen_list = True
        else:
            out += ("" if i == 0 else (" " if not seen_list else "\n" + pad)) + x
    return out + "\n" + "  " * ind + ")"

def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'

def uid():
    return str(uuid.uuid4())

_libcache = {}
def lib_symbol(lib_id):
    """Return the symbol definition (as a parsed list) renamed to lib_id."""
    lib, name = lib_id.split(":")
    if lib == NAME:
        tree = parse(open(os.path.join(PROJ, "lib", f"{NAME}.kicad_sym")).read())
    else:
        if lib not in _libcache:
            _libcache[lib] = parse(open(f"{SYMDIR}/{lib}.kicad_sym").read())
        tree = _libcache[lib]
    root = tree[0]
    syms = {x[1].strip('"'): x for x in root if isinstance(x, list) and x[0] == "symbol"}
    sym = [y for y in syms[name]]
    ext = [x for x in sym if isinstance(x, list) and x[0] == "extends"]
    if ext:  # flatten "extends": take parent's graphics/pins, child's properties
        parent = lib_symbol(f"{lib}:{ext[0][1].strip(chr(34))}")
        props = [x for x in sym if isinstance(x, list) and x[0] == "property"]
        body = [x for x in parent[2:] if not (isinstance(x, list) and x[0] == "property")]
        sym = ["symbol", q(name)] + props + body
        pname = parent[1].strip('"').split(":")[-1]
        sym = rename_units(sym, pname, name)
    sym = list(sym)
    sym[1] = q(lib_id)
    return sym

def rename_units(e, old, new):
    if isinstance(e, list):
        return [rename_units(x, old, new) for x in e]
    if e.startswith('"' + old + "_"):
        return '"' + new + e[len(old) + 1:]
    return e

def pins_of(sym):
    """{pin_number: (x, y, angle)} in symbol coordinates (y up)."""
    res = {}
    def walk(e):
        for x in e:
            if isinstance(x, list):
                if x[0] == "pin":
                    at = next(y for y in x if isinstance(y, list) and y[0] == "at")
                    num = next(y for y in x if isinstance(y, list) and y[0] == "number")[1].strip('"')
                    res[num] = (float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0)
                else:
                    walk(x)
    walk(sym)
    return res

def xform(px, py, rot):
    """symbol coords (y up) -> schematic offset (y down), symbol rotated CCW by rot."""
    import math
    r = math.radians(rot)
    x = px * math.cos(r) - py * math.sin(r)
    y = px * math.sin(r) + py * math.cos(r)
    return round(x, 4), round(-y, 4)

def outward(angle, rot):
    a = (angle + rot) % 360  # pin direction (toward body), in symbol coords
    return {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[int(a)]

# --------------------------------------------------------------------------
def write_pico_symbol():
    os.makedirs(os.path.join(PROJ, "lib"), exist_ok=True)
    pins = []
    for n, nm in PICO.items():
        if n <= 20:
            x, y, a = -15.24, 24.13 - 2.54 * (n - 1), 0
        else:
            x, y, a = 15.24, -24.13 + 2.54 * (n - 21), 180
        if nm in ("VBUS", "3V3"):
            typ = "power_out"
        elif nm in ("GND", "AGND", "VSYS", "ADC_VREF"):
            typ = "passive"
        else:
            typ = "bidirectional"
        pins.append(f'      (pin {typ} line (at {x} {y} {a}) (length 2.54)\n'
                    f'        (name {q(nm)} (effects (font (size 1.27 1.27))))\n'
                    f'        (number {q(n)} (effects (font (size 1.27 1.27)))))')
    txt = f'''(kicad_symbol_lib (version 20220914) (generator vent_fans_gen)
  (symbol "RaspberryPi_PicoW" (in_bom yes) (on_board yes)
    (property "Reference" "U" (at 0 27.94 0) (effects (font (size 1.27 1.27))))
    (property "Value" "RaspberryPi_PicoW" (at 0 -27.94 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "{NAME}:RaspberryPi_PicoW_THT" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "https://datasheets.raspberrypi.com/picow/pico-w-datasheet.pdf" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "RaspberryPi_PicoW_0_1"
      (rectangle (start -12.7 26.67) (end 12.7 -26.67) (stroke (width 0.254) (type default)) (fill (type background)))
      (text "USB" (at 0 24.13 0) (effects (font (size 1.27 1.27))))
    )
    (symbol "RaspberryPi_PicoW_1_1"
{chr(10).join(pins)}
    )
  )
)
'''
    open(os.path.join(PROJ, "lib", f"{NAME}.kicad_sym"), "w").write(txt)

def write_pico_footprint():
    d = os.path.join(PROJ, "lib", f"{NAME}.pretty")
    os.makedirs(d, exist_ok=True)
    pads = []
    for n in range(1, 41):
        if n <= 20:
            x, y = -8.89, -24.13 + 2.54 * (n - 1)
        else:
            x, y = 8.89, 24.13 - 2.54 * (n - 21)
        shape = "rect" if n == 1 else "oval"
        pads.append(f'  (pad "{n}" thru_hole {shape} (at {x} {y}) (size 1.7 1.7) (drill 1.02) '
                    f'(layers "*.Cu" "*.Mask") (tstamp {uid()}))')
    txt = f'''(footprint "RaspberryPi_PicoW_THT" (version 20221018) (generator vent_fans_gen)
  (layer "F.Cu")
  (descr "Raspberry Pi Pico W, through-hole on 2x20 2.54 mm headers (socketed). USB end at -Y, Wi-Fi antenna end at +Y: keep copper out from under the antenna.")
  (tags "RP2040 Pico W")
  (attr through_hole)
  (fp_text reference "REF**" (at 0 -27.2) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))) (tstamp {uid()}))
  (fp_text value "RaspberryPi_PicoW_THT" (at 0 27.2) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))) (tstamp {uid()}))
  (fp_text user "USB" (at 0 -23.5) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))) (tstamp {uid()}))
  (fp_text user "ANTENNA - keep clear" (at 0 21.5) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))) (tstamp {uid()}))
  (fp_rect (start -10.5 -25.5) (end 10.5 25.5) (stroke (width 0.12) (type default)) (fill none) (layer "F.SilkS") (tstamp {uid()}))
  (fp_rect (start -10.5 -25.5) (end 10.5 25.5) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab") (tstamp {uid()}))
  (fp_rect (start -10.75 -27.0) (end 10.75 25.75) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd") (tstamp {uid()}))
  (fp_rect (start -4 -26.6) (end 4 -25.5) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab") (tstamp {uid()}))
{chr(10).join(pads)}
)
'''
    open(os.path.join(d, "RaspberryPi_PicoW_THT.kicad_mod"), "w").write(txt)

# --------------------------------------------------------------------------
def build_schematic():
    root_uuid = uid()
    used = {}
    for ref, (lib_id, *_r) in PARTS.items():
        used[lib_id] = lib_symbol(lib_id)
    for p in POWER_NETS.values():
        used[p] = lib_symbol(p)
    used["power:PWR_FLAG"] = lib_symbol("power:PWR_FLAG")

    items = []
    pwr_n = [0]

    def power_sym(net, x, y, direction):
        lib = POWER_NETS[net]
        # GND symbol hangs below its pin, +5V/+3V3 stand above it.
        base = (0, 1) if net == "GND" else (0, -1)
        rot = {((0, 1), (0, 1)): 0, ((0, 1), (0, -1)): 180, ((0, 1), (1, 0)): 90, ((0, 1), (-1, 0)): 270,
               ((0, -1), (0, -1)): 0, ((0, -1), (0, 1)): 180, ((0, -1), (-1, 0)): 90, ((0, -1), (1, 0)): 270}[(base, direction)]
        pwr_n[0] += 1
        ref = f"#PWR{pwr_n[0]:02d}"
        items.append(f'''  (symbol (lib_id {q(lib)}) (at {x} {y} {rot}) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (uuid {uid()})
    (property "Reference" {q(ref)} (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Value" {q(net)} (at {x + 3 * direction[0]} {y + 3 * direction[1]} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid {uid()}))
    (instances (project {q(NAME)} (path "/{root_uuid}" (reference {q(ref)}) (unit 1))))
  )''')

    def label(net, x, y, direction):
        ang = {(-1, 0): 180, (1, 0): 0, (0, -1): 90, (0, 1): 270}[direction]
        just = "right" if ang in (180, 270) else "left"
        items.append(f'  (label {q(net)} (at {x} {y} {ang}) (fields_autoplaced)\n'
                     f'    (effects (font (size 1.27 1.27)) (justify {just} bottom)) (uuid {uid()}))')

    for ref, (lib_id, value, fp, (sx, sy), rot, nets, desc) in PARTS.items():
        sym = used[lib_id]
        pins = pins_of(sym)
        # text placement: horizontal 2-pin parts (R1, D1) get ref above / value below
        if (lib_id in ("Device:R",) and rot == 90) or (lib_id == "Device:D_Schottky" and rot == 0):
            rpos, vpos, just = (sx, sy - 3.81), (sx, sy + 3.81), ""
        elif lib_id == "Device:D_Schottky":
            rpos, vpos, just = (sx + 5.08, sy - 1.27), (sx + 5.08, sy + 1.27), " (justify left)"
        else:
            rpos, vpos, just = (sx + 3.81, sy - 1.27), (sx + 3.81, sy + 1.27), " (justify left)"
        pin_entries = "\n".join(f'    (pin {q(n)} (uuid {uid()}))' for n in pins)
        items.append(f'''  (symbol (lib_id {q(lib_id)}) (at {sx} {sy} {rot}) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (uuid {uid()})
    (property "Reference" {q(ref)} (at {rpos[0]} {rpos[1]} 0) (effects (font (size 1.27 1.27)){just}))
    (property "Value" {q(value)} (at {vpos[0]} {vpos[1]} 0) (effects (font (size 1.27 1.27)){just}))
    (property "Footprint" {q(fp)} (at {sx} {sy} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Description" {q(desc)} (at {sx} {sy} 0) (effects (font (size 1.27 1.27)) hide))
{pin_entries}
    (instances (project {q(NAME)} (path "/{root_uuid}" (reference {q(ref)}) (unit 1))))
  )''')
        for num, (px, py, pa) in pins.items():
            ox, oy = xform(px, py, rot)
            x, y = round(sx + ox, 2), round(sy + oy, 2)
            d = outward(pa, rot)
            net = nets.get(int(num)) if num.isdigit() else None
            if net is None:
                items.append(f'  (no_connect (at {x} {y}) (uuid {uid()}))')
                continue
            ex, ey = round(x + 2.54 * d[0], 2), round(y + 2.54 * d[1], 2)
            items.append(f'  (wire (pts (xy {x} {y}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid {uid()}))')
            if net in POWER_NETS:
                power_sym(net, ex, ey, d)
            else:
                label(net, ex, ey, d)

    # PWR_FLAGs: GND has no driver pin (Pico GND pins are passive); FAN-/SW are
    # driven through passives only.
    for i, net in enumerate(["GND", "FAN-", "SW"]):
        x, y = 40.64 + 12.7 * i, 30.48
        items.append(f'''  (symbol (lib_id "power:PWR_FLAG") (at {x} {y} 0) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (uuid {uid()})
    (property "Reference" "#FLG0{i + 1}" (at {x} {y - 1.9} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Value" "PWR_FLAG" (at {x} {y - 3.8} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid {uid()}))
    (instances (project {q(NAME)} (path "/{root_uuid}" (reference "#FLG0{i + 1}") (unit 1))))
  )''')
        items.append(f'  (wire (pts (xy {x} {y}) (xy {x} {y + 5.08})) (stroke (width 0) (type default)) (uuid {uid()}))')
        if net == "GND":
            power_sym("GND", x, y + 5.08, (0, 1))
        else:
            label(net, x, y + 5.08, (0, 1))

    notes = [
        (25.4, 20.32, "Vent booster fan controller - Pico W + low-side buck (fans get smooth DC = duty x 5 V)"),
        (165.1, 45.72, "POWER STAGE: GP15 PWM 40 kHz -> R1 -> Q1. L1 + C3 filter it to DC across the fans."),
        (165.1, 50.8, "FAN- is NOT ground. Never tie a fan's black wire to GND or to the metal duct."),
        (101.6, 160.02, "Optional DS18B20 duct probe (standalone fallback). Leave J4/R3 unpopulated if unused."),
    ]
    for x, y, t in notes:
        items.append(f'  (text {q(t)} (at {x} {y} 0) (effects (font (size 1.5 1.5)) (justify left bottom)) (uuid {uid()}))')

    libs = "\n".join("    " + dump(s, 2) for s in used.values())
    sch = f'''(kicad_sch (version 20230121) (generator eeschema)
  (uuid {root_uuid})
  (paper "A4")
  (title_block
    (title "Vent booster fan controller")
    (rev "1.0")
    (comment 1 "Pico W + AO3400A low-side buck, 3x 5 V 80 mm fans")
    (comment 2 "Generated by tools/gen_schematic.py - simulated in ../sim (ngspice)")
  )
  (lib_symbols
{libs}
  )
{chr(10).join(items)}
  (sheet_instances (path "/" (page "1")))
)
'''
    open(os.path.join(PROJ, f"{NAME}.kicad_sch"), "w").write(sch)

def write_project_files():
    open(os.path.join(PROJ, "sym-lib-table"), "w").write(
        f'(sym_lib_table\n  (lib (name "{NAME}")(type "KiCad")(uri "${{KIPRJMOD}}/lib/{NAME}.kicad_sym")(options "")(descr "Project symbols"))\n)\n')
    open(os.path.join(PROJ, "fp-lib-table"), "w").write(
        f'(fp_lib_table\n  (lib (name "{NAME}")(type "KiCad")(uri "${{KIPRJMOD}}/lib/{NAME}.pretty")(options "")(descr "Project footprints"))\n)\n')
    pro = {"meta": {"filename": f"{NAME}.kicad_pro", "version": 1},
           "board": {"design_settings": {"rules": {"min_clearance": 0.2, "min_track_width": 0.25},
                                          "defaults": {}}},
           "net_settings": {"classes": [
               {"name": "Default", "clearance": 0.2, "track_width": 0.3, "via_diameter": 0.8, "via_drill": 0.4},
               {"name": "Power", "clearance": 0.25, "track_width": 0.8, "via_diameter": 1.0, "via_drill": 0.5}],
               "netclass_patterns": [{"netclass": "Power", "pattern": n} for n in ("+5V", "GND", "FAN-", "SW")],
               "meta": {"version": 3}},
           "sheets": [], "boards": [], "text_variables": {}}
    path = os.path.join(PROJ, f"{NAME}.kicad_pro")
    json.dump(pro, open(path, "w"), indent=2)

if __name__ == "__main__":
    write_pico_symbol()
    write_pico_footprint()
    build_schematic()
    write_project_files()
    print("schematic written")
