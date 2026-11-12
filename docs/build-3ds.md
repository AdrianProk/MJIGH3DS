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
- **Es fehlen** `bannertool` und `makerom`. Sie werden nur für das CIA-Format gebraucht, nicht für `.3dsx`; dafür gibt es `scripts/build-ctr-tools.sh` (Abschnitt "CIA").
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
- **Hotelkarte auf dem oberen Bildschirm (Patch 0010, T5.1, Wunsch des Nutzers):**
  - **Schnittstelle:** `OSystem::setSecondaryScreen(image, marker)` ist neu in `common/system.h`, hinter `MAUSJAGD_PORT` und standardmäßig ohne Wirkung. Das 3DS-Backend zeigt das Bild oben anstelle des Spiels und lässt `marker` als 2-Pixel-Rahmen zweimal pro Sekunde blinken. Ist die eingebaute Lupe des Backends aktiv, zeigt der obere Bildschirm weiter das Spiel.
  - **Engine:** `engines/director/mausjagd-port.cpp`, aufgerufen in der Hauptschleife von `DirectorEngine::run()` nach `draw()`.
    - Sobald in `GGMDMENU` das Bild `interfinalfordir0001` (582×429, Querschnitt mit allen Zimmern) auf der Bühne ist, übernimmt das Modul: das Bild mit seiner eigenen Palette (Cast 23), verkleinert auf 320×235, die Raumnamen aus Feld `roomlist` (Zeile = Sprite − 4) und den Dachboden (Sprite 24).
    - Die Klickflächen (Sprites 5–24) liegen etwa 12 Pixel tiefer als die Zimmerbilder; der Rahmen nutzt deshalb eine im Bild gemessene Tabelle `kRoomPictures`. Für andere Bilder dienen die Sprites als Ersatz.
    - Bei jedem Filmwechsel und jeder Änderung von `miceCaught` entsteht das Bild neu: links "Mäuse N von 19", in der Mitte die Karte, der Rahmen um den aktuellen Raum. Im Menü, in `INSTRUM` und `ORCH` gibt es keinen Rahmen.
  - **Testhilfe:** `mausjagd_debug_room=ARTIST` im Abschnitt `[scummvm]` der `scummvm.ini` tut so, als sei man in diesem Raum. Zusammen mit `--start-movie=GGMDMENU.DXR@14` in der `diag.txt` lässt sich der Rahmen ohne Eingaben prüfen. Der Direkteinstieg endet nach einigen Sekunden mit einem Lingo-Fehler (`shortlist` fehlt), Karte und Rahmen sind dann aber schon sichtbar.
  - **Speicher:** etwa 1 MB im linearen Speicher (Textur 512×256 RGBA plus Pixelpuffer); merken für S6.
- **Härtung und Robustheit (Patches 0016–0022, PLAN.md §10):** Details und Tests stehen in `docs/security.md`.
  - **0016:** Das Arbeitsverzeichnis ist `sdmc:/3ds/mausjagd/` statt `sdmc:/`. Relative Pfade der Engine, z. B. für Debug-Dumps, landen so im App-Ordner.
  - **0017:** `diag.txt` nimmt nur `--debuglevel=`, `--debugflags=`, `--debug-channels-only` und `--start-movie=` an. Andere Optionen landen als Warnung im Log.
  - **0018:** Ein fataler Fehler zeigt eine Meldung mit OK statt der Debugger-Konsole, danach beendet sich die App (`engines/engine.cpp`).
  - **0019:** Der Hauptthread hat 256 KB Stack (`__stacksize__`).
  - **0020:** Im Diagnosemodus misst ein Timer alle 20 ms Heap und linearen Speicher. Die Spitzenwerte stehen als `diag: memory: …` im Log.
  - **0021:** Der Zufallsgenerator der Director-Engine kommt ohne undefiniertes Verhalten aus und liefert bit-gleiche Werte. Der Patch hat kein `#ifdef` und ist ein Kandidat für upstream.
  - **0022:** Spielstände werden atomar geschrieben, erst in eine `.tmp`-Datei, dann umbenannt.
- **Prüfung der fertigen Datei:** `py -I tools/inspect_3dsx.py dist/3ds/mausjagd.3dsx docs/inventory.md` prüft 3DSX-Kopf, SMDH und RomFS sowie die SHA-1 aller Spieldateien. Eine eingebettete `diag.txt` meldet es. Exit-Code 0 heißt: alles in Ordnung.
- **Automatischer Startlauf im Emulator:** `scripts/azahar-run.ps1` (siehe `docs/performance.md`). Mit `-MoreShots N -ShotIntervalMs X` entstehen zusätzliche Bilder, z. B. zum Prüfen des Blinkens.

### Englische Fassung (`GAME_LANG=en`, T7.2, Wunsch des Nutzers, 2026-11-12)

```bash
py -I tools/iso_extract.py extract <…>/GGMD_ENGLISH_WIN.iso game-en --profile game        # Windows, einmalig
py -I tools/inventory.py game-en docs/inventory-en.md                                      # Windows, einmalig
GAME_LANG=en CIA=1 bash /mnt/c/Users/Alphe/Documents/GitHub/MJIGH3DS/scripts/build-3ds.sh  # -> dist/3ds/ggmd.3dsx und ggmd.cia
```

- **Daten:** Die englische CD ("GGMD_ENGLISH_WIN", 389 MB) liegt entpackt in `game-en/` (ignoriert).
  - Aufbau wie bei der deutschen CD. Der Projektor heißt `GGMD.EXE`, die Ordner `ENGHELP`, `ENGVIDEO` und `ENDSOUND`. Dazu kommen das Unterspiel `MOUSMAZE` (nicht entpackt) und `INTROM.DXR`.
  - Inventar: `docs/inventory-en.md`, 443 nötige Dateien (167 MB). `tools/inventory.py` und `tools/iso_extract.py` kennen jetzt auch die englischen Dateien und Ordner.
- **Erkennung (Patch 0026):** ScummVM kannte die englische Windows-Fassung nicht. Neuer Eintrag `ggmd` mit `GGMD.EXE` (`d:e4114d5d…`, 1 444 668 Bytes) und `SHARED.DXR` (`d:c7591219…`, 391 136 Bytes). Am Desktop: "The Great Green Mouse Disaster (Windows/English)".
- **Port (Patch 0027, `-DMAUSJAGD_LANG_EN`):**
  - App-Ordner `sdmc:/3ds/ggmd/`: Konfiguration, Log und Spielstände getrennt von der deutschen Fassung.
  - Prüfdatei `GGMD.EXE`.
  - Englische Texte: Startbildschirm, Hotelkarte ("Mice N of 19") und Fehlerdialog.
  - Ohne den Schalter ändert sich nichts.
- **App:**
  - Titel "The Great Green Mouse Disaster", eigene RSF `config/ggmd.rsf` (UniqueId `0xF8D4B`, Title-ID `000400000F8D4B00`, Produktcode `CTR-H-GGMD`). Beide Fassungen lassen sich also nebeneinander installieren.
  - Banner, Icon und Banner-Ton aus dem englischen Titelbild (`scripts/make_app_art.py` findet `GGMD.EXE`; der Startfilm hat dieselbe Belegung wie der deutsche).
  - Eigener Build-Ordner `~/build/3ds-en`.
  - Das Menü der englischen Fassung hat dieselben Bausteine für die Hotelkarte (Bild `interfinalfordir0001`, `roomlist`, `soundlist`).
- **Geprüft (Azahar, 2026-11-12):**
  - Erkennung "Windows/English", Start mit Macmillan-Logo und englischem Intro.
  - Hotelkarte mit "Mice 0 of 19", Fehlerdialog auf Englisch (ausgelöst durch einen Direkteinstieg in die Hotelübersicht).
  - Im ELF stehen die englischen Texte und `sdmc:/3ds/ggmd/`, die deutschen fehlen; ctrtool zeigt die Title-ID `000400000F8D4B00`.
  - Durchspielen auf dem 3DS steht aus.

### CIA (`CIA=1`, Wunsch des Nutzers, 2026-11-11)

```bash
bash /mnt/c/Users/Alphe/Documents/GitHub/MJIGH3DS/scripts/build-ctr-tools.sh          # einmalig: makerom, bannertool, ctrtool
CIA=1 bash /mnt/c/Users/Alphe/Documents/GitHub/MJIGH3DS/scripts/build-3ds.sh          # -> dist/3ds/mausjagd.3dsx und mausjagd.cia
```

- **Werkzeuge aus dem Quellcode** (Entscheidung des Nutzers; Release-Binaries wurden nicht verwendet):
  - `scripts/build-ctr-tools.sh` klont die festen Tags, prüft den Commit und baut nach `~/ctr-tools/bin`; die Herkunft steht in `~/ctr-tools/SOURCES.txt`.
  - makerom 0.19.0 und ctrtool 1.3.0 kommen aus 3DSGuy/Project_CTR, Commit `e8f5f529`; die Abhängigkeiten liegen im Repo.
  - bannertool 1.2.3 kommt aus carstene1ns/3ds-bannertool, Commit `da573b13`. Es wird ohne cmake direkt mit g++ übersetzt, wie in der `CMakeLists.txt` beschrieben. Das optionale Ziel `update-libs` (lädt Bibliotheken nach) bleibt ungenutzt.
  - SHA-256 (2026-11-11): makerom `a0b5b4b2…`, ctrtool `98c02fe8…`, bannertool `5fe0dbde…`. bannertool baut bit-gleich nach; makerom trägt die Bauzeit im Binary.
- **Build:** `make scummvm.cia` aus `backends/platform/3ds/3ds.mk` mit `APP_RSF=config/mausjagd.rsf` sowie `MAKEROM`/`BANNERTOOL` aus `~/ctr-tools`. ELF, SMDH und RomFS sind dieselben wie bei der `.3dsx`, das Spiel steckt also auch im CIA. **Nur für den eigenen Gebrauch.** `DIAG=1` ergibt `mausjagd-diag.cia` mit derselben Title-ID, also überschreibt die Installation das normale CIA. Für `MAUSJAGD_PORT=0` gibt es kein CIA, weil es die Title-ID des offiziellen ScummVM hätte.
- **`config/mausjagd.rsf`:**
  - Grundlage ist die Vorlage von ScummVM. UniqueId `0xF8D4A`, also Title-ID `000400000F8D4A00`.
  - Freigegeben sind nur die 8 Dienste, die das Binary anfragt; die Vorlage hat 30.
  - Ohne SVC `Backdoor`. Details und Prüfung mit ctrtool in `docs/security.md` §9 (S7).
- **Icon, Banner und Banner-Ton aus dem Spiel** (`APP_ART=1`, Standard bei eingebetteten Spieldaten; Wunsch des Nutzers, 2026-11-11):
  - `scripts/make_app_art.py` liest den in `MAUSJAGD.EXE` eingebetteten Startfilm. Es dekodiert Cast 9 "german splashscreen" (640×480, 8 Bit, RLE, Palette Cast 8) und Cast 6 "Theme.aif" (`snd`, 22 050 Hz, 8 Bit, 12,4 s). Dafür reicht die Standardbibliothek; die Chunks liest `tools/dxr_inventory.py`.
  - **Banner** 256×128: obere zwei Drittel des Titelbilds (Logo, Hotelfassade, Portier). **Icon** 48×48: die grünen Mäuse in der Hand des Pagen; es gilt auch für die `.3dsx`. Beide sind mit Flächenmittel verkleinert.
  - **Banner-Ton:** die ersten 3,0 s der Titelmelodie als 16-Bit-PCM, auf 90 % Spitzenpegel angehoben und 0,35 s ausgeblendet (die Phrase endet bei 3,25 s).
  - Die Dateien entstehen nur in `~/build/3ds/app-art` und kommen nie ins Repo (PLAN.md §7). Laut §7 sind Spielgrafiken nur in einer weitergegebenen App tabu; dieser Build ist ohnehin nur für den eigenen Gebrauch.
  - Mit `APP_ART=0` oder `EMBED_GAME=0` gelten Icon und Banner von ScummVM. Ein selbst gestaltetes Icon und Banner für eine weitergebbare Fassung bleibt T6.2.
  - Geprüft: `banner` und `icon` im ExeFS des CIA sind byte-gleich mit den neu erzeugten `scummvm.bnr`/`scummvm.smdh`. Das in Azahar neu installierte CIA startet.
- **Ergebnis:** `mausjagd.cia` 202 MB, `.3dsx` 201 MB.
- **Azahar:** `azahar.exe -i <cia>` installiert, beendet sich danach aber nicht selbst. Danach steht das Spiel in der Liste der installierten Titel. Für einen automatischen Lauf geht auch `scripts/azahar-run.ps1 -Game <…\title\00040000\0f8d4a00\content\*.app>`.
- **Per QR-Code installieren** (ohne SD-Karte, Wunsch des Nutzers): `py -P scripts/serve_cia.py dist/3ds/final/mausjagd.cia` (Windows; `segno` aus den Benutzer-Paketen, deshalb `-P` statt `-I`).
  - Das Skript bietet nur diese eine Datei per HTTP im WLAN an (`http://<PC-IP>:8080/mausjagd.cia`), ohne Verzeichnisliste; andere Pfade liefern 404.
  - Es öffnet den QR-Code mit der URL als Bild. Auf dem 3DS: FBI → Remote Install → Scan QR Code. Danach lädt FBI das CIA vom PC und installiert es.
  - Der Server endet nach dem ersten vollständigen Download (`--keep` lässt ihn weiterlaufen), spätestens nach 30 Minuten (`--minutes`). Das Spiel verlässt das Heimnetz nicht.
  - 3DS und PC müssen im selben WLAN sein. Ist das WLAN in Windows als "Öffentlich" eingestuft, blockiert die Firewall eingehende Verbindungen; beim ersten Start fragt sie nach (Python zulassen) oder das Netz auf "Privat" stellen.
  - Getestet am PC (2026-11-11): HEAD 200 mit richtiger Länge, andere Pfade 404, Download beginnt mit dem CIA-Kopf.
  - **Auf dem 3DS** (2026-11-11, New 3DS des Nutzers): FBI hat nach dem Scan die ganze CIA geladen, 202,6 MB in 199 s (etwa 1 MB/s). Danach hat sich der Server beendet. Die Firewall hat den Zugriff trotz WLAN-Profil "Öffentlich" durchgelassen.
  - Alternative für den eigenen Gebrauch: CIA in Google Drive mit Link-Freigabe; dazu ein QR-Code mit dem direkten Link `https://drive.usercontent.google.com/download?id=<Datei-ID>&export=download&confirm=t`. Ohne `confirm=t` zeigt Drive bei großen Dateien eine Warnseite. Am PC geprüft: liefert die CIA ohne Weiterleitung, und der Server nimmt TLS 1.2 mit `AES128-SHA` an. Nach der Installation die Freigabe zurücknehmen, sonst kann jeder mit dem Link das Spiel laden.
- **Auf dem 3DS:** `mausjagd.cia` auf die SD-Karte kopieren und z. B. mit FBI installieren. Danach startet das Spiel vom HOME-Menü. Konfiguration, Log und Spielstände liegen wie bei der `.3dsx` in `SD:\3ds\mausjagd\`; beide Fassungen teilen sie sich.

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
