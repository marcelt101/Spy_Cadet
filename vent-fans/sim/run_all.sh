#!/bin/sh
# Runs every simulation; writes results.txt and wave_*.dat (plot with plot.py)
set -e
cd "$(dirname "$0")"
keep='^(imotor_avg|vfan_avg|vfan_min|vfan_max|vsys_max|vbus_max|vbus_min|vdrain_max|ifet_pk|il_pk|iusb_avg|iusb_pk|pfet_avg) '
{
echo "== AO3400A Rds(on) at Vgs = 2.5 / 3.3 / 4.5 V"
ngspice -b mosfet_dc.cir 2>/dev/null | grep -E '^rds'
for c in spec railcaps buck; do
  for d in 0.3 0.4 0.6 0.8 1.0; do
    sed "s/^\.param duty=[0-9.]*/.param duty=$d/" sim_$c.cir > _run.cir
    echo "== $c duty=$d"
    ngspice -b _run.cir 2>/dev/null | grep -E "$keep" | sed -E 's/ +(from|at)=.*//'
    mv wave.dat wave_${c}_$d.dat
  done
done
echo "== buck power-up, 0 -> 60 % in one step (no firmware slew limit)"
ngspice -b sim_buck_start.cir 2>/dev/null | grep -E '^(il_pk|vbus_min|vsys_min|vfan_end|vfan_pk) ' | sed -E 's/ +(from|at)=.*//'
echo "== buck power-up, 0 -> 60 % with firmware slew limit"
ngspice -b sim_buck_softstart.cir 2>/dev/null | grep -E '^(il_pk|vbus_min|vsys_min|vfan_end) ' | sed -E 's/ +(from|at)=.*//'
} > results.txt
rm -f _run.cir
cat results.txt
