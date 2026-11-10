"""Engineer-facing net names. Conventions:
  rails          +40V  -40V  +28V  -28V  +15V  -15V  GND   (unfiltered: _RAW / _IN / _FILT)
  I/O            functional names (INST_IN, FX_SEND, LINE_OUT_HOT, SPK+ ...)
  differential   trailing + / -   (PA_DRIVE+, A1_IN-)
  active-low     ~{NAME}  (KiCad overbar notation)
Nets not listed keep KiCad's automatic Net-(Ref-Pad) names."""
HVOA = {
    'VP': '+40V', 'VN': '-40V', 'VP_IN': '+40V_IN', 'VN_IN': '-40V_IN',
    'INP': 'IN+', 'INN': 'IN-', 'OUT': 'OUT',
    'REFP': 'VREF_TOP', 'REFN': 'VREF_BOT', 'TAIL': 'LTP_TAIL', 'CASB': 'CASC_BIAS',
    'M2': 'VAS_IN', 'VCR': 'VAS_CASC_BIAS', 'VASH': 'OUT_BIAS_HI', 'VASL': 'VAS_OUT',
}
PREAMP = {
    'IN_TIP': 'INST_IN', 'A1P': 'A1_IN+', 'A1N': 'A1_IN-', 'A1OUT': 'A1_OUT', 'A1O': 'A1_OUT_ISO',
    'A1BS': 'A1_BOOTSTRAP', 'A1RF': 'A1_GAIN_POT', 'PRE_AC': 'PRE_EQ',
    'N1': 'TONE_SUM', 'O1': 'TONE_OUT', 'BW': 'BASS_WIPER', 'TW': 'TREBLE_WIPER',
    'P2': 'MID_IN+', 'M2': 'MID_IN-', 'EQ_OUT': 'EQ_OUT',
    'MW': 'MID_SW_A', 'GP': 'MID_SW_B', 'X': 'GYRATOR',
    **{f'SA{i}': f'MID_CS{i}' for i in range(1, 6)}, **{f'SB{i}': f'MID_CG{i}' for i in range(1, 6)},
    'SND_C': 'FX_SEND_LVL', 'SND10': 'FX_SEND_PAD', 'SEND_TIP': 'FX_SEND', 'RET_TIP': 'FX_RETURN',
    'A2P': 'A2_IN+', 'A2N': 'A2_IN-', 'A2OUT': 'A2_OUT', 'A2BS': 'A2_BOOTSTRAP',
    'MV_TOP': 'MASTER_IN', 'MV_W': 'MASTER_WIPER', 'AUXL': 'AUX_IN_L', 'AUXR': 'AUX_IN_R',
    'MIXN': 'MIX_SUM', 'MIX': 'MIX_OUT', 'STA': 'SUBSONIC_SW_A', 'STB': 'SUBSONIC_SW_B',
    'SUB': 'PA_DRIVE+', 'SUB_INV': 'PA_DRIVE-', 'PH_L': 'PHONES_L', 'PH_R': 'PHONES_R',
    'DI_SEL': 'DI_SEL', 'DI_IN': 'DI_IN', 'PADSW': 'DI_PAD_SW',
    'XLR_HOT': 'LINE_OUT_HOT', 'XLR_COLD': 'LINE_OUT_COLD', 'XLR_P1': 'LINE_OUT_SHIELD',
    'CLLA': 'PRE_CLIP_LED_A', 'CLLK': 'PRE_CLIP_LED_K',
}
POWERAMP = {
    'VCC': '+28V', 'VEE': '-28V', 'SUB': 'PA_DRIVE+', 'SUB_INV': 'PA_DRIVE-',
    'A_P': 'U1_IN+', 'A_N': 'U1_IN-', 'B_P': 'U2_IN+', 'B_N': 'U2_IN-',
    'A_OUT': 'BTL_A_OUT', 'B_OUT': 'BTL_B_OUT', 'A_SPK': 'BTL_A_COIL', 'B_SPK': 'SPK-', 'SPK_P': 'SPK+',
    'A_MUTE': 'U1_MUTE', 'B_MUTE': 'U2_MUTE', 'MUTE_N': 'MUTE_CTRL', 'MUTE_SW': 'MUTE_CTRL_SW',
    'COILP': 'RLY_COIL+', 'COILN': '~{RLY_ON}', 'T': 'RLY_DELAY', 'TD': '~{SPK_TRIP}',
    'AC_IN': 'AC_SENSE', 'DCA': 'DC_DET_A', 'DCB': 'DC_DET_B',
    'PLEDA': 'PWR_CLIP_LED_A', 'PLEDK': 'PWR_CLIP_LED_K',
}
PSU = {
    'VCC': '+28V', 'VEE': '-28V', 'T1A': 'T1_AC1', 'T1B': 'T1_AC2', 'T2A': 'T2_AC1', 'T2B': 'T2_AC2',
    'HV_PR': '+55V_RAW', 'HV_NR': '-55V_RAW', 'P15R': '+28V_FILT', 'N15R': '-28V_FILT',
    'P15Z': '+16V_REF', 'N15Z': '-16V_REF', 'HPZ': '+43V_REF', 'HNZ': '-43V_REF',
}
RAIL_SYMBOL = {'GND': 'power:GND', '+15V': 'power:+15V', '-15V': 'power:-15V', '+28V': 'power:+28V',
               '-28V': 'bassamp:-28V', '+40V': 'bassamp:+40V', '-40V': 'bassamp:-40V'}

def apply(sheet, table):
    for p in sheet.all_parts():
        p.conn = {k: (table.get(v, v) if v is not None else None) for k, v in p.conn.items()}
    sheet.flags = [table.get(f, f) for f in sheet.flags]
    return sheet
