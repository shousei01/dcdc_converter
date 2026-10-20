#!/bin/bash
# Rev E2 board: Rev E layout + series resistors R123-R129 + courtyard / silk DRC fixes. pcb5/..._revE_preE2.kicad_pcb = the Rev E board of commit 7058945.
set -e
python3 pcb6/e2_edit.py pcb5/DCDC_LLC_4SBB_G474_revE_preE2.kicad_pcb pcb6/s1.kicad_pcb   # Rev E board: schematic paths, J6/J7 nets, new R footprints
python3 pcb6/legal.py pcb6/s1.kicad_pcb pcb6/s2.kicad_pcb      # courtyard legalisation (small moves, also writes pcb6/s2_moves.json)
python3 pcb6/insert2.py pcb6/s2.kicad_pcb pcb6/t2.kicad_pcb   # resistors put into the existing debug / +3V3 traces
python3 pcb6/fix_moves.py pcb6/t2.kicad_pcb pcb6/t3.kicad_pcb # re-attach copper of the moved parts, FPIDs
python3 pcb6/silk_sub.py pcb6/t3.kicad_pcb pcb6/t4.kicad_pcb R123,R124,R125,R126,R127,R128,R129,R114
python3 pcb6/post.py pcb6/t4.kicad_pcb pcb5/DCDC_LLC_4SBB_G474_revE_preE2.kicad_pcb pcb6/t6.kicad_pcb   # lock state of Rev E
python3 pcb6/finish_e2.py pcb6/t6.kicad_pcb pcb6/final_E2.kicad_pcb
python3 pcb6/fix_j3.py pcb6/final_E2.kicad_pcb pcb6/final_E2b.kicad_pcb   # J3 pin 3 In2 thermal spokes
python3 pcb6/fix_vip.py pcb6/final_E2b.kicad_pcb pcb6/final_E2c.kicad_pcb   # via holes out of SMD pads
python3 pcb6/drc.py pcb6/final_E2c.kicad_pcb              # expect {} and unconnected: 0
