"""remove tracks reported as dangling by DRC (repeat until none). usage: dangling.py in out"""
import sys, re, pcbnew
sys.path.insert(0, '/home/claude/dcdc'); from fix_unconnected import drc
mm, M = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
for rnd in range(1):
    drc(b, '/tmp/claude-0/dg.rpt'); t = open('/tmp/claude-0/dg.rpt').read()
    hits = re.findall(r"\[track_dangling\][^\n]*\n[^\n]*\n\s*@\(([\d.]+) mm, ([\d.]+) mm\): Track \[([^\]]+)\] on (\S+), length ([\d.]+) mm", t)
    if not hits: break
    kill = []
    for x, y, net, L, ln in hits:
        for tr in b.GetTracks():
            if tr.Type() == pcbnew.PCB_VIA_T or tr.GetNetname() != net or b.GetLayerName(tr.GetLayer()) != L: continue
            if abs(M(tr.GetLength()) - float(ln)) < 0.002 and any(abs(M(v.x) - float(x)) < 0.01 and abs(M(v.y) - float(y)) < 0.01 for v in (tr.GetStart(), tr.GetEnd())):
                kill.append(tr)
    print('round', rnd, 'remove', len(kill))
    for tr in kill: b.Remove(tr)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)
