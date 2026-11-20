# Wiring

## Circuit (what's on the PCB)

```
 USB-C charger ══ USB-C→micro-USB cable ══▶ Pico W micro-USB port

 +5V  (Pico pin 40 VBUS) ──┬──────────┬───────────────────┬───────────────┬────────────┐
                           │          │                   │               │            │
                       C1 100µF+  C2 10µF        fan red (J1–J3 pin 2)  C3 100µF+   D1 SS14
                           │          │          3 fans in parallel       │       (stripe/cathode
                          GND        GND         fan black (pin 1)        │         at the top)
                                                          │               │            │
                                                          └──── FAN- ─────┘            │
                                                                │                      │
                                                            L1 100µH                   │
                                                                │                      │
                                                                └──────── SW ──────────┘
                                                                           │
                                                                     Q1 AO3400A drain
 GP15 (Pico pin 20) ──[R1 100Ω]──┬──────────────────────────────▶ Q1 gate
                                 │                               Q1 source
                             [R2 10k]                                      │
                                GND                                       GND

 Optional duct probe:  3V3 (Pico pin 36) ──[R3 4.7k]──┬── GP16 (Pico pin 21)
                                                      └── J4 pin 2 (DQ);  J4 pin 3 = 3V3,  J4 pin 1 = GND
```

How it works: Q1 switches at 40 kHz. While it's on, current ramps up through the
fans' C3/L1 path. While it's off, L1 keeps the current flowing back to +5V
through D1. C3 smooths the result, so the fans see steady DC ≈ duty × 5 V. That
is a buck converter with the switch on the low side.

## Connectors

**Fan headers J1–J3** (2.54 mm, keyed, pin 1 marked with a square pad):

| Pin | Net | Fan wire |
|---|---|---|
| 1 | FAN- | black |
| 2 | +5V | red |
| 3 | — (not connected) | yellow/blue tach, if present |

- 2-wire fans with a 2-pin 2.54 mm plug go on pins 1–2.
- Fans with a JST-PH (2.0 mm) plug or bare leads: crimp a 2.54 mm
  KF2510/Dupont housing, or cut and solder an extension.
- **FAN- is not ground**: don't connect it to the duct, the Pico or GND.

**J4, DS18B20 probe (optional)**: 1 = GND (black), 2 = DQ (yellow), 3 = 3V3 (red).

**Power**: only the Pico's own micro-USB port. Use a charger of 5 V, ≥ 1.5 A.
Fan current flows through the Pico's VBUS pin, which is fine at ≤ 0.5 A.
Don't also power the board from your PC while the charger is plugged in. For
flashing, unplug the charger and use the PC.

## In the wall

```
        room                               wall cavity / box
  ┌──────────────┐ grille
  │ ▓ fan ▓ fan ▓ fan ▓ │◀── blows into room
  └──────┬───────┘
         │ 3 fan leads (+ probe lead, optional), through a grommet in the boot
         ▼
   ┌──────────────┐        USB-C charger in a nearby outlet
   │ carrier PCB  │◀═══════ USB cable
   │  + Pico W    │
   └──────────────┘   keep the Pico W antenna end (opposite the USB) away
                      from the metal duct for good Wi-Fi
```
