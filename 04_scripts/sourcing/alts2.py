"""Rev E 2nd / 3rd sources after the spec + footprint check (2026-10-20).
key = primary LCSC # on the JLC BOM -> dict(pkg, alts=[(LCSC, status, note), ...], use)
status: DS  = checked against the datasheet (pinout / land pattern / ratings) and the board netlist + footprint
        EQ  = same part number from another maker, or a passive with identical value / package / dielectric and
              equal-or-better tolerance / voltage / power (fits the same standard land pattern)
        CHK = usable, but one item still to confirm (noted)
        PCB = needs a PCB change (see the 'PCB reserve' sheet)
use = replacement primary when the BOM primary is out of stock / not listed / wrong (same footprint)"""

STD = "Standard"
DEF = "De-facto standard (many makers)"
VEN = "Vendor-specific"

ALTS2 = {
 # ---------------- Rev E2 debug-port series resistors
 "C82290": dict(pkg=STD + " (0402)", alts=[
     ("C5159689", "EQ", "FOJAN FRC0402F47R5TS 47.5 R 1% 0402 62.5 mW"),
     ("C159023", "EQ", "RALEC RTT0247R5FTH 47.5 R 1% 0402 62.5 mW")]),
 "C2933191": dict(pkg=STD + " (0603)", alts=[
     ("C2930558", "EQ", "YAGEO RC0603FR-7W2RL 2 R 1% 0603 200 mW")]),
 # ---------------- capacitors
 "C249664": dict(pkg=STD + " (SMD alu 10x10.5)", alts=[
     ("C46527630", "EQ", "ChengTao RVE1J470M1010: 47 uF 63 V 10x10.5, 105 C"),
     ("C51953411", "CHK", "JIERR 100 uF 63 V 10x10.5: same can, more C -> check F1 inrush")]),
 "C153036": dict(pkg=STD + " (1210)", alts=[
     ("C86054", "EQ", "Murata GRM32ER72A225KA35L 2.2 uF 100 V X7R 1210"),
     ("C92775", "EQ", "Taiyo Yuden HMK325B7225KN-T 2.2 uF 100 V X7R 1210")]),
 "C88219": dict(pkg=STD + " (0603)", alts=[
     ("C113803", "EQ", "Yageo CC0603KRX7R0BB104 100 V X7R"),
     ("C42959888", "EQ", "FH AM03B104K101NT 100 V X7R")]),
 "C14663": dict(pkg=STD + " (0603)", alts=[
     ("C314282", "EQ", "Walsin 0603B104K500CT 50 V X7R"),
     ("C161854", "EQ", "Vishay VJ0603Y104KXACW1BC 50 V X7R")]),
 "C15849": dict(pkg=STD + " (0603)", alts=[
     ("C157684", "EQ", "FH 0603X105K500NT 1 uF 50 V X5R"),
     ("C128624", "EQ", "Yageo CC0603KRX5R9BB105 1 uF 50 V X5R")]),
 "C307331": dict(pkg=STD + " (0402)", alts=[
     ("C131394", "EQ", "Yageo CC0402KRX7R9BB104 50 V X7R"),
     ("C110251", "EQ", "FH 0402B104K500NT 50 V X7R")]),
 "C15850": dict(pkg=STD + " (0805)", alts=[
     ("C18185754", "EQ", "CCTC TCC0805X5R106K350FT 10 uF 35 V X5R"),
     ("C162422", "EQ", "Murata GRM21BR6YA106KE43L 10 uF 35 V X5R")]),
 "C45783": dict(pkg=STD + " (0805)", alts=[
     ("C20416420", "EQ", "CCTC TCC0805X5R226M250FT 22 uF 25 V"),
     ("C129303", "EQ", "FH 0805X226M250NT 22 uF 25 V")]),
 "C52923": dict(pkg=STD + " (0402)", use="C20539426", alts=[
     ("C20539426", "EQ", "CCTC TCC0402X5R105K500AT 1 uF 50 V X5R (new primary)"),
     ("C1518208", "EQ", "Murata GRM155R61H105KE05D 1 uF 50 V X5R")]),
 "C1525": dict(pkg=STD + " (0402)", use="C307331", alts=[
     ("C307331", "EQ", "Samsung CL05B104KB54PNC 50 V X7R - merge into that BOM line (new primary)"),
     ("C131394", "EQ", "Yageo CC0402KRX7R9BB104 50 V X7R")]),
 "C19666": dict(pkg=STD + " (0603)", alts=[
     ("C92758", "EQ", "Taiyo Yuden EMK107ABJ475KA-T 16 V X5R"),
     ("C90057", "EQ", "Murata GRM188R61E475KE11D 25 V X5R")]),
 "C1547": dict(pkg=STD + " (0402)", alts=[
     ("C182477", "EQ", "FH 0402CG120F500NT 12 pF C0G 1 %"),
     ("C49238110", "EQ", "FH AM02CG120J500NT 12 pF C0G")]),
 "C113780": dict(pkg=STD + " (0402)", alts=[
     ("C237166", "EQ", "Walsin 0402N102J500CT 1 nF NP0"),
     ("C427014", "EQ", "Yageo AC0402JRNPO9BN102 1 nF NP0")]),
 "C106259": dict(pkg=STD + " (0402)", alts=[
     ("C295986", "EQ", "Walsin 0402N471J500CT 470 pF NP0"),
     ("C541429", "EQ", "Yageo CC0402GRNPO9BN471 470 pF NP0 2 %")]),
 "C22400107": dict(pkg=STD + " (0402)", alts=[
     ("C3855387", "EQ", "Murata GRM1555C1E103JE01D C0G 25 V (C47 sits on a 3.3 V ADC node)"),
     ("C36911359", "EQ", "HRE CGA0402C0G103J250GT C0G 25 V")]),
 "C53987": dict(pkg=STD + " (0603)", alts=[
     ("C12164", "EQ", "FH 0603B472K101NT 100 V X7R"),
     ("C168956", "EQ", "FH 0603B472J500NT 50 V X7R")]),
 "C107001": dict(pkg=STD + " (0402)", alts=[
     ("C301973", "EQ", "Walsin 0402N221J500CT 220 pF NP0"),
     ("C541425", "EQ", "Yageo CC0402GRNPO9BN221 220 pF NP0")]),
 "C53134": dict(pkg=STD + " (0805)", use="C2233314", alts=[
     ("C2233314", "DS", "KEMET C0805C473F3GECAUTO 47 nF C0G 1 % 25 V - new primary (RAMP_P node < 5 V)"),
     ("C22409143", "DS", "KEMET C0805C473K3GECTU 47 nF C0G 10 % 25 V")]),
 "C115052": dict(pkg=STD + " (0603)", alts=[
     ("C12164", "EQ", "FH 0603B472K101NT 100 V X7R"),
     ("C152940", "EQ", "Walsin 0603B472K101CT 100 V X7R")]),
 "C2940749": dict(pkg=STD + " (1206)", alts=[
     ("C405303", "EQ", "Murata GRM31C5C2A104JA01L 100 nF C0G 5 % 100 V 1206"),
     ("C338111", "EQ", "TDK C3216C0G2A104JT000E 100 nF C0G 5 % 100 V 1206")]),
 # ---------------- diodes
 "C20883337": dict(pkg=STD + " (SMB)", alts=[
     ("C1973217", "EQ", "Littelfuse SMBJ51A"), ("C10225", "EQ", "RUILON SMBJ51A")]),
 "C224219": dict(pkg=STD + " (SMA)", use="C2482", alts=[
     ("C2482", "EQ", "MDD SS110, 163 k pcs - recommend as primary"),
     ("C165701", "EQ", "ST STPS1H100A 100 V 1 A SMA (lower leakage)")]),
 "C14486": dict(pkg=STD + " (SOT-23)", alts=[
     ("C21713988", "EQ", "GOODWORK NUP2105LT1G (same part no., same pinout 1=CAN 2=CAN 3=GND)"),
     ("C284104", "EQ", "DOWO NUP2105L")]),
 "C12624": dict(pkg=STD + " (0603 LED)", alts=[
     ("C2986059", "EQ", "Everlight 19-217/GHC emerald green"),
     ("C2986030", "CHK", "Everlight yellow-green, Vf 2.0 V (brighter at the same resistor)")]),
 "C2286": dict(pkg=STD + " (0603 LED)", alts=[
     ("C2986060", "EQ", "Everlight 19-217/R6C red"), ("C2986061", "EQ", "Everlight 19-217/R6C-P1Q2 red")]),
 "C81598": dict(pkg=STD + " (SOD-123)", alts=[
     ("C108428", "EQ", "1N4448W 80 V SOD-123"), ("", "", "")]),
 # ---------------- protection / magnetics
 "C206980": dict(pkg=STD + " (1206 fuse)", alts=[
     ("C5383192", "DS", "Reomax R12.000.7 7 A 63 V DC 1206"),
     ("C3165071", "EQ", "Schurter 3413.0326.11 7 A 63 V 1206 (low stock)")]),
 "C1002": dict(pkg=STD + " (0603 bead)", use="C85833", alts=[
     ("C85833", "EQ", "Murata BLM18KG601SN1D 600R 1.3 A - new primary"),
     ("C710379", "EQ", "Murata BLM18KG601SH1D 600R 1.3 A")]),
 "C49308184": dict(pkg=DEF + " (1770 molded)", alts=[
     ("C2976969", "CHK", "Shun Xiang Nuo SMMS1770-220M 22 uH, Isat 23 A, 17.5x17.2 - same 1770 body; confirm land drawing"),
     ("C48996578", "DS", "Sunltech SLO1770C220MTT 22 uH, Isat 23 A - land 3.5x12.8 / gap 11.2 fits the SRP1770 footprint")]),
 "C86617": dict(pkg=DEF + " (5040 shielded)", use="C167974", alts=[
     ("C167974", "DS", "cjiang FNR5040S470MT 47 uH 1.2 A sat - land 1.4x4.2 gap 2.3 = footprint exactly (new primary)"),
     ("C7427133", "CHK", "APV ANR5040T470M 47 uH 1.3 A sat - no datasheet on LCSC; 5040 body")]),
 # ---------------- MOSFETs / transistors
 "C503009": dict(pkg=STD + " (DFN5x6 / PowerPAK SO-8)", alts=[
     ("C2686677", "CHK", "NCE NCEP095N10AG 100 V 12 mOhm: Qg 54 nC vs 26 nC - more gate/switching loss in the hard-switched Q1/Q4, check temp"),
     ("C503061", "CHK", "NCE NCEP068N10G 100 V 6.1 mOhm: Qg 60 nC vs 26 nC - same check")]),
 "C503012": dict(pkg=STD + " (DFN5x6 / PowerPAK SO-8)", use="C503061", alts=[
     ("C503061", "DS", "NCE NCEP068N10G 100 V 6.1 mOhm, Qg 60 nC (primary 65 nC) - new primary"),
     ("C2686677", "DS", "NCE NCEP095N10AG 100 V 12 mOhm, Qg 54 nC")]),
 "C459172": dict(pkg=STD + " (DFN5x6 / SuperSO8)", alts=[
     ("C22466810", "DS", "Siliup SP015N13GHNK 150 V 13 mOhm, Qg 30 nC (primary 19 nC) - fine for UCC27524"),
     ("C2936692", "CHK", "LRC LN7910DT1WG 150 V 15 mOhm - Qg not readable in the datasheet text")]),
 "C53444": dict(pkg=STD + " (SOT-23)", alts=[
     ("C8670", "EQ", "Nexperia PMBT3906"), ("C383300", "EQ", "LRC S-LMBT3906LT1G")]),
 "C8545": dict(pkg=STD + " (SOT-23)", alts=[
     ("C79015", "EQ", "JSCJ BSS123 100 V (G-S-D pinout)"), ("C75882", "EQ", "JSCJ CJ2310 60 V 3 A")]),
 "C891118": dict(pkg=STD + " (SOT-23)", alts=[
     ("C7421706", "EQ", "JSMSEMI FDN86246 (same part no.) 150 V"),
     ("C2987707", "EQ", "HUASHUO HSS2N15 150 V 1.8 A")]),
 # ---------------- resistors
 "C2907507": dict(pkg=STD + " (1206)", alts=[
     ("C137270", "EQ", "Yageo RC1206FR-0747KL 1 % (primary is 5 %)"), ("C2933708", "EQ", "FOJAN FRC1206F4702TS 1 %")]),
 "C23164": dict(pkg=STD + " (0603)", alts=[
     ("C2907035", "EQ", "FOJAN FRC0603F4R70TS"), ("C137705", "EQ", "Yageo RC0603FR-074R7L")]),
 "C25744": dict(pkg=STD + " (0402)", use="C2906861", alts=[
     ("C2906861", "EQ", "FOJAN FRC0402F1002TS - new primary"), ("C60490", "EQ", "Yageo RC0402FR-0710KL")]),
 "C25796": dict(pkg=STD + " (0402)", alts=[
     ("C114756", "EQ", "Yageo RC0402FR-0756KL"), ("C2906875", "EQ", "FOJAN FRC0402F5602TS")]),
 "C25756": dict(pkg=STD + " (0402)", alts=[
     ("C114761", "EQ", "Yageo RC0402FR-0715KL"), ("C2909322", "EQ", "FOJAN FRC0402F1502TS")]),
 "C122538": dict(pkg=STD + " (0603)", alts=[
     ("C844888", "EQ", "Vishay TNPW0603100KBEEA 0.1 % 25 ppm"), ("C190609", "EQ", "Panasonic ERA3AEB104V 0.1 % 25 ppm")]),
 "C186154": dict(pkg=STD + " (0402)", alts=[
     ("C852856", "EQ", "Yageo RT0402BRD075K1L 0.1 % 25 ppm"), ("C2088796", "EQ", "Vishay TNPW04025K10BEED")]),
 "C186137": dict(pkg=STD + " (0402)", alts=[
     ("C852624", "EQ", "Yageo RT0402BRD071KL 0.1 % 25 ppm"), ("C2984405", "EQ", "Viking ARG02BTC1001")]),
 "C25076": dict(pkg=STD + " (0402)", alts=[
     ("C106232", "EQ", "Yageo RC0402FR-07100RL"), ("C2906860", "EQ", "FOJAN FRC0402F1000TS")]),
 "C11702": dict(pkg=STD + " (0402)", alts=[
     ("C2906864", "EQ", "FOJAN FRC0402F1001TS"), ("C106235", "EQ", "Yageo RC0402FR-071KL")]),
 "C2933247": dict(pkg=STD + " (0603)", alts=[
     ("C245987", "EQ", "Yageo RC0603FR-0760R4L"), ("", "", "")]),
 "C22939": dict(pkg=STD + " (0603)", use="C2907006", alts=[
     ("C2907006", "EQ", "FOJAN FRC0603F2R20TS - new primary"), ("C112307", "EQ", "Yageo RC0603FR-072R2L")]),
 "C23178": dict(pkg=STD + " (0603)", alts=[
     ("C114622", "EQ", "Yageo RC0603FR-07470KL"), ("C2907040", "EQ", "FOJAN FRC0603F4703TS")]),
 "C36871": dict(pkg=STD + " (0402)", alts=[
     ("C137947", "EQ", "Yageo RC0402FR-0768KL"), ("C2909379", "EQ", "FOJAN FRC0402F6802TS")]),
 "C25750": dict(pkg=STD + " (0402)", alts=[
     ("C93945", "EQ", "Yageo RC0402FR-07120KL"), ("C2909314", "EQ", "FOJAN FRC0402F1203TS")]),
 "C870479": dict(pkg=STD + " (1206)", alts=[
     ("", "", "No other 191k 0.1 % 1206 in stock on LCSC (Panasonic ERA-8AEB1913V / Vishay TNPW1206191KBEEA at Digikey/Mouser)"), ("", "", "")]),
 "C190095": dict(pkg=STD + " (0402)", use="C844452", alts=[
     ("C844452", "EQ", "Vishay TNPW040210K0BEED 0.1 % 25 ppm - new primary"), ("C2961361", "EQ", "FH TC02G1002BT 0.1 % 25 ppm")]),
 "C11490": dict(pkg=STD + " (0402)", alts=[
     ("C138015", "EQ", "Yageo RC0402FR-072M2L"), ("C2998080", "EQ", "FOJAN FRC0402F2204TS")]),
 "C25092": dict(pkg=STD + " (0402)", use="C2929994", alts=[
     ("C2929994", "EQ", "FOJAN FRC0402F22R0TS - new primary"), ("C114765", "EQ", "Yageo RC0402FR-0722RL")]),
 "C25741": dict(pkg=STD + " (0402)", alts=[
     ("C60491", "EQ", "Yageo RC0402FR-07100KL"), ("C2906859", "EQ", "FOJAN FRC0402F1003TS")]),
 "C227116": dict(pkg=STD + " (0402)", alts=[
     ("C3013173", "EQ", "FOJAN FRC0402F4704TS"), ("C354978", "EQ", "Yageo RC0402FR-074M7L")]),
 "C22859": dict(pkg=STD + " (0603)", alts=[
     ("C109318", "EQ", "Yageo RC0603FR-0710RL"), ("C2906983", "EQ", "FOJAN FRC0603F10R0TS")]),
 "C25340": dict(pkg=STD + " (1206)", alts=[
     ("C327075", "EQ", "Yageo RL1206FR-070R5L"), ("C2759131", "EQ", "UNI-ROYAL HP06W2F500LT5E 0.5 W")]),
 "C17936": dict(pkg=STD + " (1206)", alts=[
     ("C137262", "EQ", "Yageo RC1206FR-074K7L"), ("C965034", "EQ", "UNI-ROYAL NQ06W4F4701T5E")]),
 "C25867": dict(pkg=STD + " (0402)", alts=[
     ("C114759", "EQ", "Yageo RC0402FR-071K5L"), ("C2933074", "EQ", "FOJAN FRC0402F1501TS")]),
 "C25776": dict(pkg=STD + " (0402)", alts=[
     ("C138008", "EQ", "Yageo RC0402FR-0730KL"), ("C2909347", "EQ", "FOJAN FRC0402F3002TS")]),
 "C25900": dict(pkg=STD + " (0402)", alts=[
     ("C105871", "EQ", "Yageo RC0402FR-074K7L"), ("C2765614", "EQ", "UNI-ROYAL CQ02WGF4701TCE")]),
 "C500738": dict(pkg=STD + " (2512)", use="C2904236", alts=[
     ("C2904236", "DS", "Milliohm HoJLR2512-3W-4mR-1%: 6.4x3.2 body, 0.9 mm terminations land on the R_2512 pads - new primary"),
     ("C2908366", "EQ", "Milliohm HoLR2512-3W-4mR-1%-15ppm")]),
 "C500718": dict(pkg=STD + " (2512)", alts=[
     ("C5375464", "EQ", "Milliohm HoYLR2512-3W-10mR-1%"), ("C2994644", "EQ", "Milliohm HoLLR2512-3W-10mR-1%")]),
 "C6331172": dict(pkg=DEF + " (2.54 mm SMD DIP)", alts=[
     ("C19189100", "EQ", "hanxia HX 2.54-6P TPGT (same 6.15x15.24 TPGT body; primary land 1.1 x 2.2 mm, rows 6.6 / 11 mm = footprint)"),
     ("C225006", "CHK", "Diptronics DM-06-V-T/R 6-pos 2.54 SMD - confirm row spacing vs footprint")]),
 "C5718384": dict(pkg=VEN + " (Pulse EP13Plus)", alts=[
     ("C17526143", "PCB", "Pulse PA3855.005NLT: same EP13 footprint and primary, secondaries must be in SERIES - needs the T2 jumper option"),
     ("", "", "Custom-wound EP13 to the same pinout from a local winder (no PCB change)")]),
 "C2892547": dict(pkg=STD + " (0603)", alts=[
     ("C49247666", "EQ", "R+O HNTC0603-103F3950FB 10k 1 % B25/50 3950"),
     ("C52155406", "EQ", "APV ANTC1608-103F3950FB 10k 1 % B3950")]),
 # ---------------- ICs
 "C141980": dict(pkg=STD + " (SOIC-8 PowerPAD)", alts=[
     ("C485921", "DS", "TI UCC27211AQDDARQ1 (same DDA package and pinout)"),
     ("C2871979", "DS", "TI UCC27211DR SOIC-8 (no pad): same pinout; pad 9 left unsoldered - remove its paste for this build")]),
 "C87080": dict(pkg=STD + " (SOT-23-6)", alts=[
     ("C3200285", "DS", "TI LV2862XLVDDCR: same pinout (CB GND FB EN VIN SW), 0.765 V FB, 60 V, 770 kHz; EN threshold 1.25 V -> U13 UVLO ~10 V instead of ~12 V"),
     ("C290195", "DS", "TI LMR16006YDDCR 2.1 MHz: same pinout; 47 uH fine; U13 at 48 V runs near min on-time")]),
 "C404027": dict(pkg=STD + " (SOT-23-5)", alts=[
     ("C485517", "DS", "TI TLV75733PDBVR (1 A, same pinout)"),
     ("C47773", "DS", "Richtek RT9013-33GB: VIN GND EN NC VOUT = same, 5.5 V max (input is +5V)")]),
 "C2058943": dict(pkg=STD + " (SOT-23-6)", alts=[
     ("C2861997", "EQ", "TI INA181A1IDBVT (same part, small reel)"),
     ("C45351496", "CHK", "XBLW INA181A1IDBVR clone - confirm gain error")]),
 "C2058784": dict(pkg=STD + " (SOT-23-6)", alts=[
     ("C116200", "EQ", "TI INA181A2IDBVT (same part, small reel)"),
     ("C53198613", "CHK", "lingxingic INA181A2 clone - confirm gain error")]),
 "C5338808": dict(pkg=STD + " (SOIC-16W)", alts=[
     ("C2671569", "PCB", "TI ISO1042QDWRQ1 fits the U9 footprint (pins 2-16 match) but needs pin 1 = 3.3 V and an external isolated 5 V (B0505S module) - U9 reserve option"),
     ("C1848126", "PCB", "TI ISO1042DWR - same as above")]),
 "C465729": dict(pkg=STD + " (SOIC-8)", alts=[
     ("C185857", "DS", "TI UCC27524ADR (same pinout ENA INA GND INB OUTB VDD OUTA ENB)"),
     ("C20623206", "DS", "UMW UCC27524DR - datasheet states pin-to-pin with 27524")]),
 "C4944981": dict(pkg=STD + " (SOIC-16W)", alts=[
     ("C2862403", "DS", "TI ISO7742FDWR: same pinout, default LOW (F) like CA-IS3742L - low stock"),
     ("C53446650", "DS", "YLPTEC ISO7742W0-Y: wide body, default LOW ('0') - low stock (do NOT use the N0 narrow-body part)")]),
 "C6187": dict(pkg=STD + " (SOT-223)", alts=[
     ("C6068482", "EQ", "GOODWORK AMS1117-5.0 (same part no.)"),
     ("C347230", "EQ", "UMW LD1117-5.0 (GND OUT IN, 15 V max; input +10V_P)")]),
 "C34731": dict(pkg=STD + " (SOT-23-5)", alts=[
     ("C38943276", "DS", "3PEAK LMV331X-S5TR: open-drain, pinout +IN -VS -IN OUT +VS = TI DBV, 35.9 k pcs"),
     ("C672259", "DS", "ST LMV331ILT: open-drain, same SOT23-5 pinout")]),
 "C23892": dict(pkg=STD + " (SOT-23)", alts=[
     ("C29780634", "DS", "UMW TL431AIDBZR: 1=K 2=REF 3=A = TI DBZ (U22 needs this pinout)"),
     ("C79737", "DS", "Nexperia TL431AIDBZR,215 'normal pinning' 1=K 2=REF 3=A (not the MFDT mirrored type)")]),
 "C231572": dict(pkg=STD + " (SOIC-8)", alts=[
     ("C59197", "EQ", "onsemi UC2843BD1R2G (same die, -25..85 C)"),
     ("C702405", "EQ", "TI UC3843D8TR (same 8-pin pinout, 0..70 C)")]),
 "C42381015": dict(pkg=STD + " (SOP-4 2.54)", alts=[
     ("C33068", "EQ", "LITEON LTV-357T-B (CTR 130-260 %, same pinout)"),
     ("C17702877", "EQ", "GOODWORK EL357B (CTR B)")]),
 "C13738": dict(pkg=STD + " (3225 4-pad)", alts=[
     ("C18207610", "EQ", "YXC XL2LI-111-16M 16 MHz 9 pF 50 ohm"),
     ("C5444547", "EQ", "YXC XL2EL89CLI-111YLC-16M 16 MHz 9 pF")]),
 "C529413": dict(pkg=STD + " (LQFP-64)", use="C1235414", alts=[
     ("C1235414", "EQ", "ST STM32G474RBT3 (same die, -40..125 C) - new primary"),
     ("C521608", "EQ", "ST STM32G474RET6 (512 KB, same pinout; 12 pcs)")]),

 # ---------------- hand-soldered connectors (not on the JLC BOM)
 "C441204": dict(pkg=DEF + " (5.08 pluggable header)", alts=[
     ("C699495", "EQ", "DEGSON 2EDGR-5.08-02P: same 5.08 mm 2-pin right-angle header"), ("", "", "Mating plug: Kefa KF2EDGK-5.08-2P-AA (C440880), 2 per board")]),
 "C42419910": dict(pkg=STD + " (2.54 header)", alts=[
     ("C53200685", "EQ", "XYECONN XY-PZ254V-11-03P"), ("C41425293", "EQ", "XFCN PZ254V-11-03P-RD (red)")]),
 "C42419913": dict(pkg=STD + " (2.54 header)", alts=[
     ("C53200691", "EQ", "XYECONN XY-PZ254V-11-06P"), ("C41425296", "EQ", "XFCN PZ254V-11-06P-RD (red)")]),
 "C45384660": dict(pkg=STD + " (2.54 header)", alts=[
     ("C56153598", "EQ", "XFCN PZ254V-12-04P-T"), ("C42393319", "EQ", "XFCN PZ254V-12-04P-YL")]),
 "C41376037": dict(pkg=STD + " (1.27 SMD header)", alts=[
     ("", "", "Samtec FTSH-105-01-L-DV-K or any 2x5 1.27 mm SMD header"), ("", "", "")]),
}

# new primary (applied to the BOM 2026-10-20) -> old primary key in ALTS2
REMAP = {"C1235414": "C529413", "C503061": "C503012", "C2906861": "C25744", "C20539426": "C52923",
         "C2907006": "C22939", "C2929994": "C25092", "C844452": "C190095", "C85833": "C1002", "C167974": "C86617",
         "C2233314": "C53134", "C2904236": "C500738", "C2482": "C224219"}

# risk + action per line (the rest is computed from stock)
FIX = {
 "C529413": ("CRITICAL", "Out of stock. Use STM32G474RBT3 (C1235414) - same die, firmware unchanged."),
 "C503012": ("CRITICAL", "38 pcs, 4 per board. Use NCEP068N10G (C503061): Qg 60 nC vs 65 nC, 6.1 mOhm - drop-in."),
 "C1525": ("CRITICAL", "Out of stock. Merge the 22 caps into the C307331 line."),
 "C25744": ("CRITICAL", "Out of stock (51 per board). Use FOJAN C2906861 (JLC: check its own basic-part stock first)."),
 "C52923": ("CRITICAL", "Out of stock. Use CCTC C20539426 (1 uF 50 V X5R 0402)."),
 "C22939": ("CRITICAL", "Out of stock. Use FOJAN C2907006."),
 "C25092": ("CRITICAL", "Out of stock. Use FOJAN C2929994."),
 "C190095": ("CRITICAL", "Out of stock. Use Vishay C844452 (0.1 %, 25 ppm)."),
 "C1002": ("CRITICAL", "Not listed any more. Use Murata BLM18KG601SN1D (C85833)."),
 "C86617": ("CRITICAL", "Not listed any more. Use cjiang FNR5040S470MT (C167974) - land pattern identical to the footprint."),
 "C53134": ("CRITICAL", "BOM error: C82 must be C0G. Use KEMET C0805C473F3GECAUTO (C2233314)."),
 "C500738": ("HIGH", "Marked discontinued. Use Milliohm HoJLR2512-3W-4mR (C2904236) - checked against the 2512 pads."),
 "C5718384": ("HIGH", "102 pcs, single maker (Pulse). Buy now. Backup needs the T2 jumper option (PA3855.005NLT in series)."),
 "C49308184": ("HIGH", "120 pcs. Buy now. SMMS1770-220M / SLO1770C (both 23 A sat, 1770 body) - SOREDE 16 A part dropped."),
 "C249664": ("HIGH", "175 pcs, 3 per board (58 boards). ChengTao RVE1J470M1010 is an exact 2nd source."),
 "C141980": ("HIGH", "338 pcs, 3 per board. UCC27211AQDDARQ1 (same DDA) / UCC27211DR (SOIC-8, no pad)."),
 "C5338808": ("MEDIUM", "4,777 pcs but Chipanalog only (integrated isolated DC-DC). Backup ISO1042DW + B0505S needs the U9 reserve option."),
 "C4944981": ("MEDIUM", "2,320 pcs; default-LOW wide-body alternates exist but have low stock (TI 139, YLPTEC 90)."),
 "C224219": ("MEDIUM", "1,360 pcs, 4 per board. Switch primary to MDD SS110 (C2482, 163 k pcs)."),
 "C2940749": ("MEDIUM", "902 pcs, 6 per board (150 boards). Murata / TDK 1206 C0G 100 V are verified 2nd/3rd (CCTC/HRE 'M3L' parts dropped: not C0G)."),
 "C206980": ("MEDIUM", "765 pcs. Reomax R12.000.7 verified as 2nd source."),
 "C891118": ("MEDIUM", "1,606 pcs. JSMSEMI FDN86246 / HSS2N15 (150 V) - same SOT-23 pinout."),
 "C870479": ("MEDIUM", "Single LCSC source (4,755 pcs, 1 per board). Other makers only at Digikey/Mouser."),
 "C503009": ("MEDIUM", "4,695 pcs (2,300 boards). NCE alternates have 2x the gate charge - fine, but check Q1/Q4 temperature on the bench if used."),
 "C6331172": ("LOW", "11,262 pcs; HX TPGT clone (2,002 pcs) is the same body."),
 "C2933247": ("LOW", "423 k pcs; Yageo 60.4R 2nd; no 3rd in stock."),
}
