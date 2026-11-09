#!/usr/bin/env python3
"""Schneidet die in einem Director-4-Windows-Projektor eingebetteten Filme (XFIR/MV93) als
eigenständige Dateien heraus, damit Werkzeuge wie ProjectorRays sie lesen können.

In Projektoren beziehen sich die Offsets in imap/mmap auf den Dateianfang der EXE.
Das Skript rechnet sie auf den Filmanfang um. Liest die EXE nur.

Aufruf:
    py -I tools/extract_projector_movie.py game/MAUSJAGD.EXE analysis/projector
"""
import os
import re
import struct
import sys


def extract(data, off):
    ln = struct.unpack('<I', data[off + 4:off + 8])[0]
    movie = bytearray(data[off:off + 8 + ln])
    if movie[12:16] != b'pami':
        raise ValueError('kein imap direkt nach dem Header')
    mmap_abs = struct.unpack('<I', movie[24:28])[0]
    mmap_rel = mmap_abs - off
    if movie[mmap_rel:mmap_rel + 4] != b'pamm':
        raise ValueError('mmap-Offset passt nicht')
    struct.pack_into('<I', movie, 24, mmap_rel)
    body = mmap_rel + 8
    hlen, elen = struct.unpack('<HH', movie[body:body + 4])
    used = struct.unpack('<i', movie[body + 8:body + 12])[0]
    fixed = 0
    for i in range(used):
        e = body + hlen + i * elen
        tag = bytes(movie[e:e + 4])
        coff = struct.unpack('<I', movie[e + 8:e + 12])[0]
        if tag == b'eerf' or tag == b'knuj':  # free/junk: Offset bedeutungslos
            continue
        rel = coff - off
        if 0 <= rel < len(movie) and movie[rel:rel + 4] == tag:
            struct.pack_into('<I', movie, e + 8, rel)
            fixed += 1
        elif not (0 <= coff < len(movie) and movie[coff:coff + 4] == tag):
            raise ValueError(f'Chunk {tag[::-1]!r} #{i}: Offset {coff} passt weder absolut noch relativ')
    return bytes(movie), fixed


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    exe, out_dir = sys.argv[1], sys.argv[2]
    data = open(exe, 'rb').read()
    os.makedirs(out_dir, exist_ok=True)
    n = 0
    for m in re.finditer(rb'XFIR', data):
        off = m.start()
        if data[off + 8:off + 12] != b'39VM':
            continue
        movie, fixed = extract(data, off)
        # Dateiname aus dem Pfad direkt vor dem Film (z. B. "C:\GGMD\GGMDSTRT.DIR"), sonst Offset
        before = data[max(0, off - 300):off]
        names = re.findall(rb'([A-Za-z0-9_]{1,8}\.DIR)', before, re.I)
        name = names[-1].decode() if names else f'movie_{off}.DIR'
        target = os.path.join(out_dir, name)
        with open(target, 'wb') as f:
            f.write(movie)
        n += 1
        print(f'{name}: {len(movie)} Bytes ab Offset {off}, {fixed} Chunk-Offsets umgerechnet -> {target}')
    if not n:
        sys.exit('kein eingebetteter Film gefunden')


if __name__ == '__main__':
    main()
