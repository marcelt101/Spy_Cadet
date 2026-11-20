* USB-C charger + 1 m cable, Pico W load, GPIO15 gate drive.
Vusb   usb 0 5.1
Rcab   usb c1 0.15
Lcab   c1 vbus 1u
* Pico W: VBUS -> on-board Schottky -> VSYS (10 uF) -> RT6150 buck-boost.
* VSYS absolute max is 5.5 V. Wi-Fi up draws ~80 mA.
Dpico  vbus vsys D1N5819
Cvsys  vsys 0 10u
Rpico  vsys 0 60
* GPIO15: 3.3 V push-pull, ~40 ohm output resistance at 12 mA drive strength
* Firmware soft-start: duty climbs 2 % per step (staircase below) instead of jumping
Vsaw   saw 0 PULSE(0 1 0 24.99u 10n 0 25u)
Vdut   dut 0 PWL(0 0 3m 0 3.001m 0.02 5.000m 0.02 5.001m 0.04 7.000m 0.04 7.001m 0.06 9.000m 0.06 9.001m 0.08 11.000m 0.08 11.001m 0.10 13.000m 0.10 13.001m 0.12 15.000m 0.12 15.001m 0.14 17.000m 0.14 17.001m 0.16 19.000m 0.16 19.001m 0.18 21.000m 0.18 21.001m 0.20 23.000m 0.20 23.001m 0.22 25.000m 0.22 25.001m 0.24 27.000m 0.24 27.001m 0.26 29.000m 0.26 29.001m 0.28 31.000m 0.28 31.001m 0.30 33.000m 0.30 33.001m 0.32 35.000m 0.32 35.001m 0.34 37.000m 0.34 37.001m 0.36 39.000m 0.36 39.001m 0.38 41.000m 0.38 41.001m 0.40 43.000m 0.40 43.001m 0.42 45.000m 0.42 45.001m 0.44 47.000m 0.44 47.001m 0.46 49.000m 0.46 49.001m 0.48 51.000m 0.48 51.001m 0.50 53.000m 0.50 53.001m 0.52 55.000m 0.52 55.001m 0.54 57.000m 0.54 57.001m 0.56 59.000m 0.56 59.001m 0.58 61.000m 0.58 61.001m 0.60 63.000m 0.60)
Bgpio  gp 0 V = v(dut) > v(saw) ? 3.3 : 0
Rdrv   gp gp1 40
R1     gp1 g 100            ; gate series resistor
R2     g 0 10k              ; gate pull-down (keeps fans off while Pico boots)
M1     drain g src src AO3400A
Vsense src 0 0           ; 0 V source, measures FET current
* Low-side buck: fans see smooth DC = duty x 5 V instead of chopped 5 V
X1     vbus fanm FAN
X2     vbus fanm FAN
X3     vbus fanm FAN
Cout   vbus coutn 100u      ; output cap across the fans (as in the spec)...
Rcout  coutn fanm 0.3
L1     fanm l1n {lval}      ; ...plus the inductor the spec was missing
RL1    l1n drain 0.25       ; inductor DCR
D1     drain vbus D1N5819   ; freewheel diode, cathode (stripe) to +5 V
Cin    vbus cinn 100u       ; input bulk on the 5 V rail
Rcin   cinn 0 0.3
Cin2   vbus 0 10u           ; 10 uF X7R ceramic next to the FET/diode
