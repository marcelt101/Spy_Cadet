"""PSU board: +/-28 V unregulated (T1), +/-41.6 V discrete regulated HV (T2),
+/-14.8 V discrete regulated (from the +/-28 V rails)."""
from kgen import Sheet
from parts import *

def build():
    s = Sheet('psu', 'Bass amp PSU board: +/-28 V, +/-40 V (discrete reg), +/-15 V (discrete reg)', rev='1',
              comments=['Mains wiring (IEC inlet, fuse T3.15A/230V or T6.3A/115V, switch, 5 R NTC) is chassis-wired, not on this board.',
                        'T1: 400 VA toroid 2 x 20 VAC. T2: 15-30 VA 2 x 40 VAC. Centre taps go to GND (star point = C1-C4 junction).',
                        'BR1: GBJ2506 (25 A) - check the footprint against your part; give it a small heatsink.',
                        'Q12/Q15 (MJE340/MJE350) and Q2/Q5 (BD139/BD140) need small clip-on heatsinks.'])
    b = s.block('Main rails +/-28 V (T1)', 'Star ground: GND net meets at the C1-C4 junction. Heavy tracks / wires to the power amp board.')
    b += [CONN('J1', 'T1 SEC 20-0-20 VAC', ['T1A', 'GND', 'T1B'], fp=FP['TB3']),
          Part('BR1', 'Device:D_Bridge_+AA-', 'GBJ2506', FP['GBJ'], {'1': 'VCC', '2': 'T1A', '3': 'T1B', '4': 'VEE'}),
          CP('C1', '10000u 50V', 'VCC', 'GND', 'CP30'), CP('C2', '10000u 50V', 'VCC', 'GND', 'CP30'),
          CP('C3', '10000u 50V', 'GND', 'VEE', 'CP30'), CP('C4', '10000u 50V', 'GND', 'VEE', 'CP30'),
          C('C5', '1u 100V film', 'VCC', 'GND', 'CF2'), C('C6', '1u 100V film', 'GND', 'VEE', 'CF2'),
          R('R1', '4k7 0.5W', 'VCC', 'GND', 'R05'), R('R2', '4k7 0.5W', 'GND', 'VEE', 'R05'),
          CONN('J2', 'TO POWER AMP +28/GND/-28', ['VCC', 'GND', 'VEE'], fp=FP['TB3']),
          CONN('J3', 'AC SENSE to power amp', ['T1A', 'GND'])]

    b = s.block('+15 V regulator (from +28 V)', 'Ref: 16 V zener, RC-filtered. Darlington Q1/Q2. Q3 limits at ~240 mA. Output ~ +14.8 V.')
    b += [R('R11', '10 1W', 'VCC', 'P15R', 'R05'), CP('C11', '1000u 50V', 'P15R', 'GND', 'CP12'),
          R('R12', '2k2', 'P15R', 'P15Z'), DZ('D11', '1N4745A 16V', 'GND', 'P15Z', 'DO41'), R('R13', '1k', 'P15Z', 'P15F'),
          CP('C12', '100u 25V', 'P15F', 'GND', 'CP6'), R('R14', '1k', 'P15F', 'Q1B'),
          MPSA42('Q1', 'P15R', 'Q1B', 'Q2B'), BD139('Q2', 'P15R', 'Q2B', 'P15E'), R('R15', '2R7', 'P15E', '+15V'),
          MPSA42('Q3', 'Q1B', 'P15E', '+15V'), CP('C13', '100u 25V', '+15V', 'GND', 'CP6'), C('C14', '100n', '+15V', 'GND'),
          R('R16', '4k7', '+15V', 'GND')]
    b = s.block('-15 V regulator (from -28 V)', 'Mirror of the +15 V regulator.')
    b += [R('R21', '10 1W', 'N15R', 'VEE', 'R05'), CP('C21', '1000u 50V', 'GND', 'N15R', 'CP12'),
          R('R22', '2k2', 'N15Z', 'N15R'), DZ('D21', '1N4745A 16V', 'N15Z', 'GND', 'DO41'), R('R23', '1k', 'N15Z', 'N15F'),
          CP('C22', '100u 25V', 'GND', 'N15F', 'CP6'), R('R24', '1k', 'N15F', 'Q4B'),
          MPSA92('Q4', 'N15R', 'Q4B', 'Q5B'), BD140('Q5', 'N15R', 'Q5B', 'N15E'), R('R25', '2R7', 'N15E', '-15V'),
          MPSA92('Q6', 'Q4B', 'N15E', '-15V'), CP('C23', '100u 25V', 'GND', '-15V', 'CP6'), C('C24', '100n', 'GND', '-15V'),
          R('R26', '4k7', '-15V', 'GND'),
          CONN('J4', 'TO PREAMP +15/GND/-15', ['+15V', 'GND', '-15V'])]

    b = s.block('HV raw supply (T2)', '1N4007 bridge, 1000 uF 100 V per rail: ~ +/-55 V raw.')
    b += [CONN('J5', 'T2 SEC 40-0-40 VAC', ['T2A', 'GND', 'T2B'], fp=FP['TB3']),
          D('D31', '1N4007', 'T2A', 'HV_PR', 'DO41'), D('D32', '1N4007', 'T2B', 'HV_PR', 'DO41'),
          D('D33', '1N4007', 'HV_NR', 'T2A', 'DO41'), D('D34', '1N4007', 'HV_NR', 'T2B', 'DO41'),
          CP('C31', '1000u 100V', 'HV_PR', 'GND', 'CP16'), CP('C32', '1000u 100V', 'GND', 'HV_NR', 'CP16'),
          C('C33', '100n 250V', 'HV_PR', 'GND'), C('C34', '100n 250V', 'GND', 'HV_NR')]
    b = s.block('+40 V regulator (discrete)', '43 V zener ref, RC soft start, MPSA42 + MJE340 Darlington, Q13 limits at ~55 mA. Output ~ +41.6 V.')
    b += [R('R31', '4k7 0.5W', 'HV_PR', 'HPZ', 'R05'), DZ('D35', '1N4755A 43V', 'GND', 'HPZ', 'DO41'), R('R32', '10k', 'HPZ', 'HPF'),
          CP('C35', '100u 63V', 'HPF', 'GND', 'CP8'), R('R33', '1k', 'HPF', 'Q11B'),
          MPSA42('Q11', 'HV_PR', 'Q11B', 'Q12B'), NPN_ECB('Q12', 'MJE340', 'HV_PR', 'Q12B', 'HPE'), R('R34', '12', 'HPE', '+40V'),
          MPSA42('Q13', 'Q11B', 'HPE', '+40V'), CP('C36', '100u 63V', '+40V', 'GND', 'CP8'), C('C37', '100n 100V', '+40V', 'GND'),
          R('R35', '10k 0.5W', '+40V', 'GND', 'R05')]
    b = s.block('-40 V regulator (discrete)', 'Mirror: MPSA92 + MJE350. Output ~ -41.6 V.')
    b += [R('R41', '4k7 0.5W', 'HNZ', 'HV_NR', 'R05'), DZ('D45', '1N4755A 43V', 'HNZ', 'GND', 'DO41'), R('R42', '10k', 'HNZ', 'HNF'),
          CP('C45', '100u 63V', 'GND', 'HNF', 'CP8'), R('R43', '1k', 'HNF', 'Q14B'),
          MPSA92('Q14', 'HV_NR', 'Q14B', 'Q15B'), PNP_ECB('Q15', 'MJE350', 'HV_NR', 'Q15B', 'HNE'), R('R44', '12', 'HNE', '-40V'),
          MPSA92('Q16', 'Q14B', 'HNE', '-40V'), CP('C46', '100u 63V', 'GND', '-40V', 'CP8'), C('C47', '100n 100V', 'GND', '-40V'),
          R('R45', '10k 0.5W', '-40V', 'GND', 'R05'),
          CONN('J6', 'TO PREAMP +40/GND/GND/-40', ['+40V', 'GND', 'GND', '-40V'])]
    s.flags = ['GND']
    return s

if __name__ == '__main__':
    build().write('../psu/psu.kicad_sch', cols=6)
