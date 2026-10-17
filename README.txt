DCDC converter - isolated LLC + 4-switch buck-boost, STM32G474RBT6        Rev C, 2026-10-17
12-48 V in -> 1.5-48 V / 5 A / 50 W out, 3 kVrms basic isolation, isolated CAN.

01_hardware\
  kicad_project\   KiCad project (9-sheet schematic + routed 4-layer PCB, 160 x 105 mm)
  easyeda\         DCDC_LLC_4SBB_G474_EasyEDA_import.zip -> EasyEDA Pro start page > Import > KiCad
  docs\            schematic PDF, PCB layer PDF, DRC report
  fabrication\     JLCPCB gerbers + drill (zip), pick-and-place (CPL), JLCPCB-format BOM
  bom\             full BOM with LCSC numbers, prices and notes
02_firmware\       (empty) firmware workspace: src\, inc\, docs\ - see 02_firmware\README.txt
03_calculations\   llc_calc.py (LLC sizing/losses), stage_calc2.py (4SBB losses) + results
04_scripts\        generators; design.py is the single source of truth for parts and nets
                   (gen_sch2.py schematic, gen_pcb2.py placement, pipeline.sh routing, gen_bom.py BOM)

Design notes: https://claude.ai/code/artifact/fa1d7180-cbef-41fb-9ea4-80f75c741fb5
Before ordering: check the PQ2620 transformer footprint against the bobbin drawing; tighten the
autorouted power loops (J1 input path, 4SBB switch nodes) by hand if EMI/efficiency matter.
