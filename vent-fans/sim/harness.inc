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
Vgpio  gp 0 PULSE(0 3.3 0 3n 3n {duty*per} {per})
Rdrv   gp gp1 40
R1     gp1 g 100            ; gate series resistor
R2     g 0 10k              ; gate pull-down (keeps fans off while Pico boots)
M1     drain g src src AO3400A
Vsense src 0 0           ; 0 V source, measures FET current
X1     vbus drain FAN
X2     vbus drain FAN
X3     vbus drain FAN
D1     drain vbus D1N5819   ; flyback, cathode (stripe) to +5 V
