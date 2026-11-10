"""Hand-placed drawing of the power amp board (parts and nets from board_poweramp.py)."""
from kdraw import Drawing
import board_poweramp

def chip(d, b, P, u, n0, L):
    r = lambda k: f'R{n0 + k}'
    c = lambda k: f'C{n0 + k}'
    b.add(P(u), 30, 18)
    d.stubs[(u, '4')] = [(0, 1.5), (-5, 1.5), (-5, 2.5)]
    b.add(P(c(1)), 10, 17, 90); b.add(P(r(1)), 17, 17, 90)
    b.add(P(c(2)), 13, 24); b.add(P(r(2)), 18, 24)
    b.add(P(r(7)), 30, 10, 180)
    b.add(P(r(3)), 31, 30, 270); b.add(P(r(4)), 24, 32); b.add(P(c(3)), 24, 38)
    b.add(P(r(5)), 39, 24); b.add(P(c(8)), 39, 31)
    b.add(P(L), 47, 18, 90); b.add(P(r(6)), 47, 13, 90)
    for i, k in enumerate((4, 5, 6, 7)): b.add(P(c(k)), 52 + 5 * i, 33)

def build():
    src = {p.ref: p for p in board_poweramp.build().all_parts()}
    P = lambda r: src[r]
    d = Drawing('poweramp', 'Bass amp power amplifier: 2 x LM3886T bridged (BTL), protection', paper='A2',
                comments=['BRIDGED OUTPUT: neither speaker terminal is ground. Use a Speakon NL4 (1+ = SPK+, 1- = SPK-).',
                          'Rails +/-28 V from the PSU board with heavy wire. Star ground at the PSU reservoir caps.',
                          'Heatsink <= 0.4 C/W (or <= 0.7 C/W + fan). LM3886T tab is V-: insulate it.',
                          'J5 goes to the phones jack NC switch (opens = speaker muted). Fit a jumper if unused.'])
    b = d.block('Connectors', 4, 6, 30, 52, 'J1 rails, J2 from preamp J15,\nJ3 speaker (Speakon), J4 AC sense,\nJ5 phones-mute switch, J6 clip LED.')
    for i, (j, mir) in enumerate([('J1', 'y'), ('J2', 'y'), ('J3', None), ('J4', 'y'), ('J5', None), ('J6', None)]):
        b.add(P(j), 8 if mir else 22, 8 + 7 * i, mirror=mir)
    b = d.block('LM3886 A (non-inverted half)', 38, 6, 74, 44, 'Gain 1 + 20k/1k = 21. Gain resistors 1 %, matched A to B. U1 tab = V-.')
    chip(d, b, P, 'U1', 0, 'L1')
    b = d.block('LM3886 B (inverted half)', 38, 54, 74, 44, 'Identical to A; driven from SUB_INV.')
    chip(d, b, P, 'U2', 10, 'L2')
    b = d.block('Speaker relay with ~3.5 s turn-on delay', 116, 6, 56, 34,
                'T charges via R40/C40; at ~13.6 V the 12 V zener lets Q32/Q33 pull K1 in.\nAnything that pulls TD low drops the relay within ~5 ms.')
    b.add(P('R40'), 6, 8); b.add(P('C40'), 6, 17); b.add(P('D40'), 13, 13); b.add(P('R41'), 19, 13, 90); b.add(P('R42'), 23, 20)
    b.add(P('Q32'), 30, 19); b.add(P('Q33'), 36, 24); b.add(P('R43'), 33, 28)
    b.add(P('K1'), 46, 11); b.add(P('R44'), 44, 3); b.add(P('D41'), 36, 11, 270); b.add(P('R49'), 12, 23)
    b = d.block('AC-loss detector', 116, 44, 56, 24, 'While AC is present Q36 holds Q35 off. Mains off: C41 decays in ~30 ms,\nQ35 dumps C40, relay opens, chips mute.')
    b.add(P('D42'), 7, 6, 180); b.add(P('R45'), 13, 6, 90); b.add(P('C41'), 18, 11); b.add(P('R46'), 22, 11)
    b.add(P('R47'), 27, 6, 90); b.add(P('Q36'), 34, 8); b.add(P('R48'), 39, 3); b.add(P('Q35'), 44, 8)
    b = d.block('DC-fault detectors (each output, either polarity)', 116, 72, 56, 50,
                'Output low-passed by 47k/47uF NP. > +1.3 V turns on Q37/Q39, < -1.3 V turns on Q38/Q40;\nboth dump TD. A 25 Vpk 30 Hz bass note leaves only 66 mV: no false trip.')
    for (oy, ra, ca, da, qa, qb) in ((0, 50, 'C50', 50, 'Q37', 'Q38'), (22, 60, 'C60', 60, 'Q39', 'Q40')):
        b.add(P(f'R{ra+1}'), 7, 5 + oy, 90); b.add(P(ca), 11, 10 + oy)
        b.add(P(f'R{ra+2}'), 17, 5 + oy, 90); b.add(P(f'D{da}'), 23, 5 + oy, 180); b.add(P(f'R{ra+5}'), 27, 9 + oy)
        b.add(P(qa), 33, 5 + oy)
        b.add(P(f'R{ra+3}'), 17, 14 + oy, 90); b.add(P(f'D{da+1}'), 23, 14 + oy)
        b.add(P(qb), 33, 16 + oy, mirror='x'); b.add(P(f'R{ra+4}'), 28, 20 + oy)
    b = d.block('Mute driver', 176, 6, 40, 34, 'Relay energised (COILN low) -> Q41 -> Q30 on ->\n~1.3 mA out of each MUTE pin = play.')
    b.add(P('R71'), 7, 8, 90); b.add(P('R72'), 13, 4, 180); b.add(P('Q41'), 19, 8, mirror='x')
    b.add(P('R73'), 20, 15); b.add(P('R74'), 15, 24); b.add(P('Q30'), 26, 20)
    b = d.block('POWER clip indicator', 176, 44, 46, 30, 'Peak detector on both bridge halves; lights at ~21 V peak.')
    b.add(P('R81'), 7, 5, 90); b.add(P('D81'), 13, 5, 180); b.add(P('R82'), 7, 10, 90); b.add(P('D82'), 13, 10, 180)
    b.add(P('C81'), 18, 15); b.add(P('R83'), 22, 15); b.add(P('D83'), 25, 5); b.add(P('R84'), 31, 5, 90)
    b.add(P('R85'), 35, 10); b.add(P('Q81'), 40, 7); b.add(P('R86'), 41, 1)
    d.rails = {'VCC': 'power:+28V', 'VEE': 'bassamp:-28V', 'GND': 'power:GND'}
    d.flags = [('VCC', 10, 54), ('VEE', 16, 54), ('GND', 22, 54)]
    return d

if __name__ == '__main__':
    import kdraw; kdraw.write_local_lib()
    print('\n'.join(build().write('../poweramp/poweramp.kicad_sch')) or 'all nets wired')
