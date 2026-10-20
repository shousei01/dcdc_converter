"""Rev E reference designators for JLC: 1.0 mm text, 0.15 mm stroke. Each reference is placed at the first free spot
around its own part (above / below / left / right, horizontal then vertical, stepping outwards), clear of pads
(solder-mask openings), other silkscreen (footprint outlines and references already placed), holes and the board
edge. Parts with no free spot keep the reference hidden (it stays on the fab layer / assembly drawing).
usage: silk_sub.py in.kicad_pcb out.kicad_pcb REF,REF,...  (only these references are re-placed; all other text is an obstacle)"""
import sys
import pcbnew
from shapely.geometry import box, LineString, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree

M, mm = pcbnew.ToMM, pcbnew.FromMM
H, TH = 1.0, 0.15
W_BRD, H_BRD = 160.0, 105.0


def text_box(cx, cy, n, vert):
    w = n * 0.82 * H + 0.1
    h = H + 0.2
    if vert:
        w, h = h, w
    return box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def main(src, dst, only):
    b = pcbnew.LoadBoard(src)
    obst = []
    for f in b.GetFootprints():
        for p in f.Pads():
            bb = p.GetBoundingBox()
            obst.append(box(M(bb.GetX()), M(bb.GetY()), M(bb.GetRight()), M(bb.GetBottom())).buffer(0.12))
        for g in f.GraphicalItems():
            if g.GetLayer() == pcbnew.F_SilkS and g.GetClass() not in ("PCB_TEXT", "FP_TEXT") and hasattr(g, "GetStart"):
                try:
                    s, e = g.GetStart(), g.GetEnd()
                    if g.GetShape() == pcbnew.SHAPE_T_SEGMENT:
                        obst.append(LineString([(M(s.x), M(s.y)), (M(e.x), M(e.y))]).buffer(0.2))
                    else:
                        bb = g.GetBoundingBox()
                        obst.append(box(M(bb.GetX()), M(bb.GetY()), M(bb.GetRight()), M(bb.GetBottom())).boundary.buffer(0.2))
                except Exception:
                    pass
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.F_SilkS:
            bb = d.GetBoundingBox()
            obst.append(box(M(bb.GetX()), M(bb.GetY()), M(bb.GetRight()), M(bb.GetBottom())).buffer(0.15))
    edge = box(0.6, 0.6, W_BRD - 0.6, H_BRD - 0.6)
    placed = []
    for f in b.GetFootprints():
        if f.GetReference() in only: continue
        for t in [f.Reference(), f.Value()] + [g for g in f.GraphicalItems() if g.GetClass() in ("PCB_TEXT", "FP_TEXT")]:
            if t.GetLayer() == pcbnew.F_SilkS and t.IsVisible():
                rb = t.GetBoundingBox(); placed.append(box(M(rb.GetX()), M(rb.GetY()), M(rb.GetRight()), M(rb.GetBottom())))
    shown = hidden = 0
    fps = sorted(b.GetFootprints(), key=lambda f: (M(f.GetPosition().y), M(f.GetPosition().x)))
    for f in fps:
        t = f.Reference()
        if t.GetLayer() != pcbnew.F_SilkS or f.GetReference() not in only:
            continue
        ref = f.GetReference()
        t.SetTextSize(pcbnew.VECTOR2I(mm(H), mm(H)))
        t.SetTextThickness(mm(TH))
        t.SetKeepUpright(True)
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        cy_ = f.GetCourtyard(pcbnew.F_CrtYd)
        if cy_.OutlineCount():
            bb = cy_.BBox()
            x0, y0, x1, y1 = M(bb.GetX()), M(bb.GetY()), M(bb.GetRight()), M(bb.GetBottom())
        else:
            bb = f.GetBoundingBox(False, False)
            x0, y0, x1, y1 = M(bb.GetX()), M(bb.GetY()), M(bb.GetRight()), M(bb.GetBottom())
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        n = len(ref)
        tw = n * 0.82 * H + 0.1
        cands = [(cx, cy, False), (cx, cy, True)] if (x1 - x0) * (y1 - y0) > 30 else []    # on the body of big parts
        for gap in (0.0, 0.4, 0.9, 1.5, 2.2, 3.0):
            for vert in (False, True):
                hw = (tw if not vert else H + 0.2) / 2
                hh = (H + 0.2 if not vert else tw) / 2
                cands += [(cx, y0 - gap - hh, vert), (cx, y1 + gap + hh, vert),
                          (x0 - gap - hw, cy, vert), (x1 + gap + hw, cy, vert),
                          (x0 + hw, y0 - gap - hh, vert), (x1 - hw, y0 - gap - hh, vert),
                          (x0 + hw, y1 + gap + hh, vert), (x1 - hw, y1 + gap + hh, vert)]
        tree = STRtree(obst + placed)
        allg = obst + placed
        ok = None
        for px, py, vert in cands:
            t.SetTextAngle(pcbnew.EDA_ANGLE(90.0 if vert else 0.0, pcbnew.DEGREES_T))
            t.SetPosition(pcbnew.VECTOR2I(mm(px), mm(py)))
            rb = t.GetBoundingBox()
            tb = box(M(rb.GetX()), M(rb.GetY()), M(rb.GetRight()), M(rb.GetBottom())).buffer(0.1, join_style=2)
            if not edge.contains(tb):
                continue
            if any(allg[i].intersects(tb) for i in tree.query(tb)):
                continue
            ok = (px, py, vert, tb)
            break
        if ok is None:
            t.SetVisible(False)
            hidden += 1
            continue
        px, py, vert, tb = ok
        t.SetVisible(True)
        t.SetTextAngle(pcbnew.EDA_ANGLE(90.0 if vert else 0.0, pcbnew.DEGREES_T))
        t.SetPosition(pcbnew.VECTOR2I(mm(px), mm(py)))
        placed.append(tb)
        shown += 1
    pcbnew.SaveBoard(dst, b)
    print("references shown", shown, "hidden", hidden)
    print("hidden:", " ".join(sorted(f.GetReference() for f in b.GetFootprints() if not f.Reference().IsVisible())))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], set(sys.argv[3].split(",")))
