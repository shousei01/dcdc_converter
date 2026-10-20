"""Design definition (Rev E): LLC DCX + STM32G474 four-switch buck-boost, 12-48 V in, 1.5-48 V / 5 A / 50 W out.
Rev E: isolated aux supply is a UC3843B flyback with TL431 + optocoupler secondary regulation; VREF+ = 3.3 V.

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
    "L5040": "Inductor_SMD:L_Sunlord_SWPA5040S",
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
    "FUSE1206": "Fuse:Fuse_1206_3216Metric",
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
    "SOP4": "Package_SO:SOP-4_3.8x4.1mm_P2.54mm",
    "TX_EP13": "custom_fp:TX_PA3855_EP13_10P",
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
# C. SECONDARY AUX RAILS  +10 V (from the isolated flyback, block K) -> 5 V buck -> 3.3 V LDO
#    Everything on the secondary is alive before the LLC starts: MCU, CAN, SR and 4SBB gate drivers.
# --------------------------------------------------------------------------------------------
B = "C_AUX"
add("U4", "Regulator_Switching:LMR16006YQ", "LMR16006XDDCR", "SOT23-6",
    {"1": "CB_AUX", "2": "GND", "3": "FB_AUX", "4": "EN_AUX", "5": "+10V", "6": "SW_AUX"}, B,
    lcsc="C87080", mpn="LMR16006XDDCR", note="+10 V -> +5 V buck, 0.6 A, 700 kHz (CAN 5 V + 3.3 V LDO input)")
C("C21", "10u 25V X5R", "+10V", "GND", fp="C0805", block=B, note="U4 input, at pin 5")
C("C22", "100n 25V", "+10V", "GND", fp="C0402", block=B)
R("R16", "56k 1%", "+10V", "EN_AUX", fp="R0402", block=B, note="EN divider: U4 starts at ~6 V of the +10 V rail")
R("R17", "15k 1%", "EN_AUX", "GND", fp="R0402", block=B)
C("C23", "100n 25V", "CB_AUX", "SW_AUX", fp="C0402", block=B, note="LMR16006 boot cap")
add("D2", "Device:D_Schottky", "SS110", "SMA", {"1": "SW_AUX", "2": "GND"}, B, lcsc="C224219", mpn="SS110",
    note="Schottky catch diode")
add("L2", "Device:L", "47u 1A", "L5040", {"1": "SW_AUX", "2": "+5V"}, B, lcsc="C86617", mpn="SWPA5040S470MT",
    note="47 uH, Isat >= 1 A, 5040 shielded (2nd source SRN5040-470M, NRS5040T470MMGK, NRSC5040-470M)")
R("R18", "56k 1%", "+5V", "FB_AUX", fp="R0402", block=B, note="Vout = 0.765*(1+56k/10k) = 5.05 V")
R("R19", "10k 1%", "FB_AUX", "GND", fp="R0402", block=B)
C("C24", "10u 25V X5R", "+10V", "GND", fp="C0805", block=B, note="+10 V rail bulk at the 4SBB drivers")
C("C25", "10u 25V X5R", "+10V", "GND", fp="C0805", block=B, note="+10 V rail bulk at U11 / SR")
C("C26", "10u 25V X5R", "+5V", "GND", fp="C0805", block=B, note="U4 output")
add("U5", "Regulator_Linear:TLV75533PDBV", "TLV75533PDBVR", "SOT23-5",
    {"1": "+5V", "2": "GND", "3": "+5V", "4": "NC", "5": "+3V3"}, B, lcsc="C404027", mpn="TLV75533PDBVR",
    note="3.3 V 500 mA LDO, 1 % accuracy; feeds MCU (VDD + VDDA/VREF+ via FB1), isolator side B, CAN VCCL")
C("C86", "1u 10V", "+5V", "GND", fp="C0402", block=B, note="U5 input")
C("C27", "22u 10V X5R", "+3V3", "GND", fp="C0805", block=B)
add("FB1", "Device:FerriteBead_Small", "600R@100MHz", "FB0603", {"1": "+3V3", "2": "+3V3A"}, B, note="VDDA / VREF+ filter")
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
    "28": "+3V3A",        # VREF+ = filtered VDDA (3.3 V); VREFBUF off (HIZ); firmware trims gain with VREFINT_CAL
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
C("C36", "1u 10V", "+3V3A", "GND", fp="C0402", block=B, note="VREF+ decoupling at pin 28, ADC charge reservoir")
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
R("R21", "100k 0.1%", "VBUS", "VBUS_SNS", fp="R0603", block=B, note="Isolated bus ~= VIN (DCX ratio 1); FS 68.0 V at 3.3 V VREF+")
R("R22", "5.1k 0.1%", "VBUS_SNS", "GND", fp="R0402", block=B)
C("C41", "1n C0G", "VBUS_SNS", "GND", fp="C0402", block=B)
R("R23", "100k 0.1%", "VOUT", "VOUT_SNS", fp="R0603", block=B, note="Divider referenced to GND; firmware adds Iout*RSH1")
R("R24", "5.1k 0.1%", "VOUT_SNS", "GND", fp="R0402", block=B)
C("C42", "1n C0G", "VOUT_SNS", "GND", fp="C0402", block=B)
# inductor / bridge current, bidirectional around VREF/2
add("U7", "Amplifier_Current:INA181", "INA181A1IDBVR", "SOT23-6",
    {"1": "IL_AMP", "2": "GND", "3": "PGND", "4": "GND", "5": "IL_REF", "6": "+3V3A"}, B,
    lcsc="C2058943", mpn="INA181A1IDBVR",
    note="Gain 20: IL_SNS = 1.65 V + 0.08 V/A * IL (+ in boost, - in buck), FS +/-20.6 A. IN+/IN- Kelvin to RS1 pads")
R("R25", "1k 0.1%", "+3V3A", "IL_REF", fp="R0402", block=B, note="IL zero = VREF+/2, ratiometric")
R("R26", "1k 0.1%", "IL_REF", "GND", fp="R0402", block=B)
C("C43", "100n", "IL_REF", "GND", fp="C0402", block=B)
C("C44", "100n", "+3V3A", "GND", fp="C0402", block=B)
R("R27", "100R", "IL_AMP", "IL_SNS", fp="R0402", block=B)
C("C45", "470p C0G", "IL_SNS", "GND", fp="C0402", block=B, note="Keep RC fast (~47 ns) for comparator OCP")
# output current
add("U8", "Amplifier_Current:INA181", "INA181A2IDBVR", "SOT23-6",
    {"1": "IOUT_AMP", "2": "GND", "3": "VOUT_N", "4": "GND", "5": "GND", "6": "+3V3A"}, B,
    lcsc="C2058784", mpn="INA181A2IDBVR", note="Gain 50: 0.5 V/A, 5 A = 2.5 V, FS 6.6 A")
C("C46", "100n", "+3V3A", "GND", fp="C0402", block=B)
R("R28", "1k", "IOUT_AMP", "IOUT_SNS", fp="R0402", block=B)
C("C47", "10n C0G", "IOUT_SNS", "GND", fp="C0402", block=B)
# temperature (place NTC between Q1 and Q4)
R("R29", "10k 1%", "+3V3A", "NTC_SNS", fp="R0402", block=B, note="Pull-up from VREF+, ratiometric")
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
add("F1", "Device:Fuse", "7A 63V", "FUSE1206", {"1": "VIN_RAW", "2": "VIN"}, B, lcsc="C206980", mpn="0458007.DR",
    note="Fast-acting 7 A 63 V 1206 chip fuse (Littelfuse 0458007.DR; 2nd source Schurter 3413.0326.11)")
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
# I. PRIMARY AUX + ISOLATOR  (VIN -> 10 V_P -> 5 V_P; CA-IS3742LW: OVP / VIN-PWM -> secondary, LLC gates <- secondary)
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
add("L3", "Device:L", "47u 1A", "L5040", {"1": "SW_P", "2": "+10V_P"}, B, lcsc="C86617", mpn="SWPA5040S470MT")
R("R77", "120k 1%", "+10V_P", "FB_P", fp="R0402", block=B)
R("R78", "10k 1%", "FB_P", "GNDP", fp="R0402", block=B)
C("C72", "10u 25V X5R", "+10V_P", "GNDP", fp="C0805", block=B)
add("U14", "Regulator_Linear:AMS1117-5.0", "AMS1117-5.0", "SOT223", {"1": "GNDP", "2": "+5V_P", "3": "+10V_P"}, B,
    lcsc="C6187", mpn="AMS1117-5.0", note="5 V_P for isolator side A, comparators, TL431 reference (~20 mA)")
C("C73", "22u 10V X5R", "+5V_P", "GNDP", fp="C0805", block=B)
add("U12", "custom:CA-IS3742", "CA-IS3742LW", "SOIC16W",
    {"1": "+5V_P", "2": "GNDP", "3": "OVP_P", "4": "VINPWM_P", "5": "LLC_HI_P", "6": "LLC_LO_P", "7": "+5V_P", "8": "GNDP",
     "9": "GND", "10": "+3V3", "11": "LLC_B", "12": "LLC_A", "13": "VIN_PWM", "14": "VIN_OVP", "15": "GND", "16": "+3V3"}, B,
    lcsc="C4944981", mpn="CA-IS3742LW",
    note="5 kVrms 2+2 digital isolator (no isolated power), L = outputs default low; ENA/ENB tied high; alt TI ISO7742FDWR")
C("C75", "100n", "+5V_P", "GNDP", fp="C0402", block=B, note="VDDA pin 1")
C("C77", "100n", "+3V3", "GND", fp="C0402", block=B, note="VDDB pin 16")
R("R79", "10k", "LLC_A", "GND", fp="R0402", block=B, note="Holds isolator input low while MCU in reset")
R("R80", "10k", "LLC_B", "GND", fp="R0402", block=B)


# --------------------------------------------------------------------------------------------
# I (cont.) INPUT OVP: VIN > 50 V -> OVP_P high -> U12 ch1 -> VIN_OVP (PA15 / HRTIM1_FLT2)
# --------------------------------------------------------------------------------------------
B = "I_PRI"
R("R81", "191k 0.1%", "VIN", "OVP_DIV", fp="R1206", block=B, note="OVP / VIN-monitor divider top: OVP trips at 50.26 V rising, 49.83 V falling (R84, R110 included); 0.1 % sets the VIN reading accuracy")
R("R82", "10k 0.1%", "OVP_DIV", "GNDP", fp="R0402", block=B)
C("C79", "1n C0G", "OVP_DIV", "GNDP", fp="C0402", block=B, note="Noise filter, ~10 us")
add("U15", "Comparator:LMV331", "LMV331IDBVR", "SOT23-5", {"1": "OVP_DIV", "2": "GNDP", "3": "VREF_P", "4": "OVP_P", "5": "+5V_P"}, B,
    mpn="LMV331IDBVR", note="Open-drain comparator; output high (released) = OVP")
C("C80", "100n", "+5V_P", "GNDP", fp="C0402", block=B)
R("R83", "10k", "+5V_P", "OVP_P", fp="R0402", block=B, note="Pull-up for open-drain output")
R("R84", "2.2M", "OVP_P", "OVP_DIV", fp="R0402", block=B, note="Hysteresis ~0.4 V at VIN")
add("U16", "Reference_Voltage:TL431DBZ", "TL431AIDBZR", "SOT23", {"1": "VREF_P", "2": "VREF_P", "3": "GNDP"}, B,
    mpn="TL431AIDBZR (TI pinout: 1 K, 2 REF, 3 A)", note="2.495 V reference, A grade = 1 % (TL431BIDBZR = 0.5 % drop-in)")
R("R85", "1k", "+5V_P", "VREF_P", fp="R0402", block=B, note="TL431 bias 2.5 mA")

# --------------------------------------------------------------------------------------------
# I (cont.) VIN MONITOR: linear sawtooth 0 -> VREF_P (2.495 V), compared with OVP_DIV -> PWM -> U12 VI2 -> VO2 -> PA2
#   ramp: PNP current source (~24 uA) into 47 nF C0G -> ~5 ms; U17 detects RAMP > VREF_P, D7/C81/R107 stretch the
#   reset to ~20 us, Q10 empties C82. U18: output high while RAMP < OVP_DIV; R110 hysteresis acts on the divider
#   (low impedance), never on the ramp, so the ramp stays linear.
#   VIN = 50.47 V x (t_high - t_reset) / (period - t_reset) - 0.20 V, t_reset ~20 us. Monitoring only, ~200 Hz.
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
C("C81", "220p C0G", "GATE_P", "GNDP", fp="C0402", block=B, note="Reset hold ~20 us with R107; small so the gate charges fully (0.2 us) before U17 lets go")
R("R107", "100k", "GATE_P", "GNDP", fp="R0402", block=B)
add("Q10", "Transistor_FET:2N7002", "2N7002", "SOT23", {"1": "GATE_P", "2": "GNDP", "3": "DIS_P"}, B,
    lcsc="C8545", mpn="2N7002", note="Ramp reset switch")
R("R89", "22R", "DIS_P", "RAMP_P", fp="R0402", block=B, note="Limits discharge peak current")
C("C83", "100n", "+5V_P", "GNDP", fp="C0402", block=B)
R("R109", "1k", "RAMP_P", "RAMPS_P", fp="R0402", block=B, note="Input protection series R; bias error < 0.25 mV")
add("U18", "Comparator:LMV331", "LMV331IDBVR", "SOT23-5", {"1": "OVP_DIV", "2": "GNDP", "3": "RAMPS_P", "4": "VINPWM_P", "5": "+5V_P"}, B,
    mpn="LMV331IDBVR", note="PWM comparator: output high while RAMP < OVP_DIV")
R("R110", "4.7M", "VINPWM_P", "OVP_DIV", fp="R0402", block=B, note="~10 mV hysteresis on the divider side; does not load the ramp")
R("R108", "10k", "+5V_P", "VINPWM_P", fp="R0402", block=B, note="Pull-up -> U12 VI2 (pin 4)")
C("C84", "100n", "+5V_P", "GNDP", fp="C0402", block=B)

# --------------------------------------------------------------------------------------------
# K. ISOLATED AUX FLYBACK  VIN (12-48 V) -> +10 V secondary, ~3 W capability, ~170 kHz, DCM
#    UC3843B current mode on the primary (VCC = +10V_P from U13), PA3855.006NLT EP13 (Np:Ns = 1.33:1, Lp 21 uH),
#    secondary-side regulation: TL431 senses +10 V, EL357N optocoupler pulls the UC3843 COMP pin (FB grounded).
# --------------------------------------------------------------------------------------------
B = "K_FLY"
add("U20", "Regulator_Controller:UC3843_SOIC8", "UC3843BVD1R2G", "SOIC8",
    {"1": "FLY_COMP", "2": "GNDP", "3": "FLY_CS", "4": "FLY_RT", "5": "GNDP", "6": "FLY_OUT", "7": "+10V_P", "8": "FLY_VREF"}, B,
    lcsc="C231572", mpn="UC3843BVD1R2G", note="Current-mode PWM, UVLO 8.4/7.6 V, -40..105 C; FB grounded, opto drives COMP")
C("C88", "1u 25V X7R", "+10V_P", "GNDP", fp="C0603", block=B, note="U20 VCC, at pin 7")
C("C89", "100n 25V", "+10V_P", "GNDP", fp="C0402", block=B)
C("C90", "100n", "FLY_VREF", "GNDP", fp="C0402", block=B, note="VREF bypass (>= 100 nF required)")
R("R111", "10k 1%", "FLY_VREF", "FLY_RT", fp="R0402", block=B, note="RT: f ~ 1.72/(RT*CT) = 172 kHz")
C("C91", "1n C0G", "FLY_RT", "GNDP", fp="C0402", block=B, note="CT, must be C0G")
C("C92", "1n C0G", "FLY_COMP", "GNDP", fp="C0402", block=B, note="COMP noise filter")
R("R112", "10R", "FLY_OUT", "FLY_G", fp="R0603", block=B, note="Gate resistor")
R("R113", "10k", "FLY_G", "GNDP", fp="R0402", block=B, note="Gate pull-down")
add("Q11", "Transistor_FET:2N7002", "FDN86246", "SOT23", {"1": "FLY_G", "2": "FLY_SRC", "3": "FLY_DRN"}, B,
    lcsc="C891118", mpn="FDN86246", note="150 V, 1.6 A, 195 mOhm N-MOSFET (Vds max ~95 V incl. clamp at 50 V in)")
R("R114", "0R5 1%", "FLY_SRC", "GNDP", fp="R1206", block=B, note="Current sense: Ipk limit 1.0 V / 0.5 R = 2.0 A (~6 W max)")
R("R115", "1k", "FLY_SRC", "FLY_CS", fp="R0402", block=B, note="Leading-edge blanking RC 220 ns")
C("C93", "220p C0G", "FLY_CS", "GNDP", fp="C0402", block=B)
add("T2", "custom:PA3855", "PA3855.006NLT", "TX_EP13",
    {"1": "FLY_DRN", "3": "VIN", "4": "NC", "5": "NC", "9": "FLY_SA", "10": "FLY_SA", "6": "GND", "7": "GND"}, B,
    lcsc="C5718384", mpn="PA3855.006NLT",
    note="Pulse EP13 flyback, 9-57 V, 21 uH, Np:Ns:Ns 1.33:1:1 (secondaries paralleled), Hi-pot 2250 Vdc; aux 4-5 unused")
add("D8", "Device:D_Schottky", "SS110", "SMA", {"1": "FLY_CLP", "2": "FLY_DRN"}, B, lcsc="C224219", mpn="SS110",
    note="RCD clamp diode")
R("R116", "4k7", "FLY_CLP", "VIN", fp="R1206", block=B, note="RCD clamp: Vclamp ~ 25-40 V above VIN, ~0.15 W")
C("C94", "4.7n 100V X7R", "FLY_CLP", "VIN", fp="C0603", block=B)
C("C95", "2.2u 100V X7R", "VIN", "GNDP", fp="C1210", block=B, note="Flyback input loop cap at T2 pin 3 / R114")
add("D9", "Device:D_Schottky", "SS110", "SMA", {"1": "+10V", "2": "FLY_SA"}, B, lcsc="C224219", mpn="SS110",
    note="Output rectifier, Vr ~ 48 V at 50 V in")
R("R122", "10R DNP", "FLY_SA", "FLY_SNB", fp="R0603", block=B, dnp=True, note="Rectifier RC snubber, fit if ringing")
C("C98", "470p 100V DNP", "FLY_SNB", "+10V", fp="C0603", block=B, dnp=True)
C("C96", "10u 25V X5R", "+10V", "GND", fp="C0805", block=B, note="Flyback output, at D9 / T2 return")
C("C97", "10u 25V X5R", "+10V", "GND", fp="C0805", block=B)
add("U21", "Isolator:LTV-357T", "EL357N(B)", "SOP4", {"1": "OPTO_A", "2": "OPTO_K", "3": "GNDP", "4": "FLY_COMP"}, B,
    lcsc="C42381015", mpn="EL357N(B)(TA)-G", note="Optocoupler, CTR 130-260 %, 3.75 kVrms")
R("R117", "1k5", "+10V", "OPTO_A", fp="R0402", block=B, note="LED series R: IF up to 3.2 mA with TL431 at 2.5 V")
R("R118", "1k", "OPTO_A", "OPTO_K", fp="R0402", block=B, note="LED bypass: keeps TL431 >= 1 mA")
add("U22", "Reference_Voltage:TL431DBZ", "TL431AIDBZR", "SOT23", {"1": "OPTO_K", "2": "FLY_FB", "3": "GND"}, B,
    lcsc="C23892", mpn="TL431AIDBZR", note="TI DBZ pinout 1 K, 2 REF, 3 A")
R("R119", "30k 1%", "+10V", "FLY_FB", fp="R0402", block=B, note="+10V = 2.495 * (1 + 30k/10k) = 9.98 V")
R("R120", "10k 1%", "FLY_FB", "GND", fp="R0402", block=B)
R("R121", "4k7", "OPTO_K", "FLY_CZ", fp="R0402", block=B, note="Type-2 compensation: zero 340 Hz")
C("C99", "100n", "FLY_CZ", "FLY_FB", fp="C0402", block=B)

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
       ("TP5", "VBUS", "A_POWER"), ("TP6", "+10V", "C_AUX"), ("TP7", "+5V", "C_AUX"), ("TP8", "+3V3", "C_AUX"),
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
PWR_FLAG_NETS = ["VBUS", "GND", "PGND", "+10V", "+5V", "+3V3A", "VISO", "GND_ISO", "VOUT", "VIN_RAW", "VIN", "GNDP", "+10V_P"]

BLOCK_TITLES = {
    "A_POWER": "A  Secondary 4SBB regulator - 150 kHz, L = 22 uH (input = isolated bus VBUS)",
    "B_DRIVE": "B  Gate drivers - UCC27211 x2 (HRTIM Timer A -> input leg, Timer E -> output leg)",
    "C_AUX": "C  Secondary aux - +10 V (flyback) -> 5 V buck -> 3.3 V LDO",
    "H_LLC": "H  LLC DCX - half-bridge, PQ2620 1:2:2, ~205 kHz, centre-tapped SR  (PRIMARY | SECONDARY)",
    "I_PRI": "I  Primary aux (VIN -> 10 V_P -> 5 V_P), CA-IS3742LW isolator, input OVP / VIN monitor",
    "K_FLY": "K  Isolated aux flyback - UC3843B, PA3855.006NLT, TL431 + EL357N feedback, +10 V secondary",
    "D_MCU": "D  STM32G474RBT6 - HRTIM / ADC / COMP / FDCAN1",
    "E_SENSE": "E  Sensing - VBUS, VOUT, inductor current (bidirectional), output current, NTC",
    "F_CAN": "F  Isolated CAN - CA-IS3062VW (5 kVrms, integrated isolated supply)",
    "G_IO": "G  Address (6-bit DIP + header), programming pads + ARM 10-pin SWD, status LEDs",
}

# LCSC numbers checked in the JLCPCB parts library on 2026-10-18 (package, rating, stock) for the 5-board
# assembly order. Applied to every part so the BOMs, schematic and PCB fields agree.
JLC_LCSC = {
    "SW1": "C6331172",  # SHOU HAN 2.54-6P TPGT SMD DIP-6 (assembled by JLC from 18 Oct)
    # Rev E flyback + rails (checked in the JLCPCB / LCSC library 2026-10-19)
    "U20": "C231572", "Q11": "C891118", "T2": "C5718384", "U21": "C42381015", "U22": "C23892", "U12": "C4944981",
    "U5": "C404027", "R112": "C22859", "R114": "C25340", "R116": "C17936", "C94": "C115052", "R117": "C25867",
    "R119": "C25776", "R121": "C25900", "D8": "C224219", "D9": "C224219",
    **dict.fromkeys(['FB1'], 'C1002'),
    **dict.fromkeys(['C45'], 'C106259'),
    **dict.fromkeys(['C81', 'C93'], 'C107001'),
    **dict.fromkeys(['C41', 'C42', 'C79', 'C91', 'C92'], 'C113780'),
    **dict.fromkeys(['R84'], 'C11490'),
    **dict.fromkeys(['R106', 'R109', 'R28', 'R38', 'R39', 'R40', 'R41', 'R42', 'R43', 'R44', 'R45', 'R85', 'R115', 'R118'], 'C11702'),
    **dict.fromkeys(['R21', 'R23'], 'C122538'),
    **dict.fromkeys(['D4'], 'C12624'),
    **dict.fromkeys(['D3'], 'C14486'),
    **dict.fromkeys(['C15', 'C18', 'C67'], 'C14663'),
    **dict.fromkeys(['C90', 'C99', 'C29', 'C30', 'C31', 'C32', 'C33', 'C34', 'C37', 'C40', 'C43', 'C44', 'C46', 'C48', 'C50', 'C53', 'C54', 'C75', 'C77', 'C80', 'C83', 'C84'], 'C1525'),
    **dict.fromkeys(['C10', 'C2', 'C3', 'C4', 'C5', 'C61', 'C62', 'C63', 'C7', 'C70', 'C8', 'C9', 'C95'], 'C153036'),
    **dict.fromkeys(['C38', 'C39'], 'C1547'),
    **dict.fromkeys(['C16', 'C19', 'C68', 'C69', 'C88'], 'C15849'),
    **dict.fromkeys(['C21', 'C24', 'C25', 'C26', 'C49', 'C52', 'C72', 'C96', 'C97'], 'C15850'),
    **dict.fromkeys(['R25', 'R26'], 'C186137'),
    **dict.fromkeys(['R22', 'R24'], 'C186154'),
    **dict.fromkeys(['R82'], 'C190095'),
    **dict.fromkeys(['C35'], 'C19666'),
    **dict.fromkeys(['D1'], 'C20883337'),
    **dict.fromkeys(['C47'], 'C22400107'),
    **dict.fromkeys(['R110'], 'C227116'),
    **dict.fromkeys(['D5'], 'C2286'),
    **dict.fromkeys(['R62', 'R63'], 'C22939'),
    **dict.fromkeys(['R10', 'R11', 'R4', 'R5', 'R68', 'R69'], 'C23164'),
    **dict.fromkeys(['R75'], 'C23178'),
    **dict.fromkeys(['U16'], 'C23892'),
    **dict.fromkeys(['C1', 'C11', 'C60'], 'C249664'),
    **dict.fromkeys(['R27'], 'C25076'),
    **dict.fromkeys(['R89'], 'C25092'),
    **dict.fromkeys(['R107'], 'C25741'),
    **dict.fromkeys(['R100', 'R101', 'R102', 'R103', 'R104', 'R105', 'R108', 'R12', 'R13', 'R14', 'R15', 'R19', 'R20', 'R29', 'R32', 'R33', 'R34', 'R35', 'R36', 'R37', 'R6', 'R64', 'R65', 'R66', 'R67', 'R7', 'R70', 'R71', 'R72', 'R73', 'R74', 'R78', 'R79', 'R8', 'R80', 'R83', 'R87', 'R9', 'R90', 'R91', 'R92', 'R93', 'R94', 'R95', 'R96', 'R97', 'R98', 'R99', 'R111', 'R113', 'R120'], 'C25744'),
    **dict.fromkeys(['R77'], 'C25750'),
    **dict.fromkeys(['R88', 'R17'], 'C25756'),
    **dict.fromkeys(['R86', 'R16', 'R18'], 'C25796'),
    **dict.fromkeys(['TH1'], 'C2892547'),
    **dict.fromkeys(['R1'], 'C2907507'),
    **dict.fromkeys(['R30', 'R31'], 'C2933247'),
    **dict.fromkeys(['CR1', 'CR2', 'CR3', 'CR4', 'CR5', 'CR6'], 'C2940749'),
    **dict.fromkeys(['C17', 'C20', 'C22', 'C23', 'C71', 'C89'], 'C307331'),
    **dict.fromkeys(['U15', 'U17', 'U18'], 'C34731'),
    **dict.fromkeys(['R76'], 'C36871'),
    **dict.fromkeys(['C27', 'C73'], 'C45783'),
    **dict.fromkeys(['RSH1'], 'C500718'),
    **dict.fromkeys(['RS1'], 'C500738'),
    **dict.fromkeys(['C28', 'C36', 'C51', 'C86'], 'C52923'),
    **dict.fromkeys(['C82'], 'C53134'),
    **dict.fromkeys(['Q9'], 'C53444'),
    **dict.fromkeys(['C55'], 'C53987'),
    **dict.fromkeys(['R81'], 'C870479'),
    **dict.fromkeys(['C12', 'C6'], 'C88219'),
    **dict.fromkeys([], 'C96123'),
}
for _p in P:
    if _p.ref in JLC_LCSC:
        _p.lcsc = JLC_LCSC[_p.ref]

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
