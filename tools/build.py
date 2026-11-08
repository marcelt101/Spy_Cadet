#!/usr/bin/env python3
"""Build the itch.io upload from game/ (adapted from Crater Crew's build script).

    python3 tools/build.py                                    # team games use PeerJS
    python3 tools/build.py --relay https://spy-cadet.example.org   # team games use that classroom server

Copies game/ to dist/spy-cadet/ and zips it to dist/spy-cadet-<build>.zip, with index.html at the top of the zip as
itch.io expects. The build name is the current git tag or commit. Runs the tests first and stops if any fail.
"""
import os, shutil, subprocess, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, DIST = os.path.join(ROOT, 'game'), os.path.join(ROOT, 'dist')

def build_name():
    try:
        return subprocess.check_output(['git', 'describe', '--tags', '--always', '--dirty'], cwd=ROOT, text=True).strip()
    except Exception:
        return 'local'

if __name__ == '__main__':
    relay = sys.argv[sys.argv.index('--relay') + 1].rstrip('/') if '--relay' in sys.argv else ''
    for t in ('run-tests.js', 'relay-test.js'):
        if subprocess.call(['node', os.path.join(ROOT, 'tests', t)]) != 0:
            sys.exit('tests failed: no build made')
    name = build_name()
    out = os.path.join(DIST, 'spy-cadet')
    shutil.rmtree(out, ignore_errors=True)
    shutil.copytree(SRC, out)
    if relay:
        with open(os.path.join(out, 'js', 'config.js'), 'a') as f:
            f.write(f"window.SC.RELAY_URL = {relay!r};\n")
    os.makedirs(DIST, exist_ok=True)
    zpath = os.path.join(DIST, f'spy-cadet-{name}.zip')
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for base, _, files in os.walk(out):
            for f in sorted(files):
                full = os.path.join(base, f)
                z.write(full, os.path.relpath(full, out))
    print(f'{os.path.getsize(zpath) // 1024} KB  {os.path.relpath(zpath, ROOT)}')
