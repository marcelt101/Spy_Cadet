# Automatic vent booster fans (v1)

Three quiet 80 mm 5 V fans behind a ~4"-tall supply vent. They run only while
the furnace/AC blower runs. Home Assistant watches your HomeKit thermostat and
switches them through a Pico W on a small carrier PCB. One USB-C phone charger
powers everything.

```
vent-fans/
├── README.md                  ← you are here: design, BOM, install, tuning
├── wiring.md                  ← schematic in ASCII, connector pinouts, field wiring
├── esphome/vent-fans.yaml     ← Pico W firmware (validated with ESPHome 2026.11)
├── homeassistant/automation.yaml
├── sim/                       ← ngspice models, ./run_all.sh, plot.py, results.txt, plots
└── kicad/                     ← KiCad 7 project: schematic, placed board, custom Pico W part
    └── tools/                 ← generators (gen_schematic.py, gen_pcb.py, check_netlist.py)
```

## What changed from the original spec, and why

| # | Original spec | v1 | Why (evidence in `sim/`) |
|---|---|---|---|
| 1 | 100 µF across the fans, no inductor | Add **one 100 µH inductor** between the fans and the MOSFET. That makes a proper low-side buck converter. | A capacitor across a low-side-switched load gets recharged to 5 V on every PWM pulse, so the fans saw nearly full voltage at any setting: **30 % duty still gave 90 % fan current**. With the inductor the fans get smooth DC ≈ duty × 5 V (30 % → 27 %, 60 % → 55 %, ripple ≈ 80 mV). See `plot_speed_vs_duty.png`. |
| 2 | Cap only across the fans | 100 µF + 10 µF **on the 5 V rail** (input) as well | Moving caps alone (no inductor) made it worse: every pulse recharged the fans' internal capacitors through the FET with **13–19 A spikes**. The buck version peaks at **0.4 A**. See `plot_waveforms_60pct.png`. |
| 3 | 25 kHz PWM | 40 kHz | Still inaudible. A 100 µH inductor is enough at this frequency (ripple ≈ 0.15 A). |
| 4 | Speed jumps instantly | **Soft-start in firmware**: 2 % every 20 ms | Going straight from 0 to 60 % rings the LC filter: **2.1 A** inductor peak. With the slew limiter it's **0.44 A**, so a small 1 A inductor never saturates. See `plot_powerup.png`. |
| 5 | IRLZ44N / AO3400 | **AO3400A** (SOT-23) only | Simulated Rds(on) ≈ 32 mΩ at the Pico's 3.3 V gate drive. It dissipates ~6 mW, so no heatsink. The IRLZ44N is only specified from 4 V gate drive and is huge. |
| 6 | Breadboard wiring | **Carrier PCB, 70 × 50 mm**: Pico W socketed, 3 keyed fan headers, optional DS18B20 header | Fewer loose joints in a dusty, warm, vibrating spot. Fans unplug for cleaning. |
| 7 | Automation used `delay` + `trigger.to_state` | `for:` on the triggers, re-sync on HA restart and when the board reconnects | The old version could leave fans running after an HA restart. `for:` doesn't drop a pending off when the thermostat chatters. |
| 8 | ESPHome reboots when HA is down | `reboot_timeout: 0s`, plus optional on-board fallback from a duct probe | The fans keep working (or stay safely off) with HA down. |

What stayed the same: Pico W, 5 V fans, one USB charger, HA in charge, 20 s
start delay, 30 s run-on, fans **off** if anything is unplugged or the Pico is
booting (10 k gate pull-down).

### Simulation summary (`sim/results.txt`, 3 × fans, 5.1 V charger + 1 m cable)

| Circuit | duty → fan current (% of full) | FET peak (60 %) | 5 V rail min (30 %) |
|---|---|---|---|
| Original spec | 30→90, 60→97, 80→99 | 0.78 A | 4.40 V |
| Caps on rail, no L | 30→76, 60→90, 80→97 | **13.4 A** | 4.52 V |
| **v1 buck** | **30→27, 60→55, 80→78** | **0.40 A** | 5.05 V |

The models are approximations: the AO3400A is a VDMOS fit to its datasheet, and
each fan is modelled as a reverse diode + 1 µF + 33 Ω + 1 mH. The comparison
between circuits is what matters, not the third digit. To re-run:
`cd sim && ./run_all.sh && python3 plot.py` (needs ngspice, numpy and matplotlib).

## Bill of materials

| Ref | Qty | Part | Footprint | Notes |
|---|---|---|---|---|
| U1 | 1 | Raspberry Pi Pico W, plus 2× 20-pin female headers | 2×20 THT | Socketed, so it can be swapped or reflashed |
| Q1 | 1 | AO3400A N-MOSFET | SOT-23 | Logic-level, 30 V, 5.7 A |
| L1 | 1 | 100 µH shielded power inductor, **Isat ≥ 1 A, DCR ≤ 0.4 Ω** | Bourns SRR1260 (12.5 mm) | e.g. SRR1260-101M. Check Isat on the datasheet of whatever you buy. |
| D1 | 1 | SS14 Schottky, 1 A 40 V (SMD 1N5819) | SMA | Stripe (cathode) to +5 V |
| C1, C3 | 2 | 100 µF 10 V+ low-ESR electrolytic | radial 6.3 mm, 2.5 mm pitch | C1 = input, C3 = across the fans |
| C2 | 1 | 10 µF 16 V X7R ceramic | 1206 | Close to Q1/D1 |
| R1 | 1 | 100 Ω | 0805 | gate series resistor |
| R2 | 1 | 10 kΩ | 0805 | gate pull-down |
| J1–J3 | 3 | 3-pin 2.54 mm fan header (KF2510 / Molex KK style) | `FanPinHeader_1x03` | 2-pin fan plugs fit pins 1–2 |
| J4, R3 | 1 + 1 | 3-pin header + 4.7 kΩ 0805 | | **Optional**, only with the DS18B20 probe |
| — | 3 | 80 mm **5 V** fans, 15 or 25 mm thick, sleeve/hydraulic bearing, ≤ 0.25 A | | Pick the lowest-RPM/dBA listing. Budget generic is fine. |
| — | 1 | USB-C charger (5 V, ≥ 1.5 A) + USB-C → micro-USB cable | | Plugs into the Pico's own USB port |
| — | 1 | Waterproof DS18B20 probe | | Optional |

Total draw ≈ 0.5 A at full speed, ~0.25 A at the default setting.

## Build

1. **PCB**: open `kicad/vent_fans.kicad_pro` in KiCad 7 or later. The
   schematic is complete and the board is placed with nets assigned. You do the
   routing; see [Routing the board](#routing-the-board).
2. **Solder** SMD parts first, then the caps, headers and Pico sockets.
   Check the polarity of C1/C3 (+) and D1 (stripe toward the +5V side).
3. **Firmware**: in the ESPHome add-on on your Proxmox HA, create a new device,
   paste `esphome/vent-fans.yaml`, add the secrets (`esphome/secrets.example.yaml`
   shows the names), plug the Pico W into your PC by USB and install. After that,
   updates go over Wi-Fi.
4. **Bench test** before it goes in the wall. Plug in the charger with the fans
   attached. In HA, turn on `fan.vent_fans`: the fans should ramp up over about
   a second. Measure across a fan connector (pin 2 to pin 1): ≈ 2.7 V at 1 %,
   ≈ 4 V at 60 %, ≈ 4.9 V at 100 %.
5. **Automation**: in HA, go to Developer Tools → States, filter `climate.`, and
   find your thermostat. Check that it has an `hvac_action` attribute that
   changes between `idle` and `heating`/`cooling`. HomeKit Controller thermostats
   normally do. Paste `homeassistant/automation.yaml` into a new automation and
   replace `climate.thermostat` (3 places).

## Routing the board

The board in `kicad/vent_fans.kicad_pcb` is 70 × 50 mm and two-layer. It already
has a GND pour on both layers and a copper keep-out under the Pico W antenna.
The `Power` net class (0.8 mm tracks) covers +5V, GND, FAN- and SW. Signals
default to 0.3 mm.

1. Open the PCB and press **B** to refill zones. The ratsnest shows the 20
   connections still to route.
2. Route the **switching loop** first and keep it tiny: C2 → D1 cathode, D1
   anode → Q1 drain, Q1 source → GND via next to C2's GND pad. This is the only
   fast-edge loop on the board.
3. SW (Q1 drain / D1 anode / L1 pin 2) is the noisy node. Keep it short and
   on the top layer, with no long runs.
4. +5V: from Pico pin 40 (top-left corner pad) to C1 and C2, then on to the fan
   headers' pin 2 and C3+. Use 0.8 mm or wider.
5. FAN-: from L1 pin 1 to C3−, then to pin 1 of J1–J3.
6. GP15 (bottom-right Pico pad) → R1 → gate. R2 goes from gate to GND.
7. Optional: GP16 → J4 pin 2 → R3 → 3V3 (Pico pin 36).
8. Stitch the two GND pours with a few vias, keeping them away from the
   antenna keep-out. Run **Inspect → Design Rules Checker** until it's clean.
9. **File → Fabrication Outputs → Gerbers + Drill**, zip them and order (any
   2-layer, 1.6 mm, HASL service).

`kicad/tools/` regenerates everything from one parts table, if you want to change
a part:
`python3 tools/gen_schematic.py && python3 tools/check_netlist.py && /usr/bin/python3 tools/gen_pcb.py`.
Note that this overwrites any routing you've done, so only use it before you route.

## Tuning

- **Speed**: `speed: 60` in the automation. With smooth DC the fans are much
  quieter at a given speed than with chopped PWM. Try 30–60 %.
- **Fans won't start at low speed**: raise `min_power` (0.55 ≈ 2.7 V) in
  `vent-fans.yaml`.
- **Delays**: the `for:` values in the automation (20 s on, 30 s run-on).
- **Your thermostat only shows `idle`/`heating`** (no `cooling`, or the
  attribute is missing): use the DS18B20 option. Its on-board fallback logic is
  in the YAML, or you can make the HA automation trigger on `sensor.duct_temperature`.

## Safety and install notes

- **FAN- is not ground.** The fans' black wires sit at about 5 V minus the fan
  voltage. Never tie a fan's black wire to GND, the metal duct or the Pico.
- Keep the PCB and charger outside the duct, in the wall cavity or a small box
  next to the boot. Only the fan leads (and the probe) go into the airstream. Use
  plenum-rated cable if your local code requires it for runs inside the duct.
- Keep fans away from electric heat strips. With a heat pump or electric
  furnace, mount the fans at the register end only.
- Mount fans on foam or rubber grommets, seal the frame with foam
  weatherstrip, and have the fans blow into the room.
- If Wi-Fi or HA is down, the fans stay off (or run from the duct probe if it's
  fitted). A Pico crash or unplugged charger also means fans off.

## Still open

- **Vent width and depth**: needed for the optional 3D-printed fan frame
  (`frame.scad`).
- **Thermostat model**: to confirm it exposes `hvac_action` through HomeKit.
