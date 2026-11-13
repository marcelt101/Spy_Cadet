"""Hand-laid, wired, human-readable schematic of the v2 varactor half-bridge cell.
Coordinates in units of 1.27 mm (h)."""
import uuid, math, json, re
from libtool import flat_symbol, pins
U=lambda: str(uuid.uuid4()); H=1.27
ROOT=U(); PROJ="varactor_halfbridge"
FP=dict(R="Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",C="Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
 CF="Capacitor_THT:C_Rect_L7.2mm_W5.5mm_P5.00mm_FKS2_FKP2_MKS2_MKP2",CP="Capacitor_THT:CP_Radial_D5.0mm_P2.00mm",
 DIP8="Package_DIP:DIP-8_W7.62mm",DIP14="Package_DIP:DIP-14_W7.62mm",DIP16="Package_DIP:DIP-16_W7.62mm",SO8="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
 OSC="Oscillator:Oscillator_DIP-14",TO92="Package_TO_SOT_THT:TO-92_Inline",TO92_2="Package_TO_SOT_THT:TO-92-2",
 TRIM="Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical",POT="Potentiometer_THT:Potentiometer_Alps_RK09K_Single_Vertical",
 CTRIM="Capacitor_SMD:C_Trimmer_Voltronics_JR",H2="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
 H3="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",TP="TestPoint:TestPoint_Pad_D1.5mm")
SYMLIB={"R":("Device","R"),"C":("Device","C"),"CP":("Device","C_Polarized"),"CT":("Device","C_Trim"),"VAR":("Device","D_Capacitance"),
 "POT":("Device","R_Potentiometer"),"TRIM":("Device","R_Potentiometer_Trim"),"OPA":("Amplifier_Operational","OPA2134"),
 "DG":("Analog_Switch","DG419LDJ"),"CNT":("4xxx","4040"),"NAND3":("74xx","74LS10"),"OSC":("Oscillator","ACO-xxxMHz"),
 "REF":("Reference_Voltage","LM4040LP-5"),"REG":("Regulator_Linear","L78L05_TO92"),"JP":("Jumper","Jumper_3_Open"),
 "J2":("Connector_Generic","Conn_01x02"),"J3":("Connector_Generic","Conn_01x03"),"TP":("Connector","TestPoint"),
 "+15V":("power","+15V"),"-15V":("power","-15V"),"GND":("power","GND"),"+5V":("power","+5V"),"FLG":("power","PWR_FLAG"),"INA":("Amplifier_Instrumentation","INA128")}
class Pt(tuple): pass
DX=[0]
def sh(p): return p if isinstance(p,Pt) else (p[0]+DX[0],p[1])
insts=[]; wires=[]; labels=[]; ncs=[]; texts=[]; pinpts=[]
class Inst:
    def __init__(s,ref,kind,value,fp,x,y,rot=0,mirror=False,unit=1,pwr=False):
        x=x+DX[0]
        s.ref,s.kind,s.value,s.fp,s.x,s.y,s.rot,s.mirror,s.unit,s.pwr=ref,kind,value,fp,x,y,rot,mirror,unit,pwr
        lib,sym=SYMLIB[kind]; P=pins(lib,sym); s.pl={}
        for (num,nm,typ,px,py,a) in P.get(unit,[])+P.get(0,[]):
            px/=H; py/=H
            if mirror: py=-py
            t=math.radians(rot); rx=px*math.cos(t)-py*math.sin(t); ry=px*math.sin(t)+py*math.cos(t)
            s.pl[num]=(round(x+rx,3),round(y-ry,3),typ)
        insts.append(s)
        for k,(a,b,typ) in s.pl.items(): pinpts.append((a,b,s.ref,k,typ))
    def p(s,num): a,b,_=s.pl[num]; return Pt((a,b))
def place(*a,**k): return Inst(*a,**k)
def W(*pts):
    pts=[sh(p) for p in pts]
    for a,b in zip(pts[:-1],pts[1:]):
        if a!=b:
            assert a[0]==b[0] or a[1]==b[1], f"non-orthogonal wire {a}->{b}"
            wires.append((a,b))
def L(name,pt,ang=0): labels.append((name,sh(pt),ang))
_pc=[0]
def PWR(kind,pt,rot=None):
    _pc[0]+=1
    if rot is None: rot=0
    p=sh(pt); place(f"#PWR{_pc[0]:03d}",kind,kind if kind!="FLG" else "PWR_FLAG","",p[0]-DX[0],p[1],rot=rot,pwr=True)
def NC(pt): ncs.append(sh(pt))
def T(s,x,y,size=2.5,bold=True): texts.append((s,x,y,size,bold))
def rail(kind,pin,dist=2,down=None):
    """short stub from pin to a power symbol. down: True -> stub downward"""
    x,y=pin
    x-=DX[0] if not isinstance(pin,Pt) else 0
    if down is None: down = kind in("GND","-15V")
    q=Pt((x,y+dist)) if down else Pt((x,y-dist)); W(pin,q)
    _pc[0]+=1; place(f"#PWR{_pc[0]:03d}",kind,kind,"",q[0]-DX[0],q[1],rot=180 if (kind=="-15V" and down) else 0,pwr=True)

# =============== 1  INPUT & PHASE SPLITTER ===============
T("1  INPUT",16,22); T("phase splitter: IN_HALF_NEG = -x/2, IN_HALF_POS = +x/2",16,26,1.5,False)
J2=place("J2","J2","AUDIO IN",FP["H2"],20,62,rot=180)        # pin2 = signal (upper), pin1 = GND
W(J2.p("2"),(34,60)); L("AUDIO_IN",(26,60))
W(J2.p("1"),(26,62),(26,66)); PWR("GND",(26,66))
R1=place("R1","R","100k",FP["R"],30,63)                       # pulldown
W(R1.p("2"),(30,66)); PWR("GND",(30,66))
R2=place("R2","R","20k",FP["R"],37,60,rot=90)
W((34,60),R2.p("1"))
U1A=place("U1","OPA","OPA2134PA",FP["DIP8"],50,62,mirror=True,unit=1)
W(R2.p("2"),U1A.p("2")); W(U1A.p("3"),(44,64),(44,68)); PWR("GND",(44,68))
R3=place("R3","R","10k",FP["R"],50,54,rot=90)
W((42,60),(42,54),R3.p("1")); W(R3.p("2"),(58,54),(58,62)); W(U1A.p("1"),(58,62),(62,62))
R4=place("R4","R","10k",FP["R"],65,62,rot=90)
W((62,62),R4.p("1"))
U1B=place("U1","OPA","OPA2134PA",FP["DIP8"],78,64,mirror=True,unit=2)
W(R4.p("2"),U1B.p("6")); W(U1B.p("5"),(72,66),(72,70)); PWR("GND",(72,70))
R5=place("R5","R","10k",FP["R"],78,56,rot=90)
W((70,62),(70,56),R5.p("1")); W(R5.p("2"),(86,56),(86,64)); W(U1B.p("7"),(86,64),(94,64)); L("IN_HALF_POS",(94,64))
W((60,62),(60,74),(94,74)); L("IN_HALF_NEG",(94,74))

# =============== 3  MODULATOR ===============
T("3  MODULATOR",110,22); T("DG419 choppers at the carrier",110,26,1.5,False)
U7=place("U7","DG","DG419DJ",FP["DIP8"],126,50,rot=180,unit=1)
W(U7.p("2"),(116,U7.p("2")[1])); L("IN_HALF_POS",(116,U7.p("2")[1]),180)
W(U7.p("8"),(116,U7.p("8")[1])); L("IN_HALF_NEG",(116,U7.p("8")[1]),180)
W(U7.p("6"),(126,38)); L("CARRIER_102K",(126,38),90)
R6=place("R6","R","1k",FP["R"],138,50,rot=90); W(U7.p("1"),R6.p("1")); W(R6.p("2"),(150,50)); L("CHOP_REF",(150,50))
U8=place("U8","DG","DG419DJ",FP["DIP8"],126,77,rot=180,unit=1)
W(U8.p("2"),(116,U8.p("2")[1])); L("IN_HALF_NEG",(116,U8.p("2")[1]),180)
W(U8.p("8"),(116,U8.p("8")[1])); L("IN_HALF_POS",(116,U8.p("8")[1]),180)
W(U8.p("6"),(126,66)); L("CARRIER_102K",(126,66),90)
R7=place("R7","R","1k",FP["R"],138,77,rot=90); W(U8.p("1"),R7.p("1")); W(R7.p("2"),(150,77)); L("CHOP_VAR",(150,77))
T("U7 -> fixed capacitor,  U8 -> varactor pair (opposite phase)",110,96,1.5,False)

# =============== 4  HALF-BRIDGE + CHARGE AMP ===============
T("4  HALF-BRIDGE + CHARGE AMP",164,22); T("CHG_AMP_SUM and VAR_BIAS_NODE are high-impedance: PTFE standoffs, no breadboard",164,26,1.5,False)
W((150,50),(178,50))
C40=place("C40","C","8.2p C0G",FP["C"],181,50,rot=90)
CT3=place("CT3","CT","0.5-3pF NULL",FP["CTRIM"],181,41,rot=90)
W((176,50),(176,41),CT3.p("1")); W(C40.p("2"),(188,50)); W(CT3.p("2"),(186,41),(186,50))
W((188,50),(196,50),(196,77))
D1=place("D1","VAR","MMBV2109LT1G","varactor:Varactor_SOT-23_A1-NC2-K3",171,77,rot=180)     # anode left (CHOP_VAR), cathode right
D2=place("D2","VAR","MMBV2109LT1G","varactor:Varactor_SOT-23_A1-NC2-K3",189,77,rot=0)       # cathode left (bias node), anode right (sum)
W((150,77),D1.p("2"))

W(D1.p("1"),D2.p("1")); L("VAR_BIAS_NODE",(180,81),270)
W(D2.p("2"),(196,77)); W((196,77),(201,77)); L("CHG_AMP_SUM",(196,54),0)
CT1=place("CT1","CT","0.5-3pF DNP",FP["CTRIM"],171,68,rot=90)
CT2=place("CT2","CT","0.5-3pF DNP",FP["CTRIM"],189,68,rot=90)
W(CT1.p("1"),(CT1.p("1")[0],77)); W(CT1.p("2"),(CT1.p("2")[0],77))
W(CT2.p("1"),(CT2.p("1")[0],77)); W(CT2.p("2"),(CT2.p("2")[0],77))
RB1=place("RB1","R","3.3M",FP["R"],180,90,rot=180)
W((180,77),RB1.p("2")); W(RB1.p("1"),(180,100)); L("VAR_BIAS_DRIVE",(180,100),270)
U2A=place("U2","OPA","OPA1656ID",FP["SO8"],207,79,mirror=True,unit=1)
W((201,77),U2A.p("2")); W(U2A.p("3"),(199,81),(199,85)); PWR("GND",(199,85))
C38=place("C38","C","6.8p C0G",FP["C"],207,67,rot=90); R24=place("R24","R","100M",FP["R"],207,58,rot=90)
W((198,77),(198,58),R24.p("1")); W((198,67),C38.p("1"))
W(R24.p("2"),(215,58),(215,79)); W(C38.p("2"),(215,67)); W(U2A.p("1"),(215,79),(222,79))
TP4=place("TP4","TP","CHG_AMP_OUT",FP["TP"],219,75); W((219,79),(219,75))
R8=place("R8","R","1k",FP["R"],226,94,rot=90); W((222,79),(222,94),R8.p("1"))
U2B=place("U2","OPA","OPA1656ID",FP["SO8"],238,96,mirror=True,unit=2)
W(R8.p("2"),U2B.p("6")); W(U2B.p("5"),(230,98),(230,102)); PWR("GND",(230,102))
R9=place("R9","R","1k",FP["R"],238,88,rot=90); W((231,94),(231,88),R9.p("1")); W(R9.p("2"),(246,88),(246,96))
W(U2B.p("7"),(246,96),(252,96)); L("CHG_AMP_OUT_INV",(252,96))
W((222,79),(252,79)); L("CHG_AMP_OUT",(252,79))
T("Gain = (C_pair - C_fixed) / (2 Cf).  CT3 sets the null near VB = 12 V.  CT1/CT2 optional pair-match trim.",164,118,1.6,False)

# =============== 5  DEMOD, HOLD, FILTER, OUTPUT ===============
T("5  DEMOD, HOLD, FILTER, OUTPUT",268,22); T("sync demod + gated hold + 30 kHz 4th-order Butterworth + makeup gain",268,26,1.5,False)
U9=place("U9","DG","DG419DJ",FP["DIG8"] if False else FP["DIP8"],280,80,rot=180,unit=1)
W(U9.p("2"),(270,U9.p("2")[1])); L("CHG_AMP_OUT",(270,U9.p("2")[1]),180)
W(U9.p("8"),(270,U9.p("8")[1])); L("CHG_AMP_OUT_INV",(270,U9.p("8")[1]),180)
W(U9.p("6"),(280,68)); L("CARRIER_102K",(280,68),90)
U10=place("U10","DG","DG419DJ",FP["DIP8"],300,80,rot=180,unit=1)
W(U9.p("1"),(289,80),(289,82),U10.p("2"))
NC(U10.p("8")); W(U10.p("6"),(300,68)); L("HOLD_SW_CTRL",(300,68),90)
TP5=place("TP5","TP","DEMOD_OUT",FP["TP"],289,94,rot=180); W((289,82),(289,94)); L("DEMOD_OUT",(289,86),270)
W(U10.p("1"),(314,80))
C39=place("C39","C","1n C0G",FP["C"],310,86); W((310,80),C39.p("1")); W(C39.p("2"),(310,91)); PWR("GND",(310,91))
TP6=place("TP6","TP","HOLD_CAP",FP["TP"],312,74); W((312,80),(312,74))
L("HOLD_CAP",(306,80),90)
DX[0]=8
U3A=place("U3","OPA","OPA2134PA",FP["DIP8"],320,82,unit=1)       # + on top
W(Pt((314,80)),Pt((320,80)),U3A.p("3")); W(U3A.p("2"),(313,84),(313,88),(328,88),(328,82)); W(U3A.p("1"),(334,82))
L("HOLD_BUF",(334,82))
DX[0]=16
R10=place("R10","R","4.87k",FP["R"],337,82,rot=90); R11=place("R11","R","4.87k",FP["R"],345,82,rot=90)
W(Pt((342,82)),R10.p("1")); W(R10.p("2"),R11.p("1"))
C14=place("C14","C","1.2n C0G",FP["C"],341,74,rot=180); W((341,82),C14.p("1")); W(C14.p("2"),(341,68),(366,68),(366,80))
U3B=place("U3","OPA","OPA2134PA",FP["DIP8"],356,80,mirror=True,unit=2)
W(R11.p("2"),U3B.p("5")); W(U3B.p("6"),(350,76),(366,76)); W(U3B.p("7"),(370,80))
C15=place("C15","C","1n C0G",FP["C"],348,88); W((348,82),C15.p("1")); W(C15.p("2"),(348,94)); PWR("GND",(348,94))
L("LPF1_OUT",(368,80))
DX[0]=24
R12=place("R12","R","4.22k",FP["R"],373,80,rot=90); R13=place("R13","R","4.22k",FP["R"],381,80,rot=90)
W(Pt((386,80)),R12.p("1")); W(R12.p("2"),R13.p("1"))
C16=place("C16","C","3.3n C0G",FP["C"],377,72,rot=180); W((377,80),C16.p("1")); W(C16.p("2"),(377,66),(402,66),(402,78))
U4A=place("U4","OPA","OPA2134PA",FP["DIP8"],392,78,mirror=True,unit=1)
W(R13.p("2"),U4A.p("3")); W(U4A.p("2"),(386,74),(402,74)); W(U4A.p("1"),(408,78))
C17=place("C17","C","470p C0G",FP["C"],384,86); W((384,80),C17.p("1")); W(C17.p("2"),(384,92)); PWR("GND",(384,92))
L("LPF_OUT",(405,78))
TP7=place("TP7","TP","LPF_OUT",FP["TP"],402,72); W((402,78),(402,72))
DX[0]=30
U4B=place("U4","OPA","OPA2134PA",FP["DIP8"],416,80,unit=2)        # + on top
W(Pt((432,78)),U4B.p("5")); W(U4B.p("6"),(408,82),(408,91))
RV4=place("RV4","POT","10k lin",FP["POT"],418,91,rot=270)
R14=place("R14","R","1k",FP["R"],408,97); W((408,91),R14.p("1")); W(R14.p("2"),(408,102)); PWR("GND",(408,102))
W((408,91),RV4.p("3")); W(RV4.p("2"),(418,96),(413,96),(413,91))
W(U4B.p("7"),(426,80),(430,80)); W(RV4.p("1"),(426,91),(426,80)); L("MAKEUP_OUT",(428,80))
DX[0]=36
R15=place("R15","R","100",FP["R"],433,80,rot=90); W(Pt((460,80)),R15.p("1"))
DX[0]=42
J3=place("J3","J2","AUDIO OUT",FP["H2"],446,80)
W(R15.p("2"),J3.p("1")); L("AUDIO_OUT",(431,80)); W(J3.p("2"),(440,82),(440,86)); PWR("GND",(440,86))

DX[0]=0
# =============== 2  TIMING ===============
T("2  TIMING",16,150); T("3.2768 MHz / 32 = 102.4 kHz carrier; HOLD_GATE high for counts 8..14 of each half-period",16,154,1.5,False)
X1=place("X1","OSC","3.2768MHz",FP["OSC"],30,180)
rail("+5V",X1.p("14")); rail("GND",X1.p("7")); NC(X1.p("1"))
U11=place("U11","CNT","74HC4040",FP["DIP16"],62,190)
W(X1.p("8"),U11.p("10")); L("CLK_3M2768",(42,180))
W(U11.p("11"),(46,186),(46,192)); PWR("GND",(46,192))
rail("+5V",U11.p("16")); rail("GND",U11.p("8"))
for q in ["2","4","13","12","14","15","1"]: NC(U11.p(q))
U12A=place("U12","NAND3","74HC10",FP["DIP14"],92,182,unit=1)
W(U11.p("9"),U12A.p("1")); W(U11.p("7"),U12A.p("2")); W(U11.p("6"),U12A.p("13"))
L("CNT_Q0",(76,180)); L("CNT_Q1",(76,182)); L("CNT_Q2",(76,184))
W(U11.p("3"),(80,U11.p("3")[1])); L("CARRIER_102K",(80,U11.p("3")[1]))
TP1=place("TP1","TP","CARRIER_102K",FP["TP"],78,193,rot=180); W((78,U11.p("3")[1]),(78,193))
U12B=place("U12","NAND3","74HC10",FP["DIP14"],112,194,unit=2)
W(U11.p("5"),(84,186),(84,192),U12B.p("3")); L("CNT_Q3",(96,192))
W(U12A.p("12"),(102,182),(102,194),U12B.p("4"))
W(U12B.p("5"),(98,196),(98,200)); PWR("+5V",(98,200),rot=180)
U12C=place("U12","NAND3","74HC10",FP["DIP14"],138,194,unit=3)
W(U12B.p("6"),U12C.p("10")); W(U12C.p("9"),(126,192),(126,188)); PWR("+5V",(126,188))
W(U12C.p("11"),(128,196),(128,200)); PWR("+5V",(128,200),rot=180)
L("HOLD_GATE_N",(122,194))
JP3=place("JP3","JP","HOLD POLARITY",FP["H3"],158,194)
W(U12C.p("8"),JP3.p("1")); L("HOLD_GATE",(147,194))
TP2=place("TP2","TP","HOLD_GATE",FP["TP"],151,188); W((151,194),(151,188))
W((122,194),(122,212),(170,212),(170,194),JP3.p("3"))
W(JP3.p("2"),(158,206),(140,206)); L("HOLD_SW_CTRL",(140,206),180)
TP3=place("TP3","TP","HOLD_SW_CTRL",FP["TP"],146,202); W((146,206),(146,202))
T("JP3: choose the position where TP6 (HOLD_CAP) is a clean staircase with no spikes at carrier edges",16,226,1.6,False)

# =============== 6  CONTROL ===============
T("6  CONTROL",220,150); T("VAR_BIAS_CMD = 2 x GAIN_CV + 2 x VB_OFFSET  (VB_OFFSET ~0.75 V: 1.5..11.5 V for GAIN_CV 0..5 V)",220,154,1.5,False)
R16=place("R16","R","4.7k",FP["R"],222,166); rail("+15V",R16.p("1"))
W(R16.p("2"),(222,172),(296,172)); L("REF_5V",(256,172))
U15=place("U15","REF","LM4040DIZ-5.0",FP["TO92"],228,178,rot=90)
W((228,172),U15.p("2")); W(U15.p("3"),(228,184)); PWR("GND",(228,184))
C28=place("C28","C","1u",FP["CF"],236,178); W((236,172),C28.p("1")); W(C28.p("2"),(236,184)); PWR("GND",(236,184))
RV3=place("RV3","TRIM","10k",FP["TRIM"],248,178)
W((248,172),RV3.p("1")); W(RV3.p("3"),(248,184)); PWR("GND",(248,184))
U5A=place("U5","OPA","OPA2134PA",FP["DIP8"],268,180,unit=1)
W(RV3.p("2"),U5A.p("3")); W(U5A.p("2"),(260,182),(260,188),(278,188),(278,180)); W(U5A.p("1"),(278,180),(282,180),(282,156),(357,156))
L("VB_OFFSET",(300,156))
RV2=place("RV2","POT","10k lin",FP["POT"],296,178)
W((296,172),RV2.p("1")); W(RV2.p("3"),(296,184)); PWR("GND",(296,184))
JP1=place("JP1","JP","CV SOURCE",FP["H3"],318,178,rot=180)
W(RV2.p("2"),JP1.p("3")); L("GAIN_CV_MAN",(300,178))
J4=place("J4","J2","CV IN 0-5V",FP["H2"],346,178)
W(JP1.p("1"),J4.p("1")); L("GAIN_CV_EXT",(325,178))
R18=place("R18","R","100k",FP["R"],337,184); W((337,178),R18.p("1")); W(R18.p("2"),(337,190)); PWR("GND",(337,190))
W(J4.p("2"),(341,180),(341,190)); PWR("GND",(341,190))
W(JP1.p("2"),(318,166),(357,166)); L("GAIN_CV",(322,166))
R19=place("R19","R","10k",FP["R"],360,166,rot=90); R20=place("R20","R","10k",FP["R"],360,156,rot=90)
W(R20.p("2"),(367,156),(367,166)); W(R19.p("2"),(367,166),(371,166))
U5B=place("U5","OPA","OPA2134PA",FP["DIP8"],377,168,unit=2)
W((371,166),U5B.p("5")); W(U5B.p("6"),(368,170),(368,180))
R21=place("R21","R","10k",FP["R"],368,183); W(R21.p("2"),(368,188)); PWR("GND",(368,188))
R22=place("R22","R","30.1k",FP["R"],377,180,rot=90); W((368,180),R22.p("1")); W(R22.p("2"),(386,180),(386,168))
W(U5B.p("7"),(386,168),(402,168)); L("VAR_BIAS_CMD",(392,168))
TP9=place("TP9","TP","VAR_BIAS_CMD",FP["TP"],389,164); W((389,168),(389,164))
T("RV3: set VAR_BIAS_CMD = 1.5 V with GAIN_CV = 0.  JP1 selects external CV (J4) or the manual pot RV2.",220,204,1.6,False)

# =============== 9  BIAS SERVO ===============
T("9  BIAS SERVO",420,150); T("bootstrapped feed: VAR_BIAS_DRIVE = VAR_BIAS_CMD + 0.99 x HP1Hz(BIAS_SENSE - REP_SENSE)",420,154,1.5,False)
W((462,166),(470,166)); L("VAR_BIAS_NODE",(462,166),180)
U16A=place("U16","OPA","OPA2140AID",FP["SO8"],476,168,unit=1)
W(U16A.p("2"),(468,170),(468,174),(484,174),(484,168)); W(U16A.p("1"),(484,168),(494,168),(494,174))
L("BIAS_SENSE",(486,168))
U17=place("U17","INA","INA128PA",FP["DIP8"],504,178)
W((494,174),U17.p("3")); NC(U17.p("1")); NC(U17.p("8"))
rail("+15V",U17.p("7"),down=False); rail("-15V",U17.p("4"),down=True)
W(U17.p("5"),(506,186),(509,186),(509,189)); PWR("GND",(509,189))
L_RV=None
W((424,190),(429,190)); L("VAR_BIAS_CMD",(424,190),180)
RV5=place("RV5","TRIM","1M REPLICA TRIM",FP["TRIM"],432,190,rot=90)
W(RV5.p("2"),(432,186),(436,186),(436,190)); W(RV5.p("3"),(436,190),(438,190))
R35=place("R35","R","3.0M",FP["R"],441,190,rot=90)
W(R35.p("2"),(460,190),(470,190)); L("REP_BIAS_NODE",(446,190))
D3=place("D3","VAR","MMBV2109LT1G","varactor:Varactor_SOT-23_A1-NC2-K3",452,196,rot=270)
D4=place("D4","VAR","MMBV2109LT1G","varactor:Varactor_SOT-23_A1-NC2-K3",464,196,rot=270)
D3.hv=D4.hv=True; T("D3, D4 = MMBV2109LT1G",446,206,1.27,False)
W((452,190),D3.p("1")); W((464,190),D4.p("1"))
W(D3.p("2"),(452,201)); PWR("GND",(452,201)); W(D4.p("2"),(464,201)); PWR("GND",(464,201))
U16B=place("U16","OPA","OPA2140AID",FP["SO8"],476,192,unit=2)
W((470,190),U16B.p("5")); W(U16B.p("6"),(468,194),(468,198),(484,198),(484,192)); W(U16B.p("7"),(484,192),(494,192),(494,182))
L("REP_SENSE",(486,192))
W((494,182),U17.p("2"))
W(U17.p("6"),(518,178)); L("BIAS_ERR",(512,178))
TP11=place("TP11","TP","BIAS_ERR",FP["TP"],515,172); W((515,178),(515,172))
C41=place("C41","C","1u film",FP["CF"],521,178,rot=90); W((518,178),C41.p("1"))
R34=place("R34","R","1.62k",FP["R"],529,178,rot=90); W(C41.p("2"),R34.p("1"))
W(R34.p("2"),(534,178),(542,178)); L("ERR_HP",(535,178))
R33=place("R33","R","160k",FP["R"],534,184); W((534,178),R33.p("1")); W(R33.p("2"),(534,190)); PWR("GND",(534,190))
U18=place("U18","INA","INA128PA",FP["DIP8"],548,182)
W((542,178),U18.p("3")); W(U18.p("2"),(540,186),(540,190)); PWR("GND",(540,190)); NC(U18.p("1")); NC(U18.p("8"))
rail("+15V",U18.p("7"),down=False); rail("-15V",U18.p("4"),down=True)
W(U18.p("5"),(550,186),(554,186),(554,196)); L("VAR_BIAS_CMD",(554,196),270)
W(U18.p("6"),(572,182)); L("VAR_BIAS_DRIVE",(560,182))
TP10=place("TP10","TP","VAR_BIAS_DRIVE",FP["TP"],567,178); W((567,182),(567,178))
T("Guard ring around VAR_BIAS_NODE (D1/D2 cathodes, RB1, U16A pin 3) driven by BIAS_SENSE.  Replica D3/D4: matched to D1/D2 within 0.2 %, same thermal block.",420,212,1.5,False)
T("Trim RV5: no audio, CV = 0.5 Hz square (small steps). Adjust RV5 until TP11 (BIAS_ERR) shows no step-shaped transients.",420,217,1.5,False)
T("U17/U18: INA128 at G = 1 (RG open). U18 REF carries VAR_BIAS_CMD with unity gain to the drive - this exactness is what keeps gain moves clean.",420,222,1.5,False)

# =============== 7  POWER + DECOUPLING ===============
T("7  POWER",16,250); T("+/-15 V in, 78L05 for logic and DG419 VL",16,254,1.5,False)
J1=place("J1","J3","+15 / GND / -15",FP["H3"],20,276,rot=180)   # pin3 top=+15, pin2=GND, pin1 bottom=-15
W(J1.p("3"),(32,274),(32,268)); PWR("+15V",(32,268)); place("#FLG01","FLG","PWR_FLAG","",28,270,pwr=True); W((28,270),(28,274))
W(J1.p("2"),(38,276),(38,282)); PWR("GND",(38,282)); place("#FLG02","FLG","PWR_FLAG","",42,274,pwr=True); W((42,274),(42,276),(38,276))
W(J1.p("1"),(30,278),(30,284)); PWR("-15V",(30,284),rot=180); place("#FLG03","FLG","PWR_FLAG","",34,286,pwr=True); W((34,286),(34,284),(30,284))
C34=place("C34","CP","10u",FP["CP"],52,276); rail("+15V",C34.p("1")); rail("GND",C34.p("2"))
C35=place("C35","CP","10u",FP["CP"],60,276); W(C35.p("1"),(60,271)); PWR("GND",(60,271),rot=180); rail("-15V",C35.p("2"))
U14=place("U14","REG","78L05",FP["TO92"],80,276)
W(U14.p("3"),(70,276),(70,270)); PWR("+15V",(70,270)); C36=place("C36","C","330n",FP["C"],70,282); W((70,276),C36.p("1")); rail("GND",C36.p("2"))
rail("GND",U14.p("2"))
W(U14.p("1"),(92,276),(92,270)); PWR("+5V",(92,270)); C37=place("C37","C","1u",FP["CF"],92,282); W((92,276),C37.p("1")); rail("GND",C37.p("2"))

T("8  IC SUPPLY PINS + DECOUPLING",120,250); T("one 100n per supply pin, placed right at the IC",120,254,1.5,False)
x=124
for ref,unit,val,fp in [("U1",3,"OPA2134PA","DIP8"),("U2",3,"OPA1656ID","SO8"),("U3",3,"OPA2134PA","DIP8"),("U4",3,"OPA2134PA","DIP8"),("U5",3,"OPA2134PA","DIP8")]:
    u=place(ref,"OPA",val,FP[fp],x,276,unit=unit); rail("+15V",u.p("8")); rail("-15V",u.p("4")); x+=12
for ref in ["U7","U8","U9","U10"]:
    u=place(ref,"DG","DG419DJ",FP["DIP8"],x,276,unit=2)
    rail("+15V",u.p("4")); W(u.p("5"),(u.p("5")[0],262),(u.p("5")[0]+3,262),(u.p("5")[0]+3,260)); PWR("+5V",(u.p("5")[0]+3,260))
    rail("GND",u.p("3")); W(u.p("7"),(u.p("7")[0],290),(u.p("7")[0]+3,290),(u.p("7")[0]+3,293)); PWR("-15V",(u.p("7")[0]+3,293),rot=180)
    x+=14
u=place("U12","NAND3","74HC10",FP["DIP14"],x,276,unit=4); rail("+5V",u.p("14")); rail("GND",u.p("7")); x+=14
u=place("U16","OPA","OPA2140AID",FP["SO8"],x,276,unit=3); rail("+15V",u.p("8")); rail("-15V",u.p("4")); x+=12
caps=[("C1","+15V"),("C2","-15V"),("C12","+15V"),("C13","-15V"),("C18","+15V"),("C19","-15V"),("C20","+15V"),("C21","-15V"),
      ("C22","+15V"),("C23","-15V"),("C24","+15V"),("C25","-15V"),("C30","+15V"),("C31","-15V"),("C6","+15V"),("C7","-15V"),
      ("C8","+15V"),("C9","-15V"),("C10","+5V"),("C11","+5V"),("C26","+5V"),("C27","+5V"),("C3","+5V"),("C4","+5V"),("C5","+5V"),("C42","+15V"),("C43","-15V"),("C44","+15V"),("C45","-15V"),("C46","+15V"),("C47","-15V")]
cx=124
for i,(ref,railn) in enumerate(caps):
    cy=314 if i<13 else (338 if i<26 else 362); xx=cx+(i%13)*10
    c=place(ref,"C","100n",FP["C"],xx,cy); rail(railn,c.p("1"),down=False); rail("GND",c.p("2"))
T("C1,C2: U1   C12,C13: U2   C18-C21: U9,U10   C22-C25: U3,U4   C30,C31: U5   C6-C9: U7,U8   C10,C11,C26,C27: DG419 VL   C3-C5: X1, U11, U12   C42,C43: U16   C44,C45: U17   C46,C47: U18",120,376,1.5,False)

# ---------- notes ----------
notes=["VARACTOR HALF-BRIDGE GAIN CELL  -  prototype v2 (single varactor pair).  Unverified design: build & measure.",
"Signal path (top row, left to right): input splitter -> chopper -> varactor half-bridge -> charge amp -> sync demod -> hold -> 30 kHz LPF -> makeup gain.",
"Bring-up: 1) TP1 = 102.4 kHz, TP2 high for counts 8..14;  2) JP3 so TP6 is flat at carrier edges;  3) RV3 for 1.5 V at TP9 with GAIN_CV = 0;",
"4) GAIN_CV = 5 V, adjust CT3 for about 25 dB below the GAIN_CV = 0 level;  5) optional CT1/CT2 for minimum THD.",
"Bias: RB1 3.3M fed from VAR_BIAS_DRIVE (block 9 bootstrap): ~0.8 ms gain response, sim. THD 0.03-0.04 % 50 Hz-1 kHz at +8 dBu.",
"D1, D2: onsemi MMBV2109LT1G (SOT-23, 33 pF @ 4 V) or LV2209 (TO-92, same specs; footprint varactor:Varactor_TO-92-2_A1-K2). Match <1 %, thermally coupled."]
for i,s in enumerate(notes): T(s,16,392+i*6,1.8,False)

# ================= split wires at T-points =================
pinset={(round(x,3),round(y,3)) for x,y,*_ in pinpts}
def inside(p,a,b):
    if a[0]==b[0]==p[0]: return min(a[1],b[1])<p[1]<max(a[1],b[1])
    if a[1]==b[1]==p[1]: return min(a[0],b[0])<p[0]<max(a[0],b[0])
    return False
changed=True
while changed:
    changed=False
    pts=set(pinset)|{w[0] for w in wires}|{w[1] for w in wires}
    new=[]
    for a,b in wires:
        cut=sorted([p for p in pts if inside(p,a,b)],key=lambda p:abs(p[0]-a[0])+abs(p[1]-a[1]))
        if cut:
            changed=True; seq=[a]+cut+[b]
            new+=list(zip(seq[:-1],seq[1:]))
        else: new.append((a,b))
    wires[:]=new
# ================= junctions & writer =================
from collections import Counter
ends=Counter()
for a,b in wires: ends[a]+=1; ends[b]+=1
pinset={(round(x,3),round(y,3)) for x,y,*_ in pinpts}
for p in pinset:
    if p in ends: ends[p]+=1
def interior(p,seg):
    (a,b)=seg
    if a[0]==b[0]==p[0]: return min(a[1],b[1])<p[1]<max(a[1],b[1])
    if a[1]==b[1]==p[1]: return min(a[0],b[0])<p[0]<max(a[0],b[0])
    return False
junc=set(p for p,c in ends.items() if c>=3)
for p in list(ends):
    if any(interior(p,s) for s in wires): junc.add(p)
def q(s): return '"'+str(s).replace('"','\\"')+'"'
mm=lambda v: f"{v*H:.2f}"
out=[]; libs={}
for s in insts:
    lib,sym=SYMLIB[s.kind]; key=f"{lib}:{sym}"
    if key not in libs: libs[key]=flat_symbol(lib,sym)
    hide_val=s.kind in("FLG","TP") or getattr(s,"hv",False)
    horiz=s.rot in(90,270); fa=90 if horiz else 0; rj=vj="left"
    if s.kind in("R","C","CP","CT"):
        if horiz: rx,ry,vx,vy,rj,vj,fa=s.x,s.y-3,s.x,s.y+3.2,"center","center",90
        elif getattr(s,'tl',False): rx,ry,vx,vy,rj,vj,fa=s.x-2,s.y-0.8,s.x-2,s.y+1.4,"right","right",0
        else: rx,ry,vx,vy,fa=s.x+2,s.y-0.8,s.x+2,s.y+1.4,0
    elif s.kind in("VAR","JP") and horiz: rx,ry,vx,vy,rj,vj,fa=s.x+2,s.y-0.8,s.x+2,s.y+1.4,"left","left",90
    elif s.kind in("VAR","JP"): rx,ry,vx,vy,rj,vj,fa=s.x,s.y-3,s.x,s.y+3.4,"center","center",0
    elif s.kind=="TP": rx,ry,vx,vy,fa=(s.x+1.5,s.y-3.5,s.x+1.5,s.y-2,0) if s.rot==0 else (s.x+1.5,s.y+3.5,s.x+1.5,s.y+5,0)
    elif s.kind in("POT","TRIM"): rx,ry,vx,vy,fa=(s.x+4,s.y+2,s.x+4,s.y+3.5,0) if not horiz else (s.x,s.y+6,s.x,s.y+7.5,90); rj=vj=("left" if not horiz else "center")
    elif s.kind in("OPA",): rx,ry,vx,vy,fa=(s.x+1,s.y+5,s.x+1,s.y+6.5,0) if s.unit!=3 else (s.x+1,s.y-1,s.x+1,s.y+1,0)
    elif s.kind=="DG": rx,ry,vx,vy,fa=s.x-3,s.y-4.5,s.x-3,s.y+5,0
    elif s.kind=="CNT": rx,ry,vx,vy,fa=s.x+2,s.y-22,s.x+2,s.y+24,0
    else: rx,ry,vx,vy,fa=s.x+3,s.y-6,s.x+3,s.y+7,(90 if horiz else 0)
    if s.pwr:
        up = (s.kind in("+15V","+5V","-15V","FLG") and s.rot==0) or (s.kind=="GND" and s.rot==180)
        rx,ry,vx,vy,rj,vj,fa=s.x,s.y,s.x,(s.y-3.6 if up else s.y+4.2),"center","center",0
    if s.kind=="FLG": vy=s.y-4.2
    if s.rot==180 and not s.pwr: rj,vj=[('right' if j=='left' else 'left' if j=='right' else j) for j in (rj,vj)]
    mir=" (mirror x)" if s.mirror else ""
    o=[f'(symbol (lib_id {q(key)}) (at {mm(s.x)} {mm(s.y)} {s.rot}){mir} (unit {s.unit}) (in_bom {"no" if s.pwr else "yes"}) (on_board {"no" if s.pwr else "yes"}) (dnp no) (uuid {U()})',
       f'  (property "Reference" {q(s.ref)} (at {mm(rx)} {mm(ry)} {fa}) (effects (font (size 1.27 1.27)){"" if rj=="center" else (" (justify right)" if rj=="right" else " (justify left)")}{" hide" if s.pwr else ""}))',
       f'  (property "Value" {q(s.value)} (at {mm(vx)} {mm(vy)} {fa}) (effects (font (size 1.27 1.27)){"" if vj=="center" else (" (justify right)" if vj=="right" else " (justify left)")}{" hide" if hide_val else ""}))',
       f'  (property "Footprint" {q(s.fp)} (at {mm(s.x)} {mm(s.y)} 0) (effects (font (size 1.27 1.27)) hide))',
       f'  (property "Datasheet" "~" (at {mm(s.x)} {mm(s.y)} 0) (effects (font (size 1.27 1.27)) hide))']
    for k in s.pl: o.append(f'  (pin {q(k)} (uuid {U()}))')
    o.append(f'  (instances (project {q(PROJ)} (path "/{ROOT}" (reference {q(s.ref)}) (unit {s.unit}))))'); o.append(')')
    out.append("\n".join(o))
for a,b in wires: out.append(f'(wire (pts (xy {mm(a[0])} {mm(a[1])}) (xy {mm(b[0])} {mm(b[1])})) (stroke (width 0) (type default)) (uuid {U()}))')
for p in junc: out.append(f'(junction (at {mm(p[0])} {mm(p[1])}) (diameter 0) (color 0 0 0 0) (uuid {U()}))')
for p in ncs: out.append(f'(no_connect (at {mm(p[0])} {mm(p[1])}) (uuid {U()}))')
for name,p,ang in labels:
    j="left bottom" if ang in(0,90) else "right bottom"
    out.append(f'(label {q(name)} (at {mm(p[0])} {mm(p[1])} {ang}) (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify {j})) (uuid {U()}))')
for s,x,y,size,bold in texts:
    out.append(f'(text {q(s)} (at {mm(x)} {mm(y)} 0) (effects (font (size {size} {size}){" bold" if bold else ""}) (justify left bottom)) (uuid {U()}))')
doc=[f'(kicad_sch (version 20230121) (generator eeschema)',f'(uuid {ROOT})','(paper "A1")',
 '(title_block (title "Varactor half-bridge gain cell - v3 (bootstrapped bias servo)") (date "2026-11-13") (rev "0.4") (comment 1 "One anti-series varactor pair vs fixed C0G; carrier-fed; charge amp + sync demod. 0 to ~-25 dB per cell."))',
 '(lib_symbols']+list(libs.values())+[')']+out+['(sheet_instances (path "/" (page "1")))',')']
open(f"{PROJ}.kicad_sch","w").write("\n".join(doc))
open(f"{PROJ}.kicad_pro","w").write(json.dumps({"meta":{"filename":f"{PROJ}.kicad_pro","version":1},"sheets":[[ROOT,""]]},indent=2))
from collections import defaultdict
bom=defaultdict(list); seen=set()
for i in insts:
    if i.pwr or i.ref in seen: continue
    seen.add(i.ref); bom[(i.value,SYMLIB[i.kind][1],i.fp)].append(i.ref)
import re as _re
key=lambda r:(_re.sub(r"\d+","",r),int(_re.sub(r"\D","",r) or 0))
with open("BOM.csv","w") as f:
    f.write("Qty,References,Value,Symbol,Footprint\n")
    for (v,sy,fp),refs in sorted(bom.items(),key=lambda kv:key(sorted(kv[1],key=key)[0])):
        refs=sorted(refs,key=key); f.write(f'{len(refs)},"{" ".join(refs)}","{v}",{sy},{fp}\n')
print("instances",len(insts),"wires",len(wires),"junctions",len(junc),"labels",len(labels))
