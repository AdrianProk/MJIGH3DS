# Test-Patches für ScummVM (nicht Teil des Ports)

Werkzeuge für Prüfungen am Desktop. Sie gehören **nicht** in den Branch `mausjagd` und nicht in `patches/`.

| Patch | Zweck | Anwendung |
|---|---|---|
| `score-lint.patch` | Prüft nach dem Laden eines Films **jeden Frame** des Scores und alle Film-Loops auf Verweise ins Leere: Palette, Sounds, Frame-Skript, Übergang, Cast-Member und Skripte aller Sprite-Kanäle. Schreibt `LINT …`-Zeilen ins Log und beendet die Engine. | Im Fork auf einem eigenen Branch anwenden (`git checkout -b lint-tmp mausjagd && git am …/score-lint.patch`), Linux-Build bauen, in der Test-INI unter `[scummvm]` `mausjagd_lint=true` setzen und jeden Film mit `--start-movie=<FILM>.DXR` starten. Ergebnis 2026-11-11 in `docs/compat-log.md`. |
