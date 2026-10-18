DCDC converter - LLC (isolated) + 4-switch buck-boost, STM32G474RBT6          Rev D (2026-10-18)
12-48 V in, 1.5-48 V / 5 A / 50 W out, basic isolation, isolated CAN

01_hardware
  kicad_project\   KiCad 6/7 project (9-sheet wired schematic + routed 4-layer PCB). Open in KiCad, or import
                   into EasyEDA Pro (File > Import > KiCad) - same files as easyeda\*.zip
  easyeda\         DCDC_LLC_4SBB_G474_EasyEDA_import.zip
  docs\            DCDC_Design_Notes.docx / .pdf (design notes: sizing, full scales, firmware notes, review),
                   schematic PDF, PCB layer PDF, DRC report, pin-map.xlsx (every MCU pin + all AFs + what we use),
                   T1_PQ2620_winding_guide.html (hand-winding guide, 2D/3D, dots), layout_review_layers.png
  fabrication\     JLCPCB Gerber/drill zip, CPL (pick & place), JLCPCB BOM;
                   DCDC_JLC_BOM.csv / DCDC_JLC_CPL.csv = assembly upload files (LCSC numbers checked
                   18 Oct; U1, T1, connectors, headers and SW1 are hand-soldered and left out)
  bom\             grouped BOM with prices / sources
02_firmware        firmware workspace + README (pin map, clocks, ADC full scales, VIN monitor, OVP, start-up)
03_calculations    loss / LLC sizing scripts; aux_fuse_check.py checks L2/L3 and F1 (Rev D order prep)
04_scripts         generator, routing and clean-up scripts that build this release

Rev D changes
  - NTC moved PA4 -> PA6 (ADC2_IN3); PA4 kept free for DAC1_OUT1
  - 10k pull-down to GND on every unused MCU pin (R90-R105; R93 is now the PA2 / VIN_PWM pull-down)
  - HSE crystal 16 MHz (Y1 + 12 pF C0G)
  - ADC / DAC / comparator reference: external REF3030 (U19, 3.000 V +/-0.2 %) on VREF+, no longer the
    isolator's 3.3 V rail. Full scales: VBUS / VOUT 61.8 V, IL +/-18.75 A, IOUT 6.0 A (see design notes)
  - Primary input OVP: TL431 + LMV331, trips 50.26 V rising / 49.83 V falling, through U12 isolator
    channel 1 -> PA15 (HRTIM1_FLT2)
  - Isolated VIN monitor: primary ramp (~200 Hz) + comparator PWM through U12 channel 2 -> PA2 (TIM15_CH1);
    divider R81/R82 0.1 %. Monitoring only, about +/-0.5 % after a two-point calibration
  - Test pads TP1-TP15 on rails / filtered signals only (no switch nodes)
  - T1 footprint fits the vendor PQ2620 and PQ2625 6+6 bobbins: 3.8 mm pitch inside each 3-pin group,
    7.5 mm between pins 3 and 4, 25.4 mm row-to-row, 1.2 mm holes
  - JP1 is a 2x2 header that switches both legs of the CAN split termination
  - Silkscreen: VIN+/-, VOUT+/-, CAN_H / CAN_L / CAN_GND, JP1 shunt boxes, J7 notch + pin 1, DIP A0-A5 / ON=1
  - F1 now a 1206 7 A 63 V chip fuse (Littelfuse 0458007.DR; 2nd source Schurter 3413.0326.11);
    L2 / L3 now 5040 shielded 47 uH (Sunlord SWPA5040S470MT; 2nd source Bourns SRN5040-470M,
    Taiyo Yuden NRS5040T470MMGK). EN_AUX re-routed, VIN track centred between the L3 pads.
    Every part carries a JLCPCB-checked LCSC number (design.py JLC_LCSC) in the BOMs, schematic and PCB
  - Layout review (18 Oct): smaller switch-node pours, tighter gate loops, Kelvin taps, output pour,
    straightened routing, 5 mm ground stitching
  - JLCPCB compliance (4-layer, 2 oz outer): PTH pad-to-track >= 0.28 mm, inner hole-to-copper >= 0.3 mm,
    silkscreen text >= 1.0 mm / 0.15 mm stroke; limits kept as custom DRC rules in kicad_project\*.kicad_dru
PCB status: 160 x 105 mm, 4 layers, 257 footprints, 0 DRC errors / warnings with the JLC rules loaded,
0 unconnected, primary-secondary copper gap 4.0 mm on every layer.
Order: 4 layers, 1.6 mm, 2 oz outer copper, JLC04161H-7628 stack-up; upload fabrication\*_gerbers_JLCPCB.zip.
