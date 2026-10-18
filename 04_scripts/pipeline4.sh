#!/bin/bash
# Rev D PCB flow: placement -> power pre-route -> fan-out -> Freerouting (2 runs) -> SES import -> fixers
set -e
cd /home/claude/dcdc
P=pcb4; mkdir -p $P
python3 gen_pcb3.py $P/base.kicad_pcb | tail -1
python3 preroute.py $P/base.kicad_pcb $P/pre.kicad_pcb | tail -1
python3 fanout3.py $P/pre.kicad_pcb $P/fanout.kicad_pcb | tail -1
python3 - <<'PY'
import route, pcbnew, subprocess
P = "pcb4"
b = pcbnew.LoadBoard(f"{P}/fanout.kicad_pcb"); pcbnew.ExportSpecctraDSN(b, f"{P}/b1.dsn")
t = route.edit_dsn(open(f"{P}/b1.dsn").read())
open(f"{P}/b1.dsn", "w").write(t)
r = subprocess.run(['xvfb-run', '-a', 'java', '-jar', '/home/claude/tools/freerouting.jar', '-de', f"{P}/b1.dsn", '-do', f"{P}/b1.ses",
                    '-mp', '40', '-mt', '4'], capture_output=True, text=True, timeout=3600)
open(f"{P}/b1.ses.log", "w").write(r.stdout + r.stderr)
PY
python3 ses_import.py $P/pre.kicad_pcb $P/b1.ses $P/r1.kicad_pcb
echo PIPELINE_STAGE1_DONE
