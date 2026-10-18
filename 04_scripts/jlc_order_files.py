"""Build the JLCPCB assembly upload files (DCDC_JLC_BOM.csv / DCDC_JLC_CPL.csv) from the release BOM + CPL.
LCSC numbers below were checked in the JLCPCB parts library on 2026-10-18 (package, rating, stock).
usage: jlc_order_files.py release_dir out_dir"""
import csv, sys
rel, out = sys.argv[1:3]
N = "DCDC_LLC_4SBB_G474"
# hand-soldered by the user (THT, custom, or own sample)
EXCL = {"J1", "J2", "J3", "J4", "J5", "J7", "JP1", "T1", "U1"}
DNP = {"C13", "C14", "C56", "C64", "C65", "C66", "R2", "R3", "R60", "R61"}
LCSC = {  # first designator of the BOM line -> LCSC part
    "C1": "C249664", "C2": "C153036", "C6": "C88219", "C15": "C14663", "C16": "C15849", "C17": "C307331",
    "C22": "C88219", "C24": "C15850", "C27": "C45783", "C28": "C52923", "C29": "C1525", "C35": "C19666",
    "C38": "C1547", "C41": "C113780", "C45": "C106259", "C47": "C22400107", "C49": "C15850", "C55": "C53987",
    "C78": "C96123", "C81": "C107001", "C82": "C53134", "CR1": "C2940749", "D1": "C20883337", "D3": "C14486",
    "D4": "C12624", "D5": "C2286", "F1": "C206980", "FB1": "C1002", "L2": "C86617", "Q9": "C53444",
    "R1": "C2907507", "R4": "C23164", "R6": "C25744", "R16": "C23178", "R17": "C36871", "R18": "C25750",
    "R19": "C25744", "R21": "C122538", "R22": "C186154", "R25": "C186137", "R27": "C25076", "R28": "C11702",
    "R30": "C2933247", "R62": "C22939", "R81": "C870479", "R82": "C190095", "R84": "C11490", "R86": "C25796",
    "R88": "C25756", "R89": "C25092", "R107": "C25741", "R110": "C227116", "RS1": "C500738", "RSH1": "C500718",
    "TH1": "C2892547", "U15": "C34731", "U16": "C23892",
    "SW1": "C6331172"}  # SHOU HAN 2.54-6P TPGT, SMD gull-wing 6-pos DIP
rows = list(csv.reader(open(f"{rel}/BOM_JLCPCB_{N}.csv")))
bom = [["Comment", "Designator", "Footprint", "LCSC Part #"]]
refs = set()
for c, d, fp, l in rows[1:]:
    ds = [x for x in d.split(",") if x not in EXCL]
    if not ds: continue
    l = LCSC.get(d.split(",")[0], l)
    if c.startswith("TL431"): c = "TL431AIDBZR"
    assert l, f"no LCSC for {d}"
    refs |= set(ds); bom.append([c, ",".join(ds), fp, l])
# JLC refuses the same LCSC part on two BOM lines (both get unselected): merge them
merged, seen = [bom[0]], {}
for c, d, fp, l in bom[1:]:
    if l in seen:
        r = merged[seen[l]]; r[1] = r[1] + "," + d
    else:
        seen[l] = len(merged); merged.append([c, d, fp, l])
bom = merged
csv.writer(open(f"{out}/DCDC_JLC_BOM.csv", "w", newline="")).writerows(bom)
# Rotation offsets (deg, CCW, added to the KiCad rotation) so JLC's part models line up with our pads.
# Measured from the JLC placement preview on 2026-10-18 (pin-1 marker vs KiCad pad 1), part by part.
ROT = {**dict.fromkeys(["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"], 270),      # TDSON-8 / DFN5x6
       **dict.fromkeys(["U2", "U3", "U10", "U11", "U9", "U12"], 270),             # SOIC-8(-EP), SOIC-16W
       **dict.fromkeys(["U4", "U13"], 180),                                         # LMR16006 SOT-23-6
       "U7": 0, "U8": 270,                                                          # INA181A1 / INA181A2
       **dict.fromkeys(["U15", "U17", "U18"], 180),                                 # LMV331 SOT-23-5
       **dict.fromkeys(["Q9", "Q10", "U16", "U19"], 180), "D3": 270,                # SOT-23
       **dict.fromkeys(["U5", "U14"], 180),                                         # AMS1117 SOT-223
       "SW1": 270}                                                                  # DIP-6 C6331172: 90 deg CW per JLC viewer (user, 2026-10-18)
# Centroid offsets (mm, in the footprint's own axes, KiCad orientation 0) where JLC's 3D model of the
# chosen part is not centred on the KiCad footprint. NCEP0160AG (C503012): body sits ~1.0 mm toward the
# drain side, measured in JLC's 2D placement view on 2026-10-18 (Q6 1.03 mm, Q2 0.83 mm).
import math
OFS = dict.fromkeys(["Q2", "Q3", "Q5", "Q6"], (-1.0, 0.0))
cpl = list(csv.reader(open(f"{rel}/{N}_CPL.csv")))
o = [["Designator", "Mid X", "Mid Y", "Layer", "Rotation"]]
for r in cpl[1:]:
    if r[0] in EXCL or r[0] in DNP: continue
    rot = (float(r[5]) + ROT.get(r[0], 0)) % 360
    x, y = float(r[3]), float(r[4])          # KiCad pos file: Y up (CPL convention)
    if r[0] in OFS:
        lx, ly = OFS[r[0]]; t = math.radians(float(r[5]))
        # KiCad footprint rotation is CCW; in Y-up coordinates a local vector rotates the usual way
        x += lx * math.cos(t) - (-ly) * math.sin(t)
        y += lx * math.sin(t) + (-ly) * math.cos(t)
    o.append([r[0], f"{x:.4f}mm", f"{y:.4f}mm", "Top" if r[6] == "top" else "Bottom", f"{rot:.0f}"])
csv.writer(open(f"{out}/DCDC_JLC_CPL.csv", "w", newline="")).writerows(o)
cr = {r[0] for r in o[1:]}
print(len(bom) - 1, "BOM lines (duplicate LCSC merged),", len(refs), "parts;", len(o) - 1, "CPL rows; mismatch", sorted(refs ^ cr))
