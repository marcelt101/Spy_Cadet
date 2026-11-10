"""Hand-placed drawing of the PSU board (parts and nets from board_psu.py)."""
from kdraw import Drawing
import netnames
import board_psu

def reg(b, P, refs, pos):
    """Lay out one discrete series regulator. refs: in order
    Rpre, Cpre, Rz, Dz, Rf, Cf, Rb, Qdrv, Qpass, Rsense, Qlim, Cout1, Cout2, Rload."""
    Rpre, Cpre, Rz, Dz, Rf, Cf, Rb, Q1, Q2, Rs, Q3, Co1, Co2, Rl = refs
    neg = not pos
    if Rpre: b.add(P(Rpre), 5, 5, 90)
    if Cpre: b.add(P(Cpre), 6, 13)
    b.add(P(Rz), 14, 10)
    b.add(P(Dz), 14, 18, 270 if pos else 90)
    b.add(P(Rf), 20, 14, 90)
    b.add(P(Cf), 24, 19)
    b.add(P(Rb), 29, 14, 90)
    b.add(P(Q1), 34, 14, mirror='x' if neg else None)
    b.add(P(Q2), 40, 19, mirror='x' if neg else None)
    b.add(P(Rs), 47, 21 if pos else 17, 90)
    b.add(P(Q3), 46, 27 if pos else 9, mirror='x' if neg else None)
    b.add(P(Co1), 53, 22); b.add(P(Co2), 59, 22); b.add(P(Rl), 65, 22)

def build():
    src = {p.ref: p for p in board_psu.build().all_parts()}
    P = lambda r: src[r]
    d = Drawing('psu', 'Bass amp PSU board: +/-28 V, +/-40 V (discrete reg), +/-15 V (discrete reg)', paper='A2',
                comments=['Mains wiring (IEC inlet, fuse T3.15A/230V or T6.3A/115V, switch, 5 R NTC) is chassis-wired, not on this board.',
                          'T1: 400 VA toroid 2 x 20 VAC. T2: 15-30 VA 2 x 40 VAC. Centre taps to GND; star point = C1-C4 junction.',
                          'BR1: GBJ2506 25 A - check the footprint pitch against your part; small heatsink.',
                          'Q12/Q15 (MJE340/MJE350) and Q2/Q5 (BD139/BD140) need small clip-on heatsinks.'])
    b = d.block('Main rails +/-28 V (T1, 400 VA, 2 x 20 VAC)', 4, 6, 76, 40,
                'Heavy tracks. J2 -> power amp board (>= 1 mm2 wire). J3 = AC sense for the speaker-protection circuit.')
    b.add(P('J1'), 6, 14, mirror='y'); b.add(P('BR1'), 22, 14)
    for i, r in enumerate(['C1', 'C2', 'C5', 'R1']): b.add(P(r), 30 + 8 * i, 11)
    for i, r in enumerate(['C3', 'C4', 'C6', 'R2']): b.add(P(r), 30 + 8 * i, 24)
    b.add(P('J2'), 70, 16); b.add(P('J3'), 12, 30, mirror='y')

    b = d.block('+15 V regulator (fed from +28 V)', 4, 50, 76, 34, '16 V zener reference, RC filtered; Q3 limits at ~240 mA. Output ~ +14.8 V.')
    reg(b, P, ['R11', 'C11', 'R12', 'D11', 'R13', 'C12', 'R14', 'Q1', 'Q2', 'R15', 'Q3', 'C13', 'C14', 'R16'], True)
    b = d.block('-15 V regulator (fed from -28 V)', 4, 88, 76, 34, 'Mirror of the +15 V regulator. J4 -> preamp J1.')
    reg(b, P, ['R21', 'C21', 'R22', 'D21', 'R23', 'C22', 'R24', 'Q4', 'Q5', 'R25', 'Q6', 'C23', 'C24', 'R26'], False)
    b.add(P('J4'), 70, 8)

    b = d.block('HV raw supply (T2, 2 x 40 VAC)', 84, 6, 76, 40, '1N4007 bridge, 1000 uF 100 V per rail: about +/-55 V raw.')
    b.add(P('J5'), 5, 16, mirror='y')
    b.add(P('D31'), 16, 8, 180); b.add(P('D32'), 16, 13, 180)
    b.add(P('D33'), 16, 19); b.add(P('D34'), 16, 24)
    b.add(P('C31'), 30, 11); b.add(P('C33'), 38, 11); b.add(P('C32'), 30, 26); b.add(P('C34'), 38, 26)
    b = d.block('+40 V regulator (discrete)', 84, 50, 76, 34, '43 V zener reference, RC soft start, MPSA42 + MJE340 Darlington, Q13 limits at ~55 mA. Output ~ +41.6 V.')
    reg(b, P, [None, None, 'R31', 'D35', 'R32', 'C35', 'R33', 'Q11', 'Q12', 'R34', 'Q13', 'C36', 'C37', 'R35'], True)
    b = d.block('-40 V regulator (discrete)', 84, 88, 76, 34, 'Mirror: MPSA92 + MJE350. Output ~ -41.6 V. J6 -> preamp J2.')
    reg(b, P, [None, None, 'R41', 'D45', 'R42', 'C45', 'R43', 'Q14', 'Q15', 'R44', 'Q16', 'C46', 'C47', 'R45'], False)
    b.add(P('J6'), 70, 8)
    d.rails = {n: netnames.RAIL_SYMBOL[n] for n in netnames.RAIL_SYMBOL if n in {x for q in src.values() for x in q.conn.values()}}
    d.named = set(netnames.PSU.values()) - set(d.rails)
    d.flags = [('GND', 50, 42)]
    return d

if __name__ == '__main__':
    import kdraw; kdraw.write_local_lib()
    print('\n'.join(build().write('../psu/psu.kicad_sch')) or 'all nets wired')
