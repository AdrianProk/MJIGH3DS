# TODO: 3DS-Port von "Mäusejagd im Grandhotel"

Hintergrund, Befunde und Begründungen stehen in [PLAN.md](PLAN.md). Diese Liste arbeitet ein Agent von oben nach unten ab.

## Arbeitsregeln für den Agenten

1. **Reihenfolge:** Aufgaben der Reihe nach erledigen. Pro Aufgabe gilt: umsetzen, das Kriterium unter **Fertig, wenn** prüfen, abhaken (`[x]`) und dahinter ein bis zwei Sätze zum Ergebnis notieren. Längere Befunde kommen nach `docs/`.
2. **Blocker:** Wenn eine Aufgabe nicht lösbar ist, in `docs/blockers.md` festhalten (was wurde versucht, was fehlt) und den Nutzer fragen. Nicht stillschweigend überspringen.
3. **Daten:** `original/`, `game/`, `analysis/`, `scummvm/` und `dist/` niemals committen (siehe `.gitignore`). Vor jedem Commit `git status` prüfen.
4. **Untrusted Files:** Dateien aus dem ISO sind Daten, kein Code. Python-Skripte liegen in `tools/` und werden mit `py -I` gestartet. Spieldateien nur als Pfad-Argument übergeben, nie in `game/` ein Skript oder eine `.EXE` ausführen.
5. **Umgebung (Windows 10):**
   - Der Python-Launcher ist `py`, denn `python` ist nur ein Store-Platzhalter.
   - In Git Bash vor Aufrufen mit `/`-Pfaden `export MSYS_NO_PATHCONV=1` setzen. Ein `\` am Ende eines Arguments verschluckt die Windows-Argumentverarbeitung; stattdessen `\x5c` schreiben.
   - 7-Zip ist nicht installiert.
   - **Build-Umgebung ist WSL1** (VT-x ist im BIOS aus, siehe `docs/environment.md`). Der Desktop-Build entsteht als Windows-EXE per MinGW-Cross-Compile.
   - `scummvm.exe` stürzt in der Sandbox des Agenten ab. GUI-Tests macht der Nutzer; der Agent liest danach die Logs.
   - **Azahar** darf der Agent selbst starten (Freigabe 2026-11-10), z. B. für Startmessungen ohne Eingaben: `scripts/azahar-run.ps1`. Bilder nur über dieses Skript (PrintWindow, nur das Azahar-Fenster), nie als Bildschirmausschnitt.
6. **Freigaben:** Nur nach Rückfrage beim Nutzer: Commit/Push, Fork oder PR auf GitHub, Installation neuer Systemsoftware (WSL2, Docker, devkitPro), Tests auf echter 3DS-Hardware, Entscheidungen an den Gates G1/G2.
7. **Patches:** Änderungen an ScummVM nur im Branch `mausjagd` des Forks vornehmen. Der Fork liegt seit WSL1 unter `~/scummvm` in Ubuntu, nicht mehr in `scummvm/` im Repo. Nach jeder abgeschlossenen Aufgabe mit Engine-Änderungen die Serie neu exportieren: `git -C ~/scummvm format-patch --no-signature upstream-base..mausjagd -o /mnt/c/Users/Alphe/Documents/GitHub/MJIGH3DS/patches/` (vorher alte `*.patch` löschen). Port-spezifischer Code steht hinter `#ifdef MAUSJAGD_PORT`.
8. **Sicherheit:** Für jeden Patch gelten die Regeln aus PLAN.md §10: nur in den App-Ordner schreiben, keine unnötigen Systemdienste, Längen prüfen und Zeichenoperationen begrenzen, Fehler sauber behandeln. Vor jedem Test auf echter Hardware laufen S1 und S4 für die neuen Patches.

---

## Phase 0: Repo und Umgebung

- [x] **T0.1** Ordner `tools/`, `scripts/`, `patches/`, `config/` und `docs/` anlegen (leere Ordner bekommen eine `.gitkeep`). In `docs/README.md` beschreiben, welches Dokument wohin gehört.
  *Fertig, wenn:* die Struktur der in PLAN.md §4 entspricht und `git status` weder `original/` noch andere ignorierte Ordner zeigt.
  → Erledigt 2026-11-09. Die Struktur steht, und `git status` zeigt nur eigene Dateien.
- [x] **T0.2** Werkzeuge prüfen und in `docs/environment.md` notieren: `py --version`, `git --version`, WSL2 (`wsl -l -v`), Docker, freier Plattenplatz (≥ 10 GB für ScummVM und die Toolchain).
  *Fertig, wenn:* die Datei existiert und notiert, was fehlt. Installationen nur nach Freigabe (Regel 6).
  → Erledigt. Python 3.13 und Git sind vorhanden. **Es fehlen WSL2, Docker, Compiler und devkitPro**; vor Phase 3 braucht es eine Freigabe für die Installation. Freier Platz: 410 GB.

## Phase 1: ISO extrahieren und inventarisieren

- [x] **T1.1** `tools/iso_extract.py` schreiben, nur mit der Python-Standardbibliothek. Der ISO9660-Reader liest den PVD ab Sektor 16 und läuft rekursiv über die Verzeichnisse; Versionssuffixe `;1` werden abgeschnitten. Unterbefehle:
  - `list ISO`: Pfad, Größe, LBA
  - `extract ISO ZIELORDNER [--profile game|all]`: Extraktion mit Whitelist
  - Profil `game` = alle Dateien im Wurzelverzeichnis außer Installern/Beilagen, plus `SOUNDS/`, `MUSIC/`, `MUSIC8/`, `SOLOS/`, `SOLOS8/`, `STARTSND/`, `ENDSOUNG/`, `GERHELP/`, `GERVIDEO/`, `BILDER/`. Beilagen-Ordner laut PLAN.md §1 auslassen.

  *Fertig, wenn:* `list` 27 `.DXR` und 27 `.MOV` findet und der Code nur liest. Die ISO wird nie verändert.
  → Erledigt. Das ISO hat 1494 Einträge. Das Profil `game` nimmt bewusst **alle** Wurzeldateien mit, weil die Klassifizierung erst in T1.4 kommt. Ein schlankeres Profil nur mit den nötigen Dateien folgt in T6.4.
- [x] **T1.2** Mit `--profile game` nach `game/` extrahieren. Großschreibung und 8.3-Namen beibehalten.
  *Fertig, wenn:* Anzahl und Größe jeder Datei mit `list` übereinstimmen (das Skript prüft das selbst) und `game/` ca. 180 MB groß ist.
  → Erledigt. 489 Dateien (198,1 MB), Größenprüfung ok.
- [x] **T1.3** `tools/inventory.py` schreiben. Es erzeugt `docs/inventory.md` mit Pfad, Größe, SHA-1 und Kategorie (movie, video, sound, music, xlib, projector, doc, extra) für jede Datei in `game/`. Nur Metadaten, keine Inhalte.
  *Fertig, wenn:* die Datei vollständig ist und sich reproduzierbar neu erzeugen lässt.
  → Erledigt. Die Klassifizierungsregeln stehen im Skript; das Skript bricht bei unklaren Dateien ab.
- [x] **T1.4** Unklare Dateien klassifizieren: `GALLERY.EXE`, `PEARL.EXE`, `ONLINE.EXE`, `BILDER/*.BMP`, `AUFTRAG.PDF`, `KONFIG.PDF`, `README.TXT`, `INSTALL.WRI`. Prüfen über Strings und Header, z. B. ob ein `RIFX`/`XFIR` eingebettet ist (dann ist es ein weiterer Director-Projektor), und ob die Spielfilme sie referenzieren (spätestens in T2.4).
  *Fertig, wenn:* jede Datei in `docs/inventory.md` als "nötig" oder "Beilage" markiert ist, jeweils mit Begründung.
  → Erledigt. Ergebnis: 442 nötig (176 MB), 22 optional, 25 Beilage.
    - **Optional:** `GALLERY.EXE` ist eine eigene Zusatz-App (D4-Projektor), `STARTSND/` gehört nur zu ihr, dazu die Anleitungen.
    - **Beilage:** `PEARL.EXE` (D7-Katalog), `ONLINE.EXE`, die PDFs, `README.TXT` (AGB eines Telefonanbieters) und die Ausmalbilder in `BILDER/`.
    - **Bonus:** `README.WRI` ist die Spielanleitung. Eine Zusammenfassung in eigenen Worten steht in `docs/gameplay.md`.
- [x] **T1.5** Startablauf klären: Welchen Film öffnet `MAUSJAGD.EXE` zuerst? Ist darin ein Film eingebettet (nach `RIFX`/`XFIR`/`MV93` suchen), oder nennt der Projektor nur externe Dateien (vermutlich `GGMDMENU.DXR`)? Wie wird `LINGO.INI` geladen?
  *Fertig, wenn:* `docs/startup.md` den Ablauf vom Projektor bis zum ersten Bildschirm beschreibt.
  → Erledigt. Ablauf: `MAUSJAGD.EXE` → `LINGO.INI` → eingebetteter Startfilm `GGMDSTRT.DIR` (Farbtiefe, CD-Prüfung per FileIO, XObject **Backdrop**, `theme.aif`) → `GGMDMENU.DXR`. Die 8-Bit-Musik wird über `gMusicPath`/`gSolosPath` gewählt.
- [x] **T1.6** *(optional, Freigabe nötig)* Referenz für das Originalverhalten festlegen: eine Win9x-VM (86Box/VirtualBox) mit dem Originalspiel oder ein Longplay-Video. Den Nutzer fragen, was gewünscht ist.
  *Fertig, wenn:* die Entscheidung in `docs/reference.md` steht.
  → Erledigt. Der Nutzer wählte ein Longplay-Video, im Netz war aber keins zu finden. Ersatz: der dekompilierte Code und die Anleitung. Ein Link wird nachgetragen, falls der Nutzer ein Video findet.

## Phase 2: Analyse und Lingo-Dekompilierung

- [x] **T2.1** `tools/dxr_inventory.py` schreiben. Es parst `RIFX` (Big-Endian) über die `mmap` und listet pro DXR die Chunk-Typen samt Anzahl, Cast-Member nach Typ (Bitmap, Sound, Script, Text, Palette, Digital Video/`MooV`, Shape …), die Zahl der Lingo-Skripte und die Größe des Scores.
  *Fertig, wenn:* `docs/dxr-inventory.md` alle 27 Filme abdeckt.
  → Erledigt. Abgedeckt sind 27 Filme plus der eingebettete Startfilm. Die Cast-Listen mit Namen und Bitmap-Größen liegen in `analysis/cast/` (ignoriert). Befunde:
    - **Videos:** Sie sind mit Mac-Pfaden der Entwickler verknüpft (`PixelMagic1:GGMD:kitchen.mov`, `GGMD German Mac:endseq.mov`). ScummVM muss sie über den Dateinamen finden (T3.6).
    - **Maus:** Die Bilder heißen `mice0xxx` (312 Stück in `SHARED.DXR`), Median **39×28 px** (min 14×10, max 67×74). Auf dem Touchscreen sind das etwa 19×14 px.
    - **Fallen:** `trap1`–`trap5` (35×31), `trapmark`, `traphilite`.
    - **Auffällig:** `KITCHEN.DXR` hat 342 `Lscr`-Chunks bei nur 13 Skript-Casts. Das in T2.2 prüfen.
- [x] **T2.2** ProjectorRays (github.com/ProjectorRays/ProjectorRays) besorgen: ein Release-Binary oder selbst bauen. Prüfen, ob D4 unterstützt wird. Alle 27 DXR dekompilieren und die Ausgabe nach `analysis/lingo/<FILM>/` legen (ignoriert, Regel 3). Falls ProjectorRays mit D4 scheitert, die Skript-Dump-Funktion der Director-Engine von ScummVM verwenden; sie steht ab T3.2 zur Verfügung.
  *Fertig, wenn:* für jeden Film lesbarer Lingo-Code vorliegt oder in `docs/blockers.md` begründet ist, warum nicht.
  → Erledigt mit ProjectorRays v0.2.0, lokal in `vendor/` (ignoriert). SHA-256 der EXE: `e9814428…c70db`. Aufruf: `vendor/projectorrays/projectorrays-0.2.0.exe decompile game/<FILM>.DXR --dump-scripts -o analysis/lingo/<FILM>`; der Ausgabeordner muss vorher existieren.
    - **Ergebnis:** 543 Skripte aus 27 DXR plus dem Startfilm.
    - **Projektor:** Den D4-Projektor kann ProjectorRays nicht lesen. Deshalb schneidet `tools/extract_projector_movie.py` den eingebetteten `GGMDSTRT.DIR` heraus und rechnet die Offsets um. Beim Zurückschreiben bricht ProjectorRays an einem leeren `THUM`-Chunk ab, die Skripte sind aber vollständig ausgegeben.
    - **KITCHEN:** Die 342 `Lscr`-Chunks sind Altlasten; aktiv sind 13 Skripte.
- [x] **T2.3** Spielablauf rekonstruieren: alle `go to movie`, `play movie`, `go to frame`, `play done` und Marker auswerten. Ergebnis in `docs/game-flow.md` als Mermaid-Diagramm (Film → Film) plus Tabelle mit Raum, Film, Video und Rätsel bzw. Aktion.
  *Fertig, wenn:* jeder der 27 Filme im Graphen vorkommt und erreichbar ist (oder als unbenutzt markiert ist).
  → Erledigt: `docs/game-flow.md`. Ablauf: Start → Menü/Hotelübersicht → 19 Fangräume → (Musik: INSTRUM → ORCH) → Menü … → nach 19 Räumen ATTIC → THEEND → CREDITS. EXIT ist über das Hotel-Symbol oder Esc erreichbar. SHARED ist der Shared Cast. Kein Film ist unbenutzt.
- [x] **T2.4** Externe Abhängigkeiten in `docs/dependencies.md` dokumentieren:
  - XObjects/Xlibs (`FileIO`, **Backdrop** aus dem Startfilm und eventuell weitere) mit allen aufgerufenen Methoden. Bei Backdrop klären, ob es auch unter Windows aufgerufen wird.
  - Sound-Aufrufe (`sound playFile`, `puppetSound` …) mit den verwendeten Pfaden
  - QuickTime-Casts und -Aufrufe
  - Nutzung von `theCDpath`/`theHDpath`/`gCPU`/`gMusicPath`
  - Systemabfragen (`the machineType`, `the colorDepth`, Laufwerks- und CD-Prüfungen)
  - Speichern und Laden (Dateinamen, Format)

  *Fertig, wenn:* jede externe Datei und jedes XObject mit Fundstelle (Film/Skript) aufgelistet ist.
  → Erledigt: `docs/dependencies.md`.
    - **XObjects:** Unter Windows wird nur FileIO benutzt (`read`, `append`, `mReadFile`, `mWriteString`). Backdrop gibt es nur im Mac-Zweig.
    - **Pfade:** fünf Anforderungen an die Pfadauflösung in ScummVM, Grundlage für T3.6.
    - **Risiken für ScummVM:** Warteschleifen über `the timer`, leere Zählschleifen, sowie Abfragen von `the mouseDown`, `the soundBusy` und `the movieRate` innerhalb von Schleifen.
- [x] **T2.5** Histogramm der verwendeten Lingo-Befehle, Properties und Events über alle Skripte erstellen (`tools/lingo_stats.py` auf `analysis/lingo/`). Das Ergebnis in `docs/lingo-features.md` ablegen. In T3.3 wird es mit dem Implementierungsstand von ScummVM abgeglichen.
  *Fertig, wenn:* die Liste nach Häufigkeit sortiert ist.
  → Erledigt: `docs/lingo-features.md`, erzeugt von `tools/lingo_stats.py`. Der Umfang ist klein und klassisch für D4: 4 Event-Typen, 37 Builtins und 39 Properties. Am häufigsten: `go`, `puppetSound`, `puppetSprite`, `updateStage`, `sound playFile`, `play frame`.
- [x] **T2.6** Fangmechanik analysieren. Das ist das Kernfeature (PLAN.md §3). Startpunkte aus den Namenstabellen sind `mymouse`, `waitmouse`, `holdmouse`, `movemouse`, `hideplaces`, `hidepos`, `clicked`, `caught`, `settraps`, `selecttrap`, `checktrap`, `trapsdone`, `miceCaught` und `countup`; die Raum-Logik steckt vermutlich größtenteils in `SHARED.DXR`. Ermitteln und in `docs/mouse-catching.md` festhalten:
  - In welchen Filmen werden Mäuse gefangen, wie viele pro Raum? Wie hängen Fallen und Orchester (`ORCH.DXR`, `INSTRUM.DXR`) damit zusammen?
  - Welche Cast-Member und Sprite-Kanäle sind Mäuse bzw. anklickbare Fallen? Daran erkennt die Treffhilfe (T5.3) ihre Ziele.
  - Wie wird der Klick erkannt: `mouseDown` oder `mouseUp`, Sprite-, Cast- oder Frame-Skript, `the clickOn`, `the mouseH`/`the mouseV`?
  - Wie groß sind die Maus-Sprites (Pixel bei 640×480 und bei halber Auflösung), und wie lange sind sie sichtbar (`waittime`, Tempo)?
  - Wofür werden `rollOver` (`GGMDMENU`, `ATTIC`/`rollovermap`) und die Tastenabfragen (`keyCode`, `commandDown`, `optionDown`) gebraucht?

  *Fertig, wenn:* für jeden Fangraum die Maus-Sprites mit Größe, Sichtbarkeitsdauer und Klicklogik aufgelistet sind und geklärt ist, wofür Hover und Tasten gebraucht werden.
  → Erledigt: `docs/mouse-catching.md` und `docs/room-stats.md` (erzeugt von `tools/room_stats.py`). Kernpunkte:
    - **Fangen:** Die laufende Maus ist ein Score-Sprite mit `on mouseDown caught()`; gefangen wird also beim **Aufsetzen**.
    - **Verstecke:** Sprites 30+ mit `on mouseUp clicked()`, 8–10 pro Raum.
    - **Laufzeit:** Median 34 Frames, also 4,2 s auf Level 1 und 1,5 s auf Level 3 nach 15 Mäusen; der kürzeste Weg dauert 0,36 s.
    - **Größe:** Die Maus misst etwa 19×14 Touch-Pixel.
    - **Fallen:** Die Animationen `1.x`–`5.x` sind ebenfalls fangbar.
    - **Hover:** Das Mausometer reagiert auf `rollOver` und muss per Ziehen bedienbar sein.
    - **Tasten:** Esc (Beenden-Dialog), Return (Namenseingabe).

## Phase 3: ScummVM auf dem PC

- [ ] **T3.1** Smoke-Test mit dem aktuellen offiziellen ScummVM-Release für Windows: `game/` hinzufügen. Wird das Spiel erkannt? Wenn nicht, die Fallback-Erkennung für unbekannte Director-Spiele laut ScummVM-Doku nutzen. Wie weit läuft es? Ergebnis als ersten Eintrag in `docs/compat-log.md`. Das ScummVM-Release liegt außerhalb des Repos oder in `dist/`.
  *Fertig, wenn:* der Status (startet / Menü / erster Raum / Absturz + Meldung) dokumentiert ist.
  → **Teilweise erledigt** (2026-11-09), siehe `docs/compat-log.md`. ScummVM 2026.4.0 liegt in `vendor/`.
    - **Erkennung (korrigiert 2026-11-10):** Das Spiel ist in ScummVM bereits bekannt, als `ggmd` "The Great Green Mouse Disaster", Windows, `DE_DEU`, Director 404. Der Eintrag braucht `MAUSJAGD.EXE` **und** `SHARED.DXR`; beide MD5s passen zu unserer ISO. Der zuerst gemeldete Fallback kam aus einem Testordner ohne `SHARED.DXR`.
    - In der Agenten-Sandbox stürzt `scummvm.exe` bei jedem Aufruf beim Beenden ab, auch bei `--version`.
    - **Offen:** der GUI-Spieltest durch den Nutzer nach der Anleitung in `compat-log.md`; danach wertet der Agent das Log aus.
- [x] **T3.2** ScummVM aus den Quellen bauen: `git clone https://github.com/scummvm/scummvm scummvm`, Tag oder Commit als `upstream-base` markieren, Branch `mausjagd` anlegen. Den Desktop-Build mit Director-Engine einrichten: in **WSL1** (Ubuntu), Quellcode im Linux-Dateisystem, Cross-Compile mit MinGW-w64 (`--host=x86_64-w64-mingw32`, SDL2 für MinGW) zu einer Windows-EXE. Befehle und Abhängigkeiten in `scripts/build-desktop.sh` und `docs/build-desktop.md` festhalten.
  *Fertig, wenn:* das selbst gebaute ScummVM startet und T3.1 reproduziert.
  → **In Arbeit** (2026-11-10):
    - Klon in WSL1 unter `~/scummvm` (blobless, `--filter=blob:none`).
    - `upstream-base` = `7c924b93038495de3d8cf673002e5a6f50ff0a8c` (Master vom 2026-11-10, nach `v2026.4.0`); Branch `mausjagd` angelegt.
    - Achtung: Befehle, die alte Versionen durchlaufen (`git log -L`, `git log -S`, `git blame`), laden im blobless-Klon jede Version einzeln nach und dauern sehr lange. Lieber einzelne Revisionen mit `git show <rev>:<pfad>` abfragen.
    - **Fokus (Absprache 2026-11-10):** Vorerst nur den **nativen Linux-Build** für die Tests des Agenten. Der MinGW-Windows-Build ist **zurückgestellt**, denn für die GUI-Tests des Nutzers reicht das offizielle Release, bis eigene Patches existieren. `scripts/build-desktop.sh win64` und SDL2 in `~/mingw-prefix` sind vorbereitet, aber noch nicht genutzt. Danach direkt weiter mit T4.1 (devkitPro); bei Problemen mit WSL1 auf den Windows-Installer von devkitPro ausweichen.
    - **Erledigt** (2026-11-10):
      - `bash scripts/build-desktop.sh linux` baut `~/build/linux/scummvm`, Doku in `docs/build-desktop.md`.
      - Der eigene Build erkennt das Spiel (`ggmd-win-de`) und läuft ohne Fenster bis ins Menü (`GGMDMENU.DXR`) und zum Intro-Video. Das reproduziert T3.1 und geht darüber hinaus, siehe `docs/compat-log.md`.
- [ ] **T3.3** In `engines/director/detection_tables.h` nach einem vorhandenen Eintrag suchen (englische Version, Mac-Version, Stichwörter "mouse", "GGMD"). Einen Eintrag für die deutsche Windows-Version anlegen: Director 404, `DE_DEU`, `MAUSJAGD.EXE` mit MD5 und Größe, die ScummVM beim Hinzufügen meldet. Die Game-ID am vorhandenen englischen Eintrag ausrichten, sonst eine neue vergeben (z. B. `greatgreenmouse`). Zusätzlich `docs/lingo-features.md` mit ScummVM abgleichen: Befehle, die in `engines/director/lingo/` als nicht implementiert gelten (STUB/`warning`), markieren.
  *Fertig, wenn:* ScummVM das Spiel ohne Fallback erkennt und die Liste fehlender Features steht.
  → **Erkennung schon vorhanden** (2026-11-10): `engines/director/detection_tables.h`, Game-ID `ggmd`. Der Eintrag ist `WINGAME2_l("ggmd", "", "MAUSJAGD.EXE", "d:04d63d66464bce6356f9d70d83487838", 1302352, "SHARED.DXR", "d:15f0add56f03a01a98b076f4792608f6", 389060, Common::DE_DEU, 404)` und steht schon in `v2026.4.0`. Ein eigener Patch ist nicht nötig. Quirks hängen später an `ggmd`. **Offen** ist nur noch der Abgleich der Lingo-Features.
- [ ] **T3.4** Testmatrix in `docs/compat-log.md` anlegen: eine Zeile pro Film bzw. Raum aus `docs/game-flow.md`, Spalten Grafik, Klickflächen, Mäuse fangen, Sound, Musik, Video, Übergänge, Status. Jeden Raum mit aktiven Debug-Kanälen (`lingo`, `loading`, `score`, `sound`, `video`) durchspielen und Warnungen sammeln.
  *Fertig, wenn:* jeder Raum einen Status hat.
- [ ] **T3.5** Fehler beheben. Für jeden Fehler gilt dieser Ablauf:
  1. Eintrag in `docs/compat-log.md`
  2. Ursache gegen den dekompilierten Lingo-Code eingrenzen
  3. Fix in der Engine; spielspezifische Workarounds nur als Quirk in `engines/director/game-quirks.cpp`
  4. wo möglich ein Lingo-Testskript nach dem Vorbild in `engines/director/lingo/tests/`
  5. Patch-Export (Regel 7)

  Die Fixes sollen klein und upstream-tauglich sein.
  *Fertig, wenn:* keine Zeile der Matrix mehr "kaputt" ist.
- [ ] **T3.6** Pfade und `LINGO.INI` prüfen: Wird `LINGO.INI` ausgeführt? Werden `D:\…`-Pfade, `music\`/`solos\` und `theCDpath` richtig aufgelöst? Welche Musikvariante wählt `gCPU = "486"` (`MUSIC` oder `MUSIC8`)? Bei Bedarf einen Quirk für Pfade oder Variante anlegen.
  *Fertig, wenn:* alle Sound- und Musikdateien laut `docs/dependencies.md` gefunden werden; im Log stehen keine "file not found"-Warnungen.
- [ ] **T3.7** Medien prüfen: Alle 27 MOVs spielen mit Ton (SMC + raw/twos) und synchron; die Hilfevideos `GERHELP/` und das Intro `GERVIDEO/GERINTRO.MOV` laufen; Paletten wechseln korrekt (kein Farbmüll nach Videos).
  *Fertig, wenn:* jedes Video in der Matrix den Status "ok" hat.
- [ ] **T3.8** Speichern und Laden (FileIO) testen: Spielstand anlegen, ScummVM neu starten, Spielstand laden.
  *Fertig, wenn:* der Spielstand erhalten bleibt und die Datei im ScummVM-Savepfad liegt.
- [ ] **T3.9** Kompletter Durchlauf vom Intro bis zum Abspann (`ENDSEQ.MOV`, `CREDITS.DXR`, `THEEND.DXR`) ohne Absturz.
  *Fertig, wenn:* der Durchlauf protokolliert ist.
- [ ] **G1 Gate:** Dem Nutzer den Stand berichten. Bei grundlegenden Blockern die Alternativen aus PLAN.md §2 vorlegen und auf die Entscheidung warten.

## Phase 4: 3DS-Build

- [ ] **T4.1** 3DS-Toolchain einrichten (Freigabe nötig, Regel 6): devkitPro mit devkitARM, libctru, citro3d und den Portlibs laut `scummvm/backends/platform/3ds/README.md`, dazu `bannertool` und `makerom`. Installation in **WSL1** (Ubuntu) über das devkitPro-pacman; als Rezept dient `scummvm/dockerized-bb`. Alles in `docs/build-3ds.md` dokumentieren.
  *Fertig, wenn:* `arm-none-eabi-gcc --version` in der Build-Umgebung läuft.
  → **Erledigt** (2026-11-10, Freigabe des Nutzers: "ja geh so vor"):
    - devkitpro.org sperrt automatisierte Downloads (Cloudflare/403), deshalb kommt die Toolchain aus dem offiziellen Docker-Image `devkitpro/devkitarm:20260610`. Geladen ohne Docker mit `scripts/fetch_docker_subtree.py` nach `~/devkitpro`, jede Schicht SHA-256-geprüft.
    - `arm-none-eabi-gcc (devkitARM) 16.1.0` läuft. libctru, citro3d und die Portlibs sind vorhanden; `bannertool` und `makerom` (nur für CIA) fehlen.
    - Symlink `/opt/devkitpro` → `~/devkitpro` hat der Nutzer als root angelegt, siehe `docs/build-3ds.md`.
- [ ] **T4.2** Basis-Build: unverändertes `upstream-base` für den 3DS mit nur der Director-Engine bauen (`./configure --host=3ds --disable-all-engines --enable-engine=director`, Flags gegen das README prüfen), dann `make scummvm.3dsx`.
  *Fertig, wenn:* die `.3dsx` im Emulator Azahar startet.
  → **Build erledigt** (2026-11-10): `bash scripts/build-3ds.sh` erzeugt `dist/3ds/scummvm.3dsx` (24,9 MB) aus dem unveränderten `upstream-base`. **Offen:** Starttest im Emulator oder auf echter Hardware.
- [ ] **T4.3** Branch `mausjagd` für den 3DS bauen. `scripts/build-3ds.sh` erzeugt `dist/mausjagd.3dsx` reproduzierbar.
  *Fertig, wenn:* das Skript auf einem frischen Checkout durchläuft.
  → **Weitgehend erledigt** (2026-11-10):
    - `scripts/build-3ds.sh` erzeugt `dist/3ds/mausjagd.3dsx` aus dem Branch `mausjagd` mit den Patches 0001 und 0002.
    - Das Spiel startet direkt, ohne Launcher. Die Spieldaten (442 Dateien, laut Inventar geprüft) stecken in der RomFS; die `.3dsx` ist 201 MB groß.
    - Wunsch des Nutzers: "keinen Launcher", "Spieldateien in die 3dsx".
    - **Offen:** Test auf dem Gerät, Lauf auf frischem Checkout.
- [ ] **T4.4** Emulator-Test in Azahar: `game/` auf die virtuelle SD kopieren, das Spiel hinzufügen und Menü sowie ersten Raum starten. Danach die Matrix aus T3.4 als zweite Spalte "3DS-Emu" durchgehen.
  *Fertig, wenn:* die Spalte ausgefüllt ist.
  → **Erster Lauf** (2026-11-10, Nutzer): Port-Build mit eingebetteten Daten und `dspfirm.cdc` auf der virtuellen SD.
    - Läuft: Direktstart, Startfilm, Menü, Intro mit Ton und der erste Raum.
    - Befunde B1–B6 (Verzerrung und 5 FPS beim Fangen, weiße Figuren, Rechteck beim Tippen, Startwarnung, lange Startzeit) stehen in PLAN.md §9 und werden in T4.6–T4.12 bearbeitet.
    - Die Matrix-Spalte folgt nach deren Behebung.
- [ ] **T4.5** Test auf echter Hardware (Freigabe und Hilfe des Nutzers nötig): New 3DS und, falls vorhanden, Old 3DS, per `3dslink` oder als CIA.
  *Fertig, wenn:* die Spalten "New 3DS" und "Old 3DS" in der Matrix ausgefüllt sind.
  → **Stand 2026-11-10:** Der Nutzer hat einen **New 3DS / New 2DS XL** mit Homebrew Launcher. Getestet wird zuerst die `.3dsx`, Anleitung in `docs/compat-log.md`.
    - **CIA gebaut** (2026-11-11): Der Nutzer hat erlaubt, `makerom` und `bannertool` aus dem Quellcode zu bauen (`scripts/build-ctr-tools.sh`). `CIA=1 bash scripts/build-3ds.sh` erzeugt `dist/3ds/mausjagd.cia` mit eigener RSF (`config/mausjagd.rsf`, Title-ID `000400000F8D4A00`). Im Emulator installiert und gestartet; auf dem Gerät noch offen (`docs/build-3ds.md`, Abschnitt "CIA").

### Befunde aus dem ersten 3DS-Lauf (PLAN.md §9)

Reihenfolge: T4.6 → T4.7 → T4.11/T4.12 → T4.10 → T4.9 → T4.8. Jeder Fix kommt als Patch (Regel 7) und mit Vorher/Nachher in `docs/compat-log.md`. Leistungswerte aus dem Emulator sind nur Näherungen; die endgültigen kommen von echter Hardware (T4.5, T5.5).

- [ ] **T4.6** Testhilfen und Einordnung der Befunde B1–B6.
  - **Diagnose-Build:** `scripts/build-3ds.sh` bekommt die Option `DIAG=1`. Der Port-Start hängt dann `--debuglevel=1 --debugflags=loading` (oder vergleichbar) an die Argumente an und schreibt Zeitstempel ins Log: App-Start, Backend bereit, Erkennung fertig, Engine-Start, erster Frame. So stehen geladene Filme (Räume) und die Startphasen im Log.
  - **Desktop-Vergleich (Nutzer):** dieselben Szenen im offiziellen ScummVM 2026.4.0 für Windows (`vendor/scummvm-release/…`): Raum betreten, warten, antippen bzw. klicken, eine Maus fangen. Notieren, ob B1, B3 und B4 auch dort auftreten.
  - **Desktop-Vergleich (Agent):** den betroffenen Raum im eigenen Linux-Build ohne Fenster starten (Target `ggmd-win-de`, Startfilm per `--start-movie=<RAUM>.DXR`) und mit den Debug-Kanälen `loading`, `images`, `events`, `sound` und `lingoexec` die Abläufe aus B1 und B3 nachvollziehen. Fehlende Eingaben ersetzen (z. B. `caught()` über die Lingo-Konsole des Debuggers aufrufen oder per ScummVM-Event-Recorder).
  *Fertig, wenn:* in `docs/compat-log.md` für B1–B6 jeweils "Desktop: ja/nein" und damit "Engine" oder "3DS-Backend/Leistung" steht und die betroffenen Räume bzw. Videos benannt sind.
  → **Zwischenstand** (2026-11-10, Agent):
    - **Diagnose-Build** fertig: Patch 0005, `DIAG=1` erzeugt `dist/3ds/mausjagd-diag.3dsx`. Abweichend vom Plan ist der Modus ein Laufzeitschalter (`diag.txt` in der RomFS oder auf der SD-Karte), kein eigenes Binary; so lässt er sich auf echter Hardware ohne Neubau einschalten. Er liefert Zeitstempel ab App-Start, Startmarken und alle 5 s Bildrate und Umrechnungszeiten (`docs/build-3ds.md`).
    - **Desktop-Vergleich (Agent):** B5 tritt auch am Desktop auf, B2 und B6 nicht; Details in `docs/compat-log.md`. Neues Werkzeug `tools/mov_info.py`: Alle Raumvideos haben das Format des Intros, also scheidet das Videoformat als Ursache für B1 aus.
    - **Offen:** Diag-Lauf im Emulator und Desktop-Vergleich durch den Nutzer (B1, B3, B4, Raumname); Anleitung in `docs/compat-log.md`.
    - **Update** (2026-11-10, abends): Der Diag-Lauf des Nutzers lieferte die Startphasen (B6 → T4.8 erledigt im Emulator). Laut Nutzer tritt B1 nicht mehr auf. Desktop-Vergleich zu B3 und B4 steht weiter aus.
- [x] **T4.7** **B5:** ScummVM-Warnung beim Start entfernen.
  - Ursache: `ADGF_UNSTABLE` aller Director-Einträge führt zu `Engine::warnUserAboutUnsupportedGame()`.
  - Im Port-Modus `enable_unsupported_game_warning` standardmäßig auf `false` setzen, als 3DS-Patch hinter `#ifdef MAUSJAGD_PORT`. Den Erkennungseintrag nicht ändern.
  - Danach prüfen, ob beim Kaltstart (leerer App-Ordner) weitere Dialoge oder Hinweise erscheinen, und auch diese abschalten.
  *Fertig, wenn:* ein Kaltstart im Emulator ohne jeden ScummVM-Dialog direkt im Startbildschirm des Spiels landet.
  → **Erledigt** (2026-11-10): Patch 0006 setzt im Port `enable_unsupported_game_warning` standardmäßig auf `false` (in `OSystem_3DS::initBackend()`). Kaltstart in Azahar ohne App-Ordner: kein Dialog, das Spiel startet direkt (`docs/compat-log.md`).
- [ ] **T4.8** **B6:** Startzeit messen und verkürzen.
  - Mit den Zeitstempeln aus T4.6 die Phasen messen: Laden der `.3dsx`, Backend-Init, Erkennung (durchsucht die RomFS mit 442 Dateien, Scan-Tiefe 5, MD5), Engine-Init, `SHARED.DXR`, erster Frame.
  - Kandidaten: Erkennung im Port verkürzen (z. B. mit vorkonfiguriertem Target bzw. Variante, oder nur `MAUSJAGD.EXE`/`SHARED.DXR` prüfen), RomFS-Zugriffe bündeln.
  - Die Pausen des Startbildschirms sind original und bleiben.
  *Fertig, wenn:* Messwerte vorher/nachher in `docs/performance.md` stehen und die App auf dem New 3DS nach höchstens 10 s den Startbildschirm zeigt (PLAN.md §3), oder begründet ist, warum nicht.
  → **Im Emulator erfüllt** (2026-11-10):
    - Die Erkennung schlug alle Einträge der Director-Tabelle nach und brauchte dafür 75 s. Patch 0007 beschränkt sie im Port auf `ggmd`.
    - Erstes Spielbild jetzt nach 4,1 s ab App-Start (vorher 78,6 s), nach 6–7 s Wanduhr ab Start von Azahar; Messwerte in `docs/performance.md`.
    - **Offen:** Messung auf dem New 3DS (T4.5).
- [x] **T4.13** Ladeanzeige beim Start (Wunsch des Nutzers: "Phasen-Balken").
  → **Erledigt** (2026-11-10, Patch 0008): Oben erscheinen Titel und Balken mit Statuszeile ("Spieldaten werden geprüft ...", "Spiel wird gestartet ..."), bis das Spiel sein erstes Bild zeigt; Design ohne Spielgrafik. Dazu lässt Patch 0009 den oberen Bildschirm im normalen 400×240-Modus, weil Azahar den 800-Pixel-Modus nur halb zeigt. Im Emulator per Bild geprüft.
- [x] **T4.9** **B3:** Figuren beim Betreten eines Raums weiß, bis die Raummusik endet.
  - Raum bestimmen (T4.6).
  - Lingo des Raums lesen (`analysis/lingo/<RAUM>/`): Raumstart, `puppetSound`/`soundBusy`-Schleifen, `puppetPalette`, Ink und `updateStage`.
  - Klären, ob das Original die Figuren erst nach der Musik zeigt; dann wäre der Befund das Weiß statt "unsichtbar".
  - Ursache in Palette, Ink-Rendering (Matte/Copy/Background Transparent) oder Zeichenreihenfolge finden.
  *Fertig, wenn:* die Figuren so erscheinen, wie es die Lingo-Logik und der Desktop-Vergleich vorgeben, in allen Räumen mit gleichem Aufbau.
  → **Erledigt als Originalverhalten** (2026-11-10, Entscheidung des Nutzers): Jeder Fangraum ruft im `exitFrame` von Frame 1 `startsequence` auf. Die Funktion wartet mit `repeat while the soundBusy of 1` ohne `updateStage`, bis die Raummusik endet; Frame 1 steht also absichtlich still. Der Desktop-Vergleich entfällt.
- [ ] **T4.10** **B4:** Rechteck um den Tippunkt.
  - Mit dem Desktop-Vergleich und dem Code klären, woher es kommt:
    - (a) Zeiger-Bitmap (`cursor(200)` u. a., Director-Cursor mit Maske) im 3DS-Backend ohne Transparenz
    - (b) "Hilite" geklickter Sprites als invertiertes Rechteck
    - (c) Touch-Feedback des Backends
  - Bezug zu PLAN.md §3: Der Cursor wird auf dem Touchscreen ohnehin ausgeblendet (T5.1/T5.2). Lösen sollen das Problem aber nicht nur die Ausblendung, sondern die Ursache, weil der Cursor in der Lupe sichtbar bleibt.
  *Fertig, wenn:* beim Tippen kein Rechteck mehr erscheint, vom Spiel vorgesehene Hervorhebungen erhalten bleiben und der Cursor (wo sichtbar) korrekt mit Transparenz gezeichnet wird.
- [x] **T4.11** **B1:** Verzerrtes Bild beim bzw. nach dem Fangen einer Maus.
  - Bestätigen, dass es um das Missgeschick-Video (`<RAUM>.MOV`) geht.
  - Abmessungen, Codec (SMC), Farbtiefe und Palette des Videos bestimmen, z. B. mit `tools/` oder ScummVM-Debugausgaben.
  - Den Datenweg prüfen: Videoframe → Director-Sprite → Bühne (CLUT8) → 3DS-Backend (`copyRectToScreen`, Pitch, `initSize`/Größenwechsel, Skalierung 640×480 → Bildschirm). Screenshot im Emulator; Desktop-Vergleich.
  *Fertig, wenn:* die Missgeschick-Videos der 19 Fangräume unverzerrt laufen, stichprobenartig im Emulator und vollständig per Desktop-Vergleich. Intro- und Hilfevideos werden mitgeprüft.
  → **Erledigt** (2026-11-10):
    - Laut Nutzer tritt B1 nicht mehr auf. Die Stichprobe im Emulator (ARTIST, Bild mitten im Video) ist auf beiden Bildschirmen unverzerrt; das Intro lief schon im ersten Lauf sauber.
    - Alle Raumvideos haben das Format des Intros (`tools/mov_info.py`).
    - Die Ursache ist nicht abschließend geklärt. Kandidat ist der 800-Pixel-Modus des oberen Bildschirms, den Azahar nur halb zeigte (seit Patch 0009 aus).
    - Der vollständige Desktop-Vergleich entfällt nach Rückmeldung des Nutzers. Tritt B1 wieder auf, mit Raumname und Bild neu öffnen.
- [ ] **T4.12** **B2:** Einbruch auf 5 FPS beim Fangen.
  - Zeitmessung im 3DS-Build: Dekodieren, Palettenumrechnung bzw. Dithering (`setDitheringPalette`), Kopieren auf die Bühne, Skalierung bzw. Übertragung zur GPU.
  - Erst nach T4.11 bewerten, weil die Verzerrung die Ursache sein kann (z. B. falsche Größe → falscher Pfad).
  - Kandidaten: Dithering-Tabellen einmal pro Video statt pro Frame aufbauen, die Videopalette direkt übernehmen, nur geänderte Bereiche aktualisieren (Dirty Rects).
  - Ergebnisse in `docs/performance.md`. Allgemeine Optimierung für beide Modelle folgt in T5.7.
  *Fertig, wenn:* Missgeschick-Videos im Emulator (New-3DS-Modus) in ihrer Original-Bildrate laufen und der Wert auf dem Old 3DS gemessen und eingetragen ist.
  → **Im Emulator erfüllt** (2026-11-10):
    - ARTIST-Video mit 11,4–12,3 fps (Original 12 fps); das Backend braucht 7,6 ms pro Frame. Laut Nutzer ist B2 behoben.
    - Gemessen ohne Eingaben über `diag.txt` mit `--start-movie=ARTIST.DXR@1203`; Werte in `docs/performance.md`.
    - **Offen:** Old 3DS auf echter Hardware. Der Old-3DS-Modus von Azahar liefert dieselben Werte wie der New-3DS-Modus und taugt dafür nicht.
  → **Nachtrag** (2026-11-11): Der Nutzer sah in SNOOKER wieder 5 fps und Farbrauschen. Das war die eigentliche Ursache von B1/B2, nicht das Video:
    - **Palette:** Animationsframes verweisen auf die gelöschte Palette 301 (Patch 0011).
    - **Zeichnen:** Die Leerlauf-Animationen kosteten 123–185 ms pro Zeichendurchgang (Patches 0012–0014).
    - **Jetzt:** 11 ms pro Durchgang, SNOOKER läuft mit 12 fps und farbtreu. Messwerte in `docs/performance.md`.
    - **Offen:** Rückmeldung aus dem echten Spiel (alle Räume) und der Old 3DS.
  → **Alle Räume geprüft** (2026-11-11):
    - Score-Prüfung aller 27 Filme auf Verweise ins Leere: nur SNOOKER betroffen, dazu harmlose Lücken in PLUMBER und ORCH (`docs/compat-log.md`).
    - Leistungsmessung aller 19 Räume im Emulator (`docs/performance.md`): kein Dauer-Engpass, kein Dithering.
    - Ruckler beim ersten Erscheinen großer Matte-Bilder mit Patch 0015 gemildert (SLOBS 132 → 48 ms).
- [x] **T4.14** **B7:** Katze redet im Instrumentenraum von selbst, bricht ab, ihr Bild bleibt stehen (Nutzer, 2026-11-11, meist ab Maus 2).
  *Fertig, wenn:* nach der Bored-Animation der Film in `Select` bleibt und der Nutzer B7 auf dem 3DS nicht mehr sieht.
  → **Ursache gefunden und behoben** (2026-11-11, Agent, Patch 0023):
    - Ohne Eingabe ruft INSTRUM nach 4 s über den `timeoutScript` `bored` auf: `play frame "Bored"` (Frames 1397–1413), danach `play done`.
    - ScummVM kehrte zu Frame 5 statt 4 (`Select`) zurück, weil es `play` aus Ereignis-Skripten wie aus Frame-Skripten behandelte. So lief der Film in die Hilfe-Sequenz (Frame 7) mit dem Katzenvideo `cathel11.mov`. Danach fiel `go(myhelpframe)` (nie gesetzt) bis nach ORCH durch.
    - Desktop ohne Fenster mit Zustand "Maus 2": jetzt alle 4 s Bored-Animation und Rückkehr zu Frame 4, kein Video. Details in `docs/compat-log.md`.
    - **Auf dem 3DS bestätigt** (2026-11-12, Nutzer): ganzes Spiel durchgespielt, ohne erneute Meldung zu B7.
- [x] **T4.15** **B8:** Absturz bei Maus 14, der den ganzen 3DS mitnimmt (Nutzer, 2026-11-11).
  *Fertig, wenn:* ein kompletter Durchlauf aller 19 Räume auf dem 3DS ohne Absturz gelingt.
  → **Ursache gefunden und behoben** (2026-11-12, Agent):
    - Rundtour durch alle Räume in einem Prozess (`tools/scummvm-test-patches/movie-tour.patch`), am Desktop mit und ohne ASan sowie in Azahar mit GDB.
    - Kein Speicherleck: Heap +0,3 MB pro Raum. Kein Speicherfehler (ASan).
    - In Azahar sporadischer Stillstand beim Start eines Fang-Videos, einmal genau bei Maus 14.
    - Ursache: `DigitalVideoCastMember` ließ `_scaleX`/`_scaleY` beim Lesen aus den Filmdaten uninitialisiert. Die Videos bekamen zufällige Sprite-Größen bis 13 100 × 23 424, und pro Bild wurde ein entsprechend riesiges Widget angelegt.
    - Patch 0025. Dazu Patch 0024 (veralteter Texturzeiger im 3DS-Backend, Hotelkarte).
    - Details in `docs/compat-log.md`.
  → **Auf dem 3DS bestätigt** (2026-11-12, Nutzer): CIA mit Patches 0001–0025 per QR-Code installiert, das ganze Spiel ohne Absturz durchgespielt.

## Phase 5: 3DS-Anpassung

- [ ] **T5.1** Bildschirm-Layout nach PLAN.md §3 umsetzen. Das Spiel läuft auf dem unteren Bildschirm in 320×240 (Faktor 0,5). **Oberer Bildschirm** (Entscheidung des Nutzers, 2026-11-10):
  - Bis zur ersten Hotelübersicht: Startbildschirm bzw. Spielbild.
  - Danach die **Hotelkarte**: der Querschnitt `interfinalfordir0001` aus `GGMDMENU`, verkleinert auf 320×235.
  - Der aktuelle Raum bekommt einen **blinkenden Rahmen** um sein Zimmerbild. Die Klickflächen sind die Sprites 5–23 der Hotelübersicht; Feld `roomlist` ordnet sie zu, Zeile = Sprite − 4.
  - Daneben steht der **Mäusezähler** aus `miceCaught`.
  - Die Karte verrät nicht, wo die nächste Maus steckt.

  Zuerst prüfen, was das 3DS-Backend schon kann (Bildschirmwahl, Touch-Modus), und es entsprechend konfigurieren; Fehlendes in `backends/platform/3ds/` bzw. der Director-Engine ergänzen. Skalierungsfilter vergleichen (nächster Nachbar oder linear), Kriterium ist die Lesbarkeit. Bilder kommen nach `dist/screens/`, weil sie Spielgrafik enthalten (ignoriert).
  *Fertig, wenn:* das Layout standardmäßig aktiv ist und die Entscheidungen zu Filter und Lupe in `docs/3ds-ux.md` stehen.
  → **Zwischenstand** (2026-11-11): Die **Hotelkarte oben ist umgesetzt** (Patch 0010) und im Emulator geprüft:
    - Karte in Originalfarben (eigene Palette des Bildes, Cast 23).
    - Blinkender Rahmen um ARTIST und SNOOKER korrekt.
    - Zähler "Mäuse 0 von 19" sichtbar.

    Die Klickflächen liegen etwa 12 Pixel tiefer als die Zimmerbilder; der Rahmen nutzt deshalb eine gemessene Tabelle der Zimmerbilder. **Offen:**
    - Zähler mit Werten > 0 im echten Spiel (Rückmeldung des Nutzers).
    - Der untere Bildschirm: Das Spiel nur dort zeigen, Filter vergleichen.
    - `docs/3ds-ux.md` anlegen.
- [ ] **T5.2** Direkte Touch-Eingabe umsetzen: Die Tippposition ist die Mausposition, kein Touchpad-Modus. Beim Aufsetzen springt der Zeiger auf die Tippposition, im selben Frame folgt `mouseDown`. Ziehen bewegt den Zeiger, Loslassen löst `mouseUp` an der letzten Position aus. Den Hover-Ersatz für `rollOver` laut T2.6 umsetzen; das gilt fürs Menü und vor allem für das **Mausometer** auf der Hotelübersicht, das man durch Ziehen über das Bild bewegt (siehe `docs/gameplay.md`). Den Cursor auf dem Touchscreen ausblenden. Tasten wie in PLAN.md §3 belegen, einschließlich der Tasten, die das Spiel abfragt. **Texteingabe:** Den Namen beim Speichern über die 3DS-Bildschirmtastatur eingeben; prüfen, ob das ScummVM-Backend sie schon anbietet.
  *Fertig, wenn:* ein Log des Debug-Kanals `events` für 10 Tipps zeigt, dass Klickposition und getroffenes Sprite stimmen, auch bei einer laufenden Maus. Das Mausometer lässt sich per Ziehen bedienen, und ein Spielstand mit Namen lässt sich speichern.
- [ ] **T5.3** Treffhilfe für Mäuse in der Director-Engine umsetzen, als spielspezifischen Quirk mit abschaltbarer Option (z. B. `touch_hit_radius`). Trifft ein `mouseDown` keine Maus, wird im Radius um den Tippunkt das nächste sichtbare Maus-Sprite laut `docs/mouse-catching.md` gesucht und der Klick auf dessen Mittelpunkt umgelenkt. Alle anderen Klickflächen bleiben exakt. Am Desktop entwickeln (die Option ist dort ebenfalls aktivierbar), auf dem 3DS abstimmen, danach Patch-Export (Regel 7).
  *Fertig, wenn:* die Treffhilfe in allen Fangräumen wirkt, nie ein anderes Sprite "anzieht" und sich abschalten lässt.
- [ ] **T5.4** Trefferquote auf echter Hardware messen (mit dem Nutzer, Regel 6). Azahar simuliert Touch nur per Maus und ist dafür nicht aussagekräftig. Pro Fangraum 20 Versuche mit Stift und 20 mit Finger, jeweils mit und ohne Treffhilfe. Den Radius so abstimmen, dass mit Stift mindestens 90 % gelingen, ohne Fehlklicks auf Nachbarobjekte. Ergebnis in `docs/3ds-ux.md`.
  *Fertig, wenn:* die Tabelle steht und der gewählte Radius als Standard eingetragen ist.
- [ ] **T5.5** Performance messen auf New 3DS und Old 3DS: Bildrate in Räumen, Eingabelatenz in Fangräumen (vom Tippen bis zur Reaktion), Videos (besonders `ENDSEQ.MOV` und `GERINTRO.MOV`), Aussetzer im Ton. Ergebnis in `docs/performance.md`.
  *Fertig, wenn:* zu jedem Video und jedem Raum ein Messwert vorliegt.
- [ ] **T5.6** Speicher messen: Spitzenverbrauch beim Filmwechsel und bei großen Casts (`ATTIC.DXR` mit 3,8 MB). 3DSX über Title-Takeover und CIA vergleichen, dazu den erweiterten Speichermodus des New 3DS.
  *Fertig, wenn:* es weder auf dem New 3DS noch auf dem Old 3DS einen Out-of-Memory gibt. Seit 2026-11-10 ist der Old 3DS gleichwertige Zielplattform (Wunsch des Nutzers, PLAN.md §6).
- [ ] **T5.7** Optimieren, nur wenn T5.5 oder T5.6 Probleme zeigen. Bekannte Kandidaten aus der Raumprüfung 2026-11-11 (`docs/performance.md`):
  - erste Matte-Masken großer Bilder (SLOBS 48 ms auf dem New 3DS, auf dem Old 3DS geschätzt 150 ms): Zeilen-Flutfüllung oder Masken beim Laden des Raums;
  - `MacWindow::draw()` kopiert bei jeder Änderung das ganze Fenster.

  Allgemein: Profiling zuerst, dann gezielt. Kandidaten: SMC-Decoder, Palettenkonvertierung, Dirty Rects, Musikvariante mit 8 Bit, Takt des New 3DS. Jede Optimierung mit Vorher/Nachher-Messwert in `docs/performance.md`.
  *Fertig, wenn:* die Messwerte auf **beiden** Modellen das Ziel erreichen: flüssige Räume, Videos ohne störendes Ruckeln, kein Ton-Stottern. Modellabhängige Einstellungen nur, wenn die Messung sie verlangt (Erkennung per `APT_CheckNew3DS()`).
- [ ] **T5.8** Systemverhalten: HOME-Taste, Deckel zu/auf (Sleep), Power-Taste und Beenden über das ScummVM-Menü dürfen weder Ton noch Spielstand kaputt machen.
  - **Merkposten** (2026-11-10): Ein fataler Fehler öffnet auf dem 3DS die Debugger-Konsole von ScummVM, eine Sackgasse ohne Tastatur. Prüfen, was der Spieler dann sieht und wie er beendet; gegebenenfalls im Port eine Meldung zeigen und sauber beenden.
  *Fertig, wenn:* alle Fälle in `docs/3ds-ux.md` als "ok" vermerkt sind.
- [ ] **G2 Gate:** Dem Nutzer den Stand berichten: Lassen sich die Mäuse per Touch zuverlässig fangen (T5.4)? Ist das Spiel auf dem New 3DS **und** dem Old 3DS gut spielbar? Freigabe für das Packaging einholen.

## Sicherheit (querschnittlich, PLAN.md §10)

Ergebnisse kommen nach `docs/security.md`. S1 und S4 laufen für neue Patches **vor jedem Test auf echter Hardware**, alle Aufgaben **vor dem Packaging** (Phase 6).

- [x] **S1** Patch-Review: Jeden eigenen Patch (`patches/`) gegen die Regeln aus PLAN.md §10 prüfen und das Ergebnis pro Patch in einer Checkliste festhalten. Prüfpunkte:
  - Puffer und Längen
  - begrenzte Zeichenoperationen
  - Dateipfade
  - Fehlerbehandlung
  - Dienste
  *Fertig, wenn:* die Checkliste für alle Patches vollständig ist und gefundene Mängel behoben sind.
  - **Erledigt** (2026-11-11): Checkliste für 0001–0022 in `docs/security.md` §7. Gefundene Lücken sind mit 0016–0018 und 0022 geschlossen. Für jeden neuen Patch die Tabelle ergänzen.
- [x] **S2** Sanitizer: Den Linux-Desktop-Build mit `-fsanitize=address,undefined` bauen (eigener Build-Ordner) und ohne Fenster durchlaufen lassen:
  - Start und Menü
  - jeder Raum per `--start-movie` am Anfang und am Label `caught`
  - Intro- und Hilfevideos
  - `INSTRUM`, `ORCH`, `ATTIC`, `THEEND`, `CREDITS`

  Funde in eigenem Code beheben, Funde in ScummVM dokumentieren und gegebenenfalls upstream melden (Freigabe nötig).
  *Fertig, wenn:* alle Läufe ohne Sanitizer-Meldung in eigenem Code durchgehen.
  - **Erledigt** (2026-11-11): 85 Läufe, ASan ohne Fund. UBSan meldete nur den Zufallsgenerator der Engine; behoben mit 0021 (bit-gleich), Gegenprobe sauber (`docs/security.md` §5). Upstream-Meldung von 0021 nur nach Freigabe.
- [x] **S3** Statische Analyse: Die geänderten Dateien mit `cppcheck` (bzw. `clang-tidy`) prüfen. Den 3DS-Build auf Warnungen in diesen Dateien durchsehen (`-Wall -Wextra`).
  *Fertig, wenn:* keine offenen Befunde in eigenem Code bleiben.
  - **Erledigt** (2026-11-11): statt `cppcheck` GCC `-fanalyzer` (Linux) und die Warnungen von devkitARM für die 3DS-Dateien; im eigenen Code keine Meldung (`docs/security.md` §4).
- [x] **S4** Datei- und Dienstzugriffe:
  - Im Code nachweisen, dass Konfiguration, Log, Spielstände und FileIO nur unter `sdmc:/3ds/mausjagd/` schreiben.
  - In Azahar eine Spielsitzung mit Speichern fahren und den Inhalt der virtuellen SD vorher und nachher vergleichen: Nur der App-Ordner darf sich ändern.
  - Prüfen, welche Systemdienste der Port tatsächlich initialisiert.
  *Fertig, wenn:* keine Schreibzugriffe außerhalb des App-Ordners nachweisbar sind.
  - **Erledigt** (2026-11-11): Binary-Analyse (Dienste, 27 Kernel-Aufrufe, nur SD-Archiv) und SD-Vergleiche, `docs/security.md` §2–3. Vor jedem Hardware-Test: `py -I tools/inspect_3dsx.py dist/3ds/mausjagd.3dsx docs/inventory.md` (Exit-Code 0) und Vergleich der SD vor und nach einem Kaltstart.
- [x] **S5** Fatale Fehler: Im Port statt der Debugger-Konsole eine verständliche Meldung zeigen und sauber beenden. Testfall: `--start-movie=ARTIST.DXR@1203` führt nach dem Video zu `Builtin 'getPos' did not return value`.
  *Fertig, wenn:* der Testfall mit Meldung endet und die App sich zum HOME-Menü bzw. Homebrew Launcher beenden lässt.
  - **Erledigt** (2026-11-11): Patch 0018, im Emulator mit dem Testfall geprüft (`docs/security.md` §3, H3).
- [ ] **S6** Speicher, Stack und Datenintegrität:
  - Spitzenverbrauch auf dem Old 3DS (zusammen mit T5.6).
  - Verhalten bei fehlgeschlagener Speicheranforderung.
  - Stackgröße (64 KB im Hauptthread; FreeType-Hinweis aus `docs/build-3ds.md`).
  - Spielstand beim Abschalten während des Schreibens (zusammen mit T5.8).
  *Fertig, wenn:* die Grenzen gemessen sind und kein Fall zu kaputten Spielständen oder Abstürzen ohne Meldung führt.
  - **Zwischenstand** (2026-11-11): Messung im Emulator (New- und Old-Modus) mit Patch 0020, Stack 256 KB (0019), atomare Spielstände (0022); siehe `docs/security.md` §6. Offen: Heap-Spitze auf einem echten Old 3DS (geschätzt 8 MB Reserve in ATTIC) und Abschalten während des Speicherns auf Hardware.
- [ ] **S7** CIA-Rechte:
  - Die RSF auf die nötigen Dienste kürzen; nicht nötig sind z. B. `am:net`, `http:C`, `soc:U`, `cam:u`, `mic:u`, `boss:U`, `nim:aoc`.
  - Dateisystemzugriff nur `DirectSdmc`.
  - Eigene Title-ID außerhalb der Systembereiche (mit T6.2/T6.3).
  - Installieren und Deinstallieren zuerst im Emulator testen.
  *Fertig, wenn:* das CIA mit den gekürzten Rechten läuft und sich rückstandsfrei deinstallieren lässt.
  → **Stand 2026-11-11 (Agent):**
    - `config/mausjagd.rsf` gibt nur die 8 Dienste frei, die das Binary anfragt, dazu nur `DirectSdmc`, ohne SVC `Backdoor`. UniqueId ist `0xF8D4A`.
    - Mit ctrtool am fertigen CIA geprüft (`docs/security.md` §9). In Azahar installiert und gestartet.
    - **Offen:** Start auf echter Hardware (Azahar setzt die Dienst-Liste nicht durch) und Deinstallation.

## Phase 6: Packaging

- [ ] **T6.1** Vorkonfiguration in `config/`: eine `scummvm.ini` mit dem Spieleintrag (Pfad `sdmc:/3ds/mausjagd/game/`) und den 3DS-Einstellungen aus T5.1–T5.4. Prüfen, ob ScummVM einen Direktstart unterstützt (z. B. eine `scummvm-autorun`-Datei), und ihn einbauen, sodass die App ohne Launcher ins Spiel geht.
  *Fertig, wenn:* ein Start der App direkt im Spiel landet.
- [ ] **T6.2** App-Identität: Name, eigene eindeutige Title-ID sowie selbst gestaltetes Icon (48×48) und Banner (256×128) plus Banner-Sound. Keine Grafiken aus dem Spiel verwenden (PLAN.md §7).
  → **Eigener Gebrauch** (2026-11-11, Wunsch des Nutzers): Builds mit eingebetteten Spieldaten bekommen Icon, Banner und Banner-Ton aus Titelbild und Titelmelodie des Spiels (`scripts/make_app_art.py`, `APP_ART=1`). Diese Dateien entstehen nur im Build-Ordner. Die Title-ID steht (`config/mausjagd.rsf`). **Offen:** selbst gestaltete Fassung für eine weitergebbare App.
  *Fertig, wenn:* die Dateien in `config/` liegen.
- [ ] **T6.3** `scripts/build-3ds.sh` erweitern, sodass es `dist/mausjagd.3dsx` und `dist/mausjagd.cia` erzeugt und die Konfiguration einbettet.
  *Fertig, wenn:* beide Dateien reproduzierbar entstehen und die CIA sich installieren lässt (Emulator).
  → **Teilweise** (2026-11-11): `CIA=1` erzeugt `dist/3ds/mausjagd.3dsx` und `dist/3ds/mausjagd.cia`; das CIA lässt sich in Azahar installieren. Icon und Banner kommen beim eigenen Build aus dem Spiel (T6.2). Es fehlen die selbst gestaltete Fassung für eine Weitergabe und die Konfiguration aus T6.1.
- [ ] **T6.4** `README.md` für Endnutzer auf Deutsch schreiben:
  - Voraussetzungen (3DS mit Custom Firmware, eigene Original-CD)
  - Extraktion mit `py -I tools/iso_extract.py extract … --profile game`
  - Aufbau der SD-Karte
  - Installation
  - Bedienung
  - Bekannte Einschränkungen
  - Lizenzhinweis zur GPL

  *Fertig, wenn:* jemand mit der README allein von der ISO zum laufenden Spiel kommt.
- [ ] **T6.5** Abschlusstest auf frischer SD-Karte bzw. frischem Emulator-Profil nur nach README.
  *Fertig, wenn:* der Durchlauf aus T3.9 auf dem 3DS gelingt.

## Phase 7: optional (nur auf Wunsch des Nutzers)

- [ ] **T7.1** Erkennungseintrag und Engine-Fixes als PR an `scummvm/scummvm` einreichen. Das ist nach außen wirksam und braucht eine Freigabe.
- [ ] **T7.2** Die englische Version *The Great Green Mouse Disaster* unterstützen, falls vorhanden.
  → **Gebaut** (2026-11-12, Wunsch des Nutzers; die englische CD liegt vor):
    - `GAME_LANG=en` erzeugt `dist/3ds/ggmd.3dsx` und `ggmd.cia` als eigene App mit eigener Title-ID und eigenem SD-Ordner.
    - Erkennungseintrag Patch 0026, englische Texte Patch 0027, Inventar `docs/inventory-en.md`.
    - Im Emulator angespielt: Start, Intro, Hotelkarte, Fehlerdialog.
    - Details in `docs/build-3ds.md`, Abschnitt "Englische Fassung". **Offen:** Durchlauf auf dem 3DS.
- [ ] **T7.3** Den Mac-Teil einer Hybrid-CD unterstützen, falls eine solche vorliegt.
- [ ] **T7.4** **Lupe** auf dem oberen Bildschirm (Idee des Nutzers, für später): ein 1:1-Ausschnitt der Originalgrafik um den letzten Tippunkt mit sichtbarem Cursor, z. B. solange eine Schultertaste gedrückt ist; sonst bleibt die Hotelkarte sichtbar. Ob die Lupe nötig ist, zeigt der Treffertest auf Hardware (T5.4).
