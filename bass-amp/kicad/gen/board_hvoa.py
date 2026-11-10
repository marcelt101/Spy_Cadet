"""HVOA-1 daughterboard: +/-40 V nested-cascode discrete op-amp (sim/hvoa.sub)."""
from kgen import Sheet
from parts import *
import netnames

def build():
    s = Sheet('hvoa_module', 'HVOA-1 +/-40 V nested-cascode discrete op-amp module', rev='1',
              comments=['Build twice: A1 (instrument input) and A2 (FX return). Parts marked "A1 / A2" differ.',
                        'Netlist identical to sim/hvoa.sub (checked by kicad/gen/build_all.py).',
                        'Match Q1/Q2 (Vbe 2 mV, hFE 10 %) and Q5/Q6; glue each pair together. D105/D106 touch Q11/Q12.',
                        'All TO-92 parts are E-B-C pinout (2N5087, 2N5210, MPSA42, MPSA92).'])
    b = s.block('Connector and rail filter', 'J1 mates with the 6-pin socket on the preamp board.')
    b += [CONN('J1', 'HVOA_IF', ['VP_IN', 'GND', 'VN_IN', 'OUT', 'INN', 'INP'], fp=FP['HDR6']),
          R('R1', '10', 'VP_IN', 'VP'), CP('C1', '100u 63V', 'VP', 'GND', 'CP8'), C('C2', '100n 100V', 'VP', 'GND'),
          R('R2', '10', 'VN_IN', 'VN'), CP('C3', '100u 63V', 'GND', 'VN', 'CP8'), C('C4', '100n 100V', 'GND', 'VN')]
    b = s.block('References (red LEDs ~1.7 V)')
    b += [LED('D101', 'red 3mm', 'VP', 'REFP'), R('R101', '39k', 'REFP', 'GND'), CP('C101', '10u 63V', 'VP', 'REFP', 'CP5'),
          LED('D102', 'red 3mm', 'REFN', 'VN'), R('R102', '39k', 'GND', 'REFN'), CP('C102', '10u 63V', 'REFN', 'VN', 'CP5')]
    b = s.block('Input pair 2N5087 with bootstrapped MPSA92 cascode',
                'D103 holds the cascode bases 5.6 V below TAIL: Vce(Q1,Q2) ~ 4.7 V at any common mode.')
    b += [MPSA92('Q103', 'TAIL', 'REFP', 'E103'), R('R103', '3k0 / A2: 820', 'VP', 'E103'),
          R('R104', '1k / A2: 470', 'TAIL', 'E1'), R('R105', '1k / A2: 470', 'TAIL', 'E2'),
          PNP('Q1', '2N5087', 'C1', 'INN', 'E1'), PNP('Q2', '2N5087', 'C2', 'INP', 'E2'),
          DZ('D103', '1N5232B 5V6', 'CASB', 'TAIL'), C('C103', '100n', 'TAIL', 'CASB'),
          MPSA42('Q104', 'CASB', 'REFN', 'E104'), R('R106', '10k / A2: 3k3', 'E104', 'VN'),
          MPSA92('Q3', 'M1', 'CASB', 'C1'), MPSA92('Q4', 'M2', 'CASB', 'C2')]
    b = s.block('Current mirror 2N5210')
    b += [NPN('Q5', '2N5210', 'M1', 'M1', 'E5'), NPN('Q6', '2N5210', 'M2', 'M1', 'E6'),
          R('R107', '1k', 'E5', 'VN'), R('R108', '1k', 'E6', 'VN')]
    b = s.block('VAS: MPSA42 follower, 2N5210 VAS, MPSA42 cascode, MPSA92 load',
                'CC: C0G ceramic or silver mica, >= 100 V.')
    b += [DZ('D104', '1N5226B 3V3', 'VN', 'VCR'), R('R109', '33k', 'GND', 'VCR'), CP('C104', '10u 16V', 'VCR', 'VN', 'CP5'),
          MPSA42('Q7', 'GND', 'M2', 'V7'), R('R110', '22k', 'V7', 'VN'),
          NPN('Q8', '2N5210', 'V8', 'V7', 'E8'), R('R111', '100', 'E8', 'VN'), NPN('Q15', '2N5210', 'V7', 'E8', 'VN'),
          MPSA42('Q9', 'VASL', 'VCR', 'V8'),
          MPSA92('Q105', 'VASH', 'REFP', 'E105'), R('R112', '270', 'VP', 'E105'),
          C('CC1', '68p / A2: 150p', 'VASL', 'M2', 'CC')]
    b = s.block('Output stage (2 mA idle, 11 mA limit)')
    b += [D('D105', '1N4148', 'VASH', 'B1'), D('D106', '1N4148', 'B1', 'B2'), R('R113', '100', 'B2', 'VASL'),
          MPSA42('Q11', 'VP', 'VASH', 'E11'), MPSA92('Q12', 'VN', 'VASL', 'E12'),
          R('R114', '56', 'E11', 'OUT'), R('R115', '56', 'E12', 'OUT'),
          MPSA42('Q13', 'VASH', 'E11', 'OUT'), MPSA92('Q14', 'VASL', 'E12', 'OUT')]
    s.flags = ['VP_IN', 'VN_IN', 'GND']
    return netnames.apply(s, netnames.HVOA)

if __name__ == '__main__':
    build().write('../hvoa_module/hvoa_module.kicad_sch', cols=5)
