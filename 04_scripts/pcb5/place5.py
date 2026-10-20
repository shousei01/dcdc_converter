"""Rev E placement (all parts by hand). Rev D power-stage placement (hot loops already minimised) is the starting
point; Rev E moves/adds the flyback, the secondary aux, and tidies the control area."""
import json
import sys
sys.path.insert(0, "/home/claude/dcdc")

W, H = 160.0, 105.0
XB = 70.0        # primary | secondary barrier centre
XC = 138.0       # CAN logic | CAN bus barrier centre
YC = 62.0        # top of the CAN bus domain
BAND = 2.0       # half-width of the copper-free isolation band (4 mm)
UUID_JSON = "/home/claude/dcdc/sch5/uuid_paths.json"

PRI = {"OVP_DIV", "OVP_P", "VREF_P", "VIN_RAW", "VIN", "GNDP", "HB_SW", "CR_MID", "G5", "G6", "HBP", "HOP", "LOP",
       "LLC_HI_P", "LLC_LO_P", "+10V_P", "+5V_P", "CB_P", "FB_P", "EN_P", "SW_P", "PE_P", "PB_P", "RAMP_P", "RAMPS_P",
       "RST_P", "GATE_P", "DIS_P", "VINPWM_P", "FLY_COMP", "FLY_CS", "FLY_OUT", "FLY_RT", "FLY_VREF", "FLY_G",
       "FLY_SRC", "FLY_DRN", "FLY_CLP"}
CANB = {"CANH", "CANL", "CAN_MID", "CAN_TL", "CAN_TH", "GND_ISO", "VISO"}
BRIDGE = {"T1", "T2", "U12", "U21", "U9", "C66", "C56"}
KEEPOUT = [(XB - BAND, 0, XB + BAND, H), (XC - BAND, YC - BAND, XC + BAND, H), (XC - BAND, YC - BAND, W, YC + BAND)]


def region_of(p):
    nets = set(p.pins.values())
    if nets & PRI:
        return "P"
    if nets & CANB:
        return "C"
    return "S"


def in_region(bb, reg):
    x0, y0, x1, y1 = bb
    if reg == "P":
        return x1 < XB - BAND
    if reg == "C":
        return x0 > XC + BAND and y0 > YC + BAND
    if x0 < XB + BAND:
        return False
    if x1 > XC - BAND and y1 > YC - BAND:
        return False
    return True


PL = {k: tuple(v[:3]) for k, v in json.load(open("/home/claude/dcdc/pcb5/place_revD.json")).items()}
for gone in ["U19", "C85", "C74", "C76", "C78"]:
    PL.pop(gone, None)
ALLOW_OVERLAP = set()


def put(ref, x, y, rot=0):
    PL[ref] = (round(x, 3), round(y, 3), rot)


def row(refs, x0, y, dx, rot=0):
    for i, r in enumerate(refs):
        if r:
            put(r, x0 + i * dx, y, rot)


def col(refs, x, y0, dy, rot=0):
    for i, r in enumerate(refs):
        if r:
            put(r, x, y0 + i * dy, rot)


# =========================================================================== flyback, primary side (left of T2)
put("T2", XB, 57.0, 270)          # pins 1-5 at x 62.12 (pin1 FLY_DRN y 62, pin3 VIN y 57), 6-10 at x 77.88
put("D8", 57.4, 62.0, 0)          # cathode (FLY_CLP) left, anode (drain) right next to T2 pin 1
put("C94", 55.4, 59.4, 90)        # FLY_CLP (bottom) / VIN (top)
put("R116", 53.4, 59.4, 90)       # FLY_CLP (bottom) / VIN (top)
put("C95", 59.2, 56.4, 90)        # VIN (bottom, next to T2 pin 3) / GNDP (top)
put("Q11", 60.6, 64.9, 90)        # drain up to the drain node, G left, S right
put("R114", 61.55, 68.8, 270)     # FLY_SRC top, GNDP bottom
put("R113", 58.4, 67.2, 270)      # gate pull-down: FLY_G top
put("R112", 56.4, 66.0, 90)       # FLY_OUT (bottom) -> FLY_G (top)
put("U20", 52.0, 70.4, 90)        # top row: VREF VCC OUT GND, bottom row: COMP FB CS RT
put("C90", 49.6, 65.2, 90)        # FLY_VREF (bottom) / GNDP
put("C89", 51.2, 65.2, 90)        # +10V_P (bottom) / GNDP
put("C88", 47.8, 64.9, 90)        # +10V_P (bottom) / GNDP, 0603
put("C92", 48.6, 74.6, 90)        # GNDP (top) / COMP (bottom)
put("R115", 53.0, 75.6, 90)       # FLY_SRC / FLY_CS
put("C93", 51.6, 75.6, 90)
put("R111", 56.0, 72.6, 90)
put("C91", 55.4, 75.2, 90)
# =========================================================================== flyback secondary + feedback
put("D9", 83.4, 60.75, 180)       # anode (FLY_SA) left at T2 pins 9/10, cathode (+10V) right
put("C96", 85.4, 56.6, 90)        # +10V (bottom) / GND (top)
put("C97", 87.6, 56.6, 90)
put("R122", 81.8, 63.8, 0)        # DNP snubber FLY_SA -> FLY_SNB
put("C98", 84.6, 63.8, 0)         # DNP FLY_SNB -> +10V
put("U21", XB, 70.0, 180)         # transistor (pins 3/4) left = primary, LED (1/2) right
put("R118", 74.4, 70.0, 90)       # OPTO_A (bottom) / OPTO_K (top)
put("R117", 74.4, 73.2, 90)       # +10V (bottom) / OPTO_A (top)
put("U22", 77.4, 67.6, 0)         # TL431: K left-top, REF left-bottom, A right
put("R121", 80.6, 65.8, 0)        # OPTO_K (left) -> FLY_CZ (right)
put("C99", 82.4, 67.4, 270)       # FLY_CZ (top) / FLY_FB (bottom)
put("R119", 80.0, 69.6, 90)       # +10V (bottom) / FLY_FB (top)
put("R120", 78.0, 70.4, 270)      # FLY_FB (top) / GND (bottom)
put("C77", 77.4, 80.2, 0)         # U12 VDDB pin 16
put("R79", 77.4, 86.6, 0)         # LLC_A pull-down at U12 pin 12
put("R80", 77.4, 88.0, 0)         # LLC_B pull-down at U12 pin 11

# =========================================================================== secondary aux: +10V -> +5V buck (same pattern as U13)
put("C1", 100.0, 12.0, 0)         # VBUS bulk 47 uF, above C5/C6 at the 4SBB input
put("U4", 95.0, 60.0, 0)
put("C21", 94.2, 54.0, 180)       # +10V (right) | GND (left)
put("C22", 97.2, 54.0, 90)
put("C23", 95.0, 57.5, 0)         # boot
put("D2", 100.2, 55.2, 90)         # SW (bottom) / GND (top)
put("L2", 105.0, 59.0, 0)
put("C26", 109.0, 59.0, 90)
put("R19", 92.6, 63.0, 90)        # FB / GND
put("R18", 94.2, 63.0, 270)       # +5V (top) / FB
put("R17", 97.0, 63.0, 270)       # EN (top) / GND
put("R16", 99.0, 63.0, 90)        # +10V (bottom) / EN
put("TP6", 88.2, 60.6, 0)         # +10V
put("TP7", 109.0, 63.4, 0)        # +5V

# =========================================================================== LLC tank: CR4-6 (GNDP side) on top, CR1-3 (VIN side)
# next to Q5's drain so the VIN copper from Q5 / C61-63 reaches them without crossing GNDP
col(["CR4", "CR5", "CR6"], 53.5, 15.2, 2.7, 180)
col(["CR1", "CR2", "CR3"], 53.5, 23.3, 2.7, 0)

# =========================================================================== primary aux: VIN -> +10V_P buck, +5V_P LDO
put("U13", 13.4, 67.4, 0)
put("C70", 12.6, 61.4, 180)       # VIN (right pad) | GNDP (left pad)
put("C71", 13.4, 64.9, 0)         # boot CB | SW
put("D6", 17.7, 62.6, 90)         # SW (bottom) / GNDP (top)
put("L3", 22.6, 66.4, 0)
put("C72", 26.6, 66.4, 90)
put("R78", 11.0, 70.4, 90)        # FB | GNDP
put("R77", 12.6, 70.4, 270)       # +10V_P (top) | FB
put("R76", 15.4, 70.4, 270)       # EN (top) | GNDP
put("R75", 17.4, 70.4, 90)        # VIN | EN
put("TP3", 26.6, 71.0, 0)
put("U14", 34.0, 66.0, 0)
put("C73", 40.4, 66.0, 90)
put("TP4", 40.4, 70.6, 0)

ALLOW_OVERLAP |= {(c, "T1") for c in ["CR1", "CR2", "CR3", "CR4", "CR5", "CR6"]}

# =========================================================================== input OVP + VIN monitor (primary, bottom left)
# row 1: 2.495 V reference and the OVP comparator U15 (output OVP_P -> U12 pin 3)
put("U16", 50.6, 80.4, 180)       # TL431 shunt: VREF_P pins right, GNDP left
put("R85", 53.8, 80.4, 180)       # +5V_P (right) -> VREF_P (left)
put("R81", 51.6, 84.2, 0)         # VIN (left) -> OVP_DIV (right), 1206
put("C79", 54.4, 87.0, 270)       # OVP_DIV (top) / GNDP
put("R82", 55.6, 87.0, 270)       # OVP_DIV (top) / GNDP
put("U15", 59.0, 82.6, 0)
put("C80", 61.4, 80.4, 0)
put("R83", 62.2, 83.0, 270)       # +5V_P (top) / OVP_P (bottom)
put("R84", 59.0, 85.4, 180)       # OVP_P (right) -> OVP_DIV (left), hysteresis
# row 2: PWM comparator U18 (output VINPWM_P -> U12 pin 4)
put("U18", 59.0, 89.6, 0)
put("C84", 61.4, 87.4, 0)
put("R108", 62.2, 90.0, 270)      # +5V_P (top) / VINPWM_P (bottom)
put("R110", 59.0, 92.4, 180)      # VINPWM_P (right) -> OVP_DIV (left)
put("R109", 55.6, 91.0, 0)        # RAMP_P (left) -> RAMPS_P (right)
# row 3: linear ramp (PNP current source Q9 into C82), reset comparator U17, stretcher D7/C81/R107, discharge Q10
put("R87", 36.6, 95.0, 270)       # +5V_P / PB_P
put("R88", 36.6, 97.6, 270)       # PB_P / GNDP
put("R86", 38.6, 98.6, 90)        # +5V_P (bottom) / PE_P (top)
put("Q9", 39.6, 95.4, 0)          # B left-top, E left-bottom, C right
put("C82", 42.8, 95.4, 270)       # RAMP_P (top) / GNDP
put("R89", 44.9, 94.0, 180)       # DIS_P (right) -> RAMP_P (left)
put("Q10", 47.9, 95.4, 180)       # drain left (DIS_P), gate right-bottom, source right-top
put("C81", 49.6, 98.6, 90)
put("R107", 48.4, 98.6, 90)
put("D7", 52.6, 100.2, 0)         # K (GATE_P) left, A (RST_P) right
put("U17", 53.6, 95.4, 0)
put("R106", 56.6, 96.4, 270)      # +5V_P (top) / RST_P
put("C83", 56.6, 93.8, 0)

ALLOW_OVERLAP |= {("C95", "T2"), ("D8", "T2"), ("Q11", "T2")}
put("U12", XB, 84.6, 0)

# =========================================================================== MCU decoupling at the package corners / analog pins
put("C33", 108.2, 73.4, 90)       # VDD48 / VSS47 (top-left corner)
put("C32", 120.8, 76.8, 0)        # VDD32 / VSS31 (right-top corner)
put("C31", 118.4, 88.4, 90)       # VDD16 / VSS15 (bottom-right corner)
put("C35", 120.0, 88.4, 90)       # 4.7 uF bulk
put("C34", 105.6, 85.6, 180)      # VDD64 / VSS63 (left-bottom corner)
put("C30", 106.4, 88.2, 180)      # VBAT pin 1
put("C29", 121.0, 79.0, 90)       # VDDA 100n  (pins 28/29 joined: VREF+ = VDDA)
put("C37", 122.2, 79.0, 90)       # VREF+ 100n
put("C28", 123.4, 79.0, 90)       # VDDA 1u
put("C36", 124.6, 79.0, 90)       # VREF+ 1u
put("FB1", 126.6, 77.2, 90)       # +3V3 -> +3V3A
put("R98", 124.6, 76.2, 0)        # PB10 pull-down (pin 30)
put("R97", 124.8, 81.4, 0)        # PB2 pull-down (pin 26)
put("TP9", 129.0, 76.6, 0)        # +3V3A
# 3.3 V LDO next to the MCU, fed from the +5 V buck
put("U5", 102.8, 72.8, 0)         # IN/GND/EN left, OUT right
put("C86", 100.2, 72.8, 90)
put("C27", 106.0, 72.8, 90)       # 22 uF 0805
put("TP8", 110.6, 69.6, 0)        # +3V3
put("TP10", 99.0, 76.4, 0)        # GND (secondary)
# +10V rail bulk at the drivers, VBUS test point at the bulk cap
put("C24", 99.6, 48.2, 90)       # +10V at U2
# U2 high side: HO escapes between the HB / HS links through R4, G1 via inside the bootstrap loop (pair to Q1 on In2)
put("R4", 100.75, 43.64, 180)     # HO1 (right, at U2 pin 3) -> G1 (left)
put("C15", 97.6, 43.64, 270)      # boot: HB1 (top) / SW1 (bottom)
put("C25", 102.2, 35.6, 0)         # +10V at U11 (SR driver)
put("TP5", 92.0, 9.0, 0)          # VBUS at the bulk cap
put("R45", 126.8, 74.0, 90)
ALLOW_OVERLAP |= {(c, "U1") for c in ["C30", "C31", "C32", "C33", "C34", "C35"]}
ALLOW_OVERLAP |= {("C27", "U1"), ("C94", "D8"), ("D8", "Q11"), ("D8", "R116"), ("Q11", "R114"), ("C98", "R122")}

# =========================================================================== input + LLC half-bridge driver (Rev E)
# VIN band (top copper) y ~28-37 from F1 to Q5 / CR1-3; GNDP band y ~37.6-48 under it; U10 above the VIN band.
put("J1", 10.5, 31.0, 270)        # VIN_RAW (y 31) / GNDP (y 36.08), plug from the left edge
put("F1", 17.0, 29.6, 0)
put("D1", 22.0, 33.6, 270)        # VIN (top) / GNDP (bottom)
put("C60", 30.0, 34.0, 270)       # VIN (top) / GNDP (bottom)
put("TP1", 22.0, 25.6, 0)         # VIN
put("TP2", 22.0, 41.6, 0)         # GNDP
put("U10", 44.0, 21.5, 180)       # HB/HO/HS/VDD right, HI/LI/VSS/LO left
put("C68", 47.8, 25.0, 0)         # +10V_P / GNDP at VDD
put("C67", 48.6, 20.8, 90)        # boot: HBP (bottom) / HB_SW (top)
put("R62", 47.8, 17.4, 0)         # HOP -> G5
put("R64", 55.6, 31.4, 0)         # G5 (left) / HB_SW (right) at Q5
put("R63", 39.0, 25.0, 90)        # LOP -> G6
put("R65", 46.2, 45.6, 0)         # G6 / GNDP at Q6
put("R66", 38.8, 19.6, 0)         # LLC_HI_P pull-down
put("R67", 38.8, 20.9, 0)         # LLC_LO_P pull-down
ALLOW_OVERLAP |= {("R64", "T1")}

# =========================================================================== SR driver: outputs face the SR gates, gate R in the path
put("U11", 98.6, 29.5, 180)       # left x 96.1: SR_OB 27.6, VDD 28.9, SR_OA 30.1, EN 31.4 | right x 101.1: SR2_PWM, GND, SR1_PWM, EN
put("C69", 94.0, 28.87, 180)      # VDD 1u: +10V (right, at pin 6) / GND (left, onto the SR GND strip)
put("R69", 94.0, 24.6, 90)        # SR_OB (bottom) -> G8 (top)
put("R71", 95.4, 18.59, 0)        # G8 (left) / GND
put("R68", 94.0, 34.4, 270)       # SR_OA (top) -> G7 (bottom)
put("R70", 95.4, 37.59, 0)        # G7 (left) / GND
put("C25", 97.8, 34.4, 0)         # +10V bulk 10u
put("R74", 103.4, 27.59, 0)       # SR2_PWM pull-down
put("R73", 103.4, 30.14, 0)       # SR1_PWM pull-down
put("R72", 103.4, 31.41, 0)       # SR_EN pull-down
put("C6", 101.2, 19.6, 90)        # VBUS HF cap at Q1 drain: VBUS (bottom) / GND (top)
put("R2", 114.4, 30.2, 270)       # DNP SW1 snubber R: SW1 (top) / SNB1
put("C13", 114.4, 34.3, 270)      # DNP SW1 snubber C: SNB1 (top) / PGND
# LLC low-side gate pull-down right at the Q6 gate
put("R65", 46.9, 44.6, 270)       # G6 (top) / GNDP (bottom)
ALLOW_OVERLAP |= {("C69", "U11")}

# =========================================================================== output: bulk C11 VOUT pad to the right edge strip
put("C11", 151.0, 33.4, 180)      # VOUT pad right (155.2), GND pad left (146.8)
put("C12", 153.4, 40.6, 270)      # VOUT HF cap: VOUT (top) / GND (bottom)
put("TP11", 157.2, 41.2, 0)       # VOUT
put("R3", 129.6, 30.2, 270)       # DNP SW2 snubber R: SW2 (top) / SNB2
put("C14", 129.6, 34.3, 270)      # DNP SW2 snubber C: SNB2 (top) / PGND (in the PGND bar)
put("C65", 86.53, 10.2, 90)       # DNP SR_D2 snubber C: SNB4 (bottom) / GND (top, via)

# LLC driver moved left: room for the boot cap / gate resistor between U10 and the CR column
put("U10", 40.5, 21.5, 180)
put("C67", 48.6, 20.86, 90)        # boot: HBP (bottom) / HB_SW (top); HO escapes through R62 between them
put("R62", 45.75, 20.87, 0)         # HOP -> G5, straight off U10 pin 3, G5 via to B.Cu right of it
put("C68", 45.0, 25.6, 0)          # VDD
put("R66", 35.4, 19.6, 180)       # LLC_HI_P pull-down: signal pad (right) in line with U10 pin 5
put("R67", 35.4, 20.9, 180)       # LLC_LO_P pull-down: signal pad (right) in line with U10 pin 6
put("R63", 35.6, 24.6, 90)
