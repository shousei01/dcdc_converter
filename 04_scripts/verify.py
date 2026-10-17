"""Compare KiCad-exported netlist with design.py intent; basic ERC (drivers, power pins)."""
import sys, xml.etree.ElementTree as ET
sys.path.insert(0, "/home/claude/dcdc"); import design as D
D_net=lambda n: next(p.pins.get(n[1]) for p in D.P if p.ref==n[0])
t = ET.parse(sys.argv[1]).getroot()
got = {}
for n in t.find("nets"):
    name = n.get("name").split("/")[-1]
    for nd in n.findall("node"):
        got[(nd.get("ref"), nd.get("pin"))] = (name, nd.get("pintype"))
errs = 0
want_nodes = set()
for p in D.P:
    for pin, net in p.pins.items():
        want_nodes.add((p.ref, pin))
        g = got.get((p.ref, pin))
        if net == "NC":
            if g and not g[0].startswith("unconnected-"):
                print("NC pin connected:", p.ref, pin, g); errs += 1
            continue
        if not g or g[0] != net:
            print(f"MISMATCH {p.ref}.{pin}: want {net}, got {g}"); errs += 1
# group got by net and make sure no two design nets merged
by = {}
for (r, pn), (net, _) in got.items():
    by.setdefault(net, set()).add((r, pn))
for net, nodes in by.items():
    if net.startswith("unconnected-") or net.startswith("Net-"):
        real = [n for n in nodes if not n[0].startswith("#")]
        if real and any(n in want_nodes and D_net(n)!="NC" for n in real):
            print("unlabelled/unconnected net with design pins:", net, real); errs += 1
def _x(): pass
comps = {c.get("ref") for c in t.find("components")}
missing = {p.ref for p in D.P} - comps
if missing: print("missing components:", missing); errs += 1
# simple ERC: every net with a power_in pin needs a power_out pin or PWR_FLAG
for net, nodes in by.items():
    types = [got[n][1] for n in nodes]
    if "power_in" in types and not ({"power_out"} & set(types)) and net not in D.PWR_FLAG_NETS:
        print("ERC: power_in not driven on", net, sorted(nodes)); errs += 1
    outs = [n for n in nodes if got[n][1] in ("output",)]
    if len(outs) > 1: print("ERC: multiple outputs on", net, outs); errs += 1
    if len([n for n in nodes if not n[0].startswith("#")]) < 2 and not net.startswith("unconnected-"):
        print("ERC: single-pin net", net, nodes); errs += 1
print("nets:", len([n for n in by if not n.startswith("unconnected-")]), "components:", len(comps), "errors:", errs)
if errs: sys.exit(1)

# ---- isolation check: only T1, U12 (isolator) and the DNP Y-cap may join primary and secondary nets
PRI = {"VIN_RAW", "VIN", "GNDP", "HB_SW", "CR_MID", "G5", "G6", "HBP", "HOP", "LOP", "LLC_HI_P", "LLC_LO_P",
       "+10V_P", "+5V_P", "CB_P", "FB_P", "EN_P", "SW_P"}
BRIDGES = {"T1", "U12", "C66"}
iso_err = 0
for p in D.P:
    if p.ref in BRIDGES:
        continue
    nets_used = {n for n in p.pins.values() if n != "NC"}
    if nets_used & PRI and nets_used - PRI:
        print("ISOLATION: part", p.ref, "joins", sorted(nets_used & PRI), "and", sorted(nets_used - PRI)); iso_err += 1
pri_nets_seen = {n for p in D.P for n in p.pins.values()} & PRI
print("isolation check: primary nets", len(pri_nets_seen), "errors", iso_err)
sys.exit(1 if iso_err else 0)
