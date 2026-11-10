# 3DS-Build (T4.1–T4.3)

Stand: 2026-11-10

## Toolchain (T4.1)

devkitpro.org lässt automatisierte Downloads nicht zu: `curl` und `wget` bekommen eine Cloudflare-Sperre bzw. HTTP 403, auch vom Rechner des Nutzers aus. Der Weg über `install-devkitpro-pacman` und `dkp-pacman` fällt damit aus.

Stattdessen kommt das **offizielle Docker-Image von devkitPro** zum Einsatz, ohne Docker:

| | |
|---|---|
| Image | `devkitpro/devkitarm:20260610` (Docker Hub, "gba/ds/3ds/gp32/gp2x development environment") |
| Index-Digest | `sha256:116afba8df8453961de2936ffab20dd441edf4d682856c1ec8b0e53d7ed0bbf5` |
| amd64-Manifest | `sha256:15b79ce75822c289538d8153da5fa7aafe5e6adc32ad8a575a197beca0f0761b` |
| Werkzeug | `scripts/fetch_docker_subtree.py`: Registry-API, SHA-256-Prüfung jeder Schicht, Whiteouts, nur `/opt/devkitpro` |
| Ziel | `~/devkitpro` (712 MB, 6394 Einträge), Herkunft in `~/devkitpro/.mjigh3ds-source.json` |

```bash
python3 -I scripts/fetch_docker_subtree.py devkitpro/devkitarm 20260610 \
  --blobs ~/downloads/devkitarm-20260610 --subtree opt/devkitpro --dest ~/devkitpro
```

**Inhalt:**
- `arm-none-eabi-gcc (devkitARM) 16.1.0`, libctru, citro3d, citro2d
- Portlibs unter `portlibs/3ds`: zlib, libpng, freetype, libjpeg(-turbo), libmad, libogg, libvorbisidec (Tremor), FLAC, curl, theora und weitere
- Werkzeuge: `3dsxtool`, `smdhtool`, `3dslink`, `picasso`, `tex3ds`, `mkbcfnt`
- **Es fehlen** `bannertool` und `makerom`. Sie werden nur für das CIA-Format gebraucht, nicht für `.3dsx`.
- Übersprungen wurde nur der Symlink `pacman/share/pacman/keyrings`; er ist für den Build unwichtig.

**Pfad:** Die Toolchain hat `/opt/devkitpro` an vielen Stellen fest eingetragen: in den `.pc`-Dateien, in `.la`-Dateien und in den Binärdateien. Deshalb gibt es einmalig einen Symlink, angelegt als root:

```powershell
wsl -d Ubuntu -u root ln -s /home/adrian/devkitpro /opt/devkitpro
```

## ScummVM für den 3DS bauen (T4.2/T4.3)

```bash
bash /mnt/c/Users/Alphe/Documents/GitHub/MJIGH3DS/scripts/build-3ds.sh                  # Port -> dist/3ds/mausjagd.3dsx
DIAG=1 bash /mnt/c/Users/Alphe/Documents/GitHub/MJIGH3DS/scripts/build-3ds.sh           # Port mit Diagnosemodus -> dist/3ds/mausjagd-diag.3dsx
MAUSJAGD_PORT=0 bash /mnt/c/Users/Alphe/Documents/GitHub/MJIGH3DS/scripts/build-3ds.sh  # normal -> dist/3ds/scummvm.3dsx
```

### Eigenständiger Port (`MAUSJAGD_PORT`, Standard)

Seit 2026-11-10 baut das Skript standardmäßig den eigenständigen Port. Auf Wunsch des Nutzers startet das Spiel direkt, ohne ScummVM-Launcher.

- **Patch** im Fork, Branch `mausjagd`: `3DS: Add standalone Mäusejagd build mode (MAUSJAGD_PORT)`, exportiert nach `patches/0001-…`. Alles steht hinter `#ifdef MAUSJAGD_PORT`; ohne das Define verhält sich der Fork wie normales ScummVM.
  - `backends/platform/3ds/mausjagd.h`: `MAUSJAGD_APP_DIR` = `sdmc:/3ds/mausjagd/`, `MAUSJAGD_GAME_DIR` = `…/game`, `MAUSJAGD_GAME_ID` = `director:ggmd`
  - `main.cpp`: Ohne Argumente gestartet, setzt sie `--path=sdmc:/3ds/mausjagd/game director:ggmd`. ScummVM legt dann ein temporäres Target an und erkennt die Variante im Pfad; der Launcher erscheint nicht.
  - `osystem.cpp`: Konfiguration, Log und Spielstände liegen in `sdmc:/3ds/mausjagd/`. Ein normales ScummVM unter `/3ds/scummvm/` bleibt unberührt.
  - `engines/dialogs.cpp`: "Zurück zum Launcher" im Spielmenü ist deaktiviert. Beim Beenden geht es zurück zum Homebrew Launcher bzw. HOME-Menü (`gui_return_to_launcher_at_exit` ist standardmäßig aus).
- **Build:** `CPPFLAGS=-DMAUSJAGD_PORT` an `configure`; Titel "Mäusejagd im Grandhotel" im SMDH über `make APP_TITLE=…`; Build-Ordner `~/build/3ds`. Der normale Build liegt in `~/build/3ds-vanilla`.
- **Spieldaten in der .3dsx (Patch 0002, Standard `EMBED_GAME=1`):**
  - `scripts/stage_game_data.py` kopiert die 442 als `nötig` markierten Dateien aus `docs/inventory.md` (176,1 MB) nach `~/build/3ds/romfs-extra/game` und prüft jede gegen Größe und SHA-1.
  - Über `make scummvm.3dsx DIST_3DS_EXTRA_FILES=…/game` landen sie als `romfs:/game` in der `.3dsx`. Optionale Galerie-Dateien und Beilagen sind nicht dabei.
  - Die App nimmt `romfs:/game`, wenn dort `MAUSJAGD.EXE` liegt, sonst `sdmc:/3ds/mausjagd/game`. Mit `EMBED_GAME=0` entsteht eine schlanke `.3dsx`, die die Daten von der SD-Karte liest.
  - Die RomFS hängt in ScummVMs Suchpfad nur mit Tiefe 1 (`addSysArchivesToSearchSet`), deshalb kommen sich Themes und Spieldaten nicht in die Quere.
  - Schreibzugriffe gehen trotz schreibgeschützter RomFS: FileIO schreibt über den Spielstand-Manager (`engines/director/lingo/xlibs/f/fileio.cpp`), also nach `sdmc:/3ds/mausjagd/saves/`.
  - **Diese .3dsx enthält das Spiel: nur für den eigenen Gebrauch, nicht weitergeben.** `dist/` ist ignoriert.
- **SD-Karte** (mit eingebetteten Daten):
  ```
  SD:\3ds\mausjagd\mausjagd.3dsx   <- enthält Programm und Spieldaten
  SD:\3ds\mausjagd\scummvm.ini     (legt die App selbst an)
  SD:\3ds\mausjagd\scummvm.log
  SD:\3ds\mausjagd\saves\
  ```
  Ohne eingebettete Daten (`EMBED_GAME=0`) kommt der Inhalt von `game\` nach `SD:\3ds\mausjagd\game\`.
- **Keine Startwarnung (Patch 0006, T4.7):** Alle Director-Einträge sind in ScummVM `ADGF_UNSTABLE`. Deshalb fragt `AdvancedMetaEngineBase::createInstance()` vor jedem Start "Start anyway / Cancel". Im Port steht `enable_unsupported_game_warning` standardmäßig auf `false` (`OSystem_3DS::initBackend()`); in `scummvm.ini` lässt es sich wieder einschalten. Der Erkennungseintrag bleibt unverändert.
- **Diagnosemodus (Patch 0005, T4.6):**
  - **An:** wenn `diag.txt` in `sdmc:/3ds/mausjagd/` oder in der RomFS liegt; die Datei auf der SD-Karte hat Vorrang. `DIAG=1` legt sie in die RomFS und nennt die Ausgabe `mausjagd-diag.3dsx`. Das Binary ist dasselbe wie ohne `DIAG`, nur die RomFS unterscheidet sich.
  - **Ohne Neubau** (z. B. auf echter Hardware) reicht eine Datei `SD:\3ds\mausjagd\diag.txt`, auch eine leere.
  - **Inhalt:** zusätzliche Startoptionen, getrennt durch Leerzeichen oder Zeilen; `#` leitet einen Kommentar ein. Ist die Datei leer, gilt `--debuglevel=1 --debugflags=loading` (`MAUSJAGD_DIAG_DEFAULT_ARGS`). Beim Bauen lassen sie sich mit `DIAG_ARGS="…"` setzen. Die Optionen greifen nur beim Direktstart ohne Argumente.
  - **Im Log:**
    - Jede Zeile beginnt nach dem Datum mit `[+s.mmm]`, der Zeit seit App-Start.
    - Marken: `diag: backend ready …`, `CPU extensions:` (danach läuft die Erkennung), `Running …` (Erkennung fertig), `Starting v404 Director game` (Engine), `3ds initsize`, `diag: first frame at WxH, N ms after the resolution change`.
    - Alle 5 s eine Zeile `diag: N frames in T ms (F fps), converted avg P px/frame, flush avg/max …, update avg/max …`. Dabei ist *converted* die Fläche, die das Backend pro Frame von CLUT8 in die GPU-Textur umrechnet, *flush* die Zeit dafür und *update* die Dauer von `updateScreen()` einschließlich GPU-Übergabe. Die restliche Zeit eines Frames verbraucht die Engine (Lingo, Dekodieren, Zeichnen).
  - Code: `backends/platform/3ds/mausjagd.cpp`; Anbindung in `main.cpp`, `osystem.cpp` (`logMessage`, `initBackend`) und `osystem-graphics.cpp` (`initSize`, `updateScreen`).
- **Schnelle Spielerkennung (Patch 0007, T4.8):** `AdvancedMetaEngineDetectionBase::identifyGame()` beschränkt `detectGame()` im Port auf die Einträge der gesuchten Game-ID. Vorher schlug die Erkennung die Dateien aller Director-Einträge nach; das dauerte im Emulator 75 s (Details in `docs/performance.md`). Die Änderung steht in `engines/advancedDetector.{h,cpp}` hinter `#ifdef MAUSJAGD_PORT`.
- **Startbildschirm mit Phasen-Balken (Patch 0008, Wunsch des Nutzers):**
  - Oben erscheinen der Titel "Mäusejagd im Grandhotel", "3DS-Port mit ScummVM", ein Balken und eine Statuszeile; unten bleibt es schwarz. Das Design ist eigen, ohne Grafik aus dem Spiel (PLAN.md §7). Als Schrift dient die eingebaute `kBigGUIFont` mit Umlauten, weil die GUI-Themes beim Start noch nicht geladen sind.
  - Phase 1 am Ende von `initBackend()`: "Spieldaten werden geprüft ..." (Balken 1/3). Phase 2 in `engineInit()`: "Spiel wird gestartet ..." (2/3).
  - Das Spiel übernimmt den Bildschirm beim ersten `updateScreen()`, nachdem die Engine ihre Auflösung gesetzt hat. Ein ScummVM-Dialog (Overlay, z. B. eine Fehlermeldung) beendet den Startbildschirm sofort, damit er sichtbar ist.
  - Bis dahin zeichnet `updateScreen()` nur den Startbildschirm; Bildänderungen des Spiels sammeln sich als Dirty Rects und erscheinen danach.
  - Code: `OSystem_3DS::setStartupPhase()`, `renderStartupScreen()`, `engineInit()` in `osystem-graphics.cpp`.
- **Normaler Modus des oberen Bildschirms (Patch 0009):** Das Backend schaltet sonst den 800-Pixel-Breitmodus ein (`gfxSetWide`). Azahar zeigt davon nur die linke Hälfte, doppelt so breit, und für den Port bringt der Modus nichts. Der Port bleibt bei 400×240.
- **Automatischer Startlauf im Emulator:** `scripts/azahar-run.ps1` (siehe `docs/performance.md`).

- `configure --host=3ds --disable-all-engines --enable-engine=director --disable-cloud --disable-libcurl`
- Mit nur einer Engine wird statisch gebaut. Dynamische Plugins braucht es laut README nur bei vielen Engines.
- Cloud und libcurl sind aus, weil sie sonst `cacert.pem` verlangen und für das Spiel unnötig sind.
- Ergebnis: `dist/3ds/scummvm.3dsx` (ignoriert) und `dist/3ds/SCUMMVM_COMMIT.txt`.
- **Erstes Build (2026-11-10):**
  - Basis `upstream-base` `7c924b93`, unverändert. Dauer etwa 3 Minuten, 18 Compiler-Warnungen, keine Fehler.
  - Ergebnis `scummvm.3dsx`, 24,9 MB.
  - Backend: `3ds, 16bit color, high resolution, savegame timestamp, aspect ratio correction, Nuked OPL emulator, virtual keyboard`; Engine nur `Macromedia Director`.
  - Bibliotheken: zlib, FreeType2, libjpeg, Tremor, FLAC. Ohne libcurl, Cloud, OpenGL und ImGui (vom Backend nicht unterstützt).
- **Bekanntes Risiko** laut README: Das FreeType von devkitPro belegt beim Laden der GUI-Themes zu viel Stack. Stürzt die GUI ab, auf FreeType 2.6.5 ausweichen oder mit `EXTRA_CONFIGURE=--disable-freetype2` bauen.
