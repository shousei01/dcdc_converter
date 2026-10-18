"""Design definition: STM32G474 four-switch buck-boost, 12-48 V in, 1.5-48 V / 5 A / 50 W out.

Every part: ref, symbol (lib:name or custom:name), value, footprint, pin->net map, block, LCSC, MPN, notes.
The schematic generator places parts by block and connects pins with net labels.
"""
from dataclasses import dataclass, field

FP = {
    "R0402": "Resistor_SMD:R_0402_1005Metric",
    "R0603": "Resistor_SMD:R_0603_1608Metric",
    "R1206": "Resistor_SMD:R_1206_3216Metric",
    "R2512": "Resistor_SMD:R_2512_6332Metric",
    "C0402": "Capacitor_SMD:C_0402_1005Metric",
    "C0603": "Capacitor_SMD:C_0603_1608Metric",
    "C0805": "Capacitor_SMD:C_0805_2012Metric",
    "C1206": "Capacitor_SMD:C_1206_3216Metric",
    "C1210": "Capacitor_SMD:C_1210_3225Metric",
    "CP10x10": "Capacitor_SMD:CP_Elec_10x10.5",
    "L1770": "Inductor_SMD:L_Bourns_SRP1770TA_16.9x16.9mm",
    "L5030": "Inductor_SMD:L_Bourns_SRP5030T",
    "DFN5x6": "Package_TO_SOT_SMD:TDSON-8-1",
    "SOIC8": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "TX_PQ2620": "custom_fp:TX_PQ2620_12P",
    "SOIC8EP": "Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm",
    "SOIC16W": "Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm",
    "SOT23-6": "Package_TO_SOT_SMD:SOT-23-6",
    "SOT23": "Package_TO_SOT_SMD:SOT-23",
    "SOD123": "Diode_SMD:D_SOD-123",
    "SOT23-5": "Package_TO_SOT_SMD:SOT-23-5",
    "SOT223": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    "LQFP64": "Package_QFP:LQFP-64_10x10mm_P0.5mm",
    "SMB": "Diode_SMD:D_SMB",
    "SOD123F": "Diode_SMD:D_SOD-123F",
    "SMA": "Diode_SMD:D_SMA",
    "LED0603": "LED_SMD:LED_0603_1608Metric",
    "XTAL3225": "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    "FUSE2512": "Fuse:Fuse_2512_6332Metric",
    "TB2_508": "Connector_Phoenix_MSTB:PhoenixContact_MSTBA_2,5_2-G-5,08_1x02_P5.08mm_Horizontal",
    "TP8": "custom_fp:TestPads_1x08_P2.54mm_D2.0mm",
    "SWD10": "Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD",
    "H1x2": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    "H2x2": "Connector_PinHeader_2.54mm:PinHeader_2x02_P2.54mm_Vertical",
    "H1x3": "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
    "H1x6": "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
    "H1x8": "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
    "DIP12": "Button_Switch_SMD:SW_DIP_SPSTx06_Slide_6.7x16.8mm_W8.61mm_P2.54mm_LowProfile",
    "FB0603": "Inductor_SMD:L_0603_1608Metric",
}


@dataclass
class Part:
    ref: str
    sym: str
    value: str
    fp: str
    pins: dict
    block: str
    lcsc: str = ""
    mpn: str = ""
    note: str = ""
    dnp: bool = False


P: list[Part] = []


def add(ref, sym, value, fp, pins, block, lcsc="", mpn="", note="", dnp=False):
    P.append(Part(ref, sym, value, FP.get(fp, fp), pins, block, lcsc, mpn, note, dnp))


def R(ref, value, a, b, fp="R0402", block="", **kw):
    add(ref, "Device:R", value, fp, {"1": a, "2": b}, block, **kw)


def C(ref, value, a, b, fp="C0402", block="", **kw):
    add(ref, "Device:C", value, fp, {"1": a, "2": b}, block, **kw)


def CP(ref, value, pos, neg, fp="CP10x10", block="", **kw):
    add(ref, "Device:C_Polarized", value, fp, {"1": pos, "2": neg}, block, **kw)


# --------------------------------------------------------------------------------------------
# A. POWER STAGE  (single-inductor 4-switch buck-boost, LM5175-style bridge-return sense)
# --------------------------------------------------------------------------------------------
B = "A_POWER"
CP("C1", "47u 63V", "VBUS", "GND", block=B, note="Isolated bus bulk (LLC output / 4SBB input), low-ESR")
for i, ref in enumerate(["C2", "C3", "C4", "C5"]):
    C(ref, "2.2u 100V X7R", "VBUS", "GND", fp="C1210", block=B, note="Bus hot-loop MLCC, place at Q1 drain / RS; also LLC output caps")
C("C6", "100n 100V X7R", "VBUS", "GND", fp="C0603", block=B)
add("Q1", "Transistor_FET:BSC040N10NS5", "NCEP0140AG", "DFN5x6",
    {"1": "SW1", "2": "SW1", "3": "SW1", "4": "G1", "5": "VBUS"}, B, lcsc="C503009", mpn="NCEP0140AG",
    note="Input leg high side: hard-switched in buck -> low Qgd part (100 V, 18 mOhm, 26 nC)")
add("Q2", "Transistor_FET:BSC040N10NS5", "NCEP0160AG", "DFN5x6",
    {"1": "PGND", "2": "PGND", "3": "PGND", "4": "G2", "5": "SW1"}, B, lcsc="C503012", mpn="NCEP0160AG",
    note="Input leg low side: sync rectifier in buck at up to 5 A -> low Rds part (100 V, 8.5 mOhm)")
add("Q3", "Transistor_FET:BSC040N10NS5", "NCEP0160AG", "DFN5x6",
    {"1": "SW2", "2": "SW2", "3": "SW2", "4": "G3", "5": "VOUT"}, B, lcsc="C503012", mpn="NCEP0160AG",
    note="Output leg high side: static-on in buck (carries full 5 A) / SR in boost")
add("Q4", "Transistor_FET:BSC040N10NS5", "NCEP0140AG", "DFN5x6",
    {"1": "PGND", "2": "PGND", "3": "PGND", "4": "G4", "5": "SW2"}, B, lcsc="C503009", mpn="NCEP0140AG",
    note="Output leg low side: hard-switched in boost")
add("L1", "Device:L", "22u 23A sat", "L1770", {"1": "SW1", "2": "SW2"}, B, lcsc="C49308184",
    mpn="PSPMAA1770-220M-CGP", note="22 uH, Isat 23 A, Irms 12 A, DCR 25 mOhm; alt Bourns SRP1770TA-220M (same footprint)")
R("RS1", "4m 1% 2W", "PGND", "GND", fp="R2512", block=B,
  note="Bridge-return current sense (both low-side FET sources). Kelvin traces to U7. Low-ESL 2512 wide-terminal preferred")
for ref in ["C7", "C8", "C9", "C10"]:
    C(ref, "2.2u 100V X7R", "VOUT", "GND", fp="C1210", block=B, note="Output hot-loop MLCC, place at Q3 drain / RS")
CP("C11", "47u 63V", "VOUT", "GND", block=B)
C("C12", "100n 100V X7R", "VOUT", "GND", fp="C0603", block=B)
R("RSH1", "10m 1% 1W", "VOUT_N", "GND", fp="R2512", block=B, note="Output current shunt (CC loop), Kelvin to U8")
R("R1", "47k", "VOUT", "GND", fp="R1206", block=B, note="Output pre-load / bleeder (49 mW at 48 V)")
add("J2", "Connector_Generic:Conn_01x02", "VOUT 1.5-48V", "TB2_508", {"1": "VOUT", "2": "VOUT_N"}, B,
    mpn="KF2EDGR-5.08-2P", note="Output: 5.08 mm pluggable male header, 12 A")
# switch-node snubbers, populate only if ringing measured
R("R2", "2R2 DNP", "SW1", "SNB1", fp="R1206", block=B, dnp=True)
C("C13", "1n 100V DNP", "SNB1", "PGND", fp="C0603", block=B, dnp=True)
R("R3", "2R2 DNP", "SW2", "SNB2", fp="R1206", block=B, dnp=True)
C("C14", "1n 100V DNP", "SNB2", "PGND", fp="C0603", block=B, dnp=True)

# --------------------------------------------------------------------------------------------
# B. GATE DRIVERS  (UCC27211, independent HI/LI fed from HRTIM complementary outputs)
# --------------------------------------------------------------------------------------------
B = "B_DRIVE"
DRV_PINS = ("VDD", "HB", "HO", "HS", "HI", "LI", "VSS", "LO", "EP")
for (u, hb, ho, hs, hi, li, lo, gh, gl, cb, cv, cv2, rgh, rgl, rph, rpl, rhi, rli) in [
    ("U2", "HB1", "HO1", "SW1", "PWM_A1", "PWM_A2", "LO1", "G1", "G2", "C15", "C16", "C17", "R4", "R5", "R6", "R7", "R8", "R9"),
    ("U3", "HB2", "HO2", "SW2", "PWM_E1", "PWM_E2", "LO2", "G3", "G4", "C18", "C19", "C20", "R10", "R11", "R12", "R13", "R14", "R15"),
]:
    add(u, "custom:UCC27211", "UCC27211DDAR", "SOIC8EP",
        {"1": "+10V", "2": hb, "3": ho, "4": hs, "5": hi, "6": li, "7": "PGND", "8": lo, "9": "PGND"}, B,
        lcsc="C141980", mpn="UCC27211DDAR", note="120 V half-bridge driver, internal boot diode; 2nd source SLM27211CA-DG (C967931)")
    C(cb, "100n 25V X7R", hb, hs, fp="C0603", block=B, note="Bootstrap cap")
    C(cv, "1u 25V X7R", "+10V", "PGND", fp="C0603", block=B, note="Driver VDD decoupling at pin 1-7")
    C(cv2, "100n 25V", "+10V", "PGND", fp="C0402", block=B)
    R(rgh, "4R7", ho, gh, fp="R0603", block=B, note="High-side gate resistor")
    R(rgl, "4R7", lo, gl, fp="R0603", block=B, note="Low-side gate resistor")
    R(rph, "10k", gh, hs, fp="R0402", block=B, note="Gate-source pull-down")
    R(rpl, "10k", gl, "PGND", fp="R0402", block=B, note="Gate-source pull-down")
    R(rhi, "10k", hi, "GND", fp="R0402", block=B, note="Keeps input low while MCU in reset")
    R(rli, "10k", li, "GND", fp="R0402", block=B)

# --------------------------------------------------------------------------------------------
# C. AUXILIARY SUPPLIES  VIN -> 10 V (gate drive) -> 5 V (CAN) -> 3.3 V (MCU)
# --------------------------------------------------------------------------------------------
B = "C_AUX"
add("U4", "Regulator_Switching:LMR16006YQ", "LMR16006XDDCR", "SOT23-6",
    {"1": "CB_AUX", "2": "GND", "3": "FB_AUX", "4": "EN_AUX", "5": "VBUS", "6": "SW_AUX"}, B,
    lcsc="C87080", mpn="LMR16006XDDCR", note="60 V, 0.6 A, 700 kHz buck")
C("C21", "2.2u 100V X7R", "VBUS", "GND", fp="C1210", block=B)
C("C22", "100n 100V", "VBUS", "GND", fp="C0603", block=B)
R("R16", "470k", "VBUS", "EN_AUX", fp="R0603", block=B, note="EN divider: start ~9.7 V on the isolated bus")
R("R17", "68k", "EN_AUX", "GND", fp="R0402", block=B)
C("C23", "100n 25V", "CB_AUX", "SW_AUX", fp="C0402", block=B, note="LMR16006 boot cap")
add("D2", "Device:D_Schottky", "SS110", "SMA", {"1": "SW_AUX", "2": "GND"}, B, lcsc="C224219", mpn="SS110",
    note="100 V 1 A Schottky catch diode")
add("L2", "Device:L", "47u 1A", "L5030", {"1": "SW_AUX", "2": "+10V"}, B, note="47 uH, Isat >= 1 A, 5x5 mm shielded")
R("R18", "120k 1%", "+10V", "FB_AUX", fp="R0402", block=B, note="Vout = 0.765*(1+120k/10k) = 9.95 V")
R("R19", "10k 1%", "FB_AUX", "GND", fp="R0402", block=B)
C("C24", "10u 25V X5R", "+10V", "GND", fp="C0805", block=B)
C("C25", "10u 25V X5R", "+10V", "GND", fp="C0805", block=B)
add("U5", "Regulator_Linear:AMS1117-5.0", "AMS1117-5.0", "SOT223", {"1": "GND", "2": "+5V", "3": "+10V"}, B,
    lcsc="C6187", mpn="AMS1117-5.0", note="5 V for CAN transceiver VCC (up to 125 mA dominant); live once the LLC runs")
C("C26", "10u 25V X5R", "+5V", "GND", fp="C0805", block=B)
C("C27", "22u 10V X5R", "+3V3", "GND", fp="C0805", block=B)
add("FB1", "Device:FerriteBead_Small", "600R@100MHz", "FB0603", {"1": "+3V3", "2": "+3V3A"}, B, note="VDDA filter")
C("C28", "1u 10V", "+3V3A", "GND", fp="C0402", block=B)
C("C29", "100n", "+3V3A", "GND", fp="C0402", block=B)

# --------------------------------------------------------------------------------------------
# D. MCU  STM32G474RBT6 (LQFP64)
# --------------------------------------------------------------------------------------------
B = "D_MCU"
mcu = {
    "1": "+3V3",          # VBAT
    "16": "+3V3", "32": "+3V3", "48": "+3V3", "64": "+3V3",
    "15": "GND", "31": "GND", "47": "GND", "63": "GND", "27": "GND",   # VSS x4, VSSA
    "29": "+3V3A",        # VDDA
    "28": "+3V3A",        # VREF+ used as input, tied to VDDA 3.3 V
    "5": "OSC_IN", "6": "OSC_OUT",
    "7": "NRST", "61": "BOOT0",
    "42": "PWM_A1",       # PA8  HRTIM1_CHA1 -> Q1 (input high side)
    "43": "PWM_A2",       # PA9  HRTIM1_CHA2 -> Q2 (input low side)
    "40": "PWM_E1",       # PC8  HRTIM1_CHE1 -> Q3 (output high side)
    "41": "PWM_E2",       # PC9  HRTIM1_CHE2 -> Q4 (output low side)
    "45": "CAN_RXD",      # PA11 FDCAN1_RX
    "46": "CAN_TXD",      # PA12 FDCAN1_TX
    "49": "SWDIO", "50": "SWCLK", "56": "SWO",
    "12": "VBUS_SNS",      # PA0  ADC1_IN1 / ADC2_IN1
    "13": "IOUT_SNS",     # PA1  ADC1_IN2 / ADC2_IN2
    "33": "VOUT_SNS",     # PB11 ADC1_IN14 / ADC2_IN14 + COMP6_INP (fast OVP)
    "25": "IL_SNS",       # PB1  ADC1_IN12 + COMP1_INP (positive OCP, boost)
    "24": "IL_SNS",       # PB0  COMP4_INP (negative OCP, buck; output polarity inverted)
    "20": "NTC_SNS",      # PA6  ADC2_IN3 (PA4 reserved for DAC1_OUT1)
    "51": "VIN_OVP",      # PA15 HRTIM1_FLT2 / EXTI15, input over-voltage from primary
    "19": "TP_DAC",       # PA5  DAC1_OUT2 test output
    "59": "TP_GPIO1",     # PB6  test GPIO
    "60": "TP_GPIO2",     # PB7  test GPIO
    "8": "ADDR0", "9": "ADDR1", "10": "ADDR2", "11": "ADDR3", "22": "ADDR4", "23": "ADDR5",
    "34": "LLC_A",        # PB12 HRTIM1_CHC1 -> isolator -> LLC high side (Q5)
    "35": "LLC_B",        # PB13 HRTIM1_CHC2 -> isolator -> LLC low side (Q6)
    "36": "SR1_PWM",      # PB14 HRTIM1_CHD1 -> UCC27524 A -> Q7
    "37": "SR2_PWM",      # PB15 HRTIM1_CHD2 -> UCC27524 B -> Q8
    "53": "SR_EN",        # PC11 GPIO, SR driver enable (after +10V is up)
    "62": "LED_RUN",      # PB9 (moved from PC13 for PCB routing)
    "52": "LED_FLT",      # PC10
}
add("U1", "MCU_ST_STM32G4:STM32G474RBTx", "STM32G474RBT6", "LQFP64", mcu, B, lcsc="C529413", mpn="STM32G474RBT6",
    note="Pin-compatible STM32G474RET6 (C521608) if RB is out of stock")
for ref in ["C30", "C31", "C32", "C33", "C34"]:
    C(ref, "100n", "+3V3", "GND", fp="C0402", block=B, note="One per VDD pin + VBAT")
C("C35", "4.7u 10V", "+3V3", "GND", fp="C0603", block=B)
C("C36", "1u 10V", "+3V3A", "GND", fp="C0402", block=B, note="VREF+ decoupling (VREF+ = VDDA = 3.3 V)")
C("C37", "100n", "+3V3A", "GND", fp="C0402", block=B, note="VREF+ pin 28")
add("Y1", "Device:Crystal_GND24", "16MHz 9pF", "XTAL3225", {"1": "OSC_IN", "3": "OSC_OUT", "2": "GND", "4": "GND"}, B,
    lcsc="C13738", mpn="X322516MLB4SI", note="16 MHz HSE, 9 pF load, ESR 50 Ohm; PLL /4 x85 /2 = 170 MHz")
C("C38", "12p C0G", "OSC_IN", "GND", fp="C0402", block=B)
C("C39", "12p C0G", "OSC_OUT", "GND", fp="C0402", block=B)
C("C40", "100n", "NRST", "GND", fp="C0402", block=B)
R("R20", "10k", "BOOT0", "GND", fp="R0402", block=B, note="Boot from flash")

# --------------------------------------------------------------------------------------------
# E. SENSING
# --------------------------------------------------------------------------------------------
B = "E_SENSE"
R("R21", "100k 0.1%", "VBUS", "VBUS_SNS", fp="R0603", block=B, note="Isolated bus ~= VIN (DCX ratio 1); FS 68 V at 3.3 V VREF+")
R("R22", "5.1k 0.1%", "VBUS_SNS", "GND", fp="R0402", block=B)
C("C41", "1n C0G", "VBUS_SNS", "GND", fp="C0402", block=B)
R("R23", "100k 0.1%", "VOUT", "VOUT_SNS", fp="R0603", block=B, note="Divider referenced to GND; firmware adds Iout*RSH1")
R("R24", "5.1k 0.1%", "VOUT_SNS", "GND", fp="R0402", block=B)
C("C42", "1n C0G", "VOUT_SNS", "GND", fp="C0402", block=B)
# inductor / bridge current, bidirectional around VREF/2
add("U7", "Amplifier_Current:INA181", "INA181A1IDBVR", "SOT23-6",
    {"1": "IL_AMP", "2": "GND", "3": "PGND", "4": "GND", "5": "IL_REF", "6": "+3V3A"}, B,
    lcsc="C2058943", mpn="INA181A1IDBVR",
    note="Gain 20: IL_SNS = 1.65 V + 0.08 V/A * IL (+ in boost, - in buck). IN+/IN- Kelvin to RS1 pads")
R("R25", "1k 0.1%", "+3V3A", "IL_REF", fp="R0402", block=B)
R("R26", "1k 0.1%", "IL_REF", "GND", fp="R0402", block=B)
C("C43", "100n", "IL_REF", "GND", fp="C0402", block=B)
C("C44", "100n", "+3V3A", "GND", fp="C0402", block=B)
R("R27", "100R", "IL_AMP", "IL_SNS", fp="R0402", block=B)
C("C45", "470p C0G", "IL_SNS", "GND", fp="C0402", block=B, note="Keep RC fast (~47 ns) for comparator OCP")
# output current
add("U8", "Amplifier_Current:INA181", "INA181A2IDBVR", "SOT23-6",
    {"1": "IOUT_AMP", "2": "GND", "3": "VOUT_N", "4": "GND", "5": "GND", "6": "+3V3A"}, B,
    lcsc="C2058784", mpn="INA181A2IDBVR", note="Gain 50: 0.5 V/A, 5 A = 2.5 V")
C("C46", "100n", "+3V3A", "GND", fp="C0402", block=B)
R("R28", "1k", "IOUT_AMP", "IOUT_SNS", fp="R0402", block=B)
C("C47", "10n C0G", "IOUT_SNS", "GND", fp="C0402", block=B)
# temperature (place NTC between Q1 and Q4)
R("R29", "10k 1%", "+3V3A", "NTC_SNS", fp="R0402", block=B)
add("TH1", "Device:Thermistor_NTC", "10k B3950", "R0603", {"1": "NTC_SNS", "2": "GND"}, B, note="Place at hottest FET")
C("C48", "100n", "NTC_SNS", "GND", fp="C0402", block=B)

# --------------------------------------------------------------------------------------------
# F. ISOLATED CAN
# --------------------------------------------------------------------------------------------
B = "F_CAN"
add("U9", "custom:CA-IS3062VW", "CA-IS3062VW", "SOIC16W",
    {"1": "+5V", "2": "GND", "3": "CAN_TXD", "4": "NC", "5": "CAN_RXD", "6": "NC", "7": "+3V3", "8": "GND",
     "9": "GND_ISO", "10": "GND_ISO", "11": "VISO", "12": "CANL", "13": "CANH", "14": "NC", "15": "GND_ISO",
     "16": "VISO"}, B, lcsc="C5338808", mpn="CA-IS3062VW",
    note="5 kVrms isolated CAN with integrated isolated DC-DC; VCCL=3.3 V logic")
C("C49", "10u 10V", "+5V", "GND", fp="C0805", block=B)
C("C50", "100n", "+5V", "GND", fp="C0402", block=B, note="Within 2 mm of pin 1")
C("C51", "1u 10V", "+3V3", "GND", fp="C0402", block=B, note="VCCL pin 7")
C("C52", "10u 10V", "VISO", "GND_ISO", fp="C0805", block=B)
C("C53", "100n", "VISO", "GND_ISO", fp="C0402", block=B, note="Pin 16")
C("C54", "100n", "VISO", "GND_ISO", fp="C0402", block=B, note="Pin 11")
R("R30", "60.4R", "CAN_TH", "CAN_MID", fp="R0603", block=B, note="Split termination, enabled by JP1 (both jumpers)")
R("R31", "60.4R", "CAN_MID", "CAN_TL", fp="R0603", block=B)
C("C55", "4.7n", "CAN_MID", "GND_ISO", fp="C0603", block=B)
add("JP1", "Connector_Generic:Conn_02x02_Odd_Even", "TERM", "H2x2", {"1": "CAN_TH", "2": "CANH", "3": "CANL", "4": "CAN_TL"}, B,
    note="2x2 header: fit 2 shunts (1-2 CANH, 3-4 CANL) on end-of-bus node; open = termination fully disconnected from both lines")
add("D3", "Power_Protection:NUP2105L", "NUP2105L", "SOT23", {"1": "CANH", "2": "CANL", "3": "GND_ISO"}, B,
    mpn="NUP2105LT1G", note="24 V CAN bus ESD/TVS")
add("J3", "Connector_Generic:Conn_01x03", "CAN A", "H1x3", {"1": "CANH", "2": "CANL", "3": "GND_ISO"}, B,
    mpn="2.54 mm 1x3 male pin header", note="CAN in")
add("J4", "Connector_Generic:Conn_01x03", "CAN B", "H1x3", {"1": "CANH", "2": "CANL", "3": "GND_ISO"}, B,
    mpn="2.54 mm 1x3 male pin header", note="CAN out (daisy-chain)")
C("C56", "2.2n 2kV DNP", "GND", "GND_ISO", fp="Capacitor_THT:C_Disc_D8.0mm_W5.0mm_P7.50mm", block=B, dnp=True, note="Optional Y-cap for EMI")

# --------------------------------------------------------------------------------------------
# G. ADDRESS, DEBUG, STATUS
# --------------------------------------------------------------------------------------------
B = "G_IO"
add("SW1", "Switch:SW_DIP_x06", "DIP-6", "DIP12",
    {**{str(k): f"ADDR{k-1}" for k in range(1, 7)}, **{str(13 - k): "GND" for k in range(1, 7)}}, B,
    note="ON = 0. Address = ~ADDR[5:0]")
for k in range(6):
    R(f"R{32+k}", "10k", f"ADDR{k}", "+3V3", fp="R0402", block=B)
    R(f"R{38+k}", "1k", f"ADDR_H{k}", f"ADDR{k}", fp="R0402", block=B, note="Header series protection")
add("J5", "Connector_Generic:Conn_01x06", "ADDR HDR", "H1x6", {str(k + 1): f"ADDR_H{k}" for k in range(6)}, B,
    note="Shorting a pin to GND (via harness) sets bit = 0; parallel with SW1")
add("J6", "Connector_Generic:Conn_01x08", "PROG PADS", "TP8",
    {"1": "SWDIO", "2": "SWCLK", "3": "TP_DAC", "4": "TP_GPIO1", "5": "TP_GPIO2", "6": "NRST", "7": "+3V3", "8": "GND"}, B,
    note="8 round test pads, 2.54 mm pitch, pad 1 square (pogo-pin programming fixture)")
add("J7", "Connector_Generic:Conn_02x05_Odd_Even", "ARM SWD 10", "SWD10",
    {"1": "+3V3", "2": "SWDIO", "3": "GND", "4": "SWCLK", "5": "GND", "6": "SWO", "7": "NC", "8": "NC", "9": "GND", "10": "NRST"}, B,
    mpn="FTSH-105-01-L-DV-K or equiv.", note="ARM Cortex Debug 10-pin, 1.27 mm (1 VTref, 2 SWDIO, 4 SWCLK, 6 SWO, 10 nRESET, 7 key)")
add("D4", "Device:LED", "GREEN RUN", "LED0603", {"1": "LED_RUN_K", "2": "+3V3"}, B)
R("R44", "1k", "LED_RUN_K", "LED_RUN", fp="R0402", block=B)
add("D5", "Device:LED", "RED FAULT", "LED0603", {"1": "LED_FLT_K", "2": "+3V3"}, B)
R("R45", "1k", "LED_FLT_K", "LED_FLT", fp="R0402", block=B)


# --------------------------------------------------------------------------------------------
# H. LLC DCX  (primary half-bridge, split resonant caps, PQ2620 1:2:2, centre-tapped SR)
# --------------------------------------------------------------------------------------------
B = "H_LLC"
add("J1", "Connector_Generic:Conn_01x02", "VIN 12-48V", "TB2_508", {"1": "VIN_RAW", "2": "GNDP"}, B,
    mpn="KF2EDGR-5.08-2P", note="Input: 5.08 mm pluggable male header (mates KF2EDGK plug), 12 A. PRIMARY side")
add("F1", "Device:Fuse", "7A", "FUSE2512", {"1": "VIN_RAW", "2": "VIN"}, B, note="Fast-acting 7 A chip fuse, >=63 V rating, 2512")
add("D1", "Device:D_Zener", "SMBJ51A", "SMB", {"1": "VIN", "2": "GNDP"}, B, mpn="SMBJ51A",
    note="Unidirectional TVS, 51 V standoff, 82 V clamp; with F1 also clears reverse polarity")
CP("C60", "47u 63V", "VIN", "GNDP", block=B, note="Primary bulk, low-ESR")
for ref in ["C61", "C62", "C63"]:
    C(ref, "2.2u 100V X7R", "VIN", "GNDP", fp="C1210", block=B, note="Half-bridge decoupling at Q5 drain / Q6 source")
add("Q5", "Transistor_FET:BSC040N10NS5", "NCEP0160AG", "DFN5x6",
    {"1": "HB_SW", "2": "HB_SW", "3": "HB_SW", "4": "G5", "5": "VIN"}, B, lcsc="C503012", mpn="NCEP0160AG",
    note="LLC high side, ZVS; 10 A rms at 12 V in -> lowest-Rds part")
add("Q6", "Transistor_FET:BSC040N10NS5", "NCEP0160AG", "DFN5x6",
    {"1": "GNDP", "2": "GNDP", "3": "GNDP", "4": "G6", "5": "HB_SW"}, B, lcsc="C503012", mpn="NCEP0160AG",
    note="LLC low side, ZVS")
for ref in ["CR1", "CR2", "CR3"]:
    C(ref, "100n 100V C0G", "VIN", "CR_MID", fp="C1206", block=B, note="Split resonant cap, upper half (3 x 100 nF)")
for ref in ["CR4", "CR5", "CR6"]:
    C(ref, "100n 100V C0G", "CR_MID", "GNDP", fp="C1206", block=B, note="Split resonant cap, lower half (3 x 100 nF); Cr total 600 nF")
add("T1", "Device:Transformer_1P_SS", "PQ2620 4:8+8", "TX_PQ2620",
    {"1": "HB_SW", "2": "CR_MID", "3": "SR_D1", "4": "VBUS", "5": "SR_D2"}, B,
    note="CUSTOM: PQ2620 N97/PC95, Np=4 (litz), Ns=8+8 centre-tap (TIW), Lm=50uH +/-10% (gapped), "
         "Llk=1.0uH +/-20% (is Lr), fr~205 kHz, 3 kVrms basic pri-sec, 10.1 A rms pri / 3.6 A rms per sec half")
add("Q7", "Transistor_FET:BSC040N10NS5", "BSC160N15NS5", "DFN5x6",
    {"1": "GND", "2": "GND", "3": "GND", "4": "G7", "5": "SR_D1"}, B, lcsc="C459172", mpn="BSC160N15NS5",
    note="SR, 150 V (sees 2 x Vbus = 95 V at 48 V in), 16 mOhm, 19 nC")
add("Q8", "Transistor_FET:BSC040N10NS5", "BSC160N15NS5", "DFN5x6",
    {"1": "GND", "2": "GND", "3": "GND", "4": "G8", "5": "SR_D2"}, B, lcsc="C459172", mpn="BSC160N15NS5")
R("R60", "4R7 DNP", "SR_D1", "SNB3", fp="R1206", block=B, dnp=True, note="SR snubber, fit only if ringing measured")
C("C64", "1n 200V DNP", "SNB3", "GND", fp="C0805", block=B, dnp=True)
R("R61", "4R7 DNP", "SR_D2", "SNB4", fp="R1206", block=B, dnp=True)
C("C65", "1n 200V DNP", "SNB4", "GND", fp="C0805", block=B, dnp=True)
C("C66", "1n Y1 DNP", "GNDP", "GND", fp="Capacitor_THT:C_Disc_D8.0mm_W5.0mm_P7.50mm", block=B, dnp=True,
  note="Optional pri-sec Y-cap for EMI: must be Y1/Y2 safety-rated if fitted; else leave empty")
# primary half-bridge driver
add("U10", "custom:UCC27211", "UCC27211DDAR", "SOIC8EP",
    {"1": "+10V_P", "2": "HBP", "3": "HOP", "4": "HB_SW", "5": "LLC_HI_P", "6": "LLC_LO_P", "7": "GNDP", "8": "LOP", "9": "GNDP"}, B,
    lcsc="C141980", mpn="UCC27211DDAR", note="Primary LLC half-bridge driver")
C("C67", "100n 25V X7R", "HBP", "HB_SW", fp="C0603", block=B, note="Bootstrap cap")
C("C68", "1u 25V X7R", "+10V_P", "GNDP", fp="C0603", block=B)
R("R62", "2R2", "HOP", "G5", fp="R0603", block=B)
R("R63", "2R2", "LOP", "G6", fp="R0603", block=B)
R("R64", "10k", "G5", "HB_SW", fp="R0402", block=B)
R("R65", "10k", "G6", "GNDP", fp="R0402", block=B)
R("R66", "10k", "LLC_HI_P", "GNDP", fp="R0402", block=B, note="Gate off while isolator unpowered")
R("R67", "10k", "LLC_LO_P", "GNDP", fp="R0402", block=B)
# secondary SR driver
add("U11", "custom:UCC27524", "UCC27524DR", "SOIC8",
    {"1": "SR_EN", "2": "SR1_PWM", "3": "GND", "4": "SR2_PWM", "5": "SR_OB", "6": "+10V", "7": "SR_OA", "8": "SR_EN"}, B,
    lcsc="C465729", mpn="UCC27524DR", note="Dual 5 A low-side driver for the SRs; EN low = body-diode rectification")
C("C69", "1u 25V X7R", "+10V", "GND", fp="C0603", block=B)
R("R68", "4R7", "SR_OA", "G7", fp="R0603", block=B)
R("R69", "4R7", "SR_OB", "G8", fp="R0603", block=B)
R("R70", "10k", "G7", "GND", fp="R0402", block=B)
R("R71", "10k", "G8", "GND", fp="R0402", block=B)
R("R72", "10k", "SR_EN", "GND", fp="R0402", block=B, note="SR disabled until MCU enables")
R("R73", "10k", "SR1_PWM", "GND", fp="R0402", block=B)
R("R74", "10k", "SR2_PWM", "GND", fp="R0402", block=B)

# --------------------------------------------------------------------------------------------
# I. PRIMARY AUX + ISOLATOR  (VIN -> 10 V_P -> 5 V_P; CA-IS3642LVW: power -> secondary, gates <- secondary)
# --------------------------------------------------------------------------------------------
B = "I_PRI"
add("U13", "Regulator_Switching:LMR16006YQ", "LMR16006XDDCR", "SOT23-6",
    {"1": "CB_P", "2": "GNDP", "3": "FB_P", "4": "EN_P", "5": "VIN", "6": "SW_P"}, B,
    lcsc="C87080", mpn="LMR16006XDDCR", note="Primary aux buck")
C("C70", "2.2u 100V X7R", "VIN", "GNDP", fp="C1210", block=B)
R("R75", "470k", "VIN", "EN_P", fp="R0603", block=B, note="Primary UVLO ~9.7 V")
R("R76", "68k", "EN_P", "GNDP", fp="R0402", block=B)
C("C71", "100n 25V", "CB_P", "SW_P", fp="C0402", block=B)
add("D6", "Device:D_Schottky", "SS110", "SMA", {"1": "SW_P", "2": "GNDP"}, B, lcsc="C224219", mpn="SS110", note="100 V 1 A Schottky catch diode")
add("L3", "Device:L", "47u 1A", "L5030", {"1": "SW_P", "2": "+10V_P"}, B)
R("R77", "120k 1%", "+10V_P", "FB_P", fp="R0402", block=B)
R("R78", "10k 1%", "FB_P", "GNDP", fp="R0402", block=B)
C("C72", "10u 25V X5R", "+10V_P", "GNDP", fp="C0805", block=B)
add("U14", "Regulator_Linear:AMS1117-5.0", "AMS1117-5.0", "SOT223", {"1": "GNDP", "2": "+5V_P", "3": "+10V_P"}, B,
    lcsc="C6187", mpn="AMS1117-5.0", note="5 V for the isolator (about 0.6 W in)")
C("C73", "22u 10V X5R", "+5V_P", "GNDP", fp="C0805", block=B)
add("U12", "custom:CA-IS3642LVW", "CA-IS3642LVW", "SOIC16W",
    {"1": "+5V_P", "2": "GNDP", "3": "OVP_P", "4": "VINPWM_P", "5": "LLC_HI_P", "6": "LLC_LO_P", "7": "+5V_P", "8": "GNDP",
     "9": "GND", "10": "GND", "11": "LLC_B", "12": "LLC_A", "13": "VIN_PWM", "14": "VIN_OVP", "15": "GND", "16": "+3V3"}, B,
    lcsc="C7422564", mpn="CA-IS3642LVW",
    note="5 kVrms isolator, 2 fwd + 2 rev, 650 mW isolated 3.3 V (SEL=GNDB) for the MCU; L = outputs default low")
C("C74", "10u 10V", "+5V_P", "GNDP", fp="C0805", block=B)
C("C75", "100n", "+5V_P", "GNDP", fp="C0402", block=B)
C("C76", "1u 10V", "+5V_P", "GNDP", fp="C0402", block=B, note="VDDL pin 7")
C("C77", "100n", "+3V3", "GND", fp="C0402", block=B, note="VISO pin 16, within 2 mm")
C("C78", "47u 6.3V", "+3V3", "GND", fp="C1206", block=B, note="VISO bulk (datasheet recommends 47 uF)")
R("R79", "10k", "LLC_A", "GND", fp="R0402", block=B, note="Holds isolator input low while MCU in reset")
R("R80", "10k", "LLC_B", "GND", fp="R0402", block=B)


# --------------------------------------------------------------------------------------------
# I (cont.) INPUT OVP: VIN > 50 V -> OVP_P high -> U12 ch1 -> VIN_OVP (PA15 / HRTIM1_FLT2)
# --------------------------------------------------------------------------------------------
B = "I_PRI"
R("R81", "191k 0.1%", "VIN", "OVP_DIV", fp="R1206", block=B, note="OVP / VIN-monitor divider top: 2.495 V x (1+191k/10k) = 50.15 V trip; 0.1 % sets the VIN reading accuracy")
R("R82", "10k 0.1%", "OVP_DIV", "GNDP", fp="R0402", block=B)
C("C79", "1n C0G", "OVP_DIV", "GNDP", fp="C0402", block=B, note="Noise filter, ~10 us")
add("U15", "Comparator:LMV331", "LMV331IDBVR", "SOT23-5", {"1": "OVP_DIV", "2": "GNDP", "3": "VREF_P", "4": "OVP_P", "5": "+5V_P"}, B,
    mpn="LMV331IDBVR", note="Open-drain comparator; output high (released) = OVP")
C("C80", "100n", "+5V_P", "GNDP", fp="C0402", block=B)
R("R83", "10k", "+5V_P", "OVP_P", fp="R0402", block=B, note="Pull-up for open-drain output")
R("R84", "2.2M", "OVP_P", "OVP_DIV", fp="R0402", block=B, note="Hysteresis ~0.4 V at VIN")
add("U16", "Reference_Voltage:TL431DBZ", "TL431AIDBZR", "SOT23", {"1": "VREF_P", "2": "VREF_P", "3": "GNDP"}, B,
    mpn="TL431AIDBZR (TI pinout: 1 K, 2 REF, 3 A)", note="2.495 V reference, 0.5 %")
R("R85", "1k", "+5V_P", "VREF_P", fp="R0402", block=B, note="TL431 bias 2.5 mA")

# --------------------------------------------------------------------------------------------
# I (cont.) VIN MONITOR: linear sawtooth 0 -> VREF_P (2.495 V), compared with OVP_DIV -> PWM -> U12 VI2 -> VO2 -> PA2
#   ramp: PNP current source (~24 uA) into 47 nF C0G -> ~5 ms; U17 detects RAMP > VREF_P, D7/C81/R107 stretch the
#   reset to ~20 us, Q10 empties C82. U18: output high while RAMP > OVP_DIV (R110 adds ~1 % fixed hysteresis).
#   VIN = 2.495 V / 0.04954 x (T_ramp - t_high) / T_ramp, T_ramp = period - ~20 us. Monitoring only, ~200 Hz.
# --------------------------------------------------------------------------------------------
R("R86", "56k 1%", "+5V_P", "PE_P", fp="R0402", block=B, note="Ramp current source emitter resistor (~24 uA)")
R("R87", "10k 1%", "+5V_P", "PB_P", fp="R0402", block=B, note="PNP base bias 3.0 V")
R("R88", "15k 1%", "PB_P", "GNDP", fp="R0402", block=B)
add("Q9", "Transistor_BJT:MMBT3906", "MMBT3906", "SOT23", {"1": "PB_P", "2": "PE_P", "3": "RAMP_P"}, B,
    lcsc="C2940", mpn="MMBT3906", note="Ramp current source")
C("C82", "47n C0G 50V", "RAMP_P", "GNDP", fp="C0805", block=B, note="Ramp capacitor - must be C0G (X7R bends the ramp)")
add("U17", "Comparator:LMV331", "LMV331IDBVR", "SOT23-5", {"1": "RAMP_P", "2": "GNDP", "3": "VREF_P", "4": "RST_P", "5": "+5V_P"}, B,
    mpn="LMV331IDBVR", note="Ramp top detector: output released when RAMP > VREF_P")
R("R106", "1k", "+5V_P", "RST_P", fp="R0402", block=B, note="Pull-up, charges the reset-hold cap fast")
add("D7", "Device:D", "1N4148W", "SOD123", {"1": "GATE_P", "2": "RST_P"}, B, lcsc="C81598", mpn="1N4148W")
C("C81", "1n", "GATE_P", "GNDP", fp="C0402", block=B, note="Reset hold ~20 us with R107")
R("R107", "22k", "GATE_P", "GNDP", fp="R0402", block=B)
add("Q10", "Transistor_FET:2N7002", "2N7002", "SOT23", {"1": "GATE_P", "2": "GNDP", "3": "DIS_P"}, B,
    lcsc="C8545", mpn="2N7002", note="Ramp reset switch")
R("R89", "22R", "DIS_P", "RAMP_P", fp="R0402", block=B, note="Limits discharge peak current")
C("C83", "100n", "+5V_P", "GNDP", fp="C0402", block=B)
R("R109", "10k", "RAMP_P", "RAMPS_P", fp="R0402", block=B, note="Series R for U18 hysteresis")
add("U18", "Comparator:LMV331", "LMV331IDBVR", "SOT23-5", {"1": "RAMPS_P", "2": "GNDP", "3": "OVP_DIV", "4": "VINPWM_P", "5": "+5V_P"}, B,
    mpn="LMV331IDBVR", note="PWM comparator: output high while RAMP > OVP_DIV")
R("R110", "1M", "VINPWM_P", "RAMPS_P", fp="R0402", block=B, note="~1 % fixed hysteresis, stops chatter on the slow ramp")
R("R108", "10k", "+5V_P", "VINPWM_P", fp="R0402", block=B, note="Pull-up -> U12 VI2 (pin 4)")
C("C84", "100n", "+5V_P", "GNDP", fp="C0402", block=B)

# --------------------------------------------------------------------------------------------
# D (cont.) unused MCU pins: 10k to GND each
# --------------------------------------------------------------------------------------------
B = "D_MCU"
UNUSED = [("2", "PC13"), ("3", "PC14"), ("4", "PC15"), ("14", "PA2"), ("17", "PA3"), ("18", "PA4"), ("21", "PA7"), ("26", "PB2"),
          ("30", "PB10"), ("38", "PC6"), ("39", "PC7"), ("44", "PA10"), ("54", "PC12"), ("55", "PD2"), ("57", "PB4"), ("58", "PB5")]
for i, (pin, port) in enumerate(UNUSED):
    n = "VIN_PWM" if port == "PA2" else f"SP_{port}"
    mcu[pin] = n
    R(f"R{90 + i}", "10k", n, "GND", fp="R0402", block=B, note=("VIN_PWM pull-down (PA2 = TIM15_CH1 PWM input)" if port == "PA2" else f"Unused {port} pull-down" + (" (PA4 reserved for DAC1_OUT1)" if port == "PA4" else "")))

# --------------------------------------------------------------------------------------------
# T. TEST POINTS (rails and filtered analog nodes only; no switch nodes / gates / high-Z dividers)
# --------------------------------------------------------------------------------------------
B = "T_TP"
TPS = [("TP1", "VIN", "I_PRI"), ("TP2", "GNDP", "I_PRI"), ("TP3", "+10V_P", "I_PRI"), ("TP4", "+5V_P", "I_PRI"),
       ("TP5", "VBUS", "C_AUX"), ("TP6", "+10V", "C_AUX"), ("TP7", "+5V", "C_AUX"), ("TP8", "+3V3", "C_AUX"),
       ("TP9", "+3V3A", "C_AUX"), ("TP10", "GND", "C_AUX"), ("TP11", "VOUT", "A_POWER"), ("TP12", "GND", "A_POWER"),
       ("TP13", "IL_SNS", "E_SENSE"), ("TP14", "IOUT_SNS", "E_SENSE"), ("TP15", "VIN_OVP", "D_MCU")]
for ref, net, blk in TPS:
    add(ref, "Connector:TestPoint", net, "TestPoint:TestPoint_Pad_D1.5mm", {"1": net}, blk, mpn="PCB pad, no part",
        note="1.5 mm SMD test pad")

# Mounting: 4 x M3 corner holes for standoffs (no electrical connection)
for i in range(1, 5):
    add(f"H{i}", "Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", {}, "G_IO",
        mpn="no part (M3 standoff hole)", note="3.2 mm plated-free hole, corner, 4 mm from edges")

# Nets that need a PWR_FLAG for ERC (driven by connectors/passives)
PWR_FLAG_NETS = ["VBUS", "GND", "PGND", "+10V", "+3V3A", "VISO", "GND_ISO", "VOUT", "VIN_RAW", "VIN", "GNDP", "+10V_P"]

BLOCK_TITLES = {
    "A_POWER": "A  Secondary 4SBB regulator - 150 kHz, L = 22 uH (input = isolated bus VBUS)",
    "B_DRIVE": "B  Gate drivers - UCC27211 x2 (HRTIM Timer A -> input leg, Timer E -> output leg)",
    "C_AUX": "C  Secondary aux - VBUS -> 10 V -> 5 V; 3.3 V comes from isolator U12",
    "H_LLC": "H  LLC DCX - half-bridge, PQ2620 1:2:2, ~205 kHz, centre-tapped SR  (PRIMARY | SECONDARY)",
    "I_PRI": "I  Primary aux (VIN -> 10 V_P -> 5 V_P) and CA-IS3642LVW isolator / isolated 3.3 V",
    "D_MCU": "D  STM32G474RBT6 - HRTIM / ADC / COMP / FDCAN1",
    "E_SENSE": "E  Sensing - VBUS, VOUT, inductor current (bidirectional), output current, NTC",
    "F_CAN": "F  Isolated CAN - CA-IS3062VW (5 kVrms, integrated isolated supply)",
    "G_IO": "G  Address (6-bit DIP + header), programming pads + ARM 10-pin SWD, status LEDs",
}

if __name__ == "__main__":
    refs = [p.ref for p in P]
    dup = {r for r in refs if refs.count(r) > 1}
    assert not dup, dup
    nets = {}
    for p in P:
        for pin, n in p.pins.items():
            nets.setdefault(n, []).append(f"{p.ref}.{pin}")
    single = {n: v for n, v in nets.items() if len(v) == 1 and n != "NC"}
    print(len(P), "parts,", len(nets), "nets")
    print("single-pin nets:", single)
