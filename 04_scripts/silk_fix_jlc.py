"""JLCPCB variant: 1.0 mm references, 0.15 mm stroke; board texts are obstacles.\nSilkscreen clean-up (no electrical change).
- Reference designators: 0.8 mm text, moved to the first free spot around the part (no overlap with any pad,
  other silk or other references, inside the board). Parts with no free spot keep their reference on F.Fab only.
- Footprint silk outline segments that run over another part's pads or into another part's courtyard are removed.
- Value texts stay on F.Fab (assembly drawing).
Usage: silk_fix.py in.kicad_pcb out.kicad_pcb"""
import sys
import pcbnew

mm, MM = pcbnew.FromMM, pcbnew.ToMM
TXT = 1.0
GAP = 0.25


def bbox(item):
    b = item.GetBoundingBox()
    return (MM(b.GetX()), MM(b.GetY()), MM(b.GetRight()), MM(b.GetBottom()))


def inter(a, b, g=0.0):
    return a[0] < b[2] + g and a[2] > b[0] - g and a[1] < b[3] + g and a[3] > b[1] - g


def main(src, dst):
    b = pcbnew.LoadBoard(src)
    W = MM(b.GetBoardEdgesBoundingBox().GetWidth()); H = MM(b.GetBoardEdgesBoundingBox().GetHeight())
    pads, cyards = [], {}
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            if pd.IsOnLayer(pcbnew.F_Cu) or pd.IsOnLayer(pcbnew.F_Mask):
                x0, y0, x1, y1 = bbox(pd)
                pads.append(((x0 - 0.1, y0 - 0.1, x1 + 0.1, y1 + 0.1), fp.GetReference()))
        cy = fp.GetCourtyard(pcbnew.F_CrtYd)
        if cy.OutlineCount():
            bb = cy.BBox()
            cyards[fp.GetReference()] = (MM(bb.GetX()), MM(bb.GetY()), MM(bb.GetRight()), MM(bb.GetBottom()))
        else:
            cyards[fp.GetReference()] = bbox(fp)
    # 1) trim silk outline segments that hit other parts' pads
    removed = 0
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        for it in list(fp.GraphicalItems()):
            if it.GetLayer() != pcbnew.F_SilkS or not isinstance(it, pcbnew.FP_SHAPE):
                continue
            bx = bbox(it)
            hit = any(r != ref and inter(bx, p, 0.15) for p, r in pads)
            hit = hit or any(r != ref and r[0] != "H" and inter(bx, c, -0.2) for r, c in cyards.items())
            if hit:
                fp.Remove(it)
                removed += 1
    # silk obstacles that remain (graphics only)
    silk = []

    def edges(pts, w):
        out = []
        for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
            out.append((min(x1, x2) - w, min(y1, y2) - w, max(x1, x2) + w, max(y1, y2) + w))
        return out

    for fp in b.GetFootprints():
        for it in fp.GraphicalItems():
            if it.GetLayer() == pcbnew.F_SilkS and isinstance(it, pcbnew.FP_SHAPE):
                w = MM(it.GetWidth()) / 2
                if it.GetShape() == pcbnew.SHAPE_T_RECT:
                    x0, y0, x1, y1 = bbox(it)
                    for e in edges([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], w):
                        silk.append((e, fp.GetReference()))
                elif it.GetShape() == pcbnew.SHAPE_T_POLY:
                    ps = it.GetPolyShape()
                    if ps.OutlineCount():
                        o = ps.Outline(0)
                        pts = [(MM(o.CPoint(i).x), MM(o.CPoint(i).y)) for i in range(o.PointCount())]
                        for e in edges(pts, w):
                            silk.append((e, fp.GetReference()))
                else:
                    silk.append((bbox(it), fp.GetReference()))
    # board-level silkscreen (texts, lines) and footprint user texts are obstacles too
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.F_SilkS:
            silk.append((bbox(d), "board"))
    for fp in b.GetFootprints():
        for it in fp.GraphicalItems():
            if it.GetLayer() == pcbnew.F_SilkS and it.GetClass() == "FP_TEXT" and it.IsVisible():
                silk.append((bbox(it), fp.GetReference()))
    # 2) references
    placed, hidden = [], []
    fps = sorted(b.GetFootprints(), key=lambda f: -(bbox(f)[2] - bbox(f)[0]) * (bbox(f)[3] - bbox(f)[1]))
    for fp in fps:
        ref = fp.GetReference()
        t = fp.Reference()
        if t.GetLayer() != pcbnew.F_SilkS:
            continue
        t.SetTextSize(pcbnew.VECTOR2I(mm(TXT), mm(TXT)))
        t.SetTextThickness(mm(0.15))
        cx0, cy0, cx1, cy1 = cyards[ref]
        cx, cy = (cx0 + cx1) / 2, (cy0 + cy1) / 2
        n = len(ref)
        tw, th = n * TXT * 0.8 + 0.2, TXT + 0.2
        cands = []
        for ang in (0, 90):
            w2, h2 = ((tw, th) if ang == 0 else (th, tw))
            cands += [(cx, cy0 - GAP - h2 / 2, ang), (cx, cy1 + GAP + h2 / 2, ang), (cx0 - GAP - w2 / 2, cy, ang), (cx1 + GAP + w2 / 2, cy, ang)]
            for dx in (-1.5, 1.5, -3, 3):
                cands += [(cx + dx, cy0 - GAP - h2 / 2, ang), (cx + dx, cy1 + GAP + h2 / 2, ang)]
            for dy in (-1.5, 1.5, -3, 3):
                cands += [(cx0 - GAP - w2 / 2, cy + dy, ang), (cx1 + GAP + w2 / 2, cy + dy, ang)]
            # inside the body (big parts: inductors, connectors, ICs)
            if (cx1 - cx0) > tw + 1 and (cy1 - cy0) > th + 1:
                cands.append((cx, cy, ang))
        ok = None
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        t.SetKeepUpright(True)
        for (x, y, ang) in cands:
            t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            t.SetTextAngle(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
            bx = bbox(t)
            if bx[0] < 0.4 or bx[1] < 0.4 or bx[2] > W - 0.4 or bx[3] > H - 0.4:
                continue
            if any(inter(bx, p, 0.15) for p, r in pads):
                continue
            if any(inter(bx, s_, 0.1) for s_, r in silk):
                continue
            if any(inter(bx, q, 0.15) for q in placed):
                continue
            ok = (x, y, ang, bx)
            break
        if ok:
            x, y, ang, bx = ok
            t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            t.SetTextAngle(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
            t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
            t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
            t.SetVisible(True)
            placed.append(bx)
        else:
            t.SetVisible(False)
            hidden.append(ref)
    still = []
    for ref in hidden:
        fp = b.FindFootprintByReference(ref)
        t = fp.Reference()
        cx0, cy0, cx1, cy1 = cyards[ref]
        cx, cy = (cx0 + cx1) / 2, (cy0 + cy1) / 2
        best = None
        for r in [k * 0.4 for k in range(1, 16)]:
            for k in range(24):
                import math
                a = 2 * math.pi * k / 24
                for ang in (0, 90):
                    x = cx + (r + (cx1 - cx0) / 2) * math.cos(a)
                    y = cy + (r + (cy1 - cy0) / 2) * math.sin(a)
                    t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                    t.SetTextAngle(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
                    bx = bbox(t)
                    if bx[0] < 0.4 or bx[1] < 0.4 or bx[2] > W - 0.4 or bx[3] > H - 0.4:
                        continue
                    if any(inter(bx, p, 0.12) for p, r_ in pads) or any(inter(bx, s_, 0.08) for s_, r_ in silk) \
                            or any(inter(bx, q, 0.12) for q in placed):
                        continue
                    best = (x, y, ang, bx)
                    break
                if best:
                    break
            if best:
                break
        if best:
            x, y, ang, bx = best
            t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            t.SetTextAngle(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
            t.SetVisible(True)
            placed.append(bx)
        else:
            t.SetVisible(False)
            still.append(ref)
    hidden = still
    pcbnew.SaveBoard(dst, b)
    print(f"silk segments removed {removed}; references hidden ({len(hidden)}): {' '.join(sorted(hidden))}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
