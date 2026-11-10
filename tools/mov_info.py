"""Liest die Kopfdaten von QuickTime-Dateien (.MOV) und gibt eine Markdown-Tabelle aus.

Aufruf (Regel 4: Spieldateien nur als Pfad-Argument, Start mit py -I):

    py -I tools/mov_info.py game/*.MOV game/GERHELP/*.MOV game/GERVIDEO/*.MOV

Pro Datei und Spur: Typ, Codec, Abmessungen (tkhd und Sample-Beschreibung), Farbtiefe,
Farbtabelle (ctab-ID, eingebettet ja/nein), Anzahl der Frames, Dauer und Bildrate bzw.
Audioformat. Gelesen werden nur die Atome; die Datei wird nicht dekodiert.
"""

import os
import struct
import sys

CONTAINERS = {b'moov', b'trak', b'mdia', b'minf', b'stbl', b'edts', b'dinf'}


def atoms(f, start, end):
    """Liefert (Typ, Datenanfang, Datenende) aller Atome zwischen start und end."""
    pos = start
    while pos + 8 <= end:
        f.seek(pos)
        size, kind = struct.unpack('>I4s', f.read(8))
        header = 8
        if size == 1:
            size = struct.unpack('>Q', f.read(8))[0]
            header = 16
        elif size == 0:
            size = end - pos
        if size < header or pos + size > end:
            break
        yield kind, pos + header, pos + size
        pos += size


def find(f, start, end, path):
    """Sucht ein Atom über einen Pfad wie [b'mdia', b'minf', b'stbl']."""
    for kind, a, b in atoms(f, start, end):
        if kind == path[0]:
            if len(path) == 1:
                return a, b
            return find(f, a, b, path[1:])
    return None


def read(f, span):
    f.seek(span[0])
    return f.read(span[1] - span[0])


def track_info(f, a, b):
    info = {}
    tkhd = find(f, a, b, [b'tkhd'])
    if tkhd:
        d = read(f, tkhd)
        # Version 0: Breite/Höhe als 16.16-Festkomma am Ende
        info['tkhd'] = (struct.unpack('>I', d[-8:-4])[0] >> 16, struct.unpack('>I', d[-4:])[0] >> 16)
    mdhd = find(f, a, b, [b'mdia', b'mdhd'])
    if mdhd:
        d = read(f, mdhd)
        info['timescale'], info['duration'] = struct.unpack('>II', d[12:20])
    hdlr = find(f, a, b, [b'mdia', b'hdlr'])
    if hdlr:
        info['handler'] = read(f, hdlr)[8:12].decode('latin-1')
    stbl = [b'mdia', b'minf', b'stbl']
    stsd = find(f, a, b, stbl + [b'stsd'])
    if stsd:
        d = read(f, stsd)
        entry = d[8:]
        info['codec'] = entry[4:8].decode('latin-1')
        if info.get('handler') == 'vide':
            w, h = struct.unpack('>HH', entry[32:36])
            depth, ctab = struct.unpack('>Hh', entry[82:86])
            info['size'] = (w, h)
            info['depth'] = depth
            info['ctab'] = ctab
            # ctab-ID 0: Farbtabelle folgt in der Sample-Beschreibung, -1: Standardpalette
            info['ctab_embedded'] = ctab == 0 and struct.unpack('>I', entry[0:4])[0] > 86
        elif info.get('handler') == 'soun':
            channels, bits = struct.unpack('>HH', entry[24:28])
            rate = struct.unpack('>I', entry[32:36])[0] >> 16
            info['audio'] = f'{rate} Hz, {bits} Bit, {channels} Kanal'
    stsz = find(f, a, b, stbl + [b'stsz'])
    if stsz:
        d = read(f, stsz)
        info['samples'] = struct.unpack('>I', d[8:12])[0]
    return info


def main(paths):
    print('| Datei | Spur | Codec | tkhd | Sample | Tiefe | ctab | Frames | Dauer | fps / Audio |')
    print('|---|---|---|---|---|---:|---|---:|---:|---|')
    for path in paths:
        name = os.path.relpath(path).replace('\\', '/')
        with open(path, 'rb') as f:
            f.seek(0, 2)
            end = f.tell()
            moov = find(f, 0, end, [b'moov'])
            if not moov:
                print(f'| `{name}` | – | kein moov-Atom | | | | | | | |')
                continue
            for kind, a, b in atoms(f, *moov):
                if kind != b'trak':
                    continue
                t = track_info(f, a, b)
                seconds = t['duration'] / t['timescale'] if t.get('timescale') else 0
                handler = t.get('handler', '?')
                if handler == 'vide':
                    fps = t.get('samples', 0) / seconds if seconds else 0
                    ctab = 'Standard' if t['ctab'] == -1 else ('eingebettet' if t['ctab_embedded'] else f"ID {t['ctab']}")
                    print(f"| `{name}` | Video | {t['codec']} | {t['tkhd'][0]}×{t['tkhd'][1]} | "
                          f"{t['size'][0]}×{t['size'][1]} | {t['depth']} | {ctab} | {t.get('samples', '')} | "
                          f'{seconds:.1f} s | {fps:.1f} |')
                elif handler == 'soun':
                    print(f"| `{name}` | Audio | {t['codec']} | | | | | | {seconds:.1f} s | {t.get('audio', '')} |")
                else:
                    print(f"| `{name}` | {handler} | {t.get('codec', '')} | | | | | | {seconds:.1f} s | |")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.stdout.reconfigure(encoding='utf-8')
    main(sys.argv[1:])
