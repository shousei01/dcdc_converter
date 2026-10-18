"""Remove dangling tracks/vias one at a time, keeping a removal only if the unconnected count does not change.
Usage: safe_clean.py in out   (spawns one process per candidate: pcbnew cannot reload boards reliably)"""
import json, re, subprocess, sys, shutil
src, dst = sys.argv[1], sys.argv[2]
shutil.copy(src, "/tmp/sc_cur.kicad_pcb")
WORK = r'''
import sys, re, json, pcbnew
sys.path.insert(0, "/home/claude/dcdc")
from fix_unconnected import drc
MM = pcbnew.ToMM
b = pcbnew.LoadBoard("/tmp/sc_cur.kicad_pcb"); f = pcbnew.ZONE_FILLER(b); f.Fill(b.Zones())
bad, unc = drc(b)
t = open("/tmp/fix_drc.rpt").read()
pts = [(float(x), float(y), k) for k, x, y in re.findall(r"\[(track_dangling|via_dangling)\][^\n]*\n[^\n]*\n\s*@\(([\d.]+) mm, ([\d.]+) mm\)", t)]
idx = int(sys.argv[1])
if idx >= len(pts):
    print(json.dumps({"done": True, "unc": len(unc), "bad": bad})); sys.exit()
x, y, k = pts[idx]
victim = None
for it in b.GetTracks():
    if it.IsLocked():
        continue
    if k == "via_dangling" and it.Type() == pcbnew.PCB_VIA_T and abs(MM(it.GetPosition().x) - x) < 0.01 and abs(MM(it.GetPosition().y) - y) < 0.01:
        victim = it; break
    if k == "track_dangling" and it.Type() == pcbnew.PCB_TRACE_T and any(abs(MM(p.x) - x) < 0.01 and abs(MM(p.y) - y) < 0.01 for p in (it.GetStart(), it.GetEnd())):
        victim = it; break
if victim is None:
    print(json.dumps({"skip": True, "unc": len(unc), "bad": bad})); sys.exit()
b.Remove(victim); f.Fill(b.Zones())
bad2, unc2 = drc(b)
if len(unc2) <= len(unc) and bad2 <= bad:
    pcbnew.SaveBoard("/tmp/sc_cur.kicad_pcb", b)
    print(json.dumps({"removed": True, "unc": len(unc2), "bad": bad2}))
else:
    print(json.dumps({"kept": True, "unc": len(unc2), "bad": bad2}))
'''
open("/tmp/sc_work.py", "w").write(WORK)
i = 0
while i < 200:
    out = subprocess.run([sys.executable, "/tmp/sc_work.py", str(i)], capture_output=True, text=True).stdout.strip().splitlines()
    r = json.loads(out[-1]) if out else {"done": True}
    print(i, r)
    if r.get("done"):
        break
    if not r.get("removed"):
        i += 1
shutil.copy("/tmp/sc_cur.kicad_pcb", dst)
