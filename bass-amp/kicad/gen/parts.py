"""Part helpers: symbol, footprint and pin mapping for each component kind."""
from kgen import Part

FP = {
    'R':    'Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal',   # 0.25-0.6 W metal film
    'R05':  'Resistor_THT:R_Axial_DIN0309_L9.0mm_D3.2mm_P12.70mm_Horizontal',   # 0.5-1 W
    'R2W':  'Resistor_THT:R_Axial_DIN0414_L11.9mm_D4.5mm_P15.24mm_Horizontal',  # 2 W
    'CC':   'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm',                       # C0G ceramic
    'CF':   'Capacitor_THT:C_Rect_L7.2mm_W3.5mm_P5.00mm_FKS2_FKP2_MKS2_MKP2',   # film <= 220 nF
    'CF1':  'Capacitor_THT:C_Rect_L7.2mm_W5.5mm_P5.00mm_FKS2_FKP2_MKS2_MKP2',   # film 470 nF-1 uF
    'CF2':  'Capacitor_THT:C_Rect_L13.0mm_W6.0mm_P10.00mm_FKS3_FKP3_MKS4',      # film 2.2 uF 100 V
    'CF4':  'Capacitor_THT:C_Rect_L18.0mm_W8.0mm_P15.00mm_FKS3_FKP3',           # film 4.7 uF 63 V
    'CP5':  'Capacitor_THT:CP_Radial_D5.0mm_P2.00mm',
    'CP6':  'Capacitor_THT:CP_Radial_D6.3mm_P2.50mm',
    'CP8':  'Capacitor_THT:CP_Radial_D8.0mm_P3.50mm',
    'CP10': 'Capacitor_THT:CP_Radial_D10.0mm_P5.00mm',
    'CP12': 'Capacitor_THT:CP_Radial_D12.5mm_P5.00mm',
    'CP16': 'Capacitor_THT:CP_Radial_D16.0mm_P7.50mm',
    'CP30': 'Capacitor_THT:CP_Radial_D30.0mm_P10.00mm_SnapIn',
    'TO92': 'Package_TO_SOT_THT:TO-92_Inline',
    'TO126':'Package_TO_SOT_THT:TO-126-3_Vertical',
    'DIP8': 'Package_DIP:DIP-8_W7.62mm_Socket',
    'DO35': 'Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal',
    'DO41': 'Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal',
    'LED3': 'LED_THT:LED_D3.0mm',
    'POT':  'Potentiometer_THT:Potentiometer_Alpha_RD901F-40-00D_Single_Vertical',
    'LM3886':'Package_TO_SOT_THT:TO-220-11_P3.4x5.08mm_StaggerOdd_Lead4.85mm_Vertical',
    'GBJ':  'Diode_THT:Diode_Bridge_32.0x5.6x17.0mm_P10.0mm_P7.5mm',
    'RELAY':'Relay_THT:Relay_SPDT_Omron-G5LE-1',
    'LAX':  'Inductor_THT:L_Axial_L12.0mm_D5.0mm_P15.24mm_Horizontal_Fastron_MISC',
    'HDR6': 'Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',
    'SKT6': 'Connector_PinSocket_2.54mm:PinSocket_1x06_P2.54mm_Vertical',
    'TB2':  'TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal',
    'TB3':  'TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3_1x03_P5.00mm_Horizontal',
}
def xh(n): return f'Connector_JST:JST_XH_B{n}B-XH-A_1x{n:02d}_P2.50mm_Vertical'

def R(ref, val, a, b, size='R', note=None):
    return Part(ref, 'Device:R', val, FP[size], {'1': a, '2': b}, fields={'Note': note} if note else None)
def C(ref, val, a, b, size='CF', note=None):
    return Part(ref, 'Device:C', val, FP[size], {'1': a, '2': b}, fields={'Note': note} if note else None)
def CP(ref, val, pos, neg, size='CP6', note=None):
    return Part(ref, 'Device:C_Polarized', val, FP[size], {'1': pos, '2': neg}, fields={'Note': note} if note else None)
def D(ref, val, a, k, size='DO35'):
    return Part(ref, 'Device:D', val, FP[size], {'1': k, '2': a})
def DZ(ref, val, a, k, size='DO35'):
    return Part(ref, 'Device:D_Zener', val, FP[size], {'1': k, '2': a})
def LED(ref, val, a, k):
    return Part(ref, 'Device:LED', val, FP['LED3'], {'1': k, '2': a})
def L(ref, val, a, b):
    return Part(ref, 'Device:L', val, FP['LAX'], {'1': a, '2': b})
def POT(ref, val, ccw, wiper, cw):
    """pin 1 = CCW end, pin 2 = wiper, pin 3 = CW end (Alpha 16 mm pinout)."""
    return Part(ref, 'Device:R_Potentiometer', val, FP['POT'], {'1': ccw, '2': wiper, '3': cw})

def NPN(ref, val, c, b, e):          # 2N5210 etc., EBC TO-92
    return Part(ref, 'Device:Q_NPN_EBC', val, FP['TO92'], {'1': e, '2': b, '3': c})
def PNP(ref, val, c, b, e):          # 2N5087, EBC TO-92
    return Part(ref, 'Device:Q_PNP_EBC', val, FP['TO92'], {'1': e, '2': b, '3': c})
def MPSA42(ref, c, b, e):
    return Part(ref, 'Transistor_BJT:MPSA42', 'MPSA42', FP['TO92'], {'1': e, '2': b, '3': c})
def MPSA92(ref, c, b, e):
    return Part(ref, 'Transistor_BJT:MPSA92', 'MPSA92', FP['TO92'], {'1': e, '2': b, '3': c})
def BD139(ref, c, b, e):
    return Part(ref, 'Transistor_BJT:BD139', 'BD139', FP['TO126'], {'1': e, '2': c, '3': b})
def BD140(ref, c, b, e):
    return Part(ref, 'Transistor_BJT:BD140', 'BD140', FP['TO126'], {'1': e, '2': c, '3': b})
def NPN_ECB(ref, val, c, b, e):      # MJE340 (TO-126, E-C-B)
    return Part(ref, 'Device:Q_NPN_ECB', val, FP['TO126'], {'1': e, '2': c, '3': b})
def PNP_ECB(ref, val, c, b, e):      # MJE350
    return Part(ref, 'Device:Q_PNP_ECB', val, FP['TO126'], {'1': e, '2': c, '3': b})

def NE5532(ref, unit, plus=None, minus=None, out=None, vp=None, vn=None):
    if unit == 1: return Part(ref, 'Amplifier_Operational:NE5532', 'NE5532', FP['DIP8'], {'3': plus, '2': minus, '1': out}, unit=1)
    if unit == 2: return Part(ref, 'Amplifier_Operational:NE5532', 'NE5532', FP['DIP8'], {'5': plus, '6': minus, '7': out}, unit=2)
    return Part(ref, 'Amplifier_Operational:NE5532', 'NE5532', FP['DIP8'], {'8': vp, '4': vn}, unit=3)

def CONN(ref, value, nets, fp=None):
    n = len(nets)
    return Part(ref, f'Connector_Generic:Conn_01x{n:02d}', value, fp or xh(n), {str(i + 1): net for i, net in enumerate(nets)})
