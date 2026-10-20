"""Rev E design edits (applied once to design.py):
 1. Isolated aux supply = discrete flyback: UC3843B on the primary (VCC from +10V_P), PA3855.006NLT EP13 transformer
    from VIN (12-48 V), secondary +10 V regulated by TL431 + EL357N optocoupler (secondary-side regulation).
 2. Secondary rails: +10 V (flyback) -> gate drivers; U4 LMR16006 now +10 V -> +5 V buck; U5 TLV75533 +5 V -> +3V3 LDO.
    VBUS no longer feeds any aux rail.
 3. U12 CA-IS3642LVW (isolator + isolated power) -> CA-IS3742LW plain 2+2 digital isolator (5 kVrms, default low).
 4. MCU VREF+ back to the filtered 3.3 V (+3V3A); REF3030 U19 and C85 removed.
"""
import re

s = open("design.py").read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:90])
    s = s.replace(a, b)


def drop_line(prefix):
    """remove one add()/C()/R() call that starts with prefix (may span lines up to the closing paren)"""
    global s
    i = s.find(prefix)
    assert i >= 0, prefix
    depth, j = 0, i
    while True:
        ch = s[j]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                break
        j += 1
    k = s.find("\n", j)
    s = s[:i] + s[k + 1:]


# ---------------------------------------------------------------- header / footprints
rep('"""Design definition: STM32G474 four-switch buck-boost, 12-48 V in, 1.5-48 V / 5 A / 50 W out.\n',
    '"""Design definition (Rev E): LLC DCX + STM32G474 four-switch buck-boost, 12-48 V in, 1.5-48 V / 5 A / 50 W out.\n'
    'Rev E: isolated aux supply is a UC3843B flyback with TL431 + optocoupler secondary regulation; VREF+ = 3.3 V.\n')
rep('    "FB0603": "Inductor_SMD:L_0603_1608Metric",\n',
    '    "FB0603": "Inductor_SMD:L_0603_1608Metric",\n'
    '    "SOP4": "Package_SO:SOP-4_3.8x4.1mm_P2.54mm",\n'
    '    "TX_EP13": "custom_fp:TX_PA3855_EP13_10P",\n')

# ---------------------------------------------------------------- C. secondary aux
i0 = s.find("# C. AUXILIARY SUPPLIES")
i0 = s.rfind("# ----", 0, i0)
i1 = s.find("# D. MCU")
i1 = s.rfind("# ----", 0, i1)
s = s[:i0] + '''# --------------------------------------------------------------------------------------------
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

''' + s[i1:]

# ---------------------------------------------------------------- D. MCU VREF+ = +3V3A
rep('    "28": "VREF_ADC",     # VREF+ from external REF3030 (3.000 V, 0.2 %); VREFBUF must stay off (HIZ)\n',
    '    "28": "+3V3A",        # VREF+ = filtered VDDA (3.3 V); VREFBUF off (HIZ); firmware trims gain with VREFINT_CAL\n')
rep('C("C36", "1u 10V", "VREF_ADC", "GND", fp="C0402", block=B, note="VREF+ decoupling, ADC charge reservoir")',
    'C("C36", "1u 10V", "+3V3A", "GND", fp="C0402", block=B, note="VREF+ decoupling at pin 28, ADC charge reservoir")')
rep('C("C37", "100n", "VREF_ADC", "GND", fp="C0402", block=B, note="VREF+ pin 28")',
    'C("C37", "100n", "+3V3A", "GND", fp="C0402", block=B, note="VREF+ pin 28")')
drop_line('add("U19", "Reference_Voltage:REF3030"')
drop_line('C("C85", "1u 10V", "+3V3A"')

# ---------------------------------------------------------------- E. sensing (ratiometric to 3.3 V)
rep('note="Isolated bus ~= VIN (DCX ratio 1); FS 61.8 V at 3.0 V VREF+")',
    'note="Isolated bus ~= VIN (DCX ratio 1); FS 68.0 V at 3.3 V VREF+")')
rep('note="Gain 20: IL_SNS = 1.50 V + 0.08 V/A * IL (+ in boost, - in buck), FS +/-18.75 A. IN+/IN- Kelvin to RS1 pads")',
    'note="Gain 20: IL_SNS = 1.65 V + 0.08 V/A * IL (+ in boost, - in buck), FS +/-20.6 A. IN+/IN- Kelvin to RS1 pads")')
rep('R("R25", "1k 0.1%", "VREF_ADC", "IL_REF"', 'R("R25", "1k 0.1%", "+3V3A", "IL_REF"')
rep('add("U8", "Amplifier_Current:INA181", "INA181A2IDBVR", "SOT23-6",\n    {"1": "IOUT_AMP", "2": "GND", "3": "VOUT_N", "4": "GND", "5": "GND", "6": "+3V3A"}, B,\n    lcsc="C2058784", mpn="INA181A2IDBVR", note="Gain 50: 0.5 V/A, 5 A = 2.5 V, FS 6.0 A")',
    'add("U8", "Amplifier_Current:INA181", "INA181A2IDBVR", "SOT23-6",\n    {"1": "IOUT_AMP", "2": "GND", "3": "VOUT_N", "4": "GND", "5": "GND", "6": "+3V3A"}, B,\n    lcsc="C2058784", mpn="INA181A2IDBVR", note="Gain 50: 0.5 V/A, 5 A = 2.5 V, FS 6.6 A")')
rep('R("R29", "10k 1%", "VREF_ADC", "NTC_SNS"', 'R("R29", "10k 1%", "+3V3A", "NTC_SNS"')

# ---------------------------------------------------------------- I. isolator: plain CA-IS3742LW
rep('# I. PRIMARY AUX + ISOLATOR  (VIN -> 10 V_P -> 5 V_P; CA-IS3642LVW: power -> secondary, gates <- secondary)',
    '# I. PRIMARY AUX + ISOLATOR  (VIN -> 10 V_P -> 5 V_P; CA-IS3742LW: OVP / VIN-PWM -> secondary, LLC gates <- secondary)')
rep('add("U12", "custom:CA-IS3642LVW", "CA-IS3642LVW", "SOIC16W",\n    {"1": "+5V_P", "2": "GNDP", "3": "OVP_P", "4": "VINPWM_P", "5": "LLC_HI_P", "6": "LLC_LO_P", "7": "+5V_P", "8": "GNDP",\n     "9": "GND", "10": "GND", "11": "LLC_B", "12": "LLC_A", "13": "VIN_PWM", "14": "VIN_OVP", "15": "GND", "16": "+3V3"}, B,\n    lcsc="C7422564", mpn="CA-IS3642LVW",\n    note="5 kVrms isolator, 2 fwd + 2 rev, 650 mW isolated 3.3 V (SEL=GNDB) for the MCU; L = outputs default low")',
    'add("U12", "custom:CA-IS3742", "CA-IS3742LW", "SOIC16W",\n    {"1": "+5V_P", "2": "GNDP", "3": "OVP_P", "4": "VINPWM_P", "5": "LLC_HI_P", "6": "LLC_LO_P", "7": "+5V_P", "8": "GNDP",\n     "9": "GND", "10": "+3V3", "11": "LLC_B", "12": "LLC_A", "13": "VIN_PWM", "14": "VIN_OVP", "15": "GND", "16": "+3V3"}, B,\n    lcsc="C4944981", mpn="CA-IS3742LW",\n    note="5 kVrms 2+2 digital isolator (no isolated power), L = outputs default low; ENA/ENB tied high; alt TI ISO7742FDWR")')
drop_line('C("C74", "10u 10V", "+5V_P"')
drop_line('C("C76", "1u 10V", "+5V_P"')
drop_line('C("C78", "47u 6.3V", "+3V3"')
rep('C("C75", "100n", "+5V_P", "GNDP", fp="C0402", block=B)', 'C("C75", "100n", "+5V_P", "GNDP", fp="C0402", block=B, note="VDDA pin 1")')
rep('C("C77", "100n", "+3V3", "GND", fp="C0402", block=B, note="VISO pin 16, within 2 mm")',
    'C("C77", "100n", "+3V3", "GND", fp="C0402", block=B, note="VDDB pin 16")')
rep('note="5 V for the isolator (about 0.6 W in)")', 'note="5 V_P for isolator side A, comparators, TL431 reference (~20 mA)")')

# ---------------------------------------------------------------- K. isolated aux flyback (new block)
K = '''
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
R("R117", "2k2", "+10V", "OPTO_A", fp="R0402", block=B, note="LED series R: sets the loop gain, IF <= 2.9 mA")
R("R118", "1k", "OPTO_A", "OPTO_K", fp="R0402", block=B, note="LED bypass: keeps TL431 >= 1 mA")
add("U22", "Reference_Voltage:TL431DBZ", "TL431AIDBZR", "SOT23", {"1": "OPTO_K", "2": "FLY_FB", "3": "GND"}, B,
    lcsc="C23892", mpn="TL431AIDBZR", note="TI DBZ pinout 1 K, 2 REF, 3 A")
R("R119", "30k 1%", "+10V", "FLY_FB", fp="R0402", block=B, note="+10V = 2.495 * (1 + 30k/10k) = 9.98 V")
R("R120", "10k 1%", "FLY_FB", "GND", fp="R0402", block=B)
R("R121", "4k7", "OPTO_K", "FLY_CZ", fp="R0402", block=B, note="Type-2 compensation: zero 340 Hz")
C("C99", "100n", "FLY_CZ", "FLY_FB", fp="C0402", block=B)
'''
i = s.find("# --------------------------------------------------------------------------------------------\n# D (cont.) unused MCU pins")
s = s[:i] + K.lstrip("\n") + "\n" + s[i:]

# ---------------------------------------------------------------- test points, flags, titles
rep('("TP5", "VBUS", "C_AUX")', '("TP5", "VBUS", "A_POWER")')
rep('PWR_FLAG_NETS = ["VBUS", "GND", "PGND", "+10V", "+3V3A", "VISO", "GND_ISO", "VOUT", "VIN_RAW", "VIN", "GNDP", "+10V_P"]',
    'PWR_FLAG_NETS = ["VBUS", "GND", "PGND", "+10V", "+5V", "+3V3A", "VISO", "GND_ISO", "VOUT", "VIN_RAW", "VIN", "GNDP", "+10V_P"]')
rep('    "C_AUX": "C  Secondary aux - VBUS -> 10 V -> 5 V; 3.3 V comes from isolator U12",',
    '    "C_AUX": "C  Secondary aux - +10 V (flyback) -> 5 V buck -> 3.3 V LDO",')
rep('    "I_PRI": "I  Primary aux (VIN -> 10 V_P -> 5 V_P) and CA-IS3642LVW isolator / isolated 3.3 V",',
    '    "I_PRI": "I  Primary aux (VIN -> 10 V_P -> 5 V_P), CA-IS3742LW isolator, input OVP / VIN monitor",\n'
    '    "K_FLY": "K  Isolated aux flyback - UC3843B, PA3855.006NLT, TL431 + EL357N feedback, +10 V secondary",')

# ---------------------------------------------------------------- LCSC table
for ref in ["C74", "C76", "C78", "C85"]:
    s = re.sub(r"'%s', " % ref, "", s)
    s = re.sub(r", '%s'\]" % ref, "]", s)
    s = re.sub(r"\['%s'\]" % ref, "[]", s)
rep("    **dict.fromkeys(['R17', 'R76'], 'C36871'),", "    **dict.fromkeys(['R76'], 'C36871'),")
rep("    **dict.fromkeys(['R18', 'R77'], 'C25750'),", "    **dict.fromkeys(['R77'], 'C25750'),")
rep("    **dict.fromkeys(['R16', 'R75'], 'C23178'),", "    **dict.fromkeys(['R75'], 'C23178'),")
rep("    **dict.fromkeys(['R88'], 'C25756'),", "    **dict.fromkeys(['R88', 'R17'], 'C25756'),")
rep("    **dict.fromkeys(['R86'], 'C25796'),", "    **dict.fromkeys(['R86', 'R16', 'R18'], 'C25796'),")
rep("    **dict.fromkeys(['C21', 'C10', 'C2', 'C3', 'C4', 'C5', 'C61', 'C62', 'C63', 'C7', 'C70', 'C8', 'C9'], 'C153036'),",
    "    **dict.fromkeys(['C10', 'C2', 'C3', 'C4', 'C5', 'C61', 'C62', 'C63', 'C7', 'C70', 'C8', 'C9', 'C95'], 'C153036'),") \
    if "['C21', 'C10'" in s else rep("    **dict.fromkeys(['C10', 'C2', 'C21', 'C3', 'C4', 'C5', 'C61', 'C62', 'C63', 'C7', 'C70', 'C8', 'C9'], 'C153036'),",
                                     "    **dict.fromkeys(['C10', 'C2', 'C3', 'C4', 'C5', 'C61', 'C62', 'C63', 'C7', 'C70', 'C8', 'C9', 'C95'], 'C153036'),")
rep("    **dict.fromkeys(['C12', 'C22', 'C6'], 'C88219'),", "    **dict.fromkeys(['C12', 'C6'], 'C88219'),")
rep("    **dict.fromkeys(['C24', 'C25', 'C26', 'C49', 'C52', 'C72'], 'C15850'),",
    "    **dict.fromkeys(['C21', 'C24', 'C25', 'C26', 'C49', 'C52', 'C72', 'C96', 'C97'], 'C15850'),")
rep("    **dict.fromkeys(['C17', 'C20', 'C23', 'C71'], 'C307331'),", "    **dict.fromkeys(['C17', 'C20', 'C22', 'C23', 'C71', 'C89'], 'C307331'),")
rep("    **dict.fromkeys(['C16', 'C19', 'C68', 'C69'], 'C15849'),", "    **dict.fromkeys(['C16', 'C19', 'C68', 'C69', 'C88'], 'C15849'),")
rep("    **dict.fromkeys(['C28', 'C36', 'C51'], 'C52923'),", "    **dict.fromkeys(['C28', 'C36', 'C51', 'C86'], 'C52923'),")
rep("    **dict.fromkeys(['C41', 'C42', 'C79'], 'C113780'),", "    **dict.fromkeys(['C41', 'C42', 'C79', 'C91', 'C92'], 'C113780'),")
rep("    **dict.fromkeys(['C81'], 'C107001'),", "    **dict.fromkeys(['C81', 'C93'], 'C107001'),")
rep("    **dict.fromkeys(['R106', 'R109', 'R28', 'R38', 'R39', 'R40', 'R41', 'R42', 'R43', 'R44', 'R45', 'R85'], 'C11702'),",
    "    **dict.fromkeys(['R106', 'R109', 'R28', 'R38', 'R39', 'R40', 'R41', 'R42', 'R43', 'R44', 'R45', 'R85', 'R115', 'R118'], 'C11702'),")
rep("'R95', 'R96', 'R97', 'R98', 'R99'], 'C25744'),", "'R95', 'R96', 'R97', 'R98', 'R99', 'R111', 'R113', 'R120'], 'C25744'),")
rep("    **dict.fromkeys(['C29', 'C30',", "    **dict.fromkeys(['C90', 'C99', 'C29', 'C30',")
rep('    "SW1": "C6331172",  # SHOU HAN 2.54-6P TPGT SMD DIP-6 (assembled by JLC from 18 Oct)\n',
    '    "SW1": "C6331172",  # SHOU HAN 2.54-6P TPGT SMD DIP-6 (assembled by JLC from 18 Oct)\n'
    '    # Rev E flyback + rails (checked in the JLCPCB / LCSC library 2026-10-19)\n'
    '    "U20": "C231572", "Q11": "C891118", "T2": "C5718384", "U21": "C42381015", "U22": "C23892", "U12": "C4944981",\n'
    '    "U5": "C404027", "R112": "C22859", "R114": "C25340", "R116": "C17936", "C94": "C115052", "R117": "C25879",\n'
    '    "R119": "C25776", "R121": "C25900", "D8": "C224219", "D9": "C224219",\n')
open("design.py", "w").write(s)
print("ok")
