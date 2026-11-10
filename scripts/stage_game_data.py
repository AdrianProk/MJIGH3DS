#!/usr/bin/env python3
"""Stellt die Spieldaten für die RomFS der 3DS-App zusammen.

Kopiert alle Dateien mit dem gewünschten Status aus ``docs/inventory.md``
(Standard: ``nötig``) aus dem Spielordner in einen Zielordner. Jede Datei wird
gegen Größe und SHA-1 aus dem Inventar geprüft. Bereits vorhandene, korrekte
Dateien werden nicht neu kopiert; Dateien, die nicht (mehr) dazugehören,
werden aus dem Zielordner entfernt.

    python3 -I scripts/stage_game_data.py GAME_DIR docs/inventory.md DEST [--status nötig ...]

Die Spieldaten werden nur als Daten gelesen und kopiert, nie ausgeführt.
Der Zielordner gehört nicht ins Repo (Urheberrecht, siehe PLAN.md §7).
"""
import argparse
import hashlib
import os
import re
import shutil
import sys

ROW = re.compile(r'^\| `(?P<path>[^`]+)` \| (?P<size>\d+) \| `(?P<sha1>[0-9a-f]{40})` '
                 r'\| (?P<cat>[^|]+?) \| (?P<status>[^|]+?) \|')


def sha1_file(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def read_inventory(path, statuses):
    entries = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            m = ROW.match(line)
            if m and m['status'].strip() in statuses:
                rel = m['path']
                if rel.startswith('/') or '..' in rel.split('/'):
                    sys.exit(f'Unsicherer Pfad im Inventar: {rel}')
                entries.append((rel, int(m['size']), m['sha1']))
    return entries


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('game_dir')
    ap.add_argument('inventory')
    ap.add_argument('dest')
    ap.add_argument('--status', nargs='+', default=['nötig'])
    a = ap.parse_args()

    entries = read_inventory(a.inventory, set(a.status))
    if not entries:
        sys.exit('Keine passenden Einträge im Inventar gefunden')

    os.makedirs(a.dest, exist_ok=True)
    copied = kept = 0
    total = 0
    wanted = set()
    for rel, size, sha1 in entries:
        src = os.path.join(a.game_dir, *rel.split('/'))
        dst = os.path.join(a.dest, *rel.split('/'))
        wanted.add(os.path.normcase(os.path.normpath(dst)))
        total += size
        if os.path.isfile(dst) and os.path.getsize(dst) == size and sha1_file(dst) == sha1:
            kept += 1
            continue
        if not os.path.isfile(src):
            sys.exit(f'Fehlt im Spielordner: {rel}')
        if os.path.getsize(src) != size or sha1_file(src) != sha1:
            sys.exit(f'Prüfsumme/Größe stimmt nicht mit dem Inventar überein: {rel}')
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        copied += 1

    removed = 0
    for root, dirs, files in os.walk(a.dest, topdown=False):
        for name in files:
            p = os.path.join(root, name)
            if os.path.normcase(os.path.normpath(p)) not in wanted:
                os.remove(p)
                removed += 1
        for name in dirs:
            p = os.path.join(root, name)
            if not os.listdir(p):
                os.rmdir(p)

    print(f'{len(entries)} Dateien ({total / 1e6:.1f} MB): {copied} kopiert, {kept} unverändert, {removed} entfernt')


if __name__ == '__main__':
    main()
