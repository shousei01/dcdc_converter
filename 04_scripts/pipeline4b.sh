#!/bin/bash
set -e
cd /home/claude/dcdc
P=pcb4
python3 - <<'PY'
import route, pcbnew, subprocess
P = "pcb4"
b = pcbnew.LoadBoard(f"{P}/r1.kicad_pcb"); pcbnew.ExportSpecctraDSN(b, f"{P}/b2.dsn")
t = route.edit_dsn(open(f"{P}/b2.dsn").read())
open(f"{P}/b2.dsn", "w").write(t)
r = subprocess.run(['xvfb-run', '-a', 'java', '-jar', '/home/claude/tools/freerouting.jar', '-de', f"{P}/b2.dsn", '-do', f"{P}/b2.ses",
                    '-mp', '80', '-mt', '4'], capture_output=True, text=True, timeout=3600)
open(f"{P}/b2.ses.log", "w").write(r.stdout + r.stderr)
PY
python3 ses_import.py $P/pre.kicad_pcb $P/b2.ses $P/r2.kicad_pcb
echo STAGE2_DONE
