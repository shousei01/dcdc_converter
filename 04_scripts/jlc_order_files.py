"""Build the JLCPCB assembly upload files (DCDC_JLC_BOM.csv / DCDC_JLC_CPL.csv) from the release BOM + CPL.
LCSC numbers below were checked in the JLCPCB parts library on 2026-10-18 (package, rating, stock).
usage: jlc_order_files.py release_dir out_dir"""
import csv, sys
rel, out = sys.argv[1:3]
N = "DCDC_LLC_4SBB_G474"
# hand-soldered by the user (THT, custom, or own sample)
EXCL = {"J1", "J2", "J3", "J4", "J5", "J6", "J7", "JP1", "T1", "U1"}   # J6 = SWD pads only (no part)
DNP = {"C13", "C14", "C56", "C64", "C65", "C66", "R2", "R3", "R60", "R61", "R122", "C98"}
# Rev E: every LCSC number comes from design.py (JLC_LCSC, checked in the JLCPCB / LCSC library), so the BOM
# lines carry them directly; no per-line overrides any more (they went stale when lines were regrouped).
LCSC = {}
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
       **dict.fromkeys(["U14"], 180), "U5": 180,                                    # SOT-223 / TLV75533 SOT-23-5
       "U20": 270, "U21": 270, "U22": 180, "Q11": 180,                            # Rev E flyback: SOIC-8, SOP-4, SOT-23 (check in JLC viewer)
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
