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
- **SD-Karte:**
  ```
  SD:\3ds\mausjagd\mausjagd.3dsx
  SD:\3ds\mausjagd\game\          <- Inhalt von game\ (MAUSJAGD.EXE, SHARED.DXR, …)
  SD:\3ds\mausjagd\scummvm.ini    (legt die App selbst an)
  SD:\3ds\mausjagd\scummvm.log
  SD:\3ds\mausjagd\saves\
  ```

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
