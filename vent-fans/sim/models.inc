* Shared models for the vent-fan controller simulations.
* AO3400A: approximate VDMOS fit to the datasheet (Vth ~1.05 V typ,
* Rds(on) ~ 26 mOhm @ 4.5 V, ~ 32 mOhm @ 3.3 V, ~ 43 mOhm @ 2.5 V, Ciss ~ 630 pF, Qg ~ 7 nC).
.model AO3400A VDMOS(Vto=1.05 Kp=25 Rd=8m Rs=6m Rg=1.5
+ Cgs=560p Cgdmax=160p Cgdmin=25p Cjo=110p Is=2p Rb=10m
+ ksubthres=0.12 lambda=0.01)

* 1N5819 / SS14 Schottky (1 A, 40 V)
.model D1N5819 D(Is=31.7u Rs=51m N=1.373 Cjo=110p M=0.35 Vj=0.35 BV=40 IBV=1m)

* One 80 mm 5 V two-wire BLDC fan, seen from its leads. A fan is not a bare
* motor: it has a reverse-polarity diode and a small hold-up cap feeding
* the driver IC, then the coils (~0.15 A at 5 V, so ~33 ohm, ~1 mH).
.subckt FAN p n
Dint p a DFANREV
Cint a n 1u
Rm   a m 33
Lm   m n 1m
.ends FAN
.model DFANREV D(Is=1u Rs=0.2 N=1.2 Cjo=30p)
