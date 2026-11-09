#!/usr/bin/env python3
"""Häufigkeit der verwendeten Lingo-Befehle, Properties und Events in dekompilierten Skripten.

Eingabe: die von ProjectorRays erzeugten .ls-Dateien (analysis/lingo/). Ausgabe: Markdown mit
Häufigkeiten und Fundorten (Film), aber ohne Skripttext. Eigene Handler des Spiels werden
herausgefiltert, damit nur Director-Builtins übrig bleiben.

Aufruf:
    py -I tools/lingo_stats.py analysis/lingo docs/lingo-features.md
"""
import os
import re
import sys
from collections import Counter, defaultdict

EVENTS = {
    'mouseDown', 'mouseUp', 'rightMouseDown', 'rightMouseUp', 'mouseEnter', 'mouseLeave', 'mouseWithin',
    'enterFrame', 'exitFrame', 'idle', 'startMovie', 'stopMovie', 'prepareMovie', 'prepareFrame',
    'keyDown', 'keyUp', 'timeOut', 'activateWindow', 'deactivateWindow', 'startup',
}
# Lingo-Schlüsselwörter, die keine Befehle sind
KEYWORDS = {
    'if', 'then', 'else', 'end', 'repeat', 'while', 'with', 'to', 'down', 'in', 'on', 'set', 'put', 'into',
    'after', 'before', 'global', 'property', 'return', 'exit', 'not', 'and', 'or', 'mod', 'the', 'of', 'me',
    'contains', 'starts', 'char', 'word', 'item', 'line', 'field', 'cast', 'sprite', 'sound', 'menu',
    'RETURN', 'EMPTY', 'TRUE', 'FALSE', 'VOID', 'QUOTE', 'SPACE', 'TAB', 'BACKSPACE', 'ENTER',
}


def scan(root):
    defined = set()
    files = []
    for dirpath, _, names in os.walk(root):
        for n in names:
            if n.endswith('.ls'):
                p = os.path.join(dirpath, n)
                movie = os.path.relpath(p, root).split(os.sep)[0]
                text = open(p, encoding='latin-1').read()
                files.append((movie, text))
                defined.update(re.findall(r'^on (\w+)', text, re.M))
    calls, props, events, stmts = Counter(), Counter(), Counter(), Counter()
    where = defaultdict(set)
    for movie, text in files:
        for ev in re.findall(r'^on (\w+)', text, re.M):
            if ev in EVENTS:
                events[ev] += 1
                where['ev:' + ev].add(movie)
        # Strings entfernen, damit Literale nicht mitgezählt werden
        code = re.sub(r'"[^"\n]*"', '""', text)
        for name in re.findall(r'\bthe (\w+)', code):
            props[name] += 1
            where['p:' + name].add(movie)
        for name in re.findall(r'\b(\w+)\(', code):
            if name in defined or name in KEYWORDS:
                continue
            calls[name] += 1
            where['c:' + name].add(movie)
        for m in re.findall(r'^\s*(sound (?:playFile|fadeIn|fadeOut|stop|close)|play (?:frame|movie|done)|go to|go loop|go next|go previous|pass|nothing|beep|halt|quit|restart|shutDown|updateStage|pause|continue)\b', code, re.M):
            stmts[m] += 1
            where['s:' + m].add(movie)
    return calls, props, events, stmts, where, len(files)


def table(title, counter, prefix, where):
    lines = [f'## {title}', '', '| Name | Anzahl | Filme |', '|---|---:|---|']
    for name, n in counter.most_common():
        movies = sorted(where[prefix + name])
        shown = ', '.join(movies) if len(movies) <= 6 else ', '.join(movies[:6]) + f' (+{len(movies) - 6})'
        lines.append(f'| `{name}` | {n} | {shown} |')
    return lines + ['']


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    calls, props, events, stmts, where, n = scan(sys.argv[1])
    lines = [
        '# Verwendete Lingo-Features',
        '',
        f'Generiert von `tools/lingo_stats.py` aus {n} dekompilierten Skripten (`analysis/lingo/`).',
        'Eigene Handler des Spiels sind herausgefiltert. Die Spalte "ScummVM" wird in T3.3 ergänzt; in einer eigenen Datei, damit dieses Dokument generierbar bleibt.',
        '',
    ]
    lines += table('Event-Handler', events, 'ev:', where)
    lines += table('Befehle und Funktionen (Aufrufe mit Klammern)', calls, 'c:', where)
    lines += table('Anweisungen ohne Klammern', stmts, 's:', where)
    lines += table('Properties (`the …`)', props, 'p:', where)
    with open(sys.argv[2], 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines))
    print(f'{n} Skripte: {len(events)} Events, {len(calls)} Builtins, {len(stmts)} Anweisungen, {len(props)} Properties -> {sys.argv[2]}')


if __name__ == '__main__':
    main()
