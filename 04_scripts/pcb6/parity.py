"""Schematic <-> PCB parity: every symbol pin net (kicad xml netlist) vs the board pad net, values, footprints.
usage: parity.py netlist.xml board.kicad_pcb"""
import sys, xml.etree.ElementTree as ET, pcbnew
x = ET.parse(sys.argv[1]).getroot()
sch = {}
comp = {}
for c in x.find("components"):
    comp[c.get("ref")] = (c.findtext("value"), c.findtext("footprint"))
for n in x.find("nets"):
    name = n.get("name").split("/")[-1]
    for nd in n.findall("node"):
        sch[(nd.get("ref"), nd.get("pin"))] = name
b = pcbnew.LoadBoard(sys.argv[2])
bad = []; pads = 0; seen = set()
for f in b.GetFootprints():
    r = f.GetReference(); seen.add(r)
    if r not in comp:
        bad.append(("extra fp", r)); continue
    v, fpid = comp[r]
    if v != f.GetValue(): bad.append(("value", r, v, f.GetValue()))
    if fpid != f.GetFPIDAsString(): bad.append(("footprint", r, fpid, f.GetFPIDAsString()))
    for p in f.Pads():
        if not p.GetNumber(): continue
        pads += 1
        s = sch.get((r, p.GetNumber()))
        bn = p.GetNetname()
        if s is None:
            if bn: bad.append(("pad not in sch", r, p.GetNumber(), bn))
        elif s.startswith("unconnected-") or s.startswith("Net-("):
            pass
        elif s != bn:
            bad.append(("net", r, p.GetNumber(), s, bn))
missing = [r for r in comp if r not in seen and not r.startswith("#")]
print("pads", pads, "mismatches", len(bad), "missing fps", missing)
for x_ in bad[:30]: print(x_)
