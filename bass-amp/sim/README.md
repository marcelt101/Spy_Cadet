# Simulation files

All files run with ngspice (tested with ngspice-42) and Python 3 + numpy/matplotlib.

| File | What it checks |
|---|---|
| `models.lib` | BJT/diode models (2N5087, 2N5210, MPSA42, MPSA92, 1N4148, LED, zeners) |
| `hvoa.sub` | **HVOA-1** discrete ±40 V op-amp module (the authoritative netlist) |
| `t_loop.cir` | Open-loop gain / phase margin of the module (voltage-injection method). Replace `PARAMS_HERE` with a parameter set. |
| `t_final.cir` | THD of A1 (input stage, max gain) and A2 (FX return, unity) at 20 Vrms, 1 kHz / 10 kHz / 40 Hz |
| `t_thd.cir`, `t_input.cir` | Early A1 exploration (clip point, input impedance, bootstrap peaking) |
| `t_noise.cir` + `noise_eval.py` | A-weighted output noise of A1 with a passive pickup (8 k + 3 H + 300 pF cable) vs. the pickup's own thermal noise |
| `t_noise_ref.cir` | Same pickup into a noiseless amp with a conventional 1 MΩ input, for comparison |
| `t_powerup.cir` | Rails ramp up from 0 V: confirms both modules come up in the right operating point |
| `t_eq.cir`, `opamp.sub`, `mid_tune.py`, `mid_table.py` | 3-band EQ: Baxandall bass/treble + gyrator mid, and the capacitor table for the 5-way mid switch |
| `plots.py` | Regenerates `../docs/*.png` |

```sh
ngspice -b t_final.cir | grep THD
python3 noise_eval.py "params: rtail=3k rsink=10k re=1k cc=68p"
python3 mid_table.py
python3 plots.py
```

Note: ngspice's DC solver sometimes lands on a non-physical operating point for
this circuit (the bootstrapped cascode gives it more than one mathematical
solution). The testbenches use `.nodeset` to start it in the right place, and
`t_powerup.cir` shows that a real power-up settles correctly.
