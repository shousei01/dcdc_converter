"""fill zones + KiCad DRC; summary by type.  usage: drc.py board.kicad_pcb [region x0 y0 x1 y1] [-v]"""
import sys, os, re, collections, subprocess, shutil
src = sys.argv[1]
D = "/tmp/claude-0/drcproj"; R = "/home/claude/dcdc/release_E/DCDC_LLC_4SBB_G474"
shutil.rmtree(D, ignore_errors=True); shutil.copytree(R, D, ignore=shutil.ignore_patterns("*.kicad_sch", "*.kicad_pcb"))
tmp = D + "/DCDC_LLC_4SBB_G474.kicad_pcb"
shutil.copy(src, tmp); shutil.copy("/home/claude/dcdc/pcb5/DCDC_LLC_4SBB_G474.kicad_dru", D + "/DCDC_LLC_4SBB_G474.kicad_dru")
env = dict(os.environ, KICAD7_FOOTPRINT_DIR="/usr/share/kicad/footprints")
code = r'''
import pcbnew,sys
b=pcbnew.LoadBoard(sys.argv[1]); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(sys.argv[1], b)
pcbnew.WriteDRCReport(b, "/tmp/claude-0/drc.rpt", pcbnew.EDA_UNITS_MILLIMETRES, True)
'''
r=subprocess.run(["python3", "-c", code, tmp], env=env, capture_output=True, text=True)
if r.returncode: print(r.stderr[-2000:])
txt = open("/tmp/claude-0/drc.rpt").read()
blocks = re.split(r"\n(?=\[)", txt)
cnt = collections.Counter(); out = []
for bl in blocks:
    m = re.match(r"\[(\w+)\]: (.*)", bl)
    if not m: continue
    sev = re.search(r"; (\w+)\n", bl)
    cnt[(m.group(1), sev.group(1) if sev else "?")] += 1
    out.append(bl.strip())
print(dict(cnt))
m = re.search(r"\*\* Found (\d+) unconnected pads \*\*", txt); print("unconnected:", m.group(1) if m else "?")
if "-v" in sys.argv:
    for o in out: print(o); print("--")
