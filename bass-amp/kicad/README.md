# KiCad projects

There are four boards, each a separate KiCad project. Every symbol has a footprint from the standard KiCad library already assigned, so **Tools → Update PCB from Schematic** works straight away.

| Project | Board | Parts | Notes |
|---|---|---|---|
| `hvoa_module/` | HVOA-1 ±40 V discrete op-amp daughterboard (6-pin header) | 50 | Build **two**. Parts with values marked `x / A2: y` differ: R103, R104, R105, R106, CC1 |
| `preamp/` | Sockets for A1/A2, input and FX-return networks, 3-band EQ, FX send, master/aux, subsonic, bridge phase splitter, phones, balanced DI, PRE clip | 144 | Pots are PCB-mounted (Alpha 16 mm). Jacks and switches are panel-mounted on JST-XH headers |
| `poweramp/` | 2 × LM3886T bridged, Zobels, output coils, speaker relay (turn-on delay, AC-loss, DC-fault), mute driver, POWER clip | 97 | Screw terminals for rails and speaker |
| `psu/` | ±28 V raw (T1), discrete ±41.6 V HV regulators (T2), discrete ±14.8 V regulators | 75 | Mains wiring stays off the PCB |

Each folder also has a PDF of its schematic.

**Version:** the files are written in KiCad 7 format. KiCad 8 and 9 open them and offer to upgrade them. Symbol definitions are embedded in each schematic, so nothing depends on your library setup.

## How the schematics are drawn

The schematics are drawn the conventional way:

- Parts are placed by hand in circuit order, grouped into titled sections.
- Pins are joined with real wires, with junction dots at tees.
- Supply rails use power symbols: +15V, −15V, +28V, GND, plus custom **+40V / −40V / −28V** symbols in `lib/bassamp.kicad_sym`. Each project's `sym-lib-table` finds that library automatically.
- Net labels appear only where a signal leaves its section, for example PRE_AC going from the input stage to the EQ. They also mark the fan-out to the mid-frequency switch header (J9), which is how that kind of connector is normally drawn.

The drawings come from `gen/`:

- `board_*.py` holds each board's netlist: parts, values, footprints and connections.
- `draw_*.py` holds where each part sits.
- `kdraw.py` draws the wires with an orthogonal router that won't touch another net or run through a part body.

One connection (STB, between the subsonic filter's 56 k resistor and its switch header) uses a label pair instead of a wire. Everything else is wired.

If you move things around in KiCad, the PCB update still matches as long as the connections stay the same.

## Net names

Every net an engineer needs to follow has a name, shown on the schematic and carried into the PCB netlist. The names are kept in `gen/netnames.py`.

| Kind | Convention | Examples |
|---|---|---|
| Regulated rails | Power symbols named by voltage | `+40V` `-40V` `+28V` `-28V` `+15V` `-15V` `GND` |
| Unregulated or pre-filter supplies | Voltage plus a suffix | `+55V_RAW` `-55V_RAW` `+28V_FILT` `+40V_IN` (module side of its rail filter) |
| References | Voltage + `_REF`, or function | `+43V_REF` `+16V_REF` `VREF_TOP` `CASC_BIAS` |
| Transformer secondaries | Transformer + winding | `T1_AC1` `T1_AC2` `T2_AC1` `T2_AC2` |
| External inputs | Function | `INST_IN` `FX_RETURN` `AUX_IN_L` `AUX_IN_R` `AC_SENSE` |
| External outputs | Function, with polarity for balanced and bridged pairs | `FX_SEND` `PHONES_L/R` `LINE_OUT_HOT` `LINE_OUT_COLD` `SPK+` `SPK-` |
| Board-to-board | Function | `PA_DRIVE+` `PA_DRIVE-` (preamp → power amp) |
| Amplifier pins | Stage + `_IN+` / `_IN-` / `_OUT` | `A1_IN+` `A1_IN-` `A1_OUT` `U1_IN+` `BTL_A_OUT` |
| Signal path nodes | Function | `PRE_EQ` `TONE_SUM` `TONE_OUT` `EQ_OUT` `MIX_SUM` `MIX_OUT` `GYRATOR` |
| Panel parts on headers | Part + function | `MID_SW_A` `MID_CS1..5` `MID_CG1..5` `SUBSONIC_SW_A/B` `DI_PAD_SW` `PRE_CLIP_LED_A/K` |
| Active-low controls | KiCad overbar `~{NAME}` | `~{RLY_ON}` (low when the speaker relay is energised), `~{SPK_TRIP}` (pull low to open the relay) |

Purely local junctions, such as a resistor-to-transistor-base link, keep KiCad's automatic `Net-(R42-Pad1)` names.

## Verification (`gen/build_all.py`)

The script:

1. Redraws all four schematics.
2. Has `kicad-cli` (KiCad's own parser) export each netlist, then checks that:
   - every net connects exactly the intended pins
   - every part has a footprint that exists in the KiCad library
   - every named net appears under its name, on the right pins
3. Checks that the **HVOA module schematic has the same topology as the simulated SPICE netlist** (`../sim/hvoa.sub`), pin for pin. A deliberately mis-wired copy is caught, so the check is not vacuous.
4. Writes the PDFs.

**ERC:** KiCad 7's command line has no ERC (KiCad 8 added it). PWR_FLAGs are already placed on the rails that enter each board through connectors. Run **Inspect → Electrical Rules Checker** once in KiCad and expect it to come back clean. If it flags anything, it will most likely be about text or label placement, not connectivity.

```sh
cd gen && python3 build_all.py      # needs kicad-cli (KiCad 7+) and the kicad-symbols/footprints libraries
```

## Board-to-board wiring

| From | To | Signals |
|---|---|---|
| psu J4 (XH-3) | preamp J1 | +15 V, GND, −15 V |
| psu J6 (XH-4) | preamp J2 | +40 V, GND, GND, −40 V (a different size from J1, so the two cannot be swapped) |
| psu J2 (screw) | poweramp J1 | +28 V, GND, −28 V (heavy wire, ≥ 1 mm²) |
| psu J3 (XH-2) | poweramp J4 | T1_AC1 → AC_SENSE, GND |
| preamp J15 (XH-3) | poweramp J2 | PA_DRIVE+, GND, PA_DRIVE- (twisted, or shielded 2-core) |
| phones jack NC switch | poweramp J5 | MUTE_CTRL / MUTE_CTRL_SW: opens when phones are plugged in, which mutes the speaker (fit a jumper if unused) |
| hvoa_module J1 (header) | preamp J20 (A1), J21 (A2) | +40V_IN, GND, -40V_IN, OUT, IN-, IN+ (preamp side: +40V, GND, -40V, A1_OUT/A2_OUT, A1_IN-/A2_IN-, A1_IN+/A2_IN+) |

## Before you order PCBs, check these footprints

- **BR1 (`psu`):** generic 32 × 5.6 mm, 10/7.5 mm-pitch bridge footprint for a GBJ2506. Pin order is + ~ ~ −, using symbol `D_Bridge_+AA-`. Check the pitch against the part you actually buy.
- **Film caps:** footprints are typical MKS2/MKS4 sizes (2.2 µF/100 V = 13 × 6 mm, P10; 4.7 µF/63 V = 18 × 8 mm, P15). Body sizes vary between makers.
- **10 000 µF reservoir caps:** 30 mm snap-in, 10 mm pitch.
- **Relay K1:** Omron G5LE-1 with a 24 V coil. COM = A output, NO = speaker +.
- **TO-92 parts** (2N5087, 2N5210, MPSA42, MPSA92): all are E-B-C pinout on `TO-92_Inline`. Some vendors' 2N5087/2N5210 have been sold in C-B-E pinout; check the datasheet of the batch you buy.
- **TO-126 parts:** BD139/BD140 and MJE340/MJE350 are E-C-B.
- **LM3886T:** TO-220-11 staggered. **The tab is V−**, so insulate it from the heatsink.

## PCB layout notes

- **HVOA module:**
  - Keep the input pair (Q1/Q2) and the mirror (Q5/Q6) side by side, so each matched pair can be glued together.
  - Put D105/D106 against Q11/Q12.
  - CC1 goes right at the VAS.
- **Preamp:**
  - Separate the ±40 V area (module sockets, A1/A2 networks) from the NE5532 area.
  - Keep the mid-switch header J9 close to the gyrator. Nodes X and GP are high impedance.
- **Power amp:** keep the LM3886 decoupling at the pins (C4–C7, C14–C17). Bring each chip's pin 7, the Zobel grounds and the input grounds together in a star at the board ground entry.
- **PSU:** the star ground is the junction of C1–C4. Return each board's ground there with its own wire.
