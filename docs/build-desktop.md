# Desktop-Build von ScummVM (T3.2)

Stand: 2026-11-10

## Überblick

| | Linux (nativ) | Windows (MinGW) |
|---|---|---|
| Zweck | Agenten-Tests ohne Fenster, Debug-Ausgaben | GUI-Tests des Nutzers mit eigenen Patches |
| Status | **gebaut und getestet** | vorbereitet, **zurückgestellt** (offizielles Release reicht vorerst) |
| Ergebnis | `~/build/linux/scummvm` | `dist/scummvm-win64/scummvm.exe` |

- **Quellen:** `~/scummvm` in WSL1, Branch `mausjagd`, Basis `upstream-base` = `7c924b93038495de3d8cf673002e5a6f50ff0a8c`. Die Version meldet sich als `ScummVM 2026.4.1git12582-g7c924b9303`.
- **Engines:** nur `director` (`--disable-all-engines --enable-engine=director`).
- **Linux-Backend:** SDL 2.32.10, 16-Bit-Farbe, hohe Auflösung, FreeType2, zlib, libpng und ImGui (für den Director-Debugger).
- **Werkzeuge und Umgebung:** siehe `docs/environment.md`.

## Bauen

In Ubuntu (WSL1), aus dem Repo heraus:

```bash
bash /mnt/c/Users/Alphe/Documents/GitHub/MJIGH3DS/scripts/build-desktop.sh linux   # oder win64 / all
```

- Gebaut wird außerhalb des Quellbaums unter `~/build/<ziel>`. `configure` läuft nur beim ersten Mal; mit `RECONFIGURE=1` wird es erzwungen.
- ccache greift automatisch über `/usr/lib/ccache`.
- Der Windows-Build schreibt nach `dist/scummvm-win64/`. Dazu kommen die gestrippte EXE, die DLLs, die `objdump` meldet, und eine leere `scummvm.ini`, damit ScummVM im portablen Modus läuft.

## Testen ohne Fenster (Agent)

```bash
export SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy
T=~/scummvm-test
~/build/linux/scummvm --config=$T/scummvm.ini --logfile=$T/scummvm.log \
  --extrapath=~/scummvm/dists/engine-data --themepath=~/scummvm/gui/themes \
  --debuglevel=1 --debugflags=fast,loading ggmd-win-de
```

- Das Spiel einmalig mit `--add --path=/mnt/c/Users/Alphe/Documents/GitHub/MJIGH3DS/game` eintragen. Target ist `ggmd-win-de`.
- **Startwarnung abschalten:** In `~/scummvm-test/scummvm.ini` steht unter `[scummvm]` die Zeile `enable_unsupported_game_warning=false` (seit 2026-11-10). Ohne sie wartet ScummVM ohne Fenster am Dialog "Start anyway", bis das SIGINT von `timeout` ihn schließt. Die früheren Läufe haben dadurch 40 s am Dialog verloren.
- **Raum direkt starten:** `--start-movie=ARTIST.DXR` oder an einem Frame `--start-movie=ARTIST.DXR@1203`. Die Frame-Nummern der Labels zeigt `--debuglevel=2 --debugflags=loading` (`Loading labels`); in ARTIST liegt `caught` auf Frame 1203.
- Laufzeit mit `timeout -s INT -k 3 <s>` begrenzen. SIGINT beendet ScummVM nicht, deshalb gibt es nach 3 s ein SIGKILL (Exit 137).
- **Nützliche Debug-Kanäle** der Director-Engine:
  - `fast`: ohne Frame-Pausen
  - `loading`: Filme und Casts
  - `lingoexec`: Lingo-Aufrufe mit Call-Stack
  - `xobj`: XObjects
  - `paths`: Pfadauflösung
  - `events`: Stufe 8 zeigt, worauf die Partitur wartet
  - `sound`, `lingothe`
- Es gibt **keinen** Kanal `lingo`. `screenshot` speichert nur am Ende eines Films ein Bild.
- Stufe 8 mit `loading` erzeugt Hex-Dumps und bremst das Laden stark.
