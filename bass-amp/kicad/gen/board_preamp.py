"""Preamp board: sockets for the two HVOA modules, input/return networks, 3-band EQ,
FX loop, master/aux, subsonic filter, BTL phase splitter, phones, balanced DI, PRE clip."""
from kgen import Sheet
from parts import *

def module_socket(ref, name, out, inn, inp):
    return CONN(ref, f'{name} (HVOA-1 socket)', ['+40V', 'GND', '-40V', out, inn, inp], fp=FP['SKT6'])

def build():
    s = Sheet('preamp', 'Bass amp preamp board (HV front end, EQ, I/O)', rev='1',
              comments=['Pots are PCB-mounted Alpha 16 mm (pin 3 = CW end). Jacks and switches are panel-mounted, wired to JST-XH headers.',
                        'A1/A2 are HVOA-1 daughterboards (hvoa_module project) plugged into J20/J21.',
                        'Keep the +/-40 V traces away from the NE5532 area; every HV output enters the 15 V domain AC-coupled or clamped.',
                        'Bipolar (NP) electrolytics use the CP footprint; orientation does not matter for them.'])

    b = s.block('Power input and decoupling', 'J1: +/-15 V from PSU (3-pin). J2: +/-40 V from PSU (4-pin, different size so they cannot be swapped).')
    b += [CONN('J1', 'PWR_15V', ['+15V', 'GND', '-15V']), CONN('J2', 'PWR_HV', ['+40V', 'GND', 'GND', '-40V']),
          CP('C201', '47u 25V', '+15V', 'GND', 'CP6'), CP('C202', '47u 25V', 'GND', '-15V', 'CP6'),
          CP('C203', '100u 63V', '+40V', 'GND', 'CP8'), CP('C204', '100u 63V', 'GND', '-40V', 'CP8')]
    for i, u in enumerate(['U1', 'U2', 'U3', 'U4', 'U5', 'U6']):
        b += [NE5532(u, 3, vp='+15V', vn='-15V'),
              C(f'C{211 + 2 * i}', '100n', '+15V', 'GND'), C(f'C{212 + 2 * i}', '100n', 'GND', '-15V')]

    b = s.block('A1: bootstrapped instrument input / gain (+1.7 .. +27 dB)',
                'RA (R2) bootstrapped by C3 from INN: >1 MOhm input. VR1 rheostat, gain rises CW. C2/C3: film, 100 V.')
    b += [CONN('J3', 'INPUT jack', ['IN_TIP', 'GND']),
          R('R1', '1k', 'IN_TIP', 'IN1'), C('C1', '100p C0G', 'IN1', 'GND', 'CC'), C('C2', '2u2 100V film', 'IN1', 'A1P', 'CF2'),
          R('R2', '1Meg', 'A1P', 'A1BS'), R('R3', '100k', 'A1BS', 'GND'), C('C3', '2u2 63V film', 'A1N', 'A1BS', 'CF2'),
          module_socket('J20', 'A1', 'A1OUT', 'A1N', 'A1P'),
          POT('VR1', 'GAIN 50k A', 'A1RF', 'A1OUT', 'A1OUT'), R('R4', '470', 'A1RF', 'A1N'), C('C4', '22p C0G', 'A1OUT', 'A1N', 'CC'),
          R('R5', '2k2', 'A1N', 'A1G'), CP('C5', '220u 16V', 'A1G', 'GND', 'CP8'),
          R('R6', '100', 'A1OUT', 'A1O'), C('C6', '4u7 63V film', 'A1O', 'PRE_AC', 'CF4'), R('R7', '100k', 'PRE_AC', 'GND')]

    b = s.block('EQ: Baxandall bass / treble (U1A)', 'CW = boost (wiper toward the input-side end).')
    b += [R('R11', '10k', 'PRE_AC', 'BA'), POT('VR2', 'BASS 50k B', 'BB', 'BW', 'BA'), R('R12', '10k', 'BB', 'O1'),
          C('C11', '47n', 'BA', 'BW'), C('C12', '47n', 'BW', 'BB'), R('R13', '4k7', 'BW', 'N1'),
          C('C13', '6n8', 'PRE_AC', 'TA'), POT('VR3', 'TREBLE 50k B', 'TB', 'TW', 'TA'), C('C14', '6n8', 'TB', 'O1'),
          R('R14', '1k8', 'TW', 'N1'), NE5532('U1', 1, plus='GND', minus='N1', out='O1')]

    b = s.block('EQ: mid, gyrator with 5-way frequency switch (U1B, U2A)',
                'J9 to a 2-pole rotary (pole A: MW -> Cs1..5, pole B: GP -> Cg1..5). 250/500/800/1.5k/3k Hz. Short shielded wiring.')
    b += [R('R15', '3k3', 'O1', 'P2'), NE5532('U1', 2, plus='P2', minus='M2', out='EQ_OUT'), R('R16', '3k3', 'EQ_OUT', 'M2'),
          POT('VR4', 'MID 10k B', 'P2', 'MW', 'M2'),
          R('R17', '100k', 'GP', 'GND'), NE5532('U2', 1, plus='GP', minus='GO', out='GO'), R('R18', '680', 'GO', 'X'),
          CONN('J9', 'MID FREQ switch', ['MW', 'SA1', 'SA2', 'SA3', 'SA4', 'SA5', 'GP', 'SB1', 'SB2', 'SB3', 'SB4', 'SB5'])]
    for i, (cs, cg) in enumerate([('220n', '27n'), ('100n', '15n'), ('68n', '8n2'), ('33n', '4n7'), ('18n', '2n2')]):
        b += [C(f'C{21 + i}', cs, 'X', f'SA{i + 1}', 'CF', note='Cs, 5 % film'), C(f'C{26 + i}', cg, 'X', f'SB{i + 1}', 'CF', note='Cg, 5 % film')]

    b = s.block('FX send (U2B) and FX return (A2, HV unity buffer)',
                'J5 is a switched jack: its switch lug (pin 2) carries EQ_OUT, so the loop is closed when nothing is plugged in.')
    b += [CONN('J10', 'SEND LEVEL sw', ['SND_C', 'EQ_OUT', 'SND10']), R('R31', '6k8', 'EQ_OUT', 'SND10'), R('R32', '3k3', 'SND10', 'GND'),
          R('R33', '100k', 'SND_C', 'GND'), NE5532('U2', 2, plus='SND_C', minus='SNDO', out='SNDO'),
          R('R34', '100', 'SNDO', 'SND1'), C('C31', '10u NP', 'SND1', 'SEND_TIP', 'CP6'), R('R35', '100k', 'SEND_TIP', 'GND'),
          CONN('J4', 'FX SEND jack', ['SEND_TIP', 'GND']),
          CONN('J5', 'FX RETURN jack', ['RET_TIP', 'EQ_OUT', 'GND']),
          R('R21', '1k', 'RET_TIP', 'IN2'), C('C41', '100p C0G', 'IN2', 'GND', 'CC'), C('C42', '2u2 100V film', 'IN2', 'A2P', 'CF2'),
          R('R22', '1Meg', 'A2P', 'A2BS'), R('R23', '100k', 'A2BS', 'GND'), C('C43', '2u2 63V film', 'A2OUT', 'A2BS', 'CF2'),
          module_socket('J21', 'A2', 'A2OUT', 'A2N', 'A2P'), R('R24', '1k', 'A2OUT', 'A2N'),
          R('R25', '100', 'A2OUT', 'A2O'), C('C44', '4u7 63V film', 'A2O', 'MV_TOP', 'CF4')]

    b = s.block('Master, aux in (U3A), subsonic filter (U6A), bridge phase splitter (U3B)',
                'J11 to a DPDT: closing both poles = TIGHT (~40 Hz); open = DEEP (22 Hz). J15 to the power amp board.')
    b += [POT('VR5', 'MASTER 10k A', 'GND', 'MV_W', 'MV_TOP'), R('R41', '10k', 'MV_W', 'MIXN'),
          CONN('J6', 'AUX IN jack', ['AUXL', 'AUXR', 'GND']),
          R('R44', '100k', 'AUXL', 'GND'), R('R45', '100k', 'AUXR', 'GND'),
          C('C45', '1u film', 'AUXL', 'AUXL1', 'CF1'), C('C46', '1u film', 'AUXR', 'AUXR1', 'CF1'),
          R('R42', '22k', 'AUXL1', 'MIXN'), R('R43', '22k', 'AUXR1', 'MIXN'),
          R('R46', '10k', 'MIX', 'MIXN'), C('C47', '47p C0G', 'MIX', 'MIXN', 'CC'), NE5532('U3', 1, plus='GND', minus='MIXN', out='MIX'),
          C('C51', '220n', 'MIX', 'SKJ'), C('C52', '220n', 'SKJ', 'SKP'),
          R('R61', '22k', 'SKJ', 'SUB'), R('R62', '27k', 'SKJ', 'STA'), R('R63', '47k', 'SKP', 'GND'), R('R64', '56k', 'SKP', 'STB'),
          CONN('J11', 'DEEP/TIGHT sw', ['STA', 'SUB', 'STB', 'GND']), NE5532('U6', 1, plus='SKP', minus='SUB', out='SUB'),
          NE5532('U6', 2, plus='GND', minus='U6BO', out='U6BO'),
          R('R65', '10k 0.1%', 'SUB', 'INVN'), R('R66', '10k 0.1%', 'SUB_INV', 'INVN'), NE5532('U3', 2, plus='GND', minus='INVN', out='SUB_INV'),
          CONN('J15', 'TO POWER AMP', ['SUB', 'GND', 'SUB_INV'])]

    b = s.block('Headphone amplifier (U4)', 'Phones jack switch contacts are wired to the power amp board (J5 there) to mute the speaker.')
    b += [NE5532('U4', 1, plus='MIX', minus='PHL', out='PHL'), R('R71', '47', 'PHL', 'PH_L', 'R05'),
          NE5532('U4', 2, plus='MIX', minus='PHR', out='PHR'), R('R72', '47', 'PHR', 'PH_R', 'R05'),
          CONN('J7', 'PHONES jack', ['PH_L', 'PH_R', 'GND'])]

    b = s.block('Balanced DI / line out (U5)',
                'J12: PRE/POST select. J13: closing it = -20 dB pad. J14: ground-lift switch. C81/C82 + toward the XLR (phantom).')
    b += [CONN('J12', 'DI PRE/POST sw', ['DI_SEL', 'PRE_AC', 'EQ_OUT']),
          R('R81', '2k2', 'DI_SEL', 'DI_CL'), D('D81', '1N4148', 'DI_CL', '+15V'), D('D82', '1N4148', '-15V', 'DI_CL'),
          R('R82', '10k', 'DI_CL', 'DI_IN'), R('R83', '1k1', 'DI_IN', 'PADSW'), CONN('J13', 'PAD sw', ['PADSW', 'GND']),
          NE5532('U5', 1, plus='DI_IN', minus='HOTO', out='HOTO'),
          R('R85', '10k', 'HOTO', 'COLDN'), R('R86', '10k', 'COLDO', 'COLDN'), NE5532('U5', 2, plus='GND', minus='COLDN', out='COLDO'),
          R('R87', '47', 'HOTO', 'H1'), D('D83', '1N4148', 'H1', '+15V'), D('D84', '1N4148', '-15V', 'H1'),
          CP('C81', '47u 63V', 'H2', 'H1', 'CP8'), R('R88', '10', 'H2', 'XLR_HOT'), R('R89', '100k', 'XLR_HOT', 'GND'),
          R('R90', '47', 'COLDO', 'K1N'), D('D85', '1N4148', 'K1N', '+15V'), D('D86', '1N4148', '-15V', 'K1N'),
          CP('C82', '47u 63V', 'K2N', 'K1N', 'CP8'), R('R91', '10', 'K2N', 'XLR_COLD'), R('R92', '100k', 'XLR_COLD', 'GND'),
          CONN('J8', 'XLR out (2 hot, 3 cold, 1)', ['XLR_HOT', 'XLR_COLD', 'XLR_P1']), CONN('J14', 'GND LIFT sw', ['XLR_P1', 'GND'])]

    b = s.block('PRE clip indicator', 'Lights at about +/-11.3 V peak (2.5 dB before the NE5532 stages clip). J16 to a panel LED.')
    b += [R('R93', '4k7', 'A1O', 'CLA'), D('D91', '1N4148', 'CLA', 'CLP'), R('R94', '4k7', 'O1', 'CLB'), D('D92', '1N4148', 'CLB', 'CLP'),
          CP('C91', '1u 50V', 'CLP', 'GND', 'CP5'), R('R95', '220k', 'CLP', 'GND'), DZ('D93', '1N4740A 10V', 'CLZ', 'CLP'),
          R('R96', '10k', 'CLZ', 'CLQB'), R('R97', '10k', 'CLQB', 'GND'), NPN('Q91', '2N5210', 'CLLK', 'CLQB', 'GND'),
          R('R98', '1k5', '+15V', 'CLLA'), CONN('J16', 'PRE CLIP LED', ['CLLA', 'CLLK'])]
    s.flags = ['+15V', '-15V', '+40V', '-40V', 'GND']
    return s

if __name__ == '__main__':
    build().write('../preamp/preamp.kicad_sch', cols=6)
