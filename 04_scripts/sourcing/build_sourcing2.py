"""Rev E sourcing review v2: LCSC stock (live 2026-10-20), shortage risk, 2nd/3rd sources CHECKED for spec and
footprint fit (datasheet / netlist / land pattern). Output: BOM_sourcing_revE.xlsx"""
import csv, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
sys.path.insert(0, "sourcing")
from alts2 import ALTS2, FIX, REMAP

STOCK = {}
for r in csv.reader(open("sourcing/lcsc_stock_20261020.tsv"), delimiter="\t"):
    r = r + [""] * (5 - len(r)); STOCK[r[0]] = (r[1], r[2], r[3], r[4])
bom = list(csv.reader(open("release_E/jlc/DCDC_JLC_BOM.csv")))[1:]
bom.append(["STM32G474RBT3 (hand-soldered)", "U1", "LQFP-64_10x10mm_P0.5mm", "C1235414"])
bom += [["KF2EDGR-5.08-2P (hand-soldered)", "J1,J2", "PhoenixContact_MSTBA_2,5_2-G-5,08", "C441204"],
        ["PZ254V-11-03P-A40 (hand-soldered)", "J3,J4", "PinHeader_1x03_P2.54mm_Vertical", "C42419910"],
        ["PZ254V-11-06P-A40 (hand-soldered)", "J5", "PinHeader_1x06_P2.54mm_Vertical", "C42419913"],
        ["PZ254V-12-04P-A40 (hand-soldered)", "JP1", "PinHeader_2x02_P2.54mm_Vertical", "C45384660"],
        ["HX PZ1.27-2x5P TP (hand-soldered)", "J7", "PinHeader_2x05_P1.27mm_Vertical_SMD", "C41376037"]]

def st(code):
    s = STOCK.get(code, ("", "", "", ""))[2]
    return 0 if s in ("NOTLISTED", "?", "") else int(s)

F = Font(name="Arial", size=9); B = Font(name="Arial", size=9, bold=True)
thin = Side(style="thin", color="BBBBBB"); BOR = Border(top=thin, bottom=thin, left=thin, right=thin)
fills = {"CRITICAL": "F4B6B6", "HIGH": "F9D7A8", "MEDIUM": "FFF2B3", "LOW": "D9EFD3"}
cfill = {"DS": "D9EFD3", "EQ": "E8F3E3", "CHK": "FFF2B3", "PCB": "F9D7A8", "": "FFFFFF"}

wb = Workbook(); ws = wb.active; ws.title = "Sourcing"
hdr = ["#", "Designators", "Qty / board", "Description", "Footprint", "Package type", "Primary MPN", "Manufacturer",
       "LCSC #", "LCSC stock today", "Boards covered", "Price from (USD)", "Risk", "Action",
       "Use as primary (same footprint)",
       "2nd source", "2nd LCSC #", "2nd stock", "2nd check", "2nd spec / fit note",
       "3rd source", "3rd LCSC #", "3rd stock", "3rd check", "3rd spec / fit note",
       "Sources with stock for 100 boards"]
ws.append(hdr)
rows = []
for i, (comment, des, fp, lcsc) in enumerate(bom, 1):
    qty = len(des.split(","))
    mpn, mfr, s0, fr = STOCK.get(lcsc, ("?", "?", "?", ""))
    stock = st(lcsc)
    old = REMAP.get(lcsc)
    info = ALTS2[old or lcsc]
    alist = [x for x in info["alts"] if x[0] != lcsc]
    if old and st(old) > 0:
        alist.append((old, "EQ", "previous primary (low / no stock)"))
    a = []
    for code, chk, note in (alist + [("", "", "")] * 2)[:2]:
        if code:
            m2, f2, _, _ = STOCK[code]
            a.append([f"{m2} ({f2})", code, st(code), chk, note])
        else:
            a.append(["", "", None, "", note or "none in stock on LCSC"])
    use = ""
    use_txt = f"{STOCK[use][0]} ({STOCK[use][1]}) {use}" if use else ""
    boards = stock // qty
    if lcsc in FIX:
        risk, note = FIX[lcsc]
    else:
        n_ok = sum(1 for s in [stock] + [x[2] or 0 for x in a] if s >= 100 * qty)
        risk = "HIGH" if boards < 100 else "MEDIUM" if (boards < 1000 or n_ok < 2) else "LOW"
        note = {"LOW": "Stock fine; 2nd/3rd checked.", "MEDIUM": "Primary covers the build; alternates thin - watch.",
                "HIGH": "Low stock for the qty per board - buy now."}[risk]
    rows.append([i, des, qty, comment, fp, info["pkg"], mpn, mfr, lcsc, "NOT LISTED" if s0 == "NOTLISTED" else stock,
                 None, float(fr) if fr else None, risk, note, use_txt] + a[0] + a[1])
order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
rows.sort(key=lambda r: (order[r[12]], r[0]))
for n, r in enumerate(rows, 2):
    ws.append(r)
    ws.cell(n, 11).value = f'=IF(ISNUMBER(J{n}),INT(J{n}/C{n}),0)'
    ws.cell(n, 26).value = (f'=IF(ISNUMBER(J{n}),IF(J{n}>=100*C{n},1,0),0)+IF(ISNUMBER(R{n}),IF(R{n}>=100*C{n},1,0),0)'
                            f'+IF(ISNUMBER(W{n}),IF(W{n}>=100*C{n},1,0),0)')
    for c in range(1, len(hdr) + 1):
        cell = ws.cell(n, c); cell.font = F; cell.border = BOR
        cell.alignment = Alignment(vertical="top", wrap_text=c in (2, 4, 5, 6, 14, 15, 16, 20, 21, 25))
    ws.cell(n, 13).fill = PatternFill("solid", fgColor=fills[r[12]]); ws.cell(n, 13).font = B
    for c in (19, 24):
        ws.cell(n, c).fill = PatternFill("solid", fgColor=cfill[ws.cell(n, c).value or ""]); ws.cell(n, c).font = B
    for c in (10, 11, 18, 23):
        ws.cell(n, c).number_format = "#,##0"
    ws.cell(n, 12).number_format = "0.0000"
for c in range(1, len(hdr) + 1):
    h = ws.cell(1, c); h.font = Font(name="Arial", size=9, bold=True, color="FFFFFF")
    h.fill = PatternFill("solid", fgColor="2F4F6F"); h.alignment = Alignment(wrap_text=True, vertical="center")
for i, w in enumerate([4, 20, 6, 16, 20, 18, 20, 14, 10, 10, 9, 8, 10, 46, 26, 26, 10, 9, 7, 44, 26, 10, 9, 7, 44, 10], 1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "G2"; ws.auto_filter.ref = f"A1:{get_column_letter(len(hdr))}{len(rows)+1}"; ws.row_dimensions[1].height = 42

# ---------------- Summary
s = wb.create_sheet("Summary", 0)
L = [["DCDC_LLC_4SBB_G474 Rev E - shortage risk, 2nd / 3rd sources (spec + footprint checked)"],
     ["LCSC stock read live from lcsc.com on 2026-10-20. Stock moves daily - re-check at order time. JLC basic parts may be in JLC's own SMT stock when LCSC retail shows 0."],
     [],
     ["Risk", "Lines", "Rule"],
     ["CRITICAL", '=COUNTIF(Sourcing!M:M,"CRITICAL")', "Out of stock / not listed / < 50 boards, or a BOM error - change before ordering (same footprint)"],
     ["HIGH", '=COUNTIF(Sourcing!M:M,"HIGH")', "Covers < 100-300 boards, single maker, or discontinued - buy now"],
     ["MEDIUM", '=COUNTIF(Sourcing!M:M,"MEDIUM")', "Covers < 1,000 boards or alternates thin"],
     ["LOW", '=COUNTIF(Sourcing!M:M,"LOW")', "Plenty of stock and two checked alternates"],
     [],
     ["Check", "Alternates", "Meaning"],
     ["DS", '=COUNTIF(Sourcing!S:S,"DS")+COUNTIF(Sourcing!X:X,"DS")', "Checked against the datasheet: pinout vs board netlist, land pattern vs footprint, ratings"],
     ["EQ", '=COUNTIF(Sourcing!S:S,"EQ")+COUNTIF(Sourcing!X:X,"EQ")', "Same part number from another maker, or passive with same value / package / dielectric and equal-or-better rating"],
     ["CHK", '=COUNTIF(Sourcing!S:S,"CHK")+COUNTIF(Sourcing!X:X,"CHK")', "Usable; one item to confirm (see note)"],
     ["PCB", '=COUNTIF(Sourcing!S:S,"PCB")+COUNTIF(Sourcing!X:X,"PCB")', "Needs a PCB change - see 'PCB reserve'"],
     [],
     ["Packages", "", "All lines use industry-standard packages except: T2 (Pulse EP13Plus, vendor-specific) and T1 (custom PQ2620, hand-fitted). L1 1770 / L2-L3 5040 / SW1 2.54 SMD DIP / J1-J2 5.08 pluggable are de-facto standards made by many vendors."],
     [],
     ["First source changed on the Rev E BOM today (all in stock, same footprints):"]]
for l in L: s.append(l)
for new, old in REMAP.items():
    s.append([new, STOCK[new][0] + " (" + STOCK[new][1] + ")", "replaces " + old + " " + STOCK.get(old, ("",))[0] + ("  -  not listed / out of stock" if st(old) == 0 else "")])
s.append(["C307331", "CL05B104KB54PNC", "now also used for the 22 x 100 nF that were on C1525 (out of stock)"])
s.append([]); s.append(["Buy now / watch:"])
for r in rows:
    if r[12] == "HIGH": s.append([r[8], r[1], r[13]])
s.append([])
s.append(["Not on LCSC", "T1", "Custom PQ2620 transformer - the only part not orderable from LCSC"])
s.append(["Extra to order", "J1, J2 plugs", "Kefa KF2EDGK-5.08-2P-AA (C440880), 2 per board - the cable-side plugs; JP1 needs one 2.54 mm jumper cap"])
s.column_dimensions["A"].width = 18; s.column_dimensions["B"].width = 30; s.column_dimensions["C"].width = 120
for row in s.iter_rows():
    for c in row:
        c.font = Font(name="Arial", size=10); c.alignment = Alignment(wrap_text=True, vertical="top")
s["A1"].font = Font(name="Arial", size=13, bold=True)
for rr in range(5, 9):
    s.cell(rr, 1).fill = PatternFill("solid", fgColor=fills[s.cell(rr, 1).value]); s.cell(rr, 1).font = Font(name="Arial", size=10, bold=True)
for rr in range(11, 15):
    s.cell(rr, 1).fill = PatternFill("solid", fgColor=cfill[s.cell(rr, 1).value]); s.cell(rr, 1).font = Font(name="Arial", size=10, bold=True)
for rr in (4, 10, 16, 18):
    for c in range(1, 4): s.cell(rr, c).font = Font(name="Arial", size=10, bold=True)

# ---------------- Findings from the check
f = wb.create_sheet("Spec check findings")
f.append(["Line", "Finding", "Result"])
for x in [
 ("U12 3rd", "YLPTEC ISO7742N0-Y (old 3rd source) is the NARROW SOIC-16 body", "Won't fit SOIC-16W. Replaced by ISO7742W0-Y (wide, default-low)."),
 ("U11 3rd", "Maxinmicro MX27524S: pin order could not be confirmed from its datasheet", "Dropped. TI UCC27524ADR + UMW UCC27524DR (stated pin-to-pin)."),
 ("U15/17/18", "TPV331S5 / HT331 are push-pull clones with unconfirmed pinout", "Replaced by 3PEAK LMV331X-S5TR and ST LMV331ILT (open-drain, same pinout)."),
 ("U16/U22", "TL431 SOT-23 pinout differs between makers. Board: pin1 = cathode, pin2 = REF (TI DBZ)", "U22 must use a 1=K / 2=REF part: TI, UMW, Nexperia normal pinning, HGSEMI. MSKSEMI (no pin numbers) dropped. U16 has pins 1+2 tied so any TL431 works."),
 ("TH1", "FH CMFB103F3950FANT (old 2nd) is 0805", "Won't fit the 0603 pads. Replaced by two 0603 10k 1 % B3950 parts."),
 ("CR1-CR6", "CCTC / HRE 'M3L' 100 nF 1206 caps show no dielectric - not confirmed C0G", "Resonant caps need C0G. Replaced by Murata GRM31C5C2A104JA01L / TDK C3216C0G2A104JT000E."),
 ("L1", "SOREDE SRYH.1770 (old 3rd) saturates at 16 A vs 23 A design", "Dropped. Shun Xiang Nuo SMMS1770-220M and Sunltech SLO1770C (both 23 A sat). Sunltech land checked: fits."),
 ("L2/L3", "APV ANR5040 has no datasheet on LCSC", "New primary cjiang FNR5040S470MT: recommended land 1.4 x 4.2 / gap 2.3 = our footprint exactly."),
 ("RS1", "Alloy shunt land pattern vs standard R_2512 footprint", "HoJLR2512 terminations 0.9 mm sit fully on our pads (2.35-3.58 mm from centre). OK."),
 ("SW1", "SHOU HAN TPGT land: 1.1 x 2.2 mm pads, rows 6.6 / 11 mm", "Matches our footprint (1.12 x 2.44, rows 6.16 / 10.74)."),
 ("Q1/Q4", "NCE alternates have Qg 54-60 nC vs 26 nC", "Pin-compatible DFN5x6; usable but more switching loss in the hard-switched FETs - bench check."),
 ("Q2/3/5/6", "NCEP068N10G Qg 60 nC vs 65 nC, 6.1 mOhm", "Drop-in (better Rds)."),
 ("U4/U13", "LV2862: same pinout and FB; EN threshold 1.25 V vs ~1.5 V", "U13 under-voltage start moves from ~12 V to ~10 V VIN. Acceptable; note it."),
 ("U9", "No pin-compatible integrated-power isolated CAN from another maker", "ISO1042DW matches pins 2-16; needs pin 1 = 3.3 V + external isolated 5 V. See 'PCB reserve'."),
 ("T2", "Pulse only; PA3855.005NLT same EP13 footprint", "Needs series secondaries. See 'PCB reserve'."),
 ("C82", "BOM had X7R on the ramp cap", "KEMET C0G 47 nF (25 V, node < 5 V)."),
]:
    f.append(list(x))
for c, w in zip("ABC", (12, 70, 80)):
    f.column_dimensions[c].width = w
for row in f.iter_rows():
    for c in row:
        c.font = Font(name="Arial", size=10, bold=(c.row == 1)); c.alignment = Alignment(wrap_text=True, vertical="top")

# ---------------- PCB reserve options
p = wb.create_sheet("PCB reserve")
p.append(["Part", "Why", "What to add (DNP on the normal build)", "Space", "Where", "Status"])
p.append(["T2 PA3855.006NLT", "Single maker (Pulse), 102 pcs at LCSC",
          "3 x 0805 0R jumpers on the secondary: A = pin10->FLY_SA, B = pin6->GND, C = pin6->pin10. Normal (.006): fit A+B. Backup (.005NLT, secondaries in series): fit C only.",
          "~6 x 4 mm", "Free 10 x 8 mm area right of T2 pins 6-10 (x 79.5-89.5, y 46-54)", "Waiting for your OK"])
p.append(["U9 CA-IS3062VW", "Single maker (Chipanalog), integrated isolated DC-DC",
          "1 x 0402 0R to select U9 pin 1 = +5V (CA-IS3062) or +3V3 (ISO1042DW); B0505S-1WR3 isolated 5 V SIP-4 module + 2 caps feeding VISO.",
          "~14 x 10 mm + one 0402", "Free area straddling the isolation gap directly above U9 (x 128-142, y 64-74)", "Waiting for your OK (module pin spacing vs 4 mm gap to confirm)"])
for c, w in zip("ABCDEF", (18, 30, 70, 18, 40, 26)):
    p.column_dimensions[c].width = w
for row in p.iter_rows():
    for c in row:
        c.font = Font(name="Arial", size=10, bold=(c.row == 1)); c.alignment = Alignment(wrap_text=True, vertical="top")
wb.save(sys.argv[1])
print(len(rows), "lines;", {k: sum(1 for r in rows if r[12] == k) for k in order})
