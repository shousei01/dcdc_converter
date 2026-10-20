Firmware workspace - STM32G474RBT6 (LQFP64), on the SECONDARY side            (hardware Rev E, 2026-10-20)
Suggested: STM32CubeIDE project here (src\, inc\), notes in docs\.
Full pin list with every alternate function: 01_hardware\docs\pin-map.xlsx
Full design notes (full scales, error budget, calibration): 01_hardware\docs\DCDC_Design_Notes.pdf

Clock: 16 MHz HSE crystal Y1 (PF0/PF1, 12 pF load caps) -> PLL (M=4, N=85, R=2) -> 170 MHz SYSCLK.
       FDCAN kernel clock from HSE or PLLQ.
Reference: VREF+ (pin 28) = VDDA (pin 29) = +3V3A = 3.3 V (U5 TLV75533 +/-1 % through FB1; REF3030 removed in Rev E).
       Leave VREFBUF disabled as after reset (VREFBUF_CSR: ENVR = 0, HIZ = 1).
       All ADC, DAC3 and comparator values are referred to 3.3 V. Correct the gain at run time with VREFINT:
       VDDA = 3.0 V x VREFINT_CAL / VREFINT_DATA (IL and NTC are ratiometric to +3V3A anyway).

HRTIM
  Timer A  PA8 / PA9    CHA1/CHA2 (AF13) -> U2 -> Q1/Q2   4SBB input leg  (150 kHz)
  Timer E  PC8 / PC9    CHE1/CHE2 (AF3)  -> U3 -> Q3/Q4   4SBB output leg (150 kHz)
  Timer C  PB12 / PB13  CHC1/CHC2 (AF13) -> U12 isolator -> U10 -> Q5/Q6  LLC half-bridge (~205 kHz, 50 %)
  Timer D  PB14 / PB15  CHD1/CHD2 (AF13) -> U11 -> Q7/Q8   LLC synchronous rectifiers (lead ~30 ns)
  FLT2     PA15 (AF13)  VIN_OVP, active HIGH (primary input OVP, trips 50.26 V rising / clears 49.83 V)
  SR_EN    PC11 (GPIO, high = SR driver enabled)

ADC / COMP (12-bit, 3.3 V full scale, 0.81 mV/LSB)
  PA0  VBUS_SNS   ADC1_IN1   100k/5.1k 0.1 %  -> 68.0 V full scale, 16.6 mV/LSB
  PB11 VOUT_SNS   ADC1_IN14  100k/5.1k 0.1 %  -> 68.0 V (+ COMP6 fast OVP); add IOUT x 10 mOhm for true VOUT
  PA1  IOUT_SNS   ADC1_IN2   0.5 V/A (INA181A2, 10 mOhm) -> 6.6 A full scale, 1.6 mA/LSB
  PB1  IL_SNS     ADC1_IN12  1.65 V + 0.08 V/A (INA181A1, 4 mOhm, zero = VREF/2) -> +/-20.6 A, COMP1 = +OCP (boost)
  PB0  IL_SNS     COMP4      -OCP (buck), output inverted
  PA6  NTC_SNS    ADC2_IN3   10k pull-up from +3V3A / NTC 10k B3950 (ratiometric): 25 C = 1.65 V, 100 C = 0.21 V
  Thresholds for COMP from DAC3 (0-3.3 V); COMP outputs -> HRTIM fault inputs.
  Zero IL_SNS and IOUT_SNS at start-up with the power stage off and subtract.
  PA4  reserved for DAC1_OUT1 (10k pull-down R95 fitted - a valid DAC load)

VIN monitor (isolated, monitoring only)
  PA2  VIN_PWM    TIM15_CH1 (AF9), PWM-input mode; 10k pull-down R93. ~200 Hz (4.9 ms ramp).
  Prescaler 16 -> ~51,700 counts per period. Output is HIGH while the primary ramp is below the VIN divider.
  x   = (t_high - t_reset) / (period - t_reset),   t_reset ~20 us
  VIN = 50.47 V * x - 0.20 V        (readable from ~9.7 V, primary aux start, up to the OVP trip)
  Average 8-16 periods. Calibrate gain and offset at two points (e.g. 24 V and 48 V) and store in flash:
  about +/-1.5 % untrimmed, about +/-0.5 % after calibration over temperature.

Comms / IO
  PA11 / PA12  FDCAN1 RX / TX (AF9) -> CA-IS3062VW isolated CAN
  PC0-PC5      address bits 0-5 (DIP ON = 0, pull-ups 10k)
  PB9          LED_RUN  (active low)      PC10  LED_FLT (active low)
  PA5          Test_pin_DAC (DAC1_OUT2)   PB6 / PB7  Test_pin_GPIO1 / GPIO2
  PA13/PA14/PB3  SWDIO / SWCLK / SWO      PB8 = BOOT0 (10k to GND)

Unused pins (Rev D): PC13, PC14, PC15, PA3, PA4, PA7, PA10, PB2, PB4, PB5, PB10, PC6, PC7, PC12, PD2
  each has a 10k pull-down (R90-R105 except R93, which serves PA2). Leave them in analog mode (reset state) or input.
  PB4 is NJTRST with an internal pull-up at reset; the 10k wins - harmless with SWD-only debug.

Input OVP (Rev D)
  LMV331 + TL431 on the primary side compare the VIN divider against 2.495 V; the open-drain output goes through
  isolator channel U12 VI1 -> VO1 = VIN_OVP. Configure HRTIM FLT2 (PA15, AF13) active-high, no filter or a
  short digital filter, so all outputs are cut in hardware; also read it as a GPIO / EXTI15 for logging.
  Trips 50.26 V rising, clears 49.83 V (about +/-1.3 %). VIN_OVP stays high while the primary 5 V rail is up
  and VIN is above the clear level.

Start-up sequence
  1. MCU boots from the isolated flyback rails (+10 V -> 5 V -> 3.3 V, as soon as VIN is present);
     CAN and the 4SBB / SR drivers are powered too. Keep VREFBUF off; ADC calibration
     (ADC_CR.ADCAL) single-ended, then the IL / IOUT zero measurement.
  2. Check VIN_OVP is low; arm FLT2. Start TIM15 PWM input for the VIN monitor.
  3. LLC soft-start: ~2.5 x fr, small duty -> fr, 50 % over ~10 ms; SRs off (body diodes).
  4. Wait for VBUS; enable SR_EN.
  5. Start the 4SBB (CV/CC); keep bootstrap refresh (static-on FET duty <= ~98 %).
  6. Trim LLC frequency to the measured VBUS/VIN ratio (leakage tolerance +/-20 %).

Test points (Rev D): TP1 VIN, TP2 GNDP, TP3 +10V_P, TP4 +5V_P (primary - not earth-referenced!),
  TP5 VBUS, TP6 +10V, TP7 +5V, TP8 +3V3, TP9 +3V3A, TP10 GND, TP11 VOUT, TP12 GND,
  TP13 IL_SNS, TP14 IOUT_SNS, TP15 VIN_OVP.
