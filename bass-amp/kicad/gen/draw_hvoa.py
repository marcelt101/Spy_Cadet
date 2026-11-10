"""Hand-placed drawing of the HVOA-1 module (parts and nets from board_hvoa.py)."""
from kdraw import Drawing
import board_hvoa

def build():
    src = {p.ref: p for p in board_hvoa.build().all_parts()}
    d = Drawing('hvoa_module', 'HVOA-1 +/-40 V nested-cascode discrete op-amp module', paper='A3',
                comments=['Build twice: A1 (instrument input) and A2 (FX return). Values marked "x / A2: y" differ.',
                          'Topology identical to bass-amp/sim/hvoa.sub (checked by gen/build_all.py).',
                          'Match Q1/Q2 and Q5/Q6 and glue each pair together. D105/D106 touch Q11/Q12.',
                          'All TO-92 parts E-B-C (2N5087, 2N5210, MPSA42, MPSA92).'])
    P = lambda r: src[r]
    b = d.block('Connector and rail filter', 4, 6, 26, 30, 'J1 plugs into the 6-pin socket on the preamp.')
    b.add(P('J1'), 22, 9)
    b.add(P('R1'), 12, 7, 90); b.add(P('R2'), 12, 13, 90)
    b.add(P('C1'), 3, 17); b.add(P('C2'), 9, 17); b.add(P('C3'), 15, 17); b.add(P('C4'), 21, 17)

    m = d.block('HVOA-1 circuit', 34, 6, 120, 92,
                'Q1/Q2 input pair runs at Vce ~4.7 V whatever the common mode: D103 bootstraps the Q3/Q4 cascode bases to TAIL.\n'
                'Q9 cascodes the 2N5210 VAS (Vce ~2 V). Q13/Q14 limit output current to ~11 mA, Q15 limits the VAS to ~6 mA.')
    # references
    m.add(P('D101'), 6, 10, 90); m.add(P('C101'), 14, 10); m.add(P('R101'), 6, 18)
    m.add(P('D102'), 6, 78, 90); m.add(P('C102'), 14, 78); m.add(P('R102'), 6, 70)
    # tail source and input pair
    m.add(P('R103'), 31, 9); m.add(P('Q103'), 30, 16, mirror='x')
    m.add(P('R104'), 27, 24); m.add(P('R105'), 35, 24)
    m.add(P('Q1'), 24, 31, mirror='x'); m.add(P('Q2'), 38, 31, 180)
    m.add(P('D103'), 46, 26, 270); m.add(P('C103'), 56, 26)
    m.add(P('Q3'), 27, 42, 180); m.add(P('Q4'), 36, 42, mirror='x')
    m.add(P('Q104'), 49, 52); m.add(P('R106'), 50, 60)
    # mirror
    m.add(P('Q5'), 26, 58, mirror='y'); m.add(P('Q6'), 36, 58)
    m.add(P('R107'), 25, 66); m.add(P('R108'), 37, 66)
    # VAS
    m.add(P('Q7'), 60, 50); m.add(P('R110'), 61, 66)
    m.add(P('Q8'), 70, 58); m.add(P('R111'), 71, 66); m.add(P('Q15'), 66, 74)
    m.add(P('Q9'), 70, 46); m.add(P('R109'), 82, 40); m.add(P('D104'), 80, 52, 90); m.add(P('C104'), 92, 52)
    m.add(P('R112'), 71, 9); m.add(P('Q105'), 70, 16, mirror='x')
    m.add(P('CC1'), 60, 38, 90)
    # bias chain and output
    m.add(P('D105'), 71, 24, 90); m.add(P('D106'), 71, 29, 90); m.add(P('R113'), 71, 34)
    m.add(P('Q11'), 94, 22); m.add(P('R114'), 95, 30)
    m.add(P('Q12'), 94, 46, mirror='x'); m.add(P('R115'), 95, 38)
    m.add(P('Q13'), 104, 30); m.add(P('Q14'), 104, 38, mirror='x')
    d.rails = {'VP': 'bassamp:+40V', 'VN': 'bassamp:-40V', 'GND': 'power:GND'}
    d.flags = [('VP_IN', 8, 30), ('VN_IN', 14, 30), ('GND', 20, 30)]
    return d

if __name__ == '__main__':
    import kdraw; kdraw.write_local_lib()
    rep = build().write('../hvoa_module/hvoa_module.kicad_sch')
    print('\n'.join(rep) or 'all nets wired')
