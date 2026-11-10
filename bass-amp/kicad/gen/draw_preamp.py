"""Hand-placed drawing of the preamp board (parts and nets from board_preamp.py)."""
from kdraw import Drawing
import netnames
import board_preamp

def build():
    src = {}
    for p in board_preamp.build().all_parts():
        src[(p.ref, p.unit)] = p
    P = lambda r, u=1: src[(r, u)]
    d = Drawing('preamp', 'Bass amp preamp board (HV front end, EQ, I/O)', paper='A1',
                comments=['Pots are PCB-mounted Alpha 16 mm (pin 3 = CW end). Jacks and switches are panel-mounted on JST-XH headers.',
                          'A1/A2 are HVOA-1 daughterboards (hvoa_module project) plugged into J20/J21.',
                          'Keep the +/-40 V area away from the NE5532 area; every HV output enters the 15 V domain AC-coupled or clamped.',
                          'NP = bipolar electrolytic (CP footprint, either orientation).'])
    S = d.stubs
    # ------------------------------------------------------------------ power
    b = d.block('Power input and op-amp decoupling', 4, 6, 84, 34, 'J1: +/-15 V from PSU J4.  J2: +/-40 V from PSU J6 (different size: cannot be swapped).')
    b.add(P('J1'), 6, 10, mirror='y')
    S[('J1', '1')] = [(1.5, 0), (1.5, -1.5)]; S[('J1', '2')] = [(5, 0), (5, 1.5)]; S[('J1', '3')] = [(1.5, 0), (1.5, 1.5)]
    b.add(P('J2'), 6, 23, mirror='y')
    S[('J2', '1')] = [(1.5, 0), (1.5, -1.5)]; S[('J2', '2')] = [(5.5, 0), (5.5, 1.5)]
    S[('J2', '3')] = [(3.5, 0), (3.5, 1.5)]; S[('J2', '4')] = [(1.5, 0), (1.5, 1.5)]
    b.add(P('C201'), 18, 10); b.add(P('C202'), 23, 10); b.add(P('C203'), 18, 24); b.add(P('C204'), 23, 24)
    for i, u in enumerate(['U1', 'U2', 'U3', 'U4', 'U5', 'U6']):
        b.add(P(u, 3), 33 + 9 * i, 10)
        b.add(P(f'C{211 + 2 * i}'), 31 + 9 * i, 24); b.add(P(f'C{212 + 2 * i}'), 35 + 9 * i, 24)

    # ------------------------------------------------------------------ A1
    b = d.block('A1: bootstrapped instrument input / gain (+1.7 .. +27 dB)', 92, 6, 74, 46,
                'RA (R2) is bootstrapped by C3 from IN- : >1 MOhm input impedance.\nVR1 is a rheostat: gain rises CW. C2/C3: film, 100 V.')
    b.add(P('J3'), 4, 10, mirror='y'); S[('J3', '2')] = [(1.5, 0), (1.5, 1.5)]
    b.add(P('R1'), 12, 10, 90); b.add(P('C1'), 16, 15); b.add(P('C2'), 21, 10, 90)
    b.add(P('R2'), 26, 15); b.add(P('R3'), 26, 23); b.add(P('C3'), 31, 19, 270)
    b.add(P('J20'), 46, 13)
    S[('J20', '1')] = [(-2, 0), (-2, -2)]; S[('J20', '2')] = [(-4.5, 0), (-4.5, -2)]; S[('J20', '3')] = [(-7, 0), (-7, -4)]
    b.add(P('R4'), 34, 25, 180); b.add(P('VR1'), 34, 31, 180, 'y'); b.add(P('C4'), 40, 27, 180)
    b.add(P('R5'), 29, 27); b.add(P('C5'), 29, 34)
    b.add(P('R6'), 52, 30, 90); b.add(P('C6'), 58, 30, 90); b.add(P('R7'), 63, 34)

    # ------------------------------------------------------------------ Baxandall
    b = d.block('EQ: Baxandall bass / treble (U1A)', 170, 6, 50, 46, 'CW = boost (wiper toward the input end).')
    b.add(P('R11'), 8, 8, 90); b.add(P('VR2'), 17, 8, 270); b.add(P('R12'), 27, 8, 90)
    b.add(P('C11'), 13, 13, 90); b.add(P('C12'), 21, 13, 90); b.add(P('R13'), 17, 19)
    b.add(P('U1', 1), 39, 25, mirror='x')
    b.add(P('R14'), 17, 31, 180)
    b.add(P('C13'), 8, 37, 90); b.add(P('VR3'), 17, 37, 270, 'x'); b.add(P('C14'), 27, 37, 90)

    # ------------------------------------------------------------------ mid
    b = d.block('EQ: mid, gyrator with 5-way frequency switch (U1B, U2A)', 224, 6, 76, 62,
                'J9 -> 2-pole rotary: pole A (MW) selects Cs, pole B (GP) selects Cg.\n250 / 500 / 800 / 1.5k / 3k Hz. Keep J9 wiring short and shielded.')
    b.add(P('R15'), 7, 9, 90); b.add(P('U1', 2), 24, 10); b.add(P('R16'), 24, 16, 270)
    b.add(P('VR4'), 14, 14, 0, 'y')
    for k in range(5):
        b.add(P(f'C{21 + k}'), 30 + 5 * k, 32)
        b.add(P(f'C{26 + k}'), 30 + 5 * k, 44)
        d.label_pins |= {(f'C{21 + k}', '2'), (f'C{26 + k}', '2')}
    b.add(P('J9'), 70, 30)
    d.label_pins |= {('J9', str(i)) for i in range(1, 13)}
    b.add(P('U2', 1), 12, 44); b.add(P('R17'), 6, 50); b.add(P('R18'), 20, 44, 90)
    b.text('Cs: 220n / 100n / 68n / 33n / 18n  (C21-C25, pole A)', 30, 39)
    b.text('Cg: 27n / 15n / 8n2 / 4n7 / 2n2  (C26-C30, pole B)', 30, 51)

    # ------------------------------------------------------------------ FX
    b = d.block('FX send (U2B) and FX return (A2: HV unity buffer)', 4, 56, 84, 52,
                'J5 is a switched jack: its switch lug (pin 2) carries EQ_OUT,\nso the loop is closed when nothing is plugged in.')
    b.add(P('R31'), 8, 9); b.add(P('R32'), 8, 16); b.add(P('J10'), 17, 10)
    b.add(P('U2', 2), 30, 9); b.add(P('R33'), 24, 14); b.add(P('R34'), 37, 9, 90); b.add(P('C31'), 43, 9, 90)
    b.add(P('R35'), 48, 13); b.add(P('J4'), 56, 9); S[('J4', '2')] = [(-1.5, 0), (-1.5, 1.5)]
    b.add(P('J5'), 4, 28, mirror='y'); S[('J5', '3')] = [(1.5, 0), (1.5, 1.5)]
    b.add(P('R21'), 12, 27, 90); b.add(P('C41'), 16, 32); b.add(P('C42'), 21, 27, 90)
    b.add(P('R22'), 26, 32); b.add(P('R23'), 26, 40); b.add(P('C43'), 32, 36, 270)
    b.add(P('J21'), 48, 30)
    S[('J21', '1')] = [(-2, 0), (-2, -2)]; S[('J21', '2')] = [(-4.5, 0), (-4.5, -2)]; S[('J21', '3')] = [(-7, 0), (-7, -4)]
    b.add(P('R24'), 40, 41, 90); b.add(P('R25'), 56, 41, 90); b.add(P('C44'), 62, 41, 90)

    # ------------------------------------------------------------------ master
    b = d.block('Master, aux in (U3A), subsonic filter (U6A), bridge phase splitter (U3B)', 92, 56, 112, 52,
                'J11 -> DPDT: both poles closed = TIGHT (~40 Hz), open = DEEP (22 Hz).  J15 -> power amp board J2.')
    b.add(P('VR5'), 8, 12, 180, 'y'); b.add(P('R41'), 21, 12, 90)
    b.add(P('J6'), 4, 25, mirror='y'); S[('J6', '3')] = [(1.5, 0), (1.5, 2.5)]
    b.add(P('C45'), 13, 22, 90); b.add(P('R42'), 20, 22, 90); b.add(P('C46'), 13, 28, 90); b.add(P('R43'), 20, 28, 90)
    b.add(P('R44'), 9, 34); b.add(P('R45'), 13, 34)
    b.add(P('U3', 1), 32, 16, mirror='x'); b.add(P('R46'), 32, 10, 270); b.add(P('C47'), 32, 6, 270)
    b.add(P('C51'), 44, 16, 90); b.add(P('C52'), 50, 16, 90); b.add(P('U6', 1), 60, 17)
    b.add(P('R61'), 54, 10, 90); b.add(P('R62'), 54, 5, 90); b.add(P('R63'), 53, 23); b.add(P('R64'), 57, 26)
    b.add(P('J11'), 74, 5)
    b.add(P('R65'), 72, 21, 90); b.add(P('U3', 2), 82, 22, mirror='x'); b.add(P('R66'), 82, 16, 270)
    b.add(P('J15'), 100, 22); S[('J15', '2')] = [(-1.5, 0), (-1.5, 2.5)]
    b.add(P('U6', 2), 70, 38)

    # ------------------------------------------------------------------ phones
    b = d.block('Headphone amplifier (U4)', 208, 72, 44, 34, 'Phones jack switch contacts are wired to\nthe power amp board J5 (mutes the speaker).')
    b.add(P('U4', 1), 12, 8); b.add(P('R71'), 21, 8, 90)
    b.add(P('U4', 2), 12, 19); b.add(P('R72'), 21, 19, 90)
    b.add(P('J7'), 34, 13); S[('J7', '3')] = [(-1.5, 0), (-1.5, 2.5)]

    # ------------------------------------------------------------------ DI
    b = d.block('Balanced DI / line out (U5)', 4, 112, 100, 40,
                'J12: PRE/POST select.  J13 closed = -20 dB pad.  J14: ground-lift switch.\nC81/C82 + toward the XLR (phantom power).')
    b.add(P('J12'), 6, 9, mirror='y')
    b.add(P('R81'), 15, 8, 90); b.add(P('D81'), 19, 4, 270); b.add(P('D82'), 19, 13, 270)
    b.add(P('R82'), 25, 8, 90); b.add(P('R83'), 29, 13); b.add(P('J13'), 34, 18); S[('J13', '2')] = [(-1.5, 0), (-1.5, 1.5)]
    b.add(P('U5', 1), 40, 9)
    b.add(P('R87'), 50, 9, 90); b.add(P('D83'), 55, 5, 270); b.add(P('D84'), 55, 13, 270)
    b.add(P('C81'), 61, 9, 270); b.add(P('R88'), 67, 9, 90); b.add(P('R89'), 72, 13)
    b.add(P('R85'), 47, 24, 90); b.add(P('U5', 2), 56, 25, mirror='x'); b.add(P('R86'), 56, 20, 270)
    b.add(P('R90'), 64, 25, 90); b.add(P('D85'), 68, 21, 270); b.add(P('D86'), 68, 29, 270)
    b.add(P('C82'), 74, 25, 270); b.add(P('R91'), 80, 25, 90); b.add(P('R92'), 85, 29)
    b.add(P('J8'), 95, 12); b.add(P('J14'), 95, 22); S[('J14', '2')] = [(-1.5, 0), (-1.5, 1.5)]

    # ------------------------------------------------------------------ clip
    b = d.block('PRE clip indicator', 108, 112, 60, 30, 'Lights at about +/-11.3 V peak (2.5 dB before the NE5532 stages clip).\nJ16 -> panel LED.')
    b.add(P('R93'), 7, 5, 90); b.add(P('D91'), 13, 5, 180); b.add(P('R94'), 7, 11, 90); b.add(P('D92'), 13, 11, 180)
    b.add(P('C91'), 19, 15); b.add(P('R95'), 23, 15); b.add(P('D93'), 27, 5); b.add(P('R96'), 33, 5, 90)
    b.add(P('R97'), 37, 11); b.add(P('Q91'), 42, 8); b.add(P('R98'), 50, 3); b.add(P('J16'), 56, 9)

    d.rails = {n: netnames.RAIL_SYMBOL[n] for n in netnames.RAIL_SYMBOL if n in {x for q in src.values() for x in q.conn.values()}}
    d.named = set(netnames.PREAMP.values()) - set(d.rails)
    d.flags = [('+15V', 60, 32), ('-15V', 66, 32), ('+40V', 72, 32), ('-40V', 78, 32), ('GND', 84, 32)]
    return d

if __name__ == '__main__':
    import kdraw; kdraw.write_local_lib()
    print('\n'.join(build().write('../preamp/preamp.kicad_sch')) or 'all nets wired')
