#!/usr/bin/env python3
"""Kennzahlen der Fangräume: Verstecke, Laufwege der Maus und deren Dauer je Level.

Grundlage (siehe docs/mouse-catching.md):
- Feld "hidelist": eine Zeile pro Versteck, "n:ziel1,ziel2,..." = mögliche Laufziele
- Score-Marker "MA<von>:<nach>": Laufanimation der Maus; Länge = Abstand zum nächsten Marker
- Tempo beim Laufen: mytempo = 8 / 12 / 16 fps (Level 1/2/3), +2 nach 5, 10 und 15 gefangenen Mäusen

Liest nur; nutzt die Parser aus tools/dxr_inventory.py.

Aufruf:
    py -I tools/room_stats.py game docs/room-stats.md
"""
import importlib.util
import os
import re
import struct
import sys

_spec = importlib.util.spec_from_file_location('dxr_inventory', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dxr_inventory.py'))
dxr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dxr)

ROOMS = ['ARTIST', 'BALLROOM', 'BAR', 'BATHROOM', 'BUSINESS', 'DINING', 'EXERCISE', 'FARMER', 'KITCHEN',
         'LIBRARY', 'MADSCI', 'NEWLYWED', 'PLAYROOM', 'PLUMBER', 'PRESBED', 'PRESLIV', 'SLOBS', 'SNOOKER', 'WITCHES']
TEMPOS = {'L1': 8, 'L2': 12, 'L3': 16, 'L3+15': 22}


def labels(m):
    """VWLB (D4): count(2), (frame(2), offset(2)) * (count + 1), direkt danach der Text."""
    i = m.first('VWLB')
    if i is None:
        return []
    c = m.chunk_data(i)
    n = struct.unpack('>H', c[0:2])[0]
    ents = [struct.unpack('>HH', c[2 + 4 * k: 6 + 4 * k]) for k in range(n + 1)]
    text_start = 2 + 4 * (n + 1)
    out = []
    for k in range(n):
        frame, off = ents[k]
        end = ents[k + 1][1]
        out.append((frame, c[text_start + off: text_start + end].decode('latin-1')))
    return out


def field_text(m, name):
    """Text eines Feld-Cast-Members über KEY* (Kind STXT des CASt) holen."""
    cas = m.first('CAS*')
    ids = m.chunk_data(cas)
    cast_ids = {}
    for k in range(len(ids) // 4):
        cid = struct.unpack('>I', ids[4 * k:4 * k + 4])[0]
        if cid and m.chunks[cid][0] == 'CASt':
            c = m.chunk_data(cid)
            ds, isz = struct.unpack('>HI', c[0:6])
            ent = dxr.info_entries(c[6 + ds: 6 + ds + isz])
            if len(ent) > 1 and dxr.pascal(ent[1]).lower() == name:
                cast_ids[cid] = True
    key = m.chunk_data(m.first('KEY*'))
    esz, _, total, used = struct.unpack('>HHII', key[:12])
    for k in range(used):
        sec, parent, tag = struct.unpack('>II4s', key[12 + k * 12: 24 + k * 12])
        if parent in cast_ids and tag == b'STXT':
            s = m.chunk_data(sec)
            hl, tl = struct.unpack('>II', s[:8])
            return s[hl:hl + tl].decode('latin-1').replace('\r', '\n')
    return None


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    root, out = sys.argv[1], sys.argv[2]
    rows = []
    for room in ROOMS:
        m = dxr.find_movies(os.path.join(root, room + '.DXR'))[0]
        lab = sorted(labels(m))
        runs = []
        for k, (frame, name) in enumerate(lab):
            if re.fullmatch(r'MA\d+:\d+', name, re.I):  # Director-Marker sind case-insensitiv
                nxt = lab[k + 1][0] if k + 1 < len(lab) else frame
                runs.append(nxt - frame)
        hl = field_text(m, 'hidelist') or ''
        places = [l for l in hl.split('\n') if l.strip()]
        rows.append((room, len(places), len(runs), min(runs) if runs else 0,
                     sorted(runs)[len(runs) // 2] if runs else 0, max(runs) if runs else 0))

    lines = [
        '# Kennzahlen der Fangräume',
        '',
        'Generiert von `tools/room_stats.py`. **Laufzeit** = Länge der Score-Animation `MA<von>:<nach>` in Frames geteilt durch das Tempo.',
        f'Tempo: Level 1 = {TEMPOS["L1"]} fps, Level 2 = {TEMPOS["L2"]} fps, Level 3 = {TEMPOS["L3"]} fps; nach 15 gefangenen Mäusen +6 (Level 3: {TEMPOS["L3+15"]} fps).',
        '',
        '| Raum | Verstecke | Laufwege | Frames min / median / max | Sekunden (median) L1 / L2 / L3 / L3+15 |',
        '|---|---:|---:|---|---|',
    ]
    for room, places, nruns, mn, med, mx in rows:
        secs = ' / '.join(f'{med / t:.1f}' for t in TEMPOS.values())
        lines.append(f'| {room} | {places} | {nruns} | {mn} / {med} / {mx} | {secs} |')
    allmed = sorted(r[4] for r in rows)
    lines += ['', f'Median über alle Räume: {allmed[len(allmed) // 2]} Frames.']
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
