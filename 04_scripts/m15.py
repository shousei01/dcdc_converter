import sys, pcbnew
sys.path.insert(0, "/home/claude/dcdc")
import maze
maze.TW = 0.15
pri = sys.argv[3].split(",") if len(sys.argv) > 3 else []
_d = maze.drc
def drc2(b):
    bad, unc = _d(b)
    unc.sort(key=lambda u: pri.index(u[2]) if u[2] in pri else 99)
    return bad, unc
maze.drc = drc2
maze.run(sys.argv[1], sys.argv[2])
