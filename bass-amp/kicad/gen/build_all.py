"""Regenerate the four KiCad schematics (hand-placed, wired drawings) and verify them.

board_*.py  : the netlist of each board (parts, values, footprints, connections)
draw_*.py   : where each part sits on the sheet; kdraw.py draws the wires
verify.py   : exports each schematic's netlist with kicad-cli and checks it
              against board_*.py, and the HVOA module against ../../sim/hvoa.sub
Run from this directory:  python3 build_all.py
"""
import subprocess, os
import kdraw, verify
import board_hvoa, board_preamp, board_poweramp, board_psu
import draw_hvoa, draw_preamp, draw_poweramp, draw_psu
BOARDS = [(board_hvoa, draw_hvoa, '../hvoa_module/hvoa_module.kicad_sch'),
          (board_preamp, draw_preamp, '../preamp/preamp.kicad_sch'),
          (board_poweramp, draw_poweramp, '../poweramp/poweramp.kicad_sch'),
          (board_psu, draw_psu, '../psu/psu.kicad_sch')]
kdraw.write_local_lib()
ok = True
for netlist, drawing, path in BOARDS:
    for line in drawing.build().write(path):
        print('  label instead of wire:', line)
    ok &= verify.check_against_sheet(netlist.build(), path)
    subprocess.run(['kicad-cli', 'sch', 'export', 'pdf', '-o', os.path.splitext(path)[0] + '.pdf', path], capture_output=True)
ok &= verify.check_hvoa('../hvoa_module/hvoa_module.kicad_sch', '../../sim/hvoa.sub')
raise SystemExit(0 if ok else 1)
