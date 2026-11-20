#!/usr/bin/python3
"""Build vent_fans.kicad_pcb from the PARTS table in gen_schematic.py.

Run with the system Python that has KiCad's pcbnew module:
    /usr/bin/python3 tools/gen_pcb.py            # place + outline + GND pours
    /usr/bin/python3 tools/gen_pcb.py --ses X    # ...and import a Freerouting session

Board: 70 x 50 mm, 2 layers. Pico W across the top with its USB end at the
left edge; power stage underneath; fan headers down the right edge.
"""
import os, sys
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import gen_schematic as g

FPDIR = "/usr/share/kicad/footprints"
OX, OY, W, H = 100.0, 100.0, 70.0, 50.0
mm = pcbnew.FromMM

# ref: (x, y, rotation, side)  -- absolute board coordinates in mm
PLACE = {
    "U1": (127.0, 112.5, 90, "F"),     # USB end at x~101.5 (left edge)
    "J1": (158.0, 106.0, 0, "F"),
    "J2": (158.0, 116.5, 0, "F"),
    "J3": (158.0, 127.0, 0, "F"),
    "J4": (158.5, 141.0, 0, "F"),
    "R3": (152.5, 145.5, 0, "F"),
    "C1": (109.0, 135.0, 0, "F"),
    "C2": (140.5, 128.5, 180, "F"),     # hot-loop ceramic, right at Q1/D1
    "L1": (126.0, 138.5, 0, "F"),
    "C3": (140.0, 144.0, 0, "F"),
    "D1": (140.0, 133.0, 180, "F"),
    "Q1": (147.0, 130.0, 0, "F"),
    "R1": (151.5, 125.5, 90, "F"),
    "R2": (147.0, 125.5, 0, "F"),
    "H1": (104.0, 146.0, 0, "F"),
    "H2": (166.0, 146.0, 0, "F"),
}
# Pico W Wi-Fi antenna: last ~10 mm of the module, between the pin rows.
ANTENNA_KEEPOUT = (142.0, 105.2, 153.0, 119.8)

def load_fp(fpid):
    lib, name = fpid.split(":")
    path = os.path.join(g.PROJ, "lib", f"{lib}.pretty") if lib == g.NAME else os.path.join(FPDIR, f"{lib}.pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise SystemExit(f"footprint not found: {fpid}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp

def segment(board, layer, a, b, width=0.1):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1]))); s.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
    s.SetLayer(layer); s.SetWidth(mm(width)); board.Add(s)

def rect_poly(x0, y0, x1, y1):
    ch = pcbnew.SHAPE_LINE_CHAIN()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ch.Append(mm(x), mm(y))
    ch.SetClosed(True)
    return ch

def build(ses=None, pours=True):
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    ds.m_TrackMinWidth = mm(0.25); ds.m_MinClearance = mm(0.2)
    ds.m_ViasMinSize = mm(0.6); ds.m_MinThroughDrill = mm(0.3)
    ns = ds.m_NetSettings
    dflt = ns.m_DefaultNetClass
    dflt.SetTrackWidth(mm(0.3)); dflt.SetClearance(mm(0.2)); dflt.SetViaDiameter(mm(0.8)); dflt.SetViaDrill(mm(0.4))
    pwr = pcbnew.NETCLASS("Power")
    pwr.SetTrackWidth(mm(0.8)); pwr.SetClearance(mm(0.25)); pwr.SetViaDiameter(mm(1.0)); pwr.SetViaDrill(mm(0.5))
    ns.m_NetClasses["Power"] = pwr

    nets = {}
    for ref, (_l, _v, _f, _p, _r, pn, _d) in g.PARTS.items():
        for n in pn.values():
            if n not in nets:
                ni = pcbnew.NETINFO_ITEM(board, n); board.Add(ni); nets[n] = ni
    for n in ("+5V", "GND", "FAN-", "SW"):
        nets[n].SetNetClass(pwr)

    for ref, (lib_id, value, fpid, _p, _r, pn, desc) in g.PARTS.items():
        fp = load_fp(fpid)
        fp.SetReference(ref); fp.SetValue(value)
        x, y, rot, side = PLACE[ref]
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        fp.SetOrientationDegrees(rot)
        if ref == "U1":  # keep the reference inside the board outline
            fp.Reference().SetPosition(pcbnew.VECTOR2I(mm(104.5), mm(124.5))); fp.Reference().SetTextAngleDegrees(0)
        for pad in fp.Pads():
            num = pad.GetNumber()
            if num.isdigit() and int(num) in pn:
                pad.SetNet(nets[pn[int(num)]])
        board.Add(fp)

    # outline (rounded corners would be nicer; plain rectangle keeps it simple)
    corners = [(OX, OY), (OX + W, OY), (OX + W, OY + H), (OX, OY + H)]
    for i in range(4):
        segment(board, pcbnew.Edge_Cuts, corners[i], corners[(i + 1) % 4], 0.1)

    # silkscreen notes
    for (x, y, txt, sz) in [(126.0, 148.4, "FAN- is NOT GND", 0.9),
                            (110.0, 128.0, "VENT FAN CTRL v1", 0.9),
                            (164.2, 101.6, "FANS", 0.9),
                            (164.0, 137.2, "DS18B20", 0.8)]:
        t = pcbnew.PCB_TEXT(board); t.SetText(txt); t.SetLayer(pcbnew.F_SilkS)
        t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); t.SetTextSize(pcbnew.VECTOR2I(mm(sz), mm(sz)))
        t.SetTextThickness(mm(0.15)); board.Add(t)

    # antenna keep-out: no copper (tracks, vias, pours) under the Pico W antenna
    ra = pcbnew.ZONE(board); ra.SetIsRuleArea(True)
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); ra.SetLayerSet(ls)
    ra.SetDoNotAllowCopperPour(True); ra.SetDoNotAllowTracks(True); ra.SetDoNotAllowVias(True)
    ra.SetDoNotAllowPads(False); ra.SetDoNotAllowFootprints(False)
    ra.Outline().AddOutline(rect_poly(*ANTENNA_KEEPOUT)); ra.SetZoneName("PicoW antenna keepout")
    board.Add(ra)

    if ses:
        board.Save(OUT)  # SES import needs a board on disk
        board = pcbnew.LoadBoard(OUT)
        if not pcbnew.ImportSpecctraSES(board, ses):
            raise SystemExit("SES import failed")

    # GND pour on both layers (added after routing so Freerouting routes GND as tracks too)
    for layer in ((pcbnew.F_Cu, pcbnew.B_Cu) if pours else ()):
        z = pcbnew.ZONE(board); z.SetLayer(layer); z.SetNet(board.FindNet("GND"))
        z.Outline().AddOutline(rect_poly(OX + 0.5, OY + 0.5, OX + W - 0.5, OY + H - 0.5))
        z.SetLocalClearance(mm(0.3)); z.SetMinThickness(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(mm(0.4)); z.SetThermalReliefSpokeWidth(mm(0.5))
        z.SetZoneName(f"GND {pcbnew.LayerName(layer)}")
        board.Add(z)
    board.Save(OUT)
    if pours:  # fill on a freshly loaded board (filling the in-memory one crashes KiCad 7)
        board = pcbnew.LoadBoard(OUT)
        board.BuildConnectivity()
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        board.Save(OUT)
    return board

OUT = os.path.join(g.PROJ, f"{g.NAME}.kicad_pcb")

if __name__ == "__main__":
    ses = sys.argv[sys.argv.index("--ses") + 1] if "--ses" in sys.argv else None
    b = build(ses, pours="--dsn" not in sys.argv)
    if "--dsn" in sys.argv:
        pcbnew.ExportSpecctraDSN(b, sys.argv[sys.argv.index("--dsn") + 1])
    print("board written:", OUT)
