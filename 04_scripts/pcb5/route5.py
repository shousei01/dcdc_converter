"""Rev E: DSN export -> net classes -> Freerouting -> SES import.
Power pours on F.Cu / B.Cu are exported by KiCad as conduction planes, so the router treats them as copper
(connected for their own net, obstacles for the others). usage: route5.py in.kicad_pcb out.kicad_pcb [passes]"""
import os, re, subprocess, sys
import pcbnew

PWR_W = ["+10V", "+10V_P", "+5V", "+5V_P", "VIN", "VBUS", "VOUT", "SW_AUX", "SW_P", "FLY_SRC", "FLY_CLP", "FLY_SA",
         "FLY_DRN", "VOUT_N"]
GATE = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "HO1", "HO2", "LO1", "LO2", "HOP", "LOP", "SR_OA", "SR_OB",
        "HB1", "HB2", "HBP", "HB_SW", "SW1", "SW2", "PGND", "FLY_G", "FLY_OUT", "CB_AUX", "CB_P", "SR_D1", "SR_D2", "CR_MID"]
RAIL = ["+3V3", "+3V3A", "GND", "GNDP", "GND_ISO", "VISO", "CANH", "CANL"]
CLASSES = [("PWR_W", PWR_W, 600, 250, "Via_PWR_800:400_um"), ("GATE", GATE, 400, 200, "Via[0-3]_600:300_um"),
           ("RAIL", RAIL, 250, 200, "Via[0-3]_600:300_um")]


def inflate_tht(t, extra=80):
    """grow every through-hole padstack (shapes on the inner layers, not a via) by `extra` um so the router keeps
    the JLC PTH-to-track clearance (0.28 mm) with a 0.2 mm global clearance. KiCad writes the names quoted or
    bare, and the shapes as circle / rect / path (oval) / polygon (roundrect: replaced by its grown bounding rect)"""
    out = []
    for m in re.finditer(r'\(padstack ("?)([^\s"]+)\1\n(.*?)\n    \)', t, re.S):
        name, body = m.group(2), m.group(3)
        if name.startswith("Via") or "In1.Cu" not in body:
            continue
        nb = re.sub(r"\(circle (\S+) ([\d.]+)", lambda c: f"(circle {c.group(1)} {float(c.group(2)) + 2 * extra:.0f}", body)
        nb = re.sub(r"\(path (\S+) ([\d.]+) ", lambda c: f"(path {c.group(1)} {float(c.group(2)) + 2 * extra:.0f} ", nb)
        nb = re.sub(r"\(rect (\S+) ([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)\)",
                    lambda c: f"(rect {c.group(1)} {float(c.group(2)) - extra:.0f} {float(c.group(3)) - extra:.0f} {float(c.group(4)) + extra:.0f} {float(c.group(5)) + extra:.0f})", nb)

        def poly(c):
            v = [float(x) for x in c.group(2).split()]
            xs, ys = v[0::2], v[1::2]
            return f"(rect {c.group(1)} {min(xs) - extra:.0f} {min(ys) - extra:.0f} {max(xs) + extra:.0f} {max(ys) + extra:.0f})"
        nb = re.sub(r"\(polygon (\S+) 0 ([-\d.\s]+)\)", poly, nb)
        out.append((m.start(3), m.end(3), nb))
    for a, b_, nb in reversed(out):
        t = t[:a] + nb + t[b_:]
    print("inflated THT padstacks:", len(out))
    return t


def edge_keepout(t, w=450):
    """0.45 mm wire/via keep-out band along the board outline on every copper layer (JLC routed-copper edge rule)"""
    i = t.find("(boundary")
    j = t.find("\n    (", i + 5)
    xs, ys = map(float, (0, 0))
    k = ""
    W, H = 160000, 105000
    for L in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu"):
        for x0, y0, x1, y1 in ((0, 0, W, w), (0, H - w, W, H), (0, 0, w, H), (W - w, 0, W, H)):
            k += f"\n    (keepout \"\" (rect {L} {x0} {-y1} {x1} {-y0}))"
    return t[:j] + k + t[j:]


def edit_dsn(t):
    t = edge_keepout(inflate_tht(t))
    vp = t.find('(padstack "Via[0-3]_600:300_um"')
    end = t.find("\n    )", vp) + 6
    stack = t[vp:end].replace("Via[0-3]_600:300_um", "Via_PWR_800:400_um").replace(" 600)", " 800)")
    t = t[:end] + "\n    " + stack + t[end:]
    t = t.replace('(via "Via[0-3]_600:300_um")', '(via "Via[0-3]_600:300_um" "Via_PWR_800:400_um")')
    i = t.find("(class kicad_default")
    j = t.find("(circuit", i)
    head = t[i:j]
    moved = {n for _, ns, *_ in CLASSES for n in ns}
    toks = head.split()
    keep = [tok for tok in toks if tok not in moved]
    t = t[:i] + " ".join(keep[:3]) + "\n      " + " ".join(keep[3:]) + "\n      " + t[j:]
    t = re.sub(r"\(width \d+\)\n(\s+)\(clearance [\d.]+\)", r"(width 200)\n\1(clearance 200)", t, count=1)
    k = t.find("(wiring")
    close = t.rfind(")", 0, k)
    present = set(re.findall(r"\(net (\S+)\n", t))
    extra = ""
    for name, ns, w, c, via in CLASSES:
        ns = [n for n in ns if n in present]
        if ns:
            extra += f'    (class {name} {" ".join(ns)}\n      (circuit\n        (use_via {via})\n      )\n      (rule\n        (width {w})\n        (clearance {c})\n      )\n    )\n'
    return t[:close] + extra + "  " + t[close:]


def main(src, dst, passes=40):
    work = os.path.dirname(os.path.abspath(dst))
    tag = os.path.splitext(os.path.basename(dst))[0]
    b = pcbnew.LoadBoard(src)
    dsn, ses = f"{work}/{tag}.dsn", f"{work}/{tag}.ses"
    assert pcbnew.ExportSpecctraDSN(b, dsn)
    txt = edit_dsn(open(dsn).read())
    open(dsn, "w").write(txt)
    if os.path.exists(ses):
        os.remove(ses)
    cmd = ["xvfb-run", "-a", "java", "-jar", "/home/claude/tools/freerouting.jar", "-de", dsn, "-do", ses,
           "-mp", str(passes), "-mt", "1"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=5400)
    open(f"{work}/{tag}.log", "w").write(r.stdout + r.stderr)
    assert os.path.exists(ses), "no SES produced"
    # the SES carries every non-fixed wire: drop the board's unlocked tracks/vias first (re-route passes)
    for t in list(b.GetTracks()):
        if not t.IsLocked():
            b.Remove(t)
    base = f"{work}/{tag}_base.kicad_pcb"
    pcbnew.SaveBoard(base, b)
    r = subprocess.run(["python3", "/home/claude/dcdc/ses_import.py", base, ses, dst], capture_output=True, text=True)
    print(r.stdout[-300:], r.stderr[-300:])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 40)
