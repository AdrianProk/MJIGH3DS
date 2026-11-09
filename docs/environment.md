# Entwicklungsumgebung

Stand: 2026-11-09 (T0.2)

| Werkzeug | Status |
|---|---|
| Betriebssystem | Windows 10 Pro 10.0.19045 |
| CPU / RAM | Intel Core i7-1165G7, 32 GB |
| Freier Platz C: | ca. 410 GB |
| Python | 3.13.17, Aufruf über `py` (`python` ist nur ein Store-Platzhalter) |
| Git | 2.36.1 (Git for Windows, mit Git Bash) |
| WSL2 | **nicht eingerichtet** (`wsl -l -v` zeigt nur die Hilfe) |
| Docker | **nicht installiert** |
| make / gcc | **nicht vorhanden** |
| MSYS2 | **nicht vorhanden** |
| devkitPro | **nicht vorhanden** |
| 7-Zip | nicht vorhanden (wird nicht gebraucht: `tools/iso_extract.py`) |

## Folgen für den Plan

- Phase 1 und 2 laufen vollständig mit Python, ohne weitere Installation.
- Für Phase 3 (ScummVM-Desktop-Build) und Phase 4 (3DS-Toolchain) muss eine Build-Umgebung installiert werden. Empfehlung: **WSL2 mit Ubuntu**. Darin laufen der ScummVM-Desktop-Build (SDL2) und devkitPro (über `dkp-pacman`). Installation nur nach Freigabe durch den Nutzer (TODO.md, Regel 6).
- Für den ersten Smoke-Test (T3.1) genügt ein offizielles ScummVM-Release für Windows, ohne Build-Umgebung.

## Hinweise

- In Git Bash vor Aufrufen mit `/`-Pfaden `export MSYS_NO_PATHCONV=1` setzen. Sonst schreibt MSYS Pfade wie `/ATTIC.DXR` zu `C:/Program Files/Git/ATTIC.DXR` um.
