"""Power amp board: 2 x LM3886T bridged, Zobels, output coils, speaker relay with
turn-on delay / AC-loss / DC-fault protection, mute driver, POWER clip LED."""
from kgen import Sheet
from parts import *

def chip(s, u, side, inp, n0):
    """One LM3886 half of the bridge. side = 'A' or 'B'."""
    p = side
    b = s.block(f'LM3886 {side} ({"non-inverted" if side == "A" else "inverted"} half)',
                'Gain 1 + 20k/1k = 21. Tab = V- : insulate from the heatsink. Gain resistors 1 % (match A to B).')
    b += [Part(u, 'Amplifier_Audio:LM3886', 'LM3886T', FP['LM3886'],
               {'1': 'VCC', '5': 'VCC', '4': 'VEE', '7': 'GND', '8': f'{p}_MUTE', '9': f'{p}_N', '10': f'{p}_P', '3': f'{p}_OUT',
                '2': None, '6': None, '11': None}),
          C(f'C{n0+1}', '2u2 63V film', inp, f'{p}_IN1', 'CF2'), R(f'R{n0+1}', '1k', f'{p}_IN1', f'{p}_P'),
          C(f'C{n0+2}', '220p C0G', f'{p}_P', 'GND', 'CC'), R(f'R{n0+2}', '22k', f'{p}_P', 'GND'),
          R(f'R{n0+3}', '20k 1%', f'{p}_OUT', f'{p}_N'), R(f'R{n0+4}', '1k 1%', f'{p}_N', f'{p}_G'),
          C(f'C{n0+3}', '220u 25V NP', f'{p}_G', 'GND', 'CP10'),
          CP(f'C{n0+4}', '220u 50V', 'VCC', 'GND', 'CP10'), C(f'C{n0+5}', '100n 100V', 'VCC', 'GND'),
          CP(f'C{n0+6}', '220u 50V', 'GND', 'VEE', 'CP10'), C(f'C{n0+7}', '100n 100V', 'GND', 'VEE'),
          R(f'R{n0+5}', '2R7 2W', f'{p}_OUT', f'{p}_Z', 'R2W'), C(f'C{n0+8}', '100n 100V', f'{p}_Z', 'GND'),
          L(f'L{1 if p == "A" else 2}', '0.7uH air', f'{p}_OUT', f'{p}_SPK'), R(f'R{n0+6}', '10 2W', f'{p}_OUT', f'{p}_SPK', 'R2W'),
          R(f'R{n0+7}', '20k', f'{p}_MUTE', 'MUTE_N')]

def build():
    s = Sheet('poweramp', 'Bass amp power amplifier: 2 x LM3886T bridged (BTL), protection', rev='1',
              comments=['BRIDGED OUTPUT: neither speaker terminal is ground. Use a Speakon NL4 (1+ = SPK+, 1- = SPK-).',
                        'Rails +/-28 V from the PSU board with heavy wire. Star ground at the PSU reservoir caps.',
                        'Heatsink <= 0.4 C/W (or <= 0.7 C/W + fan). LM3886T tab is V-.',
                        'J5 goes to the phones jack NC switch (opens = speaker muted). Fit a jumper if unused.'])
    b = s.block('Connectors', 'J1 rails (screw terminal). J2 signal from preamp J15. J3 speaker. J4 AC sense from one 20 VAC winding of T1.')
    b += [CONN('J1', 'RAILS +28/GND/-28', ['VCC', 'GND', 'VEE'], fp=FP['TB3']),
          CONN('J2', 'SIGNAL IN', ['SUB', 'GND', 'SUB_INV']),
          CONN('J3', 'SPEAKER', ['SPK_P', 'B_SPK'], fp=FP['TB2']),
          CONN('J4', 'AC SENSE', ['AC_IN', 'GND']),
          CONN('J5', 'PHONES MUTE SW', ['MUTE_N', 'MUTE_SW']),
          CONN('J6', 'POWER CLIP LED', ['PLEDA', 'PLEDK'])]
    chip(s, 'U1', 'A', 'SUB', 0)
    chip(s, 'U2', 'B', 'SUB_INV', 10)

    b = s.block('Speaker relay with ~3.5 s turn-on delay',
                'T charges via R40/C40; D40 (12 V) + Darlington Q32/Q33 pull in K1 at ~13.6 V. Anything pulling TD low drops the relay within ~5 ms.')
    b += [Part('K1', 'Relay:G5LE-1', 'G5LE-1 24VDC', FP['RELAY'], {'1': 'A_SPK', '3': 'SPK_P', '4': None, '2': 'COILN', '5': 'COILP'}),
          R('R40', '100k', 'VCC', 'T'), CP('C40', '47u 35V', 'T', 'GND', 'CP6'), DZ('D40', '1N4742A 12V', 'TZ', 'T'),
          R('R41', '10k', 'TZ', 'DB'), R('R42', '47k', 'DB', 'GND'),
          MPSA42('Q32', 'COILN', 'DB', 'Q33B'), BD139('Q33', 'COILN', 'Q33B', 'GND'), R('R43', '10k', 'Q33B', 'GND'),
          R('R44', '220 0.5W', 'VCC', 'COILP', 'R05'), D('D41', '1N4007', 'COILN', 'COILP', 'DO41'),
          R('R49', '100', 'T', 'TD')]

    b = s.block('AC-loss detector', 'While AC is present Q36 holds Q35 off. Mains off: C41 decays in ~30 ms, Q35 dumps C40, relay opens, chips mute.')
    b += [D('D42', '1N4148', 'AC_IN', 'AC1'), R('R45', '22k', 'AC1', 'ACA'), CP('C41', '1u 50V', 'ACA', 'GND', 'CP5'),
          R('R46', '47k', 'ACA', 'GND'), R('R47', '100k', 'ACA', 'Q36B'),
          NPN('Q36', '2N5210', 'Q35B', 'Q36B', 'GND'), R('R48', '47k', 'VCC', 'Q35B'), NPN('Q35', '2N5210', 'TD', 'Q35B', 'GND')]

    b = s.block('DC-fault detectors (one per output, either polarity)',
                'Each output low-passed by 47k/47uF (bipolar). > +1.3 V turns on Q37/Q39, < -1.3 V turns on Q38/Q40; both dump TD.')
    for side, n, qa, qb in (('A', 50, 'Q37', 'Q38'), ('B', 60, 'Q39', 'Q40')):
        b += [R(f'R{n+1}', '47k', f'{side}_OUT', f'DC{side}'), C(f'C{n}', '47u 50V NP', f'DC{side}', 'GND', 'CP8'),
              R(f'R{n+2}', '10k', f'DC{side}', f'{qa}R'), D(f'D{n}', '1N4148', f'{qa}R', f'{qa}B'),
              R(f'R{n+5}', '47k', f'{qa}B', 'GND'),
              NPN(qa, '2N5210', 'TD', f'{qa}B', 'GND'),
              R(f'R{n+3}', '1k', f'DC{side}', f'DC{side}2'), D(f'D{n+1}', '1N4148', f'{qb}E', f'DC{side}2'),
              R(f'R{n+4}', '10k', f'{qb}B', 'GND'), NPN(qb, '2N5210', 'TD', f'{qb}B', f'{qb}E')]

    b = s.block('Mute driver', 'Relay energised (COILN low) -> Q41 on -> Q30 on -> ~1.3 mA out of each MUTE pin = play. Otherwise muted.')
    b += [R('R71', '100k', 'COILN', 'Q41B'), R('R72', '100k', 'Q41B', 'VCC'), MPSA92('Q41', 'Q41C', 'Q41B', 'VCC'),
          R('R73', '47k', 'Q41C', 'Q30B'), R('R74', '47k', 'Q30B', 'VEE'), MPSA42('Q30', 'MUTE_SW', 'Q30B', 'VEE')]

    b = s.block('POWER clip indicator', 'Peak detector on both bridge halves; lights at ~21 V peak per side.')
    b += [R('R81', '4k7', 'A_OUT', 'PCA'), D('D81', '1N4148', 'PCA', 'PCP'), R('R82', '4k7', 'B_OUT', 'PCB'), D('D82', '1N4148', 'PCB', 'PCP'),
          CP('C81', '1u 50V', 'PCP', 'GND', 'CP5'), R('R83', '220k', 'PCP', 'GND'), DZ('D83', '1N4747A 20V', 'PCZ', 'PCP'),
          R('R84', '10k', 'PCZ', 'PQB'), R('R85', '10k', 'PQB', 'GND'), NPN('Q81', '2N5210', 'PLEDK', 'PQB', 'GND'),
          R('R86', '2k7', 'VCC', 'PLEDA')]
    s.flags = ['VCC', 'VEE', 'GND']
    return s

if __name__ == '__main__':
    build().write('../poweramp/poweramp.kicad_sch', cols=6)
