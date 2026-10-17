"""DSN export -> net classes -> Freerouting -> SES import. Usage: route.py board.kicad_pcb out.kicad_pcb [passes]"""
import re, subprocess, sys, os
import pcbnew

PWR_HI = ["VIN_RAW", "VIN", "HB_SW", "CR_MID", "SR_D1", "SR_D2", "VBUS", "SW1", "SW2", "VOUT", "VOUT_N", "PGND"]
PWR_MED = ["GND", "GNDP", "GND_ISO", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "HO1", "HO2", "LO1", "LO2",
           "HOP", "LOP", "SR_OA", "SR_OB", "HB1", "HB2", "HBP", "+10V", "+10V_P", "SW_AUX", "SW_P", "+5V", "+5V_P",
           "+3V3", "VISO", "SNB1", "SNB2", "SNB3", "SNB4", "CANH", "CANL"]
CLASSES = [("PWR_HI", PWR_HI, 1500, 300, "Via_PWR_800:400_um"), ("PWR_MED", PWR_MED, 500, 250, "Via[0-3]_600:300_um")]


def edit_dsn(t):
    # add a power via padstack
    vp = t.find('(padstack "Via[0-3]_600:300_um"')
    end = t.find("\n    )", vp) + 6
    stack = t[vp:end].replace("Via[0-3]_600:300_um", "Via_PWR_800:400_um").replace(" 600)", " 800)")
    t = t[:end] + "\n    " + stack + t[end:]
    # via list in structure
    t = t.replace('(via "Via[0-3]_600:300_um")', '(via "Via[0-3]_600:300_um" "Via_PWR_800:400_um")')
    # default class: remove nets that move to the power classes
    i = t.find("(class kicad_default")
    j = t.find("(circuit", i)
    head = t[i:j]
    moved = {n for _, ns, *_ in CLASSES for n in ns}
    toks = head.split()
    keep = [tok for tok in toks if tok not in moved]
    newhead = " ".join(keep[:3]) + "\n      " + " ".join(keep[3:]) + "\n      "
    t = t[:i] + newhead + t[j:]
    # default rule widths
    t = t.replace("(width 200)\n        (clearance 200.1)", "(width 250)\n        (clearance 200)", 1)
    # append classes before the closing of (network
    k = t.find("(wiring")
    close = t.rfind(")", 0, k)
    extra = ""
    present = set(re.findall(r"\(net (\S+)\n", t))
    for name, ns, w, c, via in CLASSES:
        ns = [n for n in ns if n in present]
        extra += f'    (class {name} {" ".join(ns)}\n      (circuit\n        (use_via {via})\n      )\n      (rule\n        (width {w})\n        (clearance {c})\n      )\n    )\n'
    t = t[:close] + extra + "  " + t[close:]
    return t


def main(src, dst, passes=20):
    work = os.path.dirname(os.path.abspath(dst))
    b = pcbnew.LoadBoard(src)
    dsn, ses = f"{work}/board.dsn", f"{work}/board.ses"
    assert pcbnew.ExportSpecctraDSN(b, dsn)
    txt = edit_dsn(open(dsn).read())
    open(dsn, "w").write(txt)
    if os.path.exists(ses):
        os.remove(ses)
    cmd = ["xvfb-run", "-a", "java", "-jar", "/home/claude/tools/freerouting.jar", "-de", dsn, "-do", ses,
           "-mp", str(passes), "-mt", "4"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3000)
    open(f"{work}/freerouting.log", "w").write(r.stdout + r.stderr)
    assert os.path.exists(ses), "no SES produced"
    b = pcbnew.LoadBoard(src)
    assert pcbnew.ImportSpecctraSES(b, ses)
    pcbnew.SaveBoard(dst, b)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 20)
