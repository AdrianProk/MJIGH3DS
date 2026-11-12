#!/usr/bin/env python3
"""Erzeugt docs/inventory.md: alle Dateien in game/ mit Größe, SHA-1, Kategorie und Status.

Nur Metadaten, keine Inhalte. Liest game/ ausschließlich.

Aufruf:
    py -I tools/inventory.py game docs/inventory.md
"""
import hashlib
import os
import re
import sys

# (Regex auf den Pfad relativ zu game/, Kategorie, Status, Hinweis). Erste passende Regel gewinnt.
# Status: "nötig" = vom Spiel benutzt, "optional" = Zusatz, "Beilage" = gehört nicht zum Spiel.
RULES = [
    (r'^MAUSJAGD\.EXE$', 'projector', 'nötig', 'Director-4.0.4-Projektor mit eingebettetem Startfilm GGMDSTRT.DIR'),
    (r'^LINGO\.INI$', 'config', 'nötig', 'Startskript: Pfade, gMusicPath/gSolosPath, openXlib FileIO'),
    (r'^FILEIO\.DLL$', 'xlib', 'nötig', 'FileIO-Xlib (ScummVM hat FileIO eingebaut; Datei für die Erkennung behalten)'),
    (r'^SHARED\.DXR$', 'movie', 'nötig', 'Shared Cast'),
    (r'^[^/]+\.DXR$', 'movie', 'nötig', 'Director-4-Film (geschützt)'),
    (r'^[^/]+\.MOV$', 'video', 'nötig', 'QuickTime, SMC + raw-Audio'),
    (r'^GERHELP/.*\.MOV$', 'video', 'nötig', 'Hilfevideos des Katers, SMC + twos-Audio'),
    (r'^GERVIDEO/.*\.MOV$', 'video', 'nötig', 'Intro'),
    # Englische CD ("The Great Green Mouse Disaster", Inventar docs/inventory-en.md)
    (r'^GGMD\.EXE$', 'projector', 'nötig', 'Director-4.0.4-Projektor der englischen Fassung mit eingebettetem Startfilm'),
    (r'^ENGHELP/.*\.MOV$', 'video', 'nötig', 'Hilfevideos des Katers (englisch), SMC + twos-Audio'),
    (r'^ENGVIDEO/.*\.MOV$', 'video', 'nötig', 'Intro (englisch)'),
    (r'^ENDSOUND/.*\.AIF$', 'sound', 'nötig', 'Abschluss-Sounds (englische Fassung)'),
    (r'^DESKTOP$', 'marker', 'nötig', 'leere Datei der englischen CD; vorsichtshalber dabei (die CD-Prüfung arbeitet mit Markierungsdateien)'),
    (r'^SOUNDS/SNDTEXT\.TXT$', 'marker', 'nötig', 'leere Markierungsdatei für die CD-Prüfung im Startfilm'),
    (r'^SOUNDS/.*\.AIF$', 'sound', 'nötig', 'Effekte und Sprache'),
    (r'^ENDSOUNG/.*\.AIF$', 'sound', 'nötig', 'Abschluss-Sounds'),
    (r'^MUSIC/BUILD\d\.TXT$', 'data', 'nötig', 'Instrumentenliste pro Orchester-Variante (Nutzung in T2.4 prüfen)'),
    (r'^MUSIC/.*\.AIF$', 'music', 'nötig', 'Orchester, 16 Bit (Standard, gMusicPath = music\\)'),
    (r'^MUSIC8/.*\.AIF$', 'music', 'nötig', 'Orchester, 8 Bit (gMusicPath = music8\\)'),
    (r'^SOLOS/.*\.AIF$', 'music', 'nötig', 'Instrumenten-Soli, 16 Bit (gSolosPath = solos\\)'),
    (r'^SOLOS8/.*\.AIF$', 'music', 'nötig', 'Instrumenten-Soli, 8 Bit (gSolosPath = solos8\\)'),
    (r'^STARTSND/.*\.AIF$', 'music', 'optional', 'Raummusik, nur von GALLERY.EXE referenziert'),
    (r'^GALLERY\.EXE$', 'projector', 'optional', 'Zusatz-App "Gallery" (Director-4-Projektor mit eingebettetem GALLERY.DIR)'),
    (r'^README\.WRI$', 'doc', 'optional', 'Spielanleitung (Windows Write)'),
    (r'^INSTALL\.WRI$', 'doc', 'optional', 'Installationsanleitung, erklärt die 8-Bit-Musikoption'),
    (r'^BILDER/.*\.BMP$', 'extra', 'Beilage', 'Ausmalbilder laut Anleitung, nicht vom Spiel geladen'),
    (r'^README\.TXT$', 'extra', 'Beilage', 'AGB eines Telefonanbieters'),
    (r'^(AUFTRAG|KONFIG)\.PDF$', 'extra', 'Beilage', 'Formulare/Doku des Internet-Angebots, nicht vom Spiel referenziert'),
    (r'^PEARL\.(EXE|ICO)$', 'extra', 'Beilage', 'Director-7-Projektor eines Verlagskatalogs (pearl.dir)'),
    (r'^ONLINE\.EXE$', 'extra', 'Beilage', 'Installer für einen Internetzugang'),
    (r'^(SETUP\.EXE|SETUP\.LST|SETUPKIT\.DLL|VBRUN300\.DLL|VBDB300\.DLL|MSAES110\.DLL|MSAJT110\.DLL)$',
     'extra', 'Beilage', 'Windows-Installer (Visual Basic 3)'),
    (r'^(AUTORUN\.INF|START\.BAT|START\.PIF|START\.WAV|TREND\.ICO)$', 'extra', 'Beilage', 'Autorun-Launcher der CD (MEDI8OR)'),
    (r'^SILENT\.WAV$', 'extra', 'Beilage', 'nicht referenziert (das Spiel nutzt SOUNDS/SILENT.AIF)'),
]
RULES = [(re.compile(p, re.I), c, s, h) for p, c, s, h in RULES]


def sha1(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def classify(rel):
    for rx, cat, status, hint in RULES:
        if rx.search(rel):
            return cat, status, hint
    return 'unbekannt', 'UNKLAR', 'keine Regel – in tools/inventory.py ergänzen'


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    root, out = sys.argv[1], sys.argv[2]
    rows = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, '/')
            cat, status, hint = classify(rel)
            rows.append((rel, os.path.getsize(full), sha1(full), cat, status, hint))

    summary = {}
    for rel, size, _, cat, status, _ in rows:
        key = (status, cat)
        n, s = summary.get(key, (0, 0))
        summary[key] = (n + 1, s + size)

    lines = [
        '# Inventar der Spieldaten',
        '',
        f'Generiert von `tools/inventory.py` aus `{root}/`. Nicht von Hand bearbeiten; Regeln im Skript anpassen und neu erzeugen.',
        '',
        '## Zusammenfassung',
        '',
        '| Status | Kategorie | Dateien | MB |',
        '|---|---|---:|---:|',
    ]
    order = {'nötig': 0, 'optional': 1, 'Beilage': 2, 'UNKLAR': 3}
    for (status, cat), (n, s) in sorted(summary.items(), key=lambda kv: (order.get(kv[0][0], 9), kv[0][1])):
        lines.append(f'| {status} | {cat} | {n} | {s / 1e6:.1f} |')
    for status in ('nötig', 'optional', 'Beilage', 'UNKLAR'):
        n = sum(v[0] for k, v in summary.items() if k[0] == status)
        s = sum(v[1] for k, v in summary.items() if k[0] == status)
        if n:
            lines.append(f'| **{status} gesamt** | | **{n}** | **{s / 1e6:.1f}** |')
    lines += [
        '',
        '## Dateien',
        '',
        '| Pfad | Bytes | SHA-1 | Kategorie | Status | Hinweis |',
        '|---|---:|---|---|---|---|',
    ]
    for rel, size, digest, cat, status, hint in rows:
        lines.append(f'| `{rel}` | {size} | `{digest}` | {cat} | {status} | {hint} |')
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')

    unclear = [r[0] for r in rows if r[4] == 'UNKLAR']
    print(f'{len(rows)} Dateien -> {out}')
    if unclear:
        print('UNKLAR:', *unclear, sep='\n  ')
        sys.exit(1)


if __name__ == '__main__':
    main()
