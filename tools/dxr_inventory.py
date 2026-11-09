#!/usr/bin/env python3
"""Inventar der Director-4-Filme: Chunks, Cast-Member (Typ, Name, verknüpfte Datei), Skripte.

Liest RIFX-Filme (.DXR/.DIR, big-endian) und in Projektoren eingebettete XFIR-Filme (.EXE).
Nur Python-Standardbibliothek; liest ausschließlich.

Aufruf:
    py -I tools/dxr_inventory.py game docs/dxr-inventory.md [analysis/cast]

    game             Ordner mit den Spieldaten
    docs/...md       Zusammenfassung pro Film (nur Zahlen, kommt ins Repo)
    analysis/cast    optional: pro Film eine Liste aller Cast-Member mit Namen (lokal, ignoriert)
"""
import os
import re
import struct
import sys

CAST_TYPES = {
    1: 'bitmap', 2: 'filmloop', 3: 'text', 4: 'palette', 5: 'picture', 6: 'sound',
    7: 'button', 8: 'shape', 9: 'movie', 10: 'digitalvideo', 11: 'script', 12: 'rte',
}


class Movie:
    def __init__(self, name, data, offset):
        self.name = name
        self.data = data            # ganze Datei
        self.offset = offset        # Start des RIFX/XFIR in der Datei
        self.le = data[offset:offset + 4] == b'XFIR'
        self.fmt = '<' if self.le else '>'
        self.chunks = []            # (tag, length, absolute offset of chunk header)
        self._read_mmap()

    def _u32(self, pos):
        return struct.unpack(self.fmt + 'I', self.data[pos:pos + 4])[0]

    def _read_mmap(self):
        d, off = self.data, self.offset
        # imap direkt nach dem 12-Byte-Header: zeigt auf die mmap
        imap_tag = d[off + 12:off + 16]
        if imap_tag[::-1 if self.le else 1] != b'imap':
            raise ValueError(f'{self.name}: kein imap')
        mmap_off = self._u32(off + 12 + 8 + 4)
        # mmap-Offset ist relativ zum Dateianfang (Projektor) oder zum Filmanfang (eigene Datei)
        for base in (0, off):
            pos = base + mmap_off
            if d[pos:pos + 4][::-1 if self.le else 1] == b'mmap':
                break
        else:
            raise ValueError(f'{self.name}: mmap nicht gefunden')
        self.base = base
        body = pos + 8
        hlen, elen = struct.unpack(self.fmt + 'HH', d[body:body + 4])
        used = struct.unpack(self.fmt + 'i', d[body + 8:body + 12])[0]
        for i in range(used):
            e = body + hlen + i * elen
            tag = d[e:e + 4][::-1 if self.le else 1].decode('latin-1')
            ln, coff = struct.unpack(self.fmt + 'II', d[e + 4:e + 12])
            self.chunks.append((tag, ln, base + coff))

    def chunk_data(self, idx):
        tag, ln, pos = self.chunks[idx]
        return self.data[pos + 8:pos + 8 + ln]

    def first(self, tag):
        for i, c in enumerate(self.chunks):
            if c[0] == tag:
                return i
        return None


def pascal(b):
    return b[1:1 + b[0]].decode('latin-1') if b else ''


def info_entries(info):
    """Director-4-Cast-Info: Header mit Offset, dann Liste von Strings."""
    if len(info) < 22:
        return []
    hdr = struct.unpack('>I', info[0:4])[0]
    if hdr + 2 > len(info):
        return []
    count = struct.unpack('>H', info[hdr:hdr + 2])[0] + 1
    offs = [struct.unpack('>I', info[hdr + 2 + 4 * i: hdr + 6 + 4 * i])[0] for i in range(count)]
    start = hdr + 2 + 4 * count
    out = []
    for i in range(count - 1):
        out.append(info[start + offs[i]: start + offs[i + 1]])
    return out


def read_cast(m):
    """Liefert [(Nummer, Typ, Name, Datei)] in Cast-Reihenfolge."""
    cfg = m.first('VWCF')
    min_member = 1
    if cfg is not None:
        c = m.chunk_data(cfg)
        min_member = struct.unpack('>H', c[12:14])[0] or 1
    cas = m.first('CAS*')
    if cas is None:
        return []
    ids = m.chunk_data(cas)
    members = []
    for i in range(len(ids) // 4):
        cid = struct.unpack('>I', ids[4 * i:4 * i + 4])[0]
        if cid == 0 or cid >= len(m.chunks) or m.chunks[cid][0] != 'CASt':
            continue
        c = m.chunk_data(cid)
        if len(c) < 7:
            continue
        data_size = struct.unpack('>H', c[0:2])[0]
        info_size = struct.unpack('>I', c[2:6])[0]
        ctype = c[6]
        info = c[6 + data_size: 6 + data_size + info_size]
        entries = info_entries(info)
        name = pascal(entries[1]) if len(entries) > 1 else ''
        fdir = pascal(entries[2]) if len(entries) > 2 else ''
        fname = pascal(entries[3]) if len(entries) > 3 else ''
        linked = (fdir + (':' if fdir and not fdir.endswith((':', '\\')) else '') + fname) if fname else ''
        size = ''
        if ctype == 1 and data_size >= 12:
            # Bitmap (D4): Typ(1) Flags(1) Pitch(2), dann initialRect top/left/bottom/right (je int16)
            top, left, bottom, right = struct.unpack('>hhhh', c[10:18])
            size = f'{right - left}x{bottom - top}'
        members.append((min_member + i, CAST_TYPES.get(ctype, f'typ{ctype}'), name, linked, size))
    return members


def find_movies(path):
    data = open(path, 'rb').read()
    name = os.path.basename(path)
    out = []
    if data[:4] == b'RIFX' and data[8:12] == b'MV93':
        out.append(Movie(name, data, 0))
    elif name.upper().endswith('.EXE'):
        for mt in re.finditer(rb'XFIR', data):
            off = mt.start()
            if data[off + 8:off + 12] == b'39VM':
                try:
                    out.append(Movie(f'{name} (eingebettet @{off})', data, off))
                except ValueError:
                    pass
    return out


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    root, out_md = sys.argv[1], sys.argv[2]
    cast_dir = sys.argv[3] if len(sys.argv) == 4 else None
    files = sorted(f for f in os.listdir(root) if f.upper().endswith(('.DXR', '.DIR')) or f.upper() == 'MAUSJAGD.EXE')
    rows = []
    for f in files:
        for m in find_movies(os.path.join(root, f)):
            counts = {}
            for tag, ln, _ in m.chunks:
                counts[tag] = counts.get(tag, 0) + 1
            cast = read_cast(m)
            types = {}
            for _, t, *_ in cast:
                types[t] = types.get(t, 0) + 1
            score = m.first('VWSC')
            score_kb = (m.chunks[score][1] / 1024) if score is not None else 0
            linked = sorted({m_[3] for m_ in cast if m_[3]})
            rows.append((m.name, len(cast), types, counts.get('Lscr', 0), score_kb, linked))
            if cast_dir:
                os.makedirs(cast_dir, exist_ok=True)
                with open(os.path.join(cast_dir, re.sub(r'[^A-Za-z0-9_.-]', '_', m.name) + '.md'), 'w', encoding='utf-8') as fh:
                    fh.write(f'# Cast von {m.name}\n\n| # | Typ | Name | Größe | Datei |\n|---:|---|---|---|---|\n')
                    for num, t, n, l, sz in cast:
                        fh.write(f'| {num} | {t} | {n} | {sz} | {l} |\n')

    all_types = sorted({t for r in rows for t in r[2]})
    lines = [
        '# Inventar der Director-Filme',
        '',
        'Generiert von `tools/dxr_inventory.py`. Pro Film: Anzahl der Cast-Member nach Typ, Lingo-Skripte (`Lscr`), Größe des Scores (`VWSC`) und verknüpfte externe Dateien.',
        'Die Listen der Cast-Member mit Namen liegen lokal in `analysis/cast/` (nicht im Repo).',
        '',
        '| Film | Cast | ' + ' | '.join(all_types) + ' | Lscr | Score KB |',
        '|---|---:|' + '---:|' * len(all_types) + '---:|---:|',
    ]
    for name, n, types, lscr, skb, _ in rows:
        lines.append(f'| {name} | {n} | ' + ' | '.join(str(types.get(t, '')) for t in all_types) + f' | {lscr} | {skb:.0f} |')
    lines += ['', '## Verknüpfte externe Dateien', '']
    for name, *_, linked in rows:
        if linked:
            lines.append(f'- **{name}:** ' + ', '.join(f'`{l}`' for l in linked))
    with open(out_md, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(lines) + '\n')
    print(f'{len(rows)} Filme -> {out_md}')


if __name__ == '__main__':
    main()
