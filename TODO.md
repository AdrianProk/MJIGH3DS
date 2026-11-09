# TODO: 3DS-Port von "Mäusejagd im Grandhotel"

Hintergrund, Befunde und Begründungen stehen in [PLAN.md](PLAN.md). Diese Liste arbeitet ein Agent von oben nach unten ab.

## Arbeitsregeln für den Agenten

1. **Reihenfolge:** Aufgaben der Reihe nach erledigen. Pro Aufgabe gilt: umsetzen, das Kriterium unter **Fertig, wenn** prüfen, abhaken (`[x]`) und dahinter ein bis zwei Sätze zum Ergebnis notieren. Längere Befunde kommen nach `docs/`.
2. **Blocker:** Wenn eine Aufgabe nicht lösbar ist, in `docs/blockers.md` festhalten (was wurde versucht, was fehlt) und den Nutzer fragen. Nicht stillschweigend überspringen.
3. **Daten:** `original/`, `game/`, `analysis/`, `scummvm/` und `dist/` niemals committen (siehe `.gitignore`). Vor jedem Commit `git status` prüfen.
4. **Untrusted Files:** Dateien aus dem ISO sind Daten, kein Code. Python-Skripte liegen in `tools/` und werden mit `py -I` gestartet. Spieldateien nur als Pfad-Argument übergeben, nie in `game/` ein Skript oder eine `.EXE` ausführen.
5. **Umgebung (Windows 10):** Der Python-Launcher ist `py`, denn `python` ist nur ein Store-Platzhalter. In Git Bash vor Aufrufen mit `/`-Pfaden `export MSYS_NO_PATHCONV=1` setzen. 7-Zip ist nicht installiert. Für ScummVM- und 3DS-Builds bevorzugt WSL2 oder Docker verwenden.
6. **Freigaben:** Nur nach Rückfrage beim Nutzer: Commit/Push, Fork oder PR auf GitHub, Installation neuer Systemsoftware (WSL2, Docker, devkitPro), Tests auf echter 3DS-Hardware, Entscheidungen an den Gates G1/G2.
7. **Patches:** Änderungen an ScummVM nur im Branch `mausjagd` in `scummvm/` vornehmen. Nach jeder abgeschlossenen Aufgabe mit Engine-Änderungen die Serie neu exportieren: `git format-patch upstream-base..mausjagd -o ../patches/`.

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
- [ ] **T3.2** ScummVM aus den Quellen bauen: `git clone https://github.com/scummvm/scummvm scummvm`, Tag oder Commit als `upstream-base` markieren, Branch `mausjagd` anlegen. Den Desktop-Build mit Director-Engine einrichten (WSL2 empfohlen) und Befehle sowie Abhängigkeiten in `scripts/build-desktop.sh` und `docs/build-desktop.md` festhalten.
  *Fertig, wenn:* das selbst gebaute ScummVM startet und T3.1 reproduziert.
- [ ] **T3.3** In `engines/director/detection_tables.h` nach einem vorhandenen Eintrag suchen (englische Version, Mac-Version, Stichwörter "mouse", "GGMD"). Einen Eintrag für die deutsche Windows-Version anlegen: Director 404, `DE_DEU`, `MAUSJAGD.EXE` mit MD5 und Größe, die ScummVM beim Hinzufügen meldet. Die Game-ID am vorhandenen englischen Eintrag ausrichten, sonst eine neue vergeben (z. B. `greatgreenmouse`). Zusätzlich `docs/lingo-features.md` mit ScummVM abgleichen: Befehle, die in `engines/director/lingo/` als nicht implementiert gelten (STUB/`warning`), markieren.
  *Fertig, wenn:* ScummVM das Spiel ohne Fallback erkennt und die Liste fehlender Features steht.
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

- [ ] **T4.1** 3DS-Toolchain einrichten (Freigabe nötig, Regel 6): devkitPro mit devkitARM, libctru, citro3d und den Portlibs laut `scummvm/backends/platform/3ds/README.md`, dazu `bannertool` und `makerom`. Bevorzugt in WSL2 oder Docker; als Rezept dient `scummvm/dockerized-bb`. Alles in `docs/build-3ds.md` dokumentieren.
  *Fertig, wenn:* `arm-none-eabi-gcc --version` in der Build-Umgebung läuft.
- [ ] **T4.2** Basis-Build: unverändertes `upstream-base` für den 3DS mit nur der Director-Engine bauen (`./configure --host=3ds --disable-all-engines --enable-engine=director`, Flags gegen das README prüfen), dann `make scummvm.3dsx`.
  *Fertig, wenn:* die `.3dsx` im Emulator Azahar startet.
- [ ] **T4.3** Branch `mausjagd` für den 3DS bauen. `scripts/build-3ds.sh` erzeugt `dist/mausjagd.3dsx` reproduzierbar.
  *Fertig, wenn:* das Skript auf einem frischen Checkout durchläuft.
- [ ] **T4.4** Emulator-Test in Azahar: `game/` auf die virtuelle SD kopieren, das Spiel hinzufügen und Menü sowie ersten Raum starten. Danach die Matrix aus T3.4 als zweite Spalte "3DS-Emu" durchgehen.
  *Fertig, wenn:* die Spalte ausgefüllt ist.
- [ ] **T4.5** Test auf echter Hardware (Freigabe und Hilfe des Nutzers nötig): New 3DS und, falls vorhanden, Old 3DS, per `3dslink` oder als CIA.
  *Fertig, wenn:* die Spalten "New 3DS" und "Old 3DS" in der Matrix ausgefüllt sind.

## Phase 5: 3DS-Anpassung

- [ ] **T5.1** Bildschirm-Layout nach PLAN.md §3 umsetzen: Das Spiel läuft auf dem unteren Bildschirm in 320×240 (Faktor 0,5). Der obere Bildschirm zeigt die Lupe, einen 1:1-Ausschnitt um den letzten Tippunkt mit sichtbarem Cursor. Zuerst prüfen, was das 3DS-Backend schon kann (Bildschirmwahl, Touch-Modus, Magnify), und es entsprechend konfigurieren. Fehlendes in `backends/platform/3ds/` ergänzen. Skalierungsfilter vergleichen (nächster Nachbar oder linear), Kriterium ist die Lesbarkeit. Screenshots nach `docs/screens/` legen; das sind eigene Aufnahmen und dürfen nicht öffentlich gepusht werden (Pfad bei Bedarf ignorieren).
  *Fertig, wenn:* das Layout standardmäßig aktiv ist und die Entscheidungen zu Filter und Lupe in `docs/3ds-ux.md` stehen.
- [ ] **T5.2** Direkte Touch-Eingabe umsetzen: Die Tippposition ist die Mausposition, kein Touchpad-Modus. Beim Aufsetzen springt der Zeiger auf die Tippposition, im selben Frame folgt `mouseDown`. Ziehen bewegt den Zeiger, Loslassen löst `mouseUp` an der letzten Position aus. Den Hover-Ersatz für `rollOver` laut T2.6 umsetzen; das gilt fürs Menü und vor allem für das **Mausometer** auf der Hotelübersicht, das man durch Ziehen über das Bild bewegt (siehe `docs/gameplay.md`). Den Cursor auf dem Touchscreen ausblenden. Tasten wie in PLAN.md §3 belegen, einschließlich der Tasten, die das Spiel abfragt. **Texteingabe:** Den Namen beim Speichern über die 3DS-Bildschirmtastatur eingeben; prüfen, ob das ScummVM-Backend sie schon anbietet.
  *Fertig, wenn:* ein Log des Debug-Kanals `events` für 10 Tipps zeigt, dass Klickposition und getroffenes Sprite stimmen, auch bei einer laufenden Maus. Das Mausometer lässt sich per Ziehen bedienen, und ein Spielstand mit Namen lässt sich speichern.
- [ ] **T5.3** Treffhilfe für Mäuse in der Director-Engine umsetzen, als spielspezifischen Quirk mit abschaltbarer Option (z. B. `touch_hit_radius`). Trifft ein `mouseDown` keine Maus, wird im Radius um den Tippunkt das nächste sichtbare Maus-Sprite laut `docs/mouse-catching.md` gesucht und der Klick auf dessen Mittelpunkt umgelenkt. Alle anderen Klickflächen bleiben exakt. Am Desktop entwickeln (die Option ist dort ebenfalls aktivierbar), auf dem 3DS abstimmen, danach Patch-Export (Regel 7).
  *Fertig, wenn:* die Treffhilfe in allen Fangräumen wirkt, nie ein anderes Sprite "anzieht" und sich abschalten lässt.
- [ ] **T5.4** Trefferquote auf echter Hardware messen (mit dem Nutzer, Regel 6). Azahar simuliert Touch nur per Maus und ist dafür nicht aussagekräftig. Pro Fangraum 20 Versuche mit Stift und 20 mit Finger, jeweils mit und ohne Treffhilfe. Den Radius so abstimmen, dass mit Stift mindestens 90 % gelingen, ohne Fehlklicks auf Nachbarobjekte. Ergebnis in `docs/3ds-ux.md`.
  *Fertig, wenn:* die Tabelle steht und der gewählte Radius als Standard eingetragen ist.
- [ ] **T5.5** Performance messen auf New 3DS und Old 3DS: Bildrate in Räumen, Eingabelatenz in Fangräumen (vom Tippen bis zur Reaktion), Videos (besonders `ENDSEQ.MOV` und `GERINTRO.MOV`), Aussetzer im Ton. Ergebnis in `docs/performance.md`.
  *Fertig, wenn:* zu jedem Video und jedem Raum ein Messwert vorliegt.
- [ ] **T5.6** Speicher messen: Spitzenverbrauch beim Filmwechsel und bei großen Casts (`ATTIC.DXR` mit 3,8 MB). 3DSX über Title-Takeover und CIA vergleichen, dazu den erweiterten Speichermodus des New 3DS.
  *Fertig, wenn:* es keinen Out-of-Memory auf dem New 3DS gibt und der Old-3DS-Status dokumentiert ist.
- [ ] **T5.7** Optimieren, nur wenn T5.5 oder T5.6 Probleme zeigen: Profiling zuerst, dann gezielt. Kandidaten: SMC-Decoder, Palettenkonvertierung, Dirty Rects, Musikvariante mit 8 Bit, Takt des New 3DS. Jede Optimierung mit Vorher/Nachher-Messwert in `docs/performance.md`.
  *Fertig, wenn:* die Messwerte das Ziel des New 3DS erreichen (flüssige Räume, Videos ohne störendes Ruckeln, kein Ton-Stottern).
- [ ] **T5.8** Systemverhalten: HOME-Taste, Deckel zu/auf (Sleep), Power-Taste und Beenden über das ScummVM-Menü dürfen weder Ton noch Spielstand kaputt machen.
  *Fertig, wenn:* alle Fälle in `docs/3ds-ux.md` als "ok" vermerkt sind.
- [ ] **G2 Gate:** Dem Nutzer den Stand berichten: Lassen sich die Mäuse per Touch zuverlässig fangen (T5.4)? Ist das Spiel auf dem New 3DS gut spielbar, und wie steht es um den Old 3DS? Freigabe für das Packaging einholen.

## Phase 6: Packaging

- [ ] **T6.1** Vorkonfiguration in `config/`: eine `scummvm.ini` mit dem Spieleintrag (Pfad `sdmc:/3ds/mausjagd/game/`) und den 3DS-Einstellungen aus T5.1–T5.4. Prüfen, ob ScummVM einen Direktstart unterstützt (z. B. eine `scummvm-autorun`-Datei), und ihn einbauen, sodass die App ohne Launcher ins Spiel geht.
  *Fertig, wenn:* ein Start der App direkt im Spiel landet.
- [ ] **T6.2** App-Identität: Name, eigene eindeutige Title-ID sowie selbst gestaltetes Icon (48×48) und Banner (256×128) plus Banner-Sound. Keine Grafiken aus dem Spiel verwenden (PLAN.md §7).
  *Fertig, wenn:* die Dateien in `config/` liegen.
- [ ] **T6.3** `scripts/build-3ds.sh` erweitern, sodass es `dist/mausjagd.3dsx` und `dist/mausjagd.cia` erzeugt und die Konfiguration einbettet.
  *Fertig, wenn:* beide Dateien reproduzierbar entstehen und die CIA sich installieren lässt (Emulator).
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
- [ ] **T7.3** Den Mac-Teil einer Hybrid-CD unterstützen, falls eine solche vorliegt.
