"""Placement / routing review plot: pads (colour by net class), courtyards, refs, tracks per layer, keep-outs.
usage: plotplace.py board.kicad_pcb out.png x0 y0 x1 y1 [px_per_mm] [layers: F,1,2,B]"""
import sys
import pcbnew
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle

MM = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
out = sys.argv[2]
x0, y0, x1, y1 = [float(v) for v in sys.argv[3:7]]
ppm = float(sys.argv[7]) if len(sys.argv) > 7 else 12
show = sys.argv[8] if len(sys.argv) > 8 else "F12B"
fig = plt.figure(figsize=((x1 - x0) * ppm / 100, (y1 - y0) * ppm / 100), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(x0, x1)
ax.set_ylim(y1, y0)
ax.set_aspect("equal")
ax.axis("off")
ax.add_patch(Rectangle((0, 0), 160, 105, fill=True, fc="#10241a", ec="yellow", lw=1))
LCOL = {pcbnew.F_Cu: ("F", "#d23c3c"), pcbnew.In1_Cu: ("1", "#c8a000"), pcbnew.In2_Cu: ("2", "#3cb4c8"), pcbnew.B_Cu: ("B", "#4060ff")}
NCOL = {"VIN": "#ff3030", "VIN_RAW": "#ff8080", "GNDP": "#20a040", "GND": "#207030", "GND_ISO": "#60c0a0", "HB_SW": "#ff9900",
        "CR_MID": "#b060ff", "VBUS": "#ff60c0", "SW1": "#ffbb00", "SW2": "#ffbb00", "PGND": "#00c0c0", "VOUT": "#e000e0",
        "VOUT_N": "#8080ff", "SR_D1": "#ff9900", "SR_D2": "#ff9900", "FLY_DRN": "#ff9900", "FLY_SA": "#ff9900", "+10V": "#ff6060"}
# zones (filled)
for z in b.Zones():
    if z.GetIsRuleArea():
        bb = z.GetBoundingBox()
        ax.add_patch(Rectangle((MM(bb.GetX()), MM(bb.GetY())), MM(bb.GetWidth()), MM(bb.GetHeight()), fill=False, ec="#ffffff", lw=0.6, ls="--"))
        continue
    for lid in z.GetLayerSet().Seq():
        if lid not in LCOL or LCOL[lid][0] not in show:
            continue
        fp = z.GetFilledPolysList(lid)
        for i in range(fp.OutlineCount()):
            o = fp.Outline(i)
            pts = [(MM(o.CPoint(k).x), MM(o.CPoint(k).y)) for k in range(o.PointCount())]
            if len(pts) > 2:
                ax.add_patch(Polygon(pts, closed=True, fc=NCOL.get(z.GetNetname(), LCOL[lid][1]), ec="none", alpha=0.45 if lid in (pcbnew.F_Cu, pcbnew.B_Cu) else 0.25))
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        ax.add_patch(Circle((MM(p.x), MM(p.y)), MM(t.GetWidth()) / 2, fc="#dddddd", ec="k", lw=0.2))
        continue
    lid = t.GetLayer()
    if lid not in LCOL or LCOL[lid][0] not in show:
        continue
    s, e = t.GetStart(), t.GetEnd()
    ax.plot([MM(s.x), MM(e.x)], [MM(s.y), MM(e.y)], color=LCOL[lid][1], lw=MM(t.GetWidth()) * ppm * 0.72, solid_capstyle="round", alpha=0.9)
for f in b.GetFootprints():
    f.BuildCourtyardCaches()
    c = f.GetCourtyard(pcbnew.F_CrtYd).BBox()
    if c.GetWidth() > 0:
        ax.add_patch(Rectangle((MM(c.GetX()), MM(c.GetY())), MM(c.GetWidth()), MM(c.GetHeight()), fill=False, ec="#ff66ff", lw=0.5))
    for pad in f.Pads():
        bb = pad.GetBoundingBox()
        n = pad.GetNetname()
        col = "#e0e0e0" if not n else ("#ff4040" if n in ("VIN", "VIN_RAW", "VBUS", "VOUT", "+10V", "+10V_P", "+5V", "+5V_P", "+3V3", "+3V3A") else
                                         "#40c040" if n in ("GND", "GNDP", "PGND", "GND_ISO") else "#f0c040")
        ax.add_patch(Rectangle((MM(bb.GetX()), MM(bb.GetY())), MM(bb.GetWidth()), MM(bb.GetHeight()), fc=col, ec="none", alpha=0.85))
        if ppm >= 25 and n:
            c = pad.GetPosition()
            ax.text(MM(c.x), MM(c.y), n.replace("Net-", "")[:9], color="black", fontsize=ppm * 0.11, ha="center", va="center", rotation=0)
    p = f.GetPosition()
    ax.text(MM(p.x), MM(p.y) + (0 if ppm < 25 else 0.9), f.GetReference(), color="white", fontsize=max(4, min(ppm * 0.45, 11)), ha="center", va="center", weight="bold")
for x in range(int(x0) // 10 * 10, int(x1) + 1, 10):
    ax.axvline(x, color="#304040", lw=0.3)
    ax.text(x, y0 + 0.8, str(x), color="#80a0a0", fontsize=6)
for y in range(int(y0) // 10 * 10, int(y1) + 1, 10):
    ax.axhline(y, color="#304040", lw=0.3)
    ax.text(x0 + 0.3, y, str(y), color="#80a0a0", fontsize=6)
fig.savefig(out)
