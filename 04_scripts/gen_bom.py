"""Grouped BOM (CSV), JLCPCB-format BOM, and cost roll-up at ~100 pcs."""
import csv, sys, re, collections
sys.path.insert(0, "/home/claude/dcdc"); import design as D
OUT = "/home/claude/dcdc/out"
# unit price @100 pcs (USD). src: 'LCSC' = read from LCSC listing Oct 2026, 'est' = typical estimate
PRICE = {
    "STM32G474RBT6": (7.24, "LCSC C529413 (out of stock; RET6 C521608 $10.24)"),
    "UCC27211DDAR": (1.611, "LCSC C141980"),
    "NCEP0140AG": (0.40, "LCSC C503009: $0.62@1, $0.286@1k -> ~0.40@100"),
    "NCEP0160AG": (0.7357, "LCSC C503012"),
    "22u 23A sat": (1.00, "LCSC C49308184 $1.06@30, $0.91@300"),
    "CA-IS3062VW": (2.5056, "LCSC C5338808"),
    "LMR16006XDDCR": (0.3556, "LCSC C87080"),
    "INA181A1IDBVR": (0.2399, "LCSC C2058943 @150"),
    "INA181A2IDBVR": (0.2407, "LCSC C2058784 @150"),
    "AMS1117-5.0": (0.12, "est"), "AMS1117-3.3": (0.10, "est"),
    "2.2u 100V X7R": (0.3626, "LCSC C55151 (Samsung, out of stock; cheaper 1210 100V X7R ~0.10 exist)"),
    "47u 63V": (0.10, "est"), "SMBJ51A": (0.05, "est"), "NUP2105L": (0.06, "est"), "B1100": (0.03, "est"),
    "47u 1A": (0.10, "est"), "8MHz 12pF": (0.12, "est"), "7A": (0.20, "est"), "DIP-6": (0.25, "est"),
    "VIN 12-48V": (0.25, "est"), "VOUT 1.5-48V": (0.25, "est"), "CAN A": (0.04, "est"), "CAN B": (0.04, "est"),
    "TERM": (0.02, "est"), "ADDR HDR": (0.05, "est"), "SWD/UART": (0.06, "est"),
    "4m 1% 2W": (0.08, "est"), "10m 1% 1W": (0.05, "est"), "10k B3950": (0.02, "est"),
    "600R@100MHz": (0.01, "est"),
    "BSC160N15NS5": (0.7523, "LCSC C459172"),
    "UCC27524DR": (0.2143, "LCSC C465729"),
    "CA-IS3642LVW": (2.5056, "LCSC C7422564"),
    "PQ2620 4:8+8": (2.50, "est, custom wound PQ2620 + bobbin, 1k qty"),
    "100n 100V C0G": (0.08, "est, 1206 C0G"),
    "1n Y1 DNP": (0.15, "est"),
    "47u 6.3V": (0.05, "est"),
    "PROG PADS": (0.0, "PCB pads, no part"),
    "ARM SWD 10": (0.40, "est, 2x5 1.27 mm SMD header"),
    "M3": (0.0, "PCB hole, no part"),
    "LMV331IDBVR": (0.08, "est, LCSC LMV331 SOT-23-5 class"),
    "TL431AIDBZR": (0.03, "est"),
    "SS110": (0.03, "est"),
    "16MHz 9pF": (0.12, "est, 3225 crystal"),
}
def price(p):
    if p.value in PRICE: return PRICE[p.value]
    if p.sym == "Device:LED": return (0.01, "est")
    if p.sym == "Device:C": return (0.03 if ("100V" in p.value or "25V" in p.value and "u" in p.value) else 0.003, "est")
    if p.sym == "Device:R": return (0.003 if "0.1%" not in p.value else 0.02, "est")
    return (0.0, "?")

groups = collections.OrderedDict()
for p in D.P:
    if p.value in ("M3", "PROG PADS") or p.mpn == "PCB pad, no part":
        continue
    key = (p.value, p.fp, p.lcsc, p.mpn, p.dnp)
    groups.setdefault(key, []).append(p)
def natkey(r): m = re.match(r"([A-Z]+)(\d+)", r); return (m.group(1), int(m.group(2)))
rows, total = [], 0.0
for (val, fp, lcsc, mpn, dnp), ps in groups.items():
    refs = sorted((p.ref for p in ps), key=natkey)
    up, src = price(ps[0])
    qty = len(ps)
    ext = 0 if dnp else up * qty
    total += ext
    rows.append(dict(Designator=",".join(refs), Qty=qty, Value=val, MPN=mpn, LCSC=lcsc,
                     Footprint=fp.split(":")[1], DNP="DNP" if dnp else "", Unit_USD=round(up, 4),
                     Ext_USD=round(ext, 3), Price_source=src, Note=ps[0].note))
rows.sort(key=lambda r: natkey(r["Designator"].split(",")[0]))
with open(f"{OUT}/BOM_DCDC_4SBB_G474.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
with open(f"{OUT}/BOM_JLCPCB.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    for r in rows:
        if not r["DNP"]: w.writerow([r["MPN"] or r["Value"], r["Designator"], r["Footprint"], r["LCSC"]])
print(f"lines {len(rows)}, placed parts {sum(r['Qty'] for r in rows if not r['DNP'])}, BOM @100 ~ ${total:.2f}")
# isolation (LLC) stage cost = parts in blocks H and I, minus the input parts that existed before (J1, F1, D1)
llc = sum(price(p)[0] for p in D.P if p.block in ("H_LLC", "I_PRI") and not p.dnp and p.ref not in ("J1", "F1", "D1"))
removed = PRICE["AMS1117-3.3"][0]          # secondary 3.3 V LDO no longer needed
base = total - llc + removed
print(f"LLC + isolation parts ~ ${llc:.2f}; non-isolated baseline ~ ${base:.2f}; premium +{100*(llc-removed)/base:.0f}%")
