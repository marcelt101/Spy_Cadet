tran 10n 12m 0 20n
let imotor = i(l.x1.lm)+i(l.x2.lm)+i(l.x3.lm)
meas tran imotor_avg avg imotor from=8m to=12m
meas tran vsys_max max v(vsys) from=8m to=12m
meas tran vbus_max max v(vbus) from=8m to=12m
meas tran vbus_min min v(vbus) from=8m to=12m
let vfan = v(vbus)-v(fanm)
meas tran vfan_avg avg vfan from=8m to=12m
meas tran vfan_min min vfan from=8m to=12m
meas tran vfan_max max vfan from=8m to=12m
meas tran il_pk max i(l1) from=8m to=12m
meas tran vdrain_max max v(drain) from=8m to=12m
meas tran ifet_pk max i(Vsense) from=8m to=12m
meas tran iusb_avg avg i(Vusb) from=8m to=12m
meas tran iusb_pk min i(Vusb) from=8m to=12m
let pfet = v(drain)*i(Vsense)
meas tran pfet_avg avg pfet from=8m to=12m
wrdata wave.dat v(g) v(drain) v(vbus) v(vsys) i(Vsense) imotor vfan i(l1)
quit
