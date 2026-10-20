"""print pad boxes (net, x0,y0,x1,y1) for refs or region: pads.py board x0 y0 x1 y1"""
import sys, pcbnew
MM=pcbnew.ToMM
b=pcbnew.LoadBoard(sys.argv[1]); X0,Y0,X1,Y1=[float(v) for v in sys.argv[2:6]]
rows=[]
for f in b.GetFootprints():
    for p in f.Pads():
        bb=p.GetBoundingBox(); x0,y0,x1,y1=MM(bb.GetX()),MM(bb.GetY()),MM(bb.GetRight()),MM(bb.GetBottom())
        if x1<X0 or x0>X1 or y1<Y0 or y0>Y1: continue
        rows.append((f.GetReference(),p.GetNumber(),p.GetNetname(),round((x0+x1)/2,2),round((y0+y1)/2,2),round(x0,2),round(y0,2),round(x1,2),round(y1,2),'T' if p.GetAttribute()==pcbnew.PAD_ATTRIB_PTH else ''))
rows.sort()
for r in rows: print(*r)
