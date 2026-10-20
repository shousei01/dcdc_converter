"""Rev E2 board edit: series resistors R123-R129 (MCU -> J6/J7), new nets, courtyard legalisation of the
crowded parts, and rip-up of the copper that has to be re-routed. usage: e2_edit.py in.kicad_pcb out.kicad_pcb"""
import sys, json, math
import pcbnew
from shapely.geometry import box, Point, LineString, Polygon
from shapely.ops import unary_union
sys.path.insert(0, "/home/claude/dcdc")
import design as D

M, mm = pcbnew.ToMM, pcbnew.FromMM
src, dst = sys.argv[1:3]
b = pcbnew.LoadBoard(src)
UP = json.load(open("/home/claude/dcdc/sch5/uuid_paths.json"))
P = {p.ref: p for p in D.P}
fps = {f.GetReference(): f for f in b.GetFootprints()}

# 1. schematic links (the schematic was regenerated -> new symbol UUIDs)
for r, f in fps.items():
    if r in UP:
        f.SetPath(pcbnew.KIID_PATH(UP[r]))

# 2. nets
def net(name):
    n = b.FindNet(name)
    if n is None:
        n = pcbnew.NETINFO_ITEM(b, name); b.Add(n)
    return b.FindNet(name)

for ref in ("J6", "J7"):
    for pad in fps[ref].Pads():
        want = P[ref].pins.get(pad.GetNumber())
        if want and want != "NC" and pad.GetNetname() != want:
            pad.SetNet(net(want))

# 3. new resistors
lib = "/usr/share/kicad/footprints"
def load(fp):
    l, n = fp.split(":")
    return pcbnew.FootprintLoad(f"{lib}/{l}.pretty", n)

new = {}
for r in ("R123", "R124", "R125", "R126", "R127", "R128", "R129"):
    p = P[r]
    f = load(p.fp)
    f.SetReference(r); f.SetValue(p.value)
    f.SetPath(pcbnew.KIID_PATH(UP[r]))
    for k, v in (("LCSC", p.lcsc), ("MPN", p.mpn)):
        f.SetProperty(k, v)
    b.Add(f)
    for pad in f.Pads():
        pad.SetNet(net(p.pins[pad.GetNumber()]))
    new[r] = f
    fps[r] = f
pcbnew.SaveBoard(dst, b)
print("added", list(new))
