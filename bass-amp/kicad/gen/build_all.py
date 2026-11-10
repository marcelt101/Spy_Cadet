"""Regenerate all four KiCad projects and verify them.
Run from this directory:  python3 build_all.py"""
import board_hvoa, board_preamp, board_poweramp, board_psu, verify
BOARDS = [(board_hvoa, '../hvoa_module/hvoa_module.kicad_sch', 5, 2),
          (board_preamp, '../preamp/preamp.kicad_sch', 6, 3),
          (board_poweramp, '../poweramp/poweramp.kicad_sch', 6, 3),
          (board_psu, '../psu/psu.kicad_sch', 6, 2)]
ok = True
for mod, path, cols, bcols in BOARDS:
    sheet = mod.build()
    sheet.write(path, cols=cols, blockcols=bcols)
    ok &= verify.check_against_sheet(sheet, path)
ok &= verify.check_hvoa('../hvoa_module/hvoa_module.kicad_sch', '../../sim/hvoa.sub')
import subprocess, os
for _, path, _, _ in BOARDS:
    subprocess.run(['kicad-cli', 'sch', 'export', 'pdf', '-o', os.path.splitext(path)[0] + '.pdf', path], capture_output=True)
raise SystemExit(0 if ok else 1)
