#!/usr/bin/env python3
"""ISO9660-Lister und -Extraktor für die Original-CD von "Mäusejagd im Grandhotel".

Nur Python-Standardbibliothek. Liest das ISO ausschließlich, schreibt nie hinein.

Aufruf:
    py -I tools/iso_extract.py list ISO
    py -I tools/iso_extract.py extract ISO ZIEL [--profile game|all] [--force]

Profile:
    game  Alle Dateien im Wurzelverzeichnis plus die Spielordner (GAME_DIRS).
          Beilagen-Ordner der CD (Acrobat, IE5, Netscape, ...) werden ausgelassen.
    all   Alles.
"""
import argparse
import os
import struct
import sys

SECTOR = 2048

# Unterordner, die zum Spiel gehören (Wurzeldateien sind im Profil "game" immer dabei).
GAME_DIRS = {
    'SOUNDS', 'MUSIC', 'MUSIC8', 'SOLOS', 'SOLOS8', 'STARTSND', 'ENDSOUNG',
    'GERHELP', 'GERVIDEO', 'BILDER',
    # Englische CD ("The Great Green Mouse Disaster")
    'ENDSOUND', 'ENGHELP', 'ENGVIDEO',
}


class IsoEntry:
    __slots__ = ('path', 'size', 'lba', 'is_dir')

    def __init__(self, path, size, lba, is_dir):
        self.path, self.size, self.lba, self.is_dir = path, size, lba, is_dir


def read_tree(f):
    """Liefert alle Einträge des ISO9660-Dateisystems (Pfade ohne führenden '/', mit '/' getrennt)."""
    f.seek(16 * SECTOR)
    pvd = f.read(SECTOR)
    if pvd[0] != 1 or pvd[1:6] != b'CD001':
        raise ValueError('Kein ISO9660 Primary Volume Descriptor in Sektor 16')
    root = pvd[156:156 + 34]
    entries = []
    seen = set()

    def walk(lba, size, prefix):
        if lba in seen:  # Schutz vor Schleifen in kaputten Images
            return
        seen.add(lba)
        f.seek(lba * SECTOR)
        data = f.read(size)
        pos = 0
        while pos < len(data):
            ln = data[pos]
            if ln == 0:  # Rest des Sektors ist leer
                pos = (pos // SECTOR + 1) * SECTOR
                continue
            rec = data[pos:pos + ln]
            pos += ln
            ext_lba = struct.unpack_from('<I', rec, 2)[0]
            ext_size = struct.unpack_from('<I', rec, 10)[0]
            flags = rec[25]
            raw = rec[33:33 + rec[32]]
            if raw in (b'\x00', b'\x01'):  # "." und ".."
                continue
            name = raw.decode('latin-1').split(';')[0].rstrip('.')
            if not name or name in ('.', '..') or '/' in name or '\\' in name:
                raise ValueError(f'Ungültiger Dateiname im ISO: {raw!r}')
            path = f'{prefix}{name}'
            if flags & 2:
                entries.append(IsoEntry(path, 0, ext_lba, True))
                walk(ext_lba, ext_size, path + '/')
            else:
                entries.append(IsoEntry(path, ext_size, ext_lba, False))

    walk(struct.unpack_from('<I', root, 2)[0], struct.unpack_from('<I', root, 10)[0], '')
    return entries


def in_profile(entry, profile):
    if profile == 'all':
        return True
    parts = entry.path.split('/')
    return len(parts) == 1 or parts[0] in GAME_DIRS


def cmd_list(args):
    with open(args.iso, 'rb') as f:
        for e in read_tree(f):
            print(f'{e.size:>12} {e.lba:>8} {e.path}{"/" if e.is_dir else ""}')


def cmd_extract(args):
    dest = os.path.abspath(args.dest)
    with open(args.iso, 'rb') as f:
        entries = [e for e in read_tree(f) if in_profile(e, args.profile)]
        files = [e for e in entries if not e.is_dir]
        total = sum(e.size for e in files)
        print(f'{len(files)} Dateien, {total / 1e6:.1f} MB -> {dest}')
        written = skipped = 0
        for e in files:
            target = os.path.abspath(os.path.join(dest, *e.path.split('/')))
            if os.path.commonpath([dest, target]) != dest:
                raise ValueError(f'Pfad verlässt das Zielverzeichnis: {e.path}')
            if not args.force and os.path.isfile(target) and os.path.getsize(target) == e.size:
                skipped += 1
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            f.seek(e.lba * SECTOR)
            remaining = e.size
            with open(target, 'wb') as out:
                while remaining:
                    chunk = f.read(min(remaining, 1 << 20))
                    if not chunk:
                        raise IOError(f'ISO endet vorzeitig bei {e.path}')
                    out.write(chunk)
                    remaining -= len(chunk)
            written += 1

    # Prüfung: jede Datei vorhanden und gleich groß
    bad = []
    for e in files:
        target = os.path.join(dest, *e.path.split('/'))
        if not os.path.isfile(target) or os.path.getsize(target) != e.size:
            bad.append(e.path)
    exts = {}
    for e in files:
        ext = os.path.splitext(e.path)[1].upper()
        exts[ext] = exts.get(ext, 0) + 1
    print(f'geschrieben: {written}, übersprungen (schon vorhanden): {skipped}')
    print('Dateitypen: ' + ', '.join(f'{k or "(ohne)"}={v}' for k, v in sorted(exts.items())))
    if bad:
        print(f'FEHLER: {len(bad)} Dateien fehlen oder haben falsche Größe:', *bad[:20], sep='\n  ')
        sys.exit(1)
    print('Prüfung ok: alle Dateien vorhanden, Größen stimmen.')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('list', help='Inhalt des ISO auflisten')
    p.add_argument('iso')
    p.set_defaults(func=cmd_list)
    p = sub.add_parser('extract', help='Dateien extrahieren')
    p.add_argument('iso')
    p.add_argument('dest')
    p.add_argument('--profile', choices=('game', 'all'), default='game')
    p.add_argument('--force', action='store_true', help='vorhandene Dateien überschreiben')
    p.set_defaults(func=cmd_extract)
    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
