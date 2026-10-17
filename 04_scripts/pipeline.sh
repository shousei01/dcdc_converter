#!/bin/bash
set -e
cd /home/claude/dcdc
P=pcb3; mkdir -p $P; cp pcb2/render.py $P/
python3 gen_pcb2.py $P/base.kicad_pcb
python3 fanout.py $P/base.kicad_pcb $P/fanout.kicad_pcb
python3 - <<'PY'
import route, pcbnew, subprocess
P="pcb3"
def fr(src, dsn, ses, passes, classes):
    b=pcbnew.LoadBoard(src); pcbnew.ExportSpecctraDSN(b,dsn)
    t=open(dsn).read()
    t=route.edit_dsn(t) if classes else t.replace('(width 200)\n        (clearance 200.1)','(width 250)\n        (clearance 200)',1)
    open(dsn,'w').write(t)
    r=subprocess.run(['xvfb-run','-a','java','-jar','/home/claude/tools/freerouting.jar','-de',dsn,'-do',ses,'-mp',str(passes),'-mt','4'],capture_output=True,text=True,timeout=3600)
    open(ses+'.log','w').write(r.stdout+r.stderr)
fr(f"{P}/fanout.kicad_pcb", f"{P}/b1.dsn", f"{P}/b1.ses", 40, True)
PY
python3 ses_import.py $P/base.kicad_pcb $P/b1.ses $P/r1.kicad_pcb
python3 - <<'PY'
import route, pcbnew, subprocess
P="pcb3"
b=pcbnew.LoadBoard(f"{P}/r1.kicad_pcb"); pcbnew.ExportSpecctraDSN(b,f"{P}/b2.dsn")
t=open(f"{P}/b2.dsn").read().replace('(width 200)\n        (clearance 200.1)','(width 250)\n        (clearance 200)',1)
open(f"{P}/b2.dsn",'w').write(t)
r=subprocess.run(['xvfb-run','-a','java','-jar','/home/claude/tools/freerouting.jar','-de',f"{P}/b2.dsn",'-do',f"{P}/b2.ses",'-mp','60','-mt','4'],capture_output=True,text=True,timeout=3600)
open(f"{P}/b2.ses.log",'w').write(r.stdout+r.stderr)
PY
python3 ses_import.py $P/base.kicad_pcb $P/b2.ses $P/r2.kicad_pcb
timeout 2400 python3 fix_unconnected.py $P/r2.kicad_pcb $P/r3.kicad_pcb
echo PIPELINE_DONE
