"""Schematic sheets and hand placement (A3, mm). PLACE[ref] = (x, y, rot[, mirror])."""

SHEETS = {
    "llc":     (["H_LLC"],  "LLC isolation stage - half-bridge, PQ2620, synchronous rectifier"),
    "pri_aux": (["I_PRI"],  "Primary aux supply, CA-IS3742 isolator, input OVP and VIN monitor"),
    "iso_pwr": (["K_FLY"],  "Isolated aux flyback - UC3843B, PA3855, TL431 + optocoupler"),
    "sbb":     (["A_POWER", "B_DRIVE"], "4SBB regulator - power stage and gate drivers"),
    "sec_aux": (["C_AUX"],  "Secondary aux supplies"),
    "mcu":     (["D_MCU"],  "STM32G474RBT3 MCU"),
    "sense":   (["E_SENSE"], "Sensing - VBUS, VOUT, inductor and output current, NTC"),
    "can":     (["F_CAN"],  "Isolated CAN"),
    "io":      (["G_IO"],   "Address switch, programming pads, ARM SWD, LEDs"),
}

PLACE = {}


def put(ref, x, y, rot=0, mirror=False):
    PLACE[ref] = (x, y, rot, mirror)


# ============================ LLC (H_LLC) ============================
put("J1", 25.4, 63.5, 180)
put("F1", 43.18, 63.5, 90)
put("D1", 48.26, 78.74, 270)
for i, r in enumerate(["C60", "C61", "C62", "C63"]):
    put(r, 58.42 + 17.78 * i, 78.74)
put("Q5", 139.7, 63.5)
put("Q6", 139.7, 101.6)
put("R62", 121.92, 63.5, 90)      # HOP -> G5
put("R64", 129.54, 76.2)          # G5 / HB_SW
put("R63", 121.92, 101.6, 90)     # LOP -> G6
put("R65", 129.54, 114.3)         # G6 / GNDP
put("U10", 88.9, 116.84)
put("C67", 106.68, 104.14)        # boot HBP / HB_SW
put("C68", 66.04, 104.14)         # +10V_P
put("R66", 68.58, 132.08)         # LLC_HI_P pulldown
put("R67", 76.2, 132.08)          # LLC_LO_P pulldown
for i, r in enumerate(["CR1", "CR2", "CR3"]):
    put(r, 157.48 + 17.78 * i, 101.6)
for i, r in enumerate(["CR4", "CR5", "CR6"]):
    put(r, 157.48 + 17.78 * i, 121.92)
put("T1", 218.44, 88.9)
put("Q7", 271.78, 106.68)          # SR_D1
put("Q8", 271.78, 68.58)           # SR_D2
put("R68", 251.46, 106.68, 90)    # SR_OA -> G7
put("R70", 259.08, 119.38)
put("R69", 251.46, 68.58, 90)     # SR_OB -> G8
put("R71", 259.08, 81.28)
put("R60", 294.64, 109.22)        # SR snubbers
put("C64", 294.64, 121.92)
put("R61", 294.64, 71.12)
put("C65", 294.64, 83.82)
put("U11", 218.44, 152.4)
put("R72", 172.72, 175.26)
put("R73", 185.42, 175.26)
put("R74", 198.12, 175.26)
put("C69", 241.3, 175.26)
put("C66", 218.44, 210.82)

# ============================ Primary aux + isolator (I_PRI) ============================
put("C70", 40.64, 83.82)
put("R75", 50.8, 81.28)
put("R76", 50.8, 96.52)
put("U13", 76.2, 83.82)
put("C71", 101.6, 76.2)
put("D6", 106.68, 96.52, 270)
put("L3", 121.92, 83.82, 90)
put("R77", 137.16, 93.98)
put("R78", 137.16, 109.22)
put("C72", 147.32, 93.98)
put("U14", 175.26, 83.82)
put("C73", 193.04, 93.98)
put("C75", 218.44, 93.98)
put("U12", 264.16, 101.6)
put("R79", 297.18, 121.92)
put("R80", 309.88, 121.92)
put("C77", 309.88, 93.98)

# ============================ 4SBB power + drivers (A_POWER + B_DRIVE) ============================
for i, r in enumerate(["C1", "C2", "C3", "C4", "C5", "C6"]):
    put(r, 25.4 + 17.78 * i, 45.72)
put("Q1", 116.84, 76.2)
put("Q2", 116.84, 114.3)
put("L1", 152.4, 96.52, 90)
put("Q3", 187.96, 76.2, 0, True)
put("Q4", 187.96, 114.3, 0, True)
put("RS1", 152.4, 139.7)
put("R2", 137.16, 121.92)
put("C13", 137.16, 134.62)
put("R3", 167.64, 121.92)
put("C14", 167.64, 134.62)
# left driver U2 -> Q1/Q2
put("U2", 58.42, 96.52)
put("R4", 93.98, 76.2, 90)        # HO1 -> G1
put("R6", 104.14, 86.36)          # G1 / SW1
put("R5", 93.98, 114.3, 90)       # LO1 -> G2
put("R7", 104.14, 124.46)         # G2 / PGND
put("C15", 76.2, 81.28)           # boot HB1 / SW1
put("C16", 30.48, 86.36)
put("C17", 38.1, 86.36)
put("R8", 30.48, 116.84)
put("R9", 38.1, 116.84)
# right driver U3 (mirrored) -> Q3/Q4
put("U3", 248.92, 96.52, 0, True)
put("R10", 210.82, 76.2, 270)     # HO2 -> G3 (pin1 right)
put("R12", 200.66, 86.36)         # G3 / SW2
put("R11", 210.82, 114.3, 270)    # LO2 -> G4
put("R13", 200.66, 124.46)        # G4 / PGND
put("C18", 231.14, 81.28)         # boot HB2 / SW2
put("C19", 276.86, 86.36)
put("C20", 284.48, 86.36)
put("R14", 276.86, 116.84)
put("R15", 284.48, 116.84)
for i, r in enumerate(["C7", "C8", "C9", "C10", "C11", "C12", "R1"]):
    put(r, 190.5 + 17.78 * i, 167.64)
put("RSH1", 307.34, 180.34)
put("J2", 330.2, 167.64)

# ============================ Secondary aux (C_AUX) ============================
put("C21", 40.64, 83.82)
put("C22", 22.86, 83.82)
put("R16", 58.42, 81.28)
put("R17", 58.42, 96.52)
put("U4", 83.82, 83.82)
put("C23", 109.22, 76.2)
put("D2", 114.3, 96.52, 270)
put("L2", 129.54, 83.82, 90)
put("R18", 144.78, 93.98)
put("R19", 144.78, 109.22)
put("C24", 154.94, 93.98)
put("C25", 167.64, 93.98)
put("U5", 190.5, 83.82)
put("C26", 208.28, 93.98)
put("C86", 220.98, 93.98)
put("C27", 236.22, 93.98)
put("FB1", 251.46, 83.82, 90)
put("C28", 266.7, 93.98)
put("C29", 279.4, 93.98)

# ============================ MCU (D_MCU) ============================
put("U1", 203.2, 144.78)
for i, r in enumerate(["C30", "C31", "C32", "C33", "C34", "C35"]):
    put(r, 129.54 + 12.7 * i, 63.5)
put("C36", 218.44, 63.5)
put("C37", 231.14, 63.5)
put("Y1", 149.86, 96.52, 0)
put("C38", 137.16, 102.87)
put("C39", 162.56, 102.87)
put("C40", 175.26, 78.74)
NOWIRE = {("C40", "1")}
put("R20", 246.38, 177.8)

# ============================ Sensing (E_SENSE) ============================
put("U7", 106.68, 81.28)
put("R25", 132.08, 101.6)
put("R26", 132.08, 116.84)
put("C43", 144.78, 116.84)
put("C44", 93.98, 63.5)
put("R27", 132.08, 81.28, 90)
put("C45", 142.24, 91.44)
put("U8", 106.68, 152.4)
put("C46", 93.98, 134.62)
put("R28", 132.08, 152.4, 90)
put("C47", 142.24, 162.56)
put("R21", 205.74, 73.66)
put("R22", 205.74, 91.44)
put("C41", 218.44, 91.44)
put("R23", 246.38, 73.66)
put("R24", 246.38, 91.44)
put("C42", 259.08, 91.44)
put("R29", 205.74, 139.7)
put("TH1", 205.74, 157.48)
put("C48", 218.44, 157.48)
NOWIRE |= {("R29", "1"), ("R25", "1")}   # VREF_ADC by label (avoid wires across the GND row)

# ============================ CAN (F_CAN) ============================
put("U9", 152.4, 101.6)
put("C49", 96.52, 76.2)
put("C50", 109.22, 76.2)
put("C51", 121.92, 76.2)
put("C52", 182.88, 73.66)
put("C53", 195.58, 73.66)
put("C54", 208.28, 73.66)
put("R30", 210.82, 106.68)           # CAN_TH -> CAN_MID (split termination)
put("R31", 210.82, 121.92)           # CAN_MID -> CAN_TL
put("C55", 220.98, 121.92)           # CAN_MID -> GND_ISO
put("JP1", 195.58, 114.3)            # TERM 2x2: 1 CAN_TH-2 CANH, 3 CANL-4 CAN_TL (shunts across rows)
NOWIRE |= {("JP1", "2"), ("JP1", "3")}
put("D3", 241.3, 109.22)             # NUP2105 TVS under the bus
put("J3", 299.72, 99.06)             # bus straight into J3 pins 1/2
put("J4", 299.72, 114.3)             # daisy-chain connector: named pins
NOWIRE |= {("J4", "1"), ("J4", "2")}
put("C56", 152.4, 152.4)

# ============================ IO (G_IO) ============================
put("SW1", 165.1, 101.6)
for i in range(6):
    put(f"R{32 + i}", 66.04 + 12.7 * (5 - i), 71.12, 180)    # pull-ups, +3V3 on top (ADDR0 column nearest SW1)
    put(f"R{38 + i}", 66.04 + 12.7 * (5 - i), 129.54, 180)   # header series, ADDR on top
put("J5", 96.52, 157.48, 270)
put("J6", 172.72, 180.34)
put("J7", 228.6, 180.34)
for _i, _r in enumerate(["R123", "R124", "R125", "R126", "R127", "R128", "R129"]):
    put(_r, 139.7, 157.48 + 7.62 * _i, 90)          # Rev E2 series resistors MCU -> J6 / J7
put("D4", 274.32, 76.2)
put("R44", 254.0, 76.2, 270)
put("D5", 274.32, 96.52)
put("R45", 254.0, 96.52, 270)
for i, (x, y) in enumerate([(40.64, 210.82), (60.96, 210.82), (81.28, 210.82), (101.6, 210.82)]):
    put(f"H{i + 1}", x, y)

# ============================ Rev D additions ============================
FIELDS = {}     # ref -> {"ref": (x, y) or None, "value": (x, y) or None (hidden)}
NOTES = {}      # sheet -> [(x, y, text)]

# --- primary input OVP comparator (pri_aux sheet, below the aux buck) ---
put("R81", 200.66, 152.4)            # VIN -> OVP_DIV
put("R82", 200.66, 172.72)           # OVP_DIV -> GNDP
put("C79", 190.5, 172.72)            # OVP_DIV filter
put("U15", 226.06, 162.56)           # LMV331: + = OVP_DIV, - = VREF_P
put("R84", 222.25, 142.24, 270)      # hysteresis OVP_P (right) -> OVP_DIV (left)
put("R83", 241.3, 152.4)             # pull-up +5V_P -> OVP_P
put("C80", 248.92, 175.26)           # comparator decoupling
put("U16", 213.36, 185.42)           # TL431 2.495 V reference
put("R85", 228.6, 179.07)            # TL431 bias from +5V_P
NOTES["pri_aux"] = [(124.46, 152.4, "INPUT OVP (primary side)\n"
                                     "Trip = 2.495 V x (1 + 191k/10k) = 50.2 V rising\n"
                                     "Hysteresis ~0.4 V (R84 2.2M)\n"
                                     "OVP_P high = over-voltage -> U12 VI1 -> VO1\n"
                                     "-> VIN_OVP -> PA15 (HRTIM1_FLT2 / EXTI15)")]
# --- VIN monitor PWM (pri_aux sheet, bottom) ---
put("R87", 76.2, 208.28)             # base bias top
put("R88", 76.2, 228.6)              # base bias bottom
put("R86", 96.52, 203.2)             # emitter resistor
put("Q9", 93.98, 220.98, 0)          # PNP current source
put("C82", 111.76, 236.22)           # ramp cap (C0G)
put("R89", 124.46, 228.6)            # discharge series R
put("Q10", 129.54, 243.84)           # reset NMOS
put("U17", 152.4, 220.98)            # top detector
put("R106", 170.18, 208.28)          # pull-up
put("D7", 180.34, 223.52, 180)       # to hold cap
put("C81", 190.5, 236.22)            # hold cap
put("R107", 200.66, 236.22)          # hold discharge
put("C83", 157.48, 241.3)            # U17 decoupling
put("R109", 223.52, 223.52, 90)      # ramp series R (to U18 IN-)
put("U18", 246.38, 220.98)           # PWM comparator
put("R110", 246.38, 205.74, 90)      # hysteresis (to OVP_DIV)
put("R108", 266.7, 208.28)           # pull-up -> U12 VI2
put("C84", 254.0, 241.3)             # U18 decoupling
NOWIRE |= {("R109", "1"), ("U18", "1"), ("R110", "2"), ("U12", "4"), ("U17", "3")}   # RAMP_P / OVP_DIV / OVP_DIV / VINPWM_P / VREF_P by label
NOTES["pri_aux"].append((40.64, 256.54, "VIN MONITOR (primary side, monitoring only)\n"
                         "Ramp 0 -> 2.495 V in ~5 ms (Q9 ~24 uA into C82 47n C0G), reset ~20 us by U17/D7/C81/Q10\n"
                         "U18: VINPWM_P high while RAMP < OVP_DIV (R110 hysteresis on the divider side)  ->  U12 VI2 -> VO2 -> VIN_PWM -> PA2 (TIM15_CH1 PWM input)\n"
                         "VIN = 50.47 V x (t_high - t_reset) / (period - t_reset) - 0.20 V,  t_reset ~20 us; calibrate once"))
for i, (r, net) in enumerate([("TP1", "VIN"), ("TP2", "GNDP"), ("TP3", "+10V_P"), ("TP4", "+5V_P")]):
    put(r, 284.48 + 12.7 * i, 152.4, 0 if net == "GNDP" else 180)

# --- secondary rail test points (sec_aux sheet) ---
for i, (r, net) in enumerate([("TP5", "VBUS"), ("TP6", "+10V"), ("TP7", "+5V"), ("TP8", "+3V3"), ("TP9", "+3V3A"), ("TP10", "GND")]):
    put(r, 40.64 + 12.7 * i, 139.7, 0 if net == "GND" else 180)

# --- output test points (sbb sheet) ---
put("TP11", 355.6, 160.02, 180)
put("TP12", 368.3, 160.02, 0)

# --- sense test points ---
put("TP13", 152.4, 71.12, 180)
put("TP14", 152.4, 142.24, 180)

# --- MCU: VIN_OVP test point and in-line 10k pull-downs on every unused pin ---
put("TP15", 248.92, 134.62, 180)


def _pulldowns():
    import design as D
    import gen_sch as G0
    import math
    u1 = next(p for p in D.P if p.ref == "U1")
    sym = G0.get_symbol(u1.sym)
    pins = {sp.number: sp for sp in G0.all_pins(sym)}
    ux, uy = PLACE["U1"][0], PLACE["U1"][1]
    for p in D.P:
        if not (p.block == "D_MCU" and (p.pins.get("1", "").startswith("SP_") or p.pins.get("1", "") == "VIN_PWM")):
            continue
        num = next(k for k, v in u1.pins.items() if v == p.pins["1"])
        sp = pins[num]
        tx, ty = ux + sp.position.X, uy - sp.position.Y
        a = (sp.position.angle + 180) % 360
        vx, vy = round(math.cos(math.radians(a))), -round(math.sin(math.radians(a)))
        d = 2.54 + 8.89 + 2.54 + 3.81          # MCU stub, wire (room for the net label), R stub, half R
        cx, cy = tx + vx * d, ty + vy * d
        rot = {(-1, 0): 270, (1, 0): 90, (0, -1): 180, (0, 1): 0}[(vx, vy)]
        put(p.ref, round(cx, 3), round(cy, 3), rot)
        far = 3.81 + 2.54 + 7.0
        FIELDS[p.ref] = {"ref": (round(cx + vx * far, 3), round(cy + vy * far, 3), "left" if vx > 0 else "right"), "value": None}


_pulldowns()
NOTES["mcu"] = [(129.54, 203.2, "Unused GPIOs (PC13-15, PA3-4, PA7, PA10, PB2, PB4, PB5, PB10, PC6, PC7, PC12, PD2):\n"
                                 "10k pull-down to GND each (R90-R105). PA4 is kept free for DAC1_OUT1 (Test_pin_DAC).\n"
                                 "PA2 = VIN_PWM (TIM15_CH1 PWM input, VIN monitor from the primary); R93 is its pull-down.")]


# ============================ Rev E: isolated aux flyback (K_FLY), primary left | secondary right ============================
put("C89", 68.58, 101.6)             # U20 VCC 100n
put("C88", 76.2, 101.6)              # U20 VCC 1u
put("U20", 101.6, 119.38)
put("C92", 60.96, 118.11)            # COMP filter (top pin on the COMP line)
put("C90", 68.58, 125.73)            # VREF bypass (top pin on the VREF line)
put("R111", 76.2, 127.0)             # RT: VREF -> RT/CT
put("C91", 83.82, 134.62)            # CT
put("R112", 124.46, 114.3, 90)       # gate R: OUT left, gate right
put("R113", 132.08, 121.92)          # gate pull-down
put("Q11", 139.7, 114.3)             # FDN86246
put("R114", 142.24, 134.62)          # current sense
put("R115", 124.46, 124.46, 270)     # CS filter R: FLY_SRC right, FLY_CS left
put("C93", 116.84, 132.08)           # CS filter C
put("D8", 172.72, 55.88, 270)        # clamp diode: anode = drain (bottom), cathode = FLY_CLP (top)
put("C94", 182.88, 45.72, 90)        # clamp C  FLY_CLP | VIN
put("R116", 182.88, 38.1, 90)        # clamp R  FLY_CLP | VIN
put("C95", 195.58, 88.9)             # VIN loop cap at T2
put("T2", 215.9, 76.2)               # PA3855: primary pins left, secondary right
put("D9", 238.76, 68.58, 180)        # rectifier: FLY_SA left, +10V right
put("R122", 238.76, 58.42, 90)       # DNP snubber
put("C98", 250.19, 58.42, 90)
put("C96", 256.54, 76.2)
put("C97", 266.7, 76.2)
put("U21", 241.3, 177.8, 0, True)    # opto mirrored: transistor (primary) left, LED (secondary) right
put("R117", 254.0, 167.64)           # +10V -> OPTO_A
put("R118", 259.08, 179.07)          # LED bypass OPTO_A (top) / OPTO_K (bottom)
put("U22", 284.48, 177.8, 0, True)   # TL431 mirrored: K left, A right, REF up
put("R119", 284.48, 154.94)          # +10V -> FLY_FB
put("R120", 292.1, 166.37)           # FLY_FB -> GND
put("C99", 271.78, 166.37, 180)      # FLY_FB (top) / FLY_CZ (bottom)
put("R121", 271.78, 173.99, 180)     # FLY_CZ (top) / OPTO_K (bottom)
NOWIRE |= {("U21", "4")}            # FLY_COMP by label (no wire across Q11)
NOTES["iso_pwr"] = [(30.48, 195.58,
    "Isolated aux flyback: VIN 12-48 V -> +10 V secondary (1.35 W typ, 3 W design, ~170 kHz DCM).\n"
    "UC3843B current mode, VCC = +10V_P (U13). Ipk limit 1.0 V / R114 = 2.0 A. RCD clamp D8/R116/C94: Vds < 85 V at 50 V in (150 V FET).\n"
    "PA3855.006NLT: Np:Ns 1.33:1, Lp 21 uH; secondaries 9-6 and 10-7 in parallel; aux 4-5 not used. Hi-pot 2250 Vdc.\n"
    "Regulation on the secondary: TL431 U22 (+10V = 2.495 x (1 + R119/R120) = 9.98 V) drives the EL357N LED; the opto\n"
    "transistor pulls COMP down (FB grounded). Type-2 compensation R121/C99 (zero 340 Hz). Check the step response on the bench.")]
