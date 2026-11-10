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

The schematics are generated from Python netlist descriptions in `gen/`:

- Parts are grouped into titled, dashed blocks by function.
- Every pin is connected by a **net label**, not a drawn wire.

This is electrically complete and unambiguous, but it reads like a netlist rather than a hand-drawn circuit diagram. You can redraw any block with wires in KiCad. Keep the net names and the PCB update will still match.

## Verification (`gen/build_all.py`)

The script:

1. Regenerates all four schematics.
2. Has `kicad-cli` (KiCad's own parser) export each netlist, then checks that:
   - every net connects exactly the intended pins
   - every part has a footprint that exists in the KiCad library
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
| psu J3 (XH-2) | poweramp J4 | AC sense (one 20 VAC winding) |
| preamp J15 (XH-3) | poweramp J2 | SUB, GND, SUB_INV (twisted, or shielded 2-core) |
| phones jack NC switch | poweramp J5 | Opens when phones are plugged in, which mutes the speaker (fit a jumper if unused) |
| hvoa_module J1 (header) | preamp J20 (A1), J21 (A2) | +40 V, GND, −40 V, OUT, IN−, IN+ |

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
