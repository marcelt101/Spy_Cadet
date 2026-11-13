# Varactor half-bridge gain cell: v3 (bootstrapped bias servo)
> **Folder contents:**
> - `varactor_halfbridge.kicad_pro` / `.kicad_sch`: the current v3 design (open in KiCad 7 or 8).
> - `varactor.pretty/` + `fp-lib-table`: project footprints with datasheet-correct varactor pinouts.
> - `BOM.csv`, `varactor_halfbridge.net`, `varactor_halfbridge.pdf`: exports.
> - `draw.py` / `check.py`: schematic generator and netlist checker. Running `draw.py` overwrites the .kicad_sch; `check.py` needs the v2 generator in `history/` to rebuild its reference netlist.
> - `sim/`: behavioural models (bias servo, gain cell) and listening-test WAVs.
> - `history/`: v1 (full bridge), v2 (half-bridge) and v2.1 (wired) project zips.


Electrically this is v2, redrawn by hand. Every part is wired, net labels are used only where a signal travels between blocks, and every named net describes its purpose.
Connectivity is checked automatically against the verified v2 netlist plus the v3 additions: 57 of 57 nets match. The only unconnected pins are the intentional no-connects.

## New in v3: block 9, bias servo
The plain resistor bias feed in v2.1 forced a choice between fast gain control and clean bass (0.2–0.5% THD at 50–200 Hz with 10 MΩ).
v3 removes that trade-off with a bootstrapped feed and a signal-free replica of the varactor pair.

**How it works**
- **U16A (OPA2140)** senses VAR_BIAS_NODE (BIAS_SENSE). Its output also drives the guard ring around that node.
- **The replica:** D3/D4 (matched to D1/D2) are fed from VAR_BIAS_CMD through RV5 + R35. U16B senses them (REP_SENSE).
- **U17 (INA128, G = 1):** BIAS_ERR = BIAS_SENSE − REP_SENSE. This is the signal-induced wander of the bias node.
- **C41/R34/R33:** 1 Hz high-pass with ×0.99 attenuation (ERR_HP).
- **U18 (INA128, G = 1, REF = VAR_BIAS_CMD):** VAR_BIAS_DRIVE = VAR_BIAS_CMD + 0.99·ERR_HP. It drives RB1 (3.3 MΩ) into VAR_BIAS_NODE.

**Simulated results** (2 Vrms input, worst case over 0/−12/−25 dB; includes 1 pF node capacitance, 0.2%/0.1% replica match, 0.02% INA REF error, leakage, bias current and resistor noise):

| | THD 50 Hz | THD 200 Hz | THD 1 kHz | 20 dB attack / release (90%) | Settle to 0.1 dB |
|---|---|---|---|---|---|
| v2.1, 10 MΩ plain feed | 0.50% | 0.23% | 0.08% | 1.95 / 1.91 ms | 3.5 ms |
| **v3, bias servo** | **0.033%** | **0.041%** | **0.042%** | **0.78 / 0.74 ms** | **1.0–1.5 ms** |

**Design rules learned in simulation (don't change these without re-simulating)**
- **The command must reach the main node and the replica with exactly matched gain.** That's why VAR_BIAS_CMD goes to U18's REF pin (unity by the INA's internal trimmed resistors) and directly to the replica. A 0.1% gain difference in that path produces 0.4 dB gain errors lasting 50–100 ms after every move. A 0.05% REF error starts to show; 0.02% is fine.
- **Loop gain must stay below 1.** R34/R33 set ×0.99. At 1.0 or above, the bias node runs away slowly.
- **Feeding the replica from VAR_BIAS_DRIVE** (shared drive) cancels the bootstrap: don't do it.
- **Keep the node's stray capacitance low** (target about 1 pF, guarded). It sets the distortion floor: 5 pF → 0.067%, 1 pF → 0.042%.
- **Expect about 1 s of settling at power-up** (the 1 Hz high-pass).

**Trimming RV5**
1. No audio.
2. Drive CV with a slow square wave (0.5 Hz, about 1 V).
3. Watch TP11 (BIAS_ERR) and adjust RV5 until the step-shaped transients disappear.

**Not yet modelled:** the op-amps in the bootstrap path were treated as instantaneous. How a real 11 MHz part tracks the 100 kHz carrier component on the bias node is the first thing to check on the bench.

## Changes from v2 (kept in v3)
- **Varactors D1, D2:** onsemi **MMBV2109LT1G** (SOT-23), replacing the obsolete MV2109 (TO-92). The **LV2209** (TO-92, same specification) is a through-hole alternative.
- **Varactor footprints corrected.** KiCad's varactor symbol has pin 1 = cathode, but onsemi packages have pin 1 = anode. The previous footprints would have mounted the diodes backwards. The project library `varactor.pretty` holds renumbered footprints:
  - `Varactor_SOT-23_A1-NC2-K3`: SOT-23 style 8 (1 = anode, 2 = no connect, 3 = cathode)
  - `Varactor_TO-92-2_A1-K2`: TO-92 style 1 (1 = anode, 2 = cathode)
- **Bias feed:** JP2/RB2 are removed in v3. RB1 = 3.3 MΩ from VAR_BIAS_DRIVE.
- **Connector pinouts:**
  - J1: pin 3 = +15 V, pin 2 = GND, pin 1 = -15 V.
  - J2 (audio in): pin 2 = signal, pin 1 = GND.
  - J3 (audio out): pin 1 = signal, pin 2 = GND.
  - J4 (CV in): pin 1 = CV, pin 2 = GND.

## Sheet layout (A1)
- **Top row (signal path, left to right):**
  - 1 Input
  - 3 Modulator
  - 4 Half-bridge + charge amp
  - 5 Demodulator, hold, filter, output
- **Middle row:** 2 Timing, 6 Control, 9 Bias servo
- **Bottom row:** 7 Power, 8 IC supply pins + decoupling

## Net glossary
| Net | Purpose |
|---|---|
| AUDIO_IN / AUDIO_OUT | Cell input and output |
| IN_HALF_NEG / IN_HALF_POS | -x/2 and +x/2 from the input phase splitter |
| CARRIER_102K | 102.4 kHz carrier clock: drives the modulator switches U7 and U8 and the demodulator switch U9 |
| CHOP_REF | Chopped signal feeding the fixed capacitor C40 + CT3 |
| CHOP_VAR | Chopped signal feeding the varactor pair D1 + D2 (opposite phase to CHOP_REF) |
| VAR_BIAS_NODE | Floating centre (cathodes) of the varactor pair; high impedance |
| VAR_BIAS_CMD | Bias command from the control block; feeds the replica directly and U18's REF pin |
| VAR_BIAS_DRIVE | Bootstrapped bias drive (U18 output) into RB1 |
| BIAS_SENSE / REP_SENSE | Buffered main and replica bias-node voltages (BIAS_SENSE also drives the guard ring) |
| REP_BIAS_NODE | Replica varactor pair's bias node |
| BIAS_ERR / ERR_HP | Main minus replica, and its 1 Hz high-passed, ×0.99 version |
| CHG_AMP_SUM | Charge amplifier summing node (inverting input of U2A); high impedance |
| CHG_AMP_OUT / CHG_AMP_OUT_INV | Charge amplifier output and its inverted copy |
| DEMOD_OUT | Output of the synchronous demodulator (U9) |
| HOLD_CAP / HOLD_BUF | Gated hold capacitor, and its buffered version |
| LPF1_OUT / LPF_OUT | Output of the first filter stage / output of the full 30 kHz filter |
| MAKEUP_OUT | Output of the makeup gain stage |
| CLK_3M2768, CNT_Q0..Q3 | Master clock and counter phase bits |
| HOLD_GATE / HOLD_GATE_N | Hold window (counts 8–14 of each half-period) and its inverse |
| HOLD_SW_CTRL | Hold switch control, selected by JP3 |
| REF_5V | 5 V reference (U15) |
| VB_OFFSET | Bias offset set by RV3 (VAR_BIAS_CMD = 1.5 V at zero CV) |
| GAIN_CV / GAIN_CV_EXT / GAIN_CV_MAN | Selected gain control voltage / from J4 / from the manual pot RV2 |

## Opening in KiCad
Open `varactor_halfbridge.kicad_pro` in KiCad 7 or 8. The project footprint library is registered in `fp-lib-table`.
Run ERC once in the GUI. KiCad 7's command line cannot run ERC, so connectivity was verified through the exported netlist instead.

Construction and bring-up notes are unchanged from v2; see the v2 README.
