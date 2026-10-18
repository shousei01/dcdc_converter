Firmware workspace - STM32G474RBT6 (LQFP64), on the SECONDARY side            (hardware Rev D)
Suggested: STM32CubeIDE project here (src\, inc\), notes in docs\.
Full pin list with every alternate function: 01_hardware\docs\pin-map.xlsx

Clock: 16 MHz HSE crystal Y1 (PF0/PF1, 12 pF load caps) -> PLL (M=4, N=85, R=2) -> 170 MHz SYSCLK.
       FDCAN kernel clock from HSE or PLLQ.
VREF+ = VDDA = 3.3 V (VREFBUF off, VREF+ used as input).

HRTIM
  Timer A  PA8 / PA9    CHA1/CHA2 (AF13) -> U2 -> Q1/Q2   4SBB input leg  (150 kHz)
  Timer E  PC8 / PC9    CHE1/CHE2 (AF3)  -> U3 -> Q3/Q4   4SBB output leg (150 kHz)
  Timer C  PB12 / PB13  CHC1/CHC2 (AF13) -> U12 isolator -> U10 -> Q5/Q6  LLC half-bridge (~205 kHz, 50 %)
  Timer D  PB14 / PB15  CHD1/CHD2 (AF13) -> U11 -> Q7/Q8   LLC synchronous rectifiers (lead ~30 ns)
  FLT2     PA15 (AF13)  VIN_OVP, active HIGH  (Rev D: primary input OVP, trips at 50.2 V rising)
  SR_EN    PC11 (GPIO, high = SR driver enabled)

ADC / COMP
  PA0  VBUS_SNS   ADC1_IN1   100k/5.1k  -> 68 V full scale
  PB11 VOUT_SNS   ADC1_IN14  100k/5.1k (+ COMP6 fast OVP); add IOUT x 10 mOhm for true VOUT
  PA1  IOUT_SNS   ADC1_IN2   0.5 V/A (INA181A2, 10 mOhm)
  PB1  IL_SNS     ADC1_IN12  1.65 V + 0.08 V/A (INA181A1, 4 mOhm), COMP1 = +OCP (boost)
  PB0  IL_SNS     COMP4      -OCP (buck), output inverted
  PA6  NTC_SNS    ADC2_IN3   10k / NTC 10k B3950          (Rev D: moved from PA4)
  Thresholds for COMP from DAC3; COMP outputs -> HRTIM fault inputs.
  PA4  reserved for DAC1_OUT1 (10k pull-down R95 fitted - a valid DAC load)

Comms / IO
  PA11 / PA12  FDCAN1 RX / TX (AF9) -> CA-IS3062VW isolated CAN
  PC0-PC5      address bits 0-5 (DIP ON = 0, pull-ups 10k)
  PB9          LED_RUN  (active low)      PC10  LED_FLT (active low)
  PA5          Test_pin_DAC (DAC1_OUT2)   PB6 / PB7  Test_pin_GPIO1 / GPIO2
  PA13/PA14/PB3  SWDIO / SWCLK / SWO      PB8 = BOOT0 (10k to GND)

Unused pins (Rev D): PC13, PC14, PC15, PA2, PA3, PA4, PA7, PA10, PB2, PB4, PB5, PB10, PC6, PC7, PC12, PD2
  each has a 10k pull-down (R90-R105). Leave them in analog mode (reset state) or input.
  PB4 is NJTRST with an internal pull-up at reset; the 10k wins - harmless with SWD-only debug.

Input OVP (Rev D)
  LMV331 + TL431 on the primary side compare VIN/20.1 against 2.495 V; the open-drain output goes through
  isolator channel U12 VI1 -> VO1 = VIN_OVP. Configure HRTIM FLT2 (PA15, AF13) active-high, no filter or a
  short digital filter, so all outputs are cut in hardware; also read it as a GPIO / EXTI15 for logging.
  Hysteresis ~0.4 V. VIN_OVP stays high while the primary 5 V rail is up and VIN > ~49.8 V.

Start-up sequence
  1. MCU boots from the isolator's 3.3 V (as soon as VIN is present).
  2. Check VIN_OVP is low; arm FLT2.
  3. LLC soft-start: ~2.5 x fr, small duty -> fr, 50 % over ~10 ms; SRs off (body diodes).
  4. Wait for VBUS and the secondary 10 V / 5 V rails; enable SR_EN.
  5. Start the 4SBB (CV/CC); keep bootstrap refresh (static-on FET duty <= ~98 %).
  6. Trim LLC frequency to the measured VBUS/VIN ratio (leakage tolerance +/-20 %).

Test points (Rev D): TP1 VIN, TP2 GNDP, TP3 +10V_P, TP4 +5V_P (primary - not earth-referenced!),
  TP5 VBUS, TP6 +10V, TP7 +5V, TP8 +3V3, TP9 +3V3A, TP10 GND, TP11 VOUT, TP12 GND,
  TP13 IL_SNS, TP14 IOUT_SNS, TP15 VIN_OVP.
