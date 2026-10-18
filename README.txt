DCDC converter - LLC (isolated) + 4-switch buck-boost, STM32G474RBT6          Rev D (2026-10-18)
12-48 V in, 1.5-48 V / 5 A / 50 W out, basic isolation, isolated CAN

01_hardware
  kicad_project\   KiCad 6/7 project (9-sheet wired schematic + routed 4-layer PCB). Open in KiCad, or import
                   into EasyEDA Pro (File > Import > KiCad) - same files as easyeda\*.zip
  easyeda\         DCDC_LLC_4SBB_G474_EasyEDA_import.zip
  docs\            schematic PDF, PCB layer PDF, DRC report, pin-map.xlsx (every MCU pin + all AFs + what we use)
  fabrication\     JLCPCB Gerber/drill zip, CPL (pick & place), JLCPCB BOM
  bom\             grouped BOM with prices / sources
02_firmware        firmware workspace + README (pin map, clocks, start-up, OVP)
03_calculations    loss / LLC sizing scripts (unchanged in Rev D)
04_scripts         generator and routing scripts that build this release

Rev D changes
  - NTC moved PA4 -> PA6 (ADC2_IN3); PA4 kept free for DAC1_OUT1
  - 10k pull-down to GND on every unused MCU pin (R90-R105)
  - HSE crystal 16 MHz (Y1 + 12 pF C0G)
  - Primary input OVP: TL431 + LMV331, trip 50.2 V, through the spare U12 isolator channel -> PA15 (HRTIM1_FLT2)
  - Test pads TP1-TP15 on rails / filtered signals only (no switch nodes)
  - PQ2620 footprint: 3.8 mm pitch inside each 3-pin group, 7.5 mm between pins 3 and 4
    (row-to-row spacing is still a 22.5 mm placeholder - confirm with your bobbin)
  - Schematic text overlaps removed; PCB re-placed for tight power loops, re-routed, silkscreen cleaned
PCB status: 160 x 105 mm, 4 layers, 0 DRC errors, 0 unconnected, 0 silkscreen warnings
(199 "footprint differs from library" notices only appear because the KiCad libraries were not installed where DRC ran).
