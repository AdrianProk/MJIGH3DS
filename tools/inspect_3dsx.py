"""Prüft eine .3dsx-Datei des Ports: Aufbau, SMDH, RomFS-Inhalt und Spieldaten.

Aufruf (Regel 4: Daten nur als Pfad-Argument, Start mit py -I):

    py -I tools/inspect_3dsx.py dist/3ds/mausjagd.3dsx docs/inventory.md [--allow diag.txt]

Geprüft wird:
- 3DSX-Kopf (Magic, Segmentgrößen) und erweiterter Kopf (SMDH, RomFS), alle Bereiche
  innerhalb der Datei;
- SMDH: Magic und Titel;
- RomFS: Verzeichnisbaum, jede Datei innerhalb der RomFS;
- alle Dateien unter game/ gegen Größe und SHA-1 aus docs/inventory.md (Status "nötig"),
  fehlende und zusätzliche Dateien;
- Dateien außerhalb von game/, die nicht zu ScummVM gehören (z. B. eine vergessene diag.txt).

Exit-Code 0, wenn alles stimmt, sonst 1.
"""
import argparse
import hashlib
import re
import struct
import sys

# Dateien, die ScummVM selbst in die RomFS legt (Themes, Engine-Daten, Tastatur)
SCUMMVM_FILES = re.compile(r'^[^/]+\.(zip|dat)$')
INVENTORY_ROW = re.compile(r'^\| `(?P<path>[^`]+)` \| (?P<size>\d+) \| `(?P<sha1>[0-9a-f]{40})` '
                           r'\| (?P<cat>[^|]+?) \| (?P<status>[^|]+?) \|')
NONE = 0xFFFFFFFF


class Problem(Exception):
    pass


def read_inventory(path):
    files = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            m = INVENTORY_ROW.match(line)
            if m and m['status'].strip() == 'nötig':
                files[m['path'].upper()] = (int(m['size']), m['sha1'])
    return files


def check_range(name, offset, size, total):
    if offset < 0 or size < 0 or offset + size > total:
        raise Problem(f'{name} liegt außerhalb der Datei: Offset {offset}, Größe {size}, Datei {total}')


def parse_header(f, total):
    head = f.read(32)
    magic, header_size, reloc_size, version, flags, code, rodata, data, bss = struct.unpack('<4sHHIIIIII', head)
    if magic != b'3DSX':
        raise Problem(f'kein 3DSX (Magic {magic!r})')
    info = dict(header_size=header_size, reloc_size=reloc_size, version=version, flags=flags,
                code=code, rodata=rodata, data=data, bss=bss)
    if header_size >= 44:
        smdh_off, smdh_size, fs_off = struct.unpack('<III', f.read(12))
        check_range('SMDH', smdh_off, smdh_size, total)
        info.update(smdh_off=smdh_off, smdh_size=smdh_size, fs_off=fs_off)
    return info


def parse_smdh(f, offset):
    f.seek(offset)
    smdh = f.read(0x36C0)
    if smdh[:4] != b'SMDH':
        raise Problem('SMDH ohne Magic')
    titles = []
    for lang in range(16):
        base = 8 + lang * 0x200
        short = smdh[base:base + 0x80].decode('utf-16-le').rstrip('\0')
        titles.append(short)
    return titles


def walk_romfs(f, base, total):
    f.seek(base)
    hdr = struct.unpack('<10I', f.read(40))
    (header_size, dir_hash_off, dir_hash_size, dir_off, dir_size,
     file_hash_off, file_hash_size, file_off, file_size, data_off) = hdr
    if header_size != 0x28:
        raise Problem(f'RomFS-Kopf hat unerwartete Größe {header_size:#x}')
    for name, off, size in (('Verzeichnistabelle', dir_off, dir_size), ('Dateitabelle', file_off, file_size)):
        check_range(f'RomFS-{name}', base + off, size, total)
    f.seek(base + dir_off)
    dirs = f.read(dir_size)
    f.seek(base + file_off)
    filetab = f.read(file_size)

    def name_at(table, pos, fixed):
        length = struct.unpack_from('<I', table, pos + fixed - 4)[0]
        return table[pos + fixed:pos + fixed + length].decode('utf-16-le')

    files = []

    def visit_dir(pos, path, depth):
        if depth > 32:
            raise Problem('RomFS zu tief verschachtelt')
        parent, sibling, child_dir, child_file, _, _ = struct.unpack_from('<6I', dirs, pos)
        f_pos = child_file
        seen = 0
        while f_pos != NONE:
            parent_f, sibling_f, d_off, d_size, _, _ = struct.unpack_from('<IIQQII', filetab, f_pos)
            fname = name_at(filetab, f_pos, 32)
            check_range(f'RomFS-Datei {path}{fname}', base + data_off + d_off, d_size, total)
            files.append((path + fname, base + data_off + d_off, d_size))
            f_pos = sibling_f
            seen += 1
            if seen > 100000:
                raise Problem('RomFS-Dateiliste endet nicht')
        d_pos = child_dir
        while d_pos != NONE:
            dname = name_at(dirs, d_pos, 24)
            visit_dir(d_pos, path + dname + '/', depth + 1)
            d_pos = struct.unpack_from('<I', dirs, d_pos + 4)[0]

    visit_dir(0, '', 0)
    return files


def sha1_range(f, offset, size):
    h = hashlib.sha1()
    f.seek(offset)
    left = size
    while left:
        chunk = f.read(min(left, 1 << 20))
        if not chunk:
            raise Problem('Datei endet unerwartet')
        h.update(chunk)
        left -= len(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('file')
    ap.add_argument('inventory')
    ap.add_argument('--allow', action='append', default=[], help='zusätzlich erlaubte Datei außerhalb von game/')
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')

    problems = []
    with open(args.file, 'rb') as f:
        f.seek(0, 2)
        total = f.tell()
        f.seek(0)
        info = parse_header(f, total)
        print(f'Datei: {args.file}, {total} Bytes')
        print(f"3DSX: Kopf {info['header_size']} Bytes, Code {info['code']}, Rodata {info['rodata']}, "
              f"Data {info['data']}, BSS {info['bss']} Bytes")
        if 'smdh_off' not in info:
            raise Problem('kein erweiterter Kopf (SMDH/RomFS fehlen)')
        titles = parse_smdh(f, info['smdh_off'])
        print(f'SMDH: Titel englisch "{titles[1]}", deutsch "{titles[3]}"')
        files = walk_romfs(f, info['fs_off'], total)
        print(f'RomFS: {len(files)} Dateien, {sum(s for _, _, s in files)} Bytes')

        inventory = read_inventory(args.inventory)
        game = {p[len('game/'):].upper(): (o, s) for p, o, s in files if p.startswith('game/')}
        others = sorted(p for p, _, _ in files if not p.startswith('game/'))
        for rel, (size, sha1) in sorted(inventory.items()):
            if rel not in game:
                problems.append(f'fehlt in der RomFS: game/{rel}')
                continue
            off, actual = game[rel]
            if actual != size:
                problems.append(f'Größe falsch: game/{rel} ({actual} statt {size})')
            elif sha1_range(f, off, actual) != sha1:
                problems.append(f'SHA-1 falsch: game/{rel}')
        for rel in sorted(set(game) - set(inventory)):
            problems.append(f'unerwartet in game/: {rel}')
        print(f'Spieldaten: {len(game)} Dateien, {len(inventory)} laut Inventar, alle per SHA-1 geprüft')
        unexpected = [p for p in others if not SCUMMVM_FILES.match(p) and p not in args.allow]
        print('Außerhalb von game/: ' + ', '.join(others))
        for p in unexpected:
            problems.append(f'unerwartete Datei außerhalb von game/: {p}')

    if problems:
        print('\nPROBLEME:')
        for p in problems:
            print('  - ' + p)
        return 1
    print('\nKeine Probleme gefunden.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Problem as e:
        print(f'FEHLER: {e}')
        sys.exit(1)
