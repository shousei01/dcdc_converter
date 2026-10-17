Firmware workspace - STM32G474RBT6 (LQFP64), on the SECONDARY side
Suggested: STM32CubeIDE project here (src\, inc\), notes in docs\.

Clock: 8 MHz HSE crystal (PF0/PF1) -> 170 MHz SYSCLK; FDCAN kernel clock from HSE/PLL.
VREF+ = VDDA = 3.3 V (VREFBUF off, VREF+ as input).

HRTIM
  Timer A  PA8 / PA9    CHA1/CHA2 -> U2 -> Q1/Q2   4SBB input leg  (150 kHz)
  Timer E  PC8 / PC9    CHE1/CHE2 -> U3 -> Q3/Q4   4SBB output leg (150 kHz)
  Timer C  PB12 / PB13  CHC1/CHC2 -> U12 isolator -> U10 -> Q5/Q6  LLC half-bridge (~205 kHz, 50 %)
  Timer D  PB14 / PB15  CHD1/CHD2 -> U11 -> Q7/Q8   LLC synchronous rectifiers (lead ~30 ns)
  SR_EN    PC11 (GPIO, high = SR driver enabled)

ADC / COMP
  PA0  VBUS_SNS   ADC1_IN1   100k/5.1k  -> 68 V full scale
  PB11 VOUT_SNS   ADC1_IN14  100k/5.1k (+ COMP6 fast OVP); add IOUT x 10 mOhm for true VOUT
  PA1  IOUT_SNS   ADC1_IN2   0.5 V/A (INA181A2, 10 mOhm)
  PB1  IL_SNS     ADC1_IN12  1.65 V + 0.08 V/A (INA181A1, 4 mOhm), COMP1 = +OCP (boost)
  PB0  IL_SNS     COMP4      -OCP (buck), output inverted
  PA4  NTC_SNS    ADC2_IN17  10k / NTC 10k B3950
  Thresholds for COMP from DAC3; COMP outputs -> HRTIM fault inputs.

Comms / IO
  PA11 / PA12  FDCAN1 RX / TX  -> CA-IS3062VW isolated CAN
  PC0-PC5      address bits 0-5 (DIP ON = 0, pull-ups 10k)
  PB9          LED_RUN  (active low)      PC10  LED_FLT (active low)
  PA5          Test_pin_DAC (DAC1_OUT2)   PB6 / PB7  Test_pin_GPIO1 / GPIO2
  PA13/PA14/PB3  SWDIO / SWCLK / SWO      PB8 = BOOT0 (10k to GND)

Start-up sequence
  1. MCU boots from the isolator's 3.3 V (as soon as VIN is present).
  2. LLC soft-start: ~2.5 x fr, small duty -> fr, 50 % over ~10 ms; SRs off (body diodes).
  3. Wait for VBUS and the secondary 10 V / 5 V rails; enable SR_EN.
  4. Start the 4SBB (CV/CC); keep bootstrap refresh (static-on FET duty <= ~98 %).
  5. Trim LLC frequency to the measured VBUS/VIN ratio (leakage tolerance +/-20 %).
