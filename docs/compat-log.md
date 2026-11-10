# Kompatibilitäts-Log

Testmatrix und Fehlerprotokoll. Neueste Einträge oben im Protokoll.

## Protokoll

### 2026-11-10 – B1, B2, B3 eingeordnet

- **Rückmeldung des Nutzers:** "die weißen Figuren sind wohl vom Spiel so" (B3), "die FPS hat sich auch schon gefixt" (B2).
- **B3, Lingo bestätigt den Ablauf:**
  - Jeder Fangraum ruft im `exitFrame` von Frame 1 `startsequence` auf (z. B. ARTIST, ScoreScript 1). Die Funktion wartet in `repeat while the soundBusy of 1` ohne `updateStage`, bis die Raummusik endet.
  - Bis dahin steht also absichtlich Frame 1 still; erst danach läuft der Raum weiter.
  - Eingeordnet als **Originalverhalten** (Entscheidung des Nutzers). Ein Desktop-Vergleich ist nicht mehr nötig.
- **B2 gemessen:** Das Missgeschick-Video von ARTIST läuft in Azahar mit 11,4–12,3 fps bei 12 fps im Original. Details in `docs/performance.md`. Der Old-3DS-Modus von Azahar liefert dieselben Werte und ist deshalb nicht aussagekräftig.
- **B1 Stichprobe:** Bild mitten im ARTIST-Video auf beiden Bildschirmen unverzerrt (Patches 0001–0009).
- **Nebenbefund:** Ein fataler Lingo-Fehler öffnet auf dem 3DS die Debugger-Konsole von ScummVM. Das ist im normalen Spiel bisher nicht aufgetreten, wäre für Spieler aber eine Sackgasse; Merkposten für T5.8.

### 2026-11-10 – Startzeit, Startbildschirm, Kaltstart (Agent, Azahar selbst gestartet)

- **Build:** `mausjagd.3dsx`, Fork `2022c2c09f`, Patches 0001–0009. Azahar startet der Agent seit heute selbst über `scripts/azahar-run.ps1` (Freigabe des Nutzers).
- **Rückmeldung des Nutzers** zum Diag-Lauf um 20:45: Das Fangen einer Maus funktioniert, das Bild wird dabei **nicht mehr verzerrt** (B1). Kein Dialog beim Start (B5).
- **Diag-Lauf 20:45** (Log des Nutzers): Backend bereit nach 0,7 s, Erkennung von +1,3 s bis +76,2 s, erstes Spielbild bei +78,6 s, Menü bei +93,3 s. Das Log endet beim Start des Intros.
- **B6 behoben (T4.8):**
  - Mit `--debugflags=detection` lag die Zeit vollständig im Durchlauf über die Director-Erkennungstabelle.
  - Patch 0007 beschränkt ihn auf die Einträge von `ggmd`: Erkennung jetzt 0,17 s, erstes Spielbild nach 4,1 s (vorher 78,6 s).
  - Messwerte stehen in `docs/performance.md`.
- **Startbildschirm** (Patch 0008): Titel und Phasen-Balken oben, bis das Spiel sein erstes Bild zeigt. Im Emulator per Bild geprüft: zentriert, Umlaute korrekt.
- **Oberer Bildschirm im 800-Pixel-Modus:**
  - Azahar zeigte oben nur die linke Hälfte des Bildes, doppelt so breit; das betraf Startbildschirm **und** Spiel.
  - Ursache ist `gfxSetWide(true)` im Backend. Patch 0009 lässt den Port im normalen 400×240-Modus, danach war das Bild oben vollständig.
  - Möglicherweise war das der "waagerecht verschmierte, versetzte" Eindruck aus B1. Der Nutzer hat aber den Zustand vor Patch 0009 als unverzerrt gemeldet; das bleibt in T4.11 zu klären.
- **Kaltstart (T4.7):** App-Ordner entfernt, keine `diag.txt`. Ergebnis: kein ScummVM-Dialog, `sdmc:/3ds/mausjagd/` mit `scummvm.ini`, Log und `saves/` wird angelegt, das Spiel startet direkt. Erstes Spielbild nach 5,9 s (Wanduhr ab Start von Azahar), 20 s später läuft der Startfilm (Hotel) auf beiden Bildschirmen.

### 2026-11-10 – T4.6 Testhilfen und erste Einordnung B1–B6 (Agent)

- **Diagnose-Build:** `DIAG=1 bash scripts/build-3ds.sh` erzeugt `dist/3ds/mausjagd-diag.3dsx`, Fork `215225f512`, Patches 0001–0006. Bedienung und Log-Format stehen in `docs/build-3ds.md` (Diagnosemodus). Die normale `dist/3ds/mausjagd.3dsx` hat denselben Stand, nur ohne `diag.txt`.
- **B5 behoben im Code** (Patch 0006, T4.7), Test im Emulator steht aus.
- **Videos** (`py -I tools/mov_info.py game/*.MOV game/GERHELP/*.MOV game/GERVIDEO/*.MOV`):
  - Alle 19 Missgeschick-Videos haben **dasselbe Format wie das Intro** `GERINTRO.MOV`, das auf dem 3DS sauber lief: 640×480, `smc`, 8 Bit, Farbtabelle in der Datei, Ton `raw` 22050 Hz 8 Bit mono.
  - Bildraten: meist 12 fps, sonst 8 fps (BATHROOM, EXERCISE, FARMER, PLAYROOM, PLUMBER, WITCH), 9 fps (PRESBED), 5,7 fps (LIBRARY) und 4,8 fps (SNOOKER).
  - `ENDSEQ.MOV` hat 640×400 bei 8 fps; die Hilfevideos `GERHELP/*` haben 320×200 bei 12 fps mit Ton `twos` 16 Bit.
  - Die Cast-Member sind in ARTIST (`artist.mov`) und im Menü (`introvideo`) gleich: Rechteck 640×480, `directToStage=1`, `crop=0`, `center=0`, Flags `0xa00042a`.
  - **Folgerung:** Das Videoformat als Ursache für B1 ist ausgeschlossen. Infrage kommen die Einbindung im Raum (Sprite-Rechteck, Ink, gleichzeitig laufende Score-Sprites, Palette des Raums) oder der Zustand nach `caught()` (Zeiger, Puppet-Sprites).
- **Desktop ohne Fenster** (eigener Linux-Build, Startwarnung in der Test-INI abgeschaltet):
  - Start bis `Running …` etwa 1 s, inklusive Erkennung.
  - `--start-movie=ARTIST.DXR@1203` (Label `caught`): `artist.mov` läuft von `STARTING VIDEO` bis `STOPPING VIDEO` in 15 s, also in Echtzeit (Länge 14,8 s), ohne Warnungen. Danach folgt der Raumabschluss mit `b_getPos: list arg should be of type ARRAY` (Folge des Direkteinstiegs ohne `startsequence`).
  - Ohne Fenster lässt sich das **Bild** nicht prüfen; das übernimmt der Desktop-Vergleich des Nutzers.
- **Einordnung (Stand Agent):**

  | ID | Desktop | Einordnung | Betroffen | Nächster Schritt |
  |---|---|---|---|---|
  | B1 | Bild offen (Nutzer); Ablauf und Tempo am Desktop unauffällig | offen | Raum aus dem ersten Lauf unbekannt; alle 19 Raumvideos | Desktop-Vergleich, Diag-Lauf mit Raumname |
  | B2 | nein: Echtzeit am Desktop | 3DS-Leistung | jedes Missgeschick-Video | Diag-Lauf: fps, *converted*, *flush*, *update* |
  | B3 | offen (Nutzer) | offen | Raum unbekannt | Desktop-Vergleich |
  | B4 | offen (Nutzer) | offen; Kandidat: Hilite-Invertierung (`Window::renderChannel` → `invertChannel`) | alle Räume? | Desktop-Vergleich |
  | B5 | ja: auch am Desktop (40 s Wartezeit ohne Fenster) | allgemeines ScummVM-Verhalten (`ADGF_UNSTABLE`), kein Engine-Fehler | jeder Start | im Port abgeschaltet (Patch 0006) |
  | B6 | nein: etwa 1 s bis `Running` am Desktop | 3DS-Backend/Leistung, Anteil des Dialogs aus B5 unbekannt | Start | Diag-Lauf: Startphasen messen |

### 2026-11-10 – Erster spielbarer Lauf im Emulator Azahar

- **Build:** `mausjagd.3dsx`, Fork `a485c59020` (Patches 0001–0004), Spieldaten in der RomFS. Auf der virtuellen SD liegt `dspfirm.cdc`.
- **Läuft:** Direktstart, Erkennung in `romfs:/game`, Startfilm, Menü, Intro-Video komplett mit Ton, erster Raum.
- **Log** (`%APPDATA%\Azahar\sdmc\3ds\mausjagd\scummvm.log`):
  - geöffnet 19:29:51, `Running The Great Green Mouse Disaster (Windows/German)` um 19:31:36
  - `3ds initsize w:640 h:480`, `pixelformat: 1 0 0 0 0` (CLUT8)
  - `FileIO … D:\saveinfo.txt` fehlt beim ersten Start; das ist normal.
- **Befunde** (Nutzer, Details und Aufgaben in PLAN.md §9):
  - B1: verzerrtes Bild beim Fangen einer Maus
  - B2: Einbruch auf 5 FPS
  - B3: Figuren weiß, bis die Raummusik endet
  - B4: Rechteck um den Tippunkt
  - B5: ScummVM-Warnung beim Start
  - B6: lange Startzeit
- **Einordnung Desktop/3DS:** offen (T4.6).

### 2026-11-10 – Eigener Linux-Build, Läufe ohne Fenster

Build: `upstream-base` `7c924b93`, nur die Director-Engine, siehe `docs/build-desktop.md`. Bild und Ton liefen über die SDL-Dummy-Treiber, Eingaben gab es keine.

- **Erkennung:** `director:ggmd` "The Great Green Mouse Disaster (Windows/German)", Target `ggmd-win-de`. Mitgefunden werden `ggmdpics` (Galerie, `GALLERY.EXE`) und `otelo` (Demo, `PEARL.EXE`).
- **Kein Absturz** unter WSL1, anders als das offizielle Windows-Release in der Agenten-Sandbox.
- **Start:**
  - `MAUSJAGD.EXE` lädt den eingebetteten `GGMDSTRT.DIR` und `SHARED.DXR`. `LINGO.INI` läuft, denn `thecdpath` ist gesetzt.
  - `startit` und `checkifcd` laufen ohne Fehler. **Die Pfadabbildung klappt:** `D:\lingo.ini` wird auf `game/LINGO.INI` aufgelöst, und `FileIO` findet `FILEIO.DLL`.
  - Frame 2 spielt `theme.aif`. Die Frames 3–10 warten nur auf die **Zeit**, nicht auf Klick oder Sound; der Startbildschirm hat lange Frame-Pausen.
- **Menü:** Mit dem Kanal `fast` wechselt der Startfilm zu `GGMDMENU.DXR` (38 Frames). Danach startet das QuickTime-Intro (Audio-Codec `raw `).
- **Warnungen**, je einmal und vermutlich harmlos:
  - `Score::getChannelById(0): out of bounds` und `Score::getSpriteById(): sprite on frame 1 with id 0 not found` im Startfilm
  - `SearchSet::add: archive … already present`
- **Grenze:** Ohne Eingaben lässt sich nicht weiter testen. Spielablauf, Fangen und Raumwechsel prüft der GUI-Test des Nutzers; später kommen eventuell Aufzeichnungen über den Event-Recorder von ScummVM dazu.

### 2026-11-10 – Korrektur zur Erkennung

- Im ScummVM-Quellcode (`v2026.4.0` und Master `7c924b93`) steht das Spiel in `engines/director/detection_tables.h` als **`ggmd`** "The Great Green Mouse Disaster" mit dem Eintrag `WINGAME2_l("ggmd", "", "MAUSJAGD.EXE", "d:04d63d66…", 1302352, "SHARED.DXR", "d:15f0add5…", 389060, Common::DE_DEU, 404)`.
- Die MD5s der ersten 5000 Bytes von `game/MAUSJAGD.EXE` und `game/SHARED.DXR` stimmen mit dem Eintrag überein.
- Der Fallback vom 2026-11-09 kam aus dem Testordner `vendor/scummvm-test/a`, der nur `MAUSJAGD.EXE` und `LINGO.INI` enthielt. Mit dem vollständigen Ordner `b` gab es keine Meldung "unbekannte Variante".
- **Folge:** Für die Erkennung ist kein Patch nötig (T3.3). Beim Hinzufügen von `game/` sollte ScummVM das Spiel direkt als "The Great Green Mouse Disaster (Windows/Deutsch)" erkennen.

### 2026-11-09 – T3.1 Smoke-Test, ScummVM 2026.4.0 (offizielles Release, Windows x86_64)

- **Download:** `https://downloads.scummvm.org/frs/scummvm/2026.4.0/scummvm-2026.4.0-win32-x86_64.zip`, SHA-256 `fb60cfc0…56736` (stimmt mit der offiziellen `.sha256` überein). Entpackt nach `vendor/scummvm-release/` (ignoriert).
- **Erkennung:** Das Spiel ist **nicht** in der Erkennungstabelle von ScummVM. Die **Fallback-Erkennung greift**:
  ```
  Matched game IDs for the director engine: director-win-fallback
    {"MAUSJAGD.EXE", 0, "t:474c6d4f15d30c1d6ec6ed3b3c6e7e67", 1302352},
  WARNING: Director fallback detection D4.00 (uses tail MD5)!
  ```
  Diese Daten gehen in T3.3 in den Erkennungseintrag (Tail-MD5, Größe, Version 404).
- **Absturz:** In der Sandbox des Agenten stürzt `scummvm.exe` bei **jedem** Kommandozeilen-Aufruf beim Beenden ab, auch bei `--version` und bei einem leeren Ordner. Es ist eine Heap-Beschädigung `0xC0000374` bzw. bei portabler Konfiguration `0xC0000005`, jeweils in `ntdll.dll`. Die Konfigurationsdatei wird nie geschrieben. Ursache vermutlich die Sandbox, kein Zusammenhang mit dem Spiel. Ein Aufruf ohne Sandbox wurde nicht freigegeben.
- **Folge:** Der eigentliche Spieltest (GUI) läuft durch den Nutzer, siehe "Anleitung Spieltest" unten.
- **Portabler Modus:** Beim Test mit portabler Konfiguration ist neben der EXE eine leere `scummvm.ini` entstanden. Solange sie existiert, schreibt ScummVM Konfiguration **und** Log in den Programmordner (`vendor\scummvm-release\scummvm-2026.4.0-win32-x86_64\scummvm.ini` und `…\scummvm.log`) statt nach `%APPDATA%\ScummVM\`. Das ist gewollt: Spieleintrag und Log bleiben im ignorierten `vendor/`.
- **Stand 2026-11-10:** Laut Windows-Ereignisprotokoll gab es nach den Agenten-Tests (19:01–19:02) keinen weiteren Start von `scummvm.exe`. Der Spieltest steht noch aus.
- **Status:** Erkennung ok (Fallback), Spieltest offen.

## Anleitung Diagnose-Lauf und Desktop-Vergleich (T4.6, für den Nutzer)

**A. Emulator Azahar mit `dist\3ds\mausjagd-diag.3dsx`**

1. **Kaltstart vorbereiten:** Den Ordner `%APPDATA%\Azahar\sdmc\3ds\mausjagd` in `mausjagd-alt` umbenennen (das alte Log bleibt so erhalten). `dspfirm.cdc` bleibt, wo es ist.
2. In Azahar prüfen und notieren, ob unter Einstellungen → System der **New-3DS-Modus** an ist.
3. `mausjagd-diag.3dsx` starten und mit der Stoppuhr messen, wie lange es bis zum **Startbildschirm des Spiels** dauert. Erscheint irgendein ScummVM-Dialog? (Erwartet: keiner.)
4. Menü → einen Raum wählen. **Den Namen des Raums notieren.**
5. Im Raum: bis zum Ende der Raummusik warten (B3: Sind die Figuren weiß?), irgendwo hintippen (B4: Rechteck?), dann eine Maus aufscheuchen und **fangen** (B1, B2). Das Missgeschick-Video bis zum Ende laufen lassen und die App-FPS von Azahar ablesen.
6. Zurück zur Hotelübersicht, dann über das Hotel-Symbol oder Esc beenden.
7. Dem Agenten Bescheid geben. Er liest `%APPDATA%\Azahar\sdmc\3ds\mausjagd\scummvm.log` selbst; Screenshots von B1, B3 und B4 bitte dazulegen.

**B. Desktop-Vergleich mit dem offiziellen ScummVM 2026.4.0**

1. `vendor\scummvm-release\scummvm-2026.4.0-win32-x86_64\scummvm.exe` starten. Ist das Spiel noch nicht eingetragen, wie unten unter "Anleitung Spieltest" hinzufügen.
2. **Denselben Raum** wie in A wählen und dieselben Schritte machen: Raum betreten und auf die Musik warten, hinklicken, eine Maus fangen, das Video ansehen.
3. Für B1, B3 und B4 jeweils notieren: **tritt auch hier auf ja/nein**, bei "ja" mit Screenshot.


1. `vendor\scummvm-release\scummvm-2026.4.0-win32-x86_64\scummvm.exe` per Doppelklick starten.
2. **Spiel hinzufügen…** und den Ordner `C:\Users\Alphe\Documents\GitHub\MJIGH3DS\game` wählen. ScummVM sollte "The Great Green Mouse Disaster (Windows/Deutsch)" erkennen. Meldet es stattdessen eine unbekannte Variante, trotzdem hinzufügen und dem Agenten Bescheid geben.
3. Spiel starten und notieren:
   - Erscheint das Menü? Läuft das Intro-Video mit Ton?
   - Lässt sich ein Level wählen und "Start" drücken? Erscheint die Hotelübersicht?
   - Reagiert das Mausometer beim Bewegen und gibt es Alarm?
   - Kommt man in einen Raum? Lässt sich die Maus aufscheuchen und **fangen**?
   - Läuft das Missgeschick-Video danach?
   - Fehlermeldungen oder Abstürze? An welcher Stelle?
4. ScummVM über "Beenden" schließen (nicht das Fenster abschießen), damit Konfiguration und Log geschrieben werden. Das Log liegt dann im portablen Modus unter `vendor\scummvm-release\scummvm-2026.4.0-win32-x86_64\scummvm.log`, sonst unter `%APPDATA%\ScummVM\Logs\scummvm.log`. Der Agent prüft beide Orte und das Windows-Ereignisprotokoll (Abstürze von `scummvm.exe`).

### 2026-11-10 – Port im Emulator Azahar: Absturz beim Start (behoben: Absturz; offen: Ton)

- **Symptom:** `mausjagd.3dsx` mit eingebetteten Daten, direkt in Azahar geladen. Es kommt "An exception occurred", "Undefined Instruction" im Thread `mausjagd-main`, `LR = 0x0012F9C8`.
- **Auflösung** mit `arm-none-eabi-addr2line` auf `~/build/3ds/scummvm.elf`: `Director::DirectorEngine::~DirectorEngine()`, `director.cpp:173`, also `_stage->decRefCount()`.
- **Ursache:**
  - `OSystem_3DS::initAudio()` ruft `ndspInit()` auf. Ohne DSP-Firmware `sdmc:/3ds/dspfirm.cdc` schlägt das fehl. Dann startet kein Audio-Thread, und der Mixer bleibt `setReady(false)`.
  - `DirectorEngine::run()` bricht deshalb sofort mit `kAudioDeviceInitFailed` ab, noch bevor `_stage` angelegt ist.
  - Der Destruktor dereferenziert dann den Nullzeiger `_stage`. Das ist ein allgemeiner Fehler in ScummVM.
- **Behoben:** Patch 0003 `DIRECTOR: Fix crash in destructor when run() exits early` (Kandidat für upstream).
- **Zusätzlich:** Patch 0004 legt `sdmc:/3ds/mausjagd/` beim Start an. In Azahar fehlte der Ordner, deshalb gab es kein Log.
- **Offen:**
  - Für Ton braucht die App `dspfirm.cdc` auf der (virtuellen) SD-Karte.
  - Ohne die Datei startet die Director-Engine nicht; ScummVM zeigt dann nur eine Fehlermeldung. Für den Port ist ein verständlicher Hinweis geplant (T6).
- **Korrektur zum Test von 17:56:**
  - Dieser Test lief ebenfalls in Azahar, mit dem unveränderten Build. Laut `%APPDATA%\Azahar\sdmc\3ds\scummvm\scummvm.log` und `scummvm.ini` kam nur der ScummVM-Launcher; es wurde kein Spiel hinzugefügt.
  - Das Spiel selbst lief auf 3DS bzw. Emulator also noch nie.

### 2026-11-10 – Wünsche des Nutzers zum Port

- Das Spiel soll direkt starten, ohne ScummVM-Launcher. Umgesetzt mit dem Port-Modus `MAUSJAGD_PORT` (Patch 0001), siehe `docs/build-3ds.md`. Die SD-Struktur ist jetzt `SD:\3ds\mausjagd\`.
- Die Spieldaten sollen in die `.3dsx`. Umgesetzt mit Patch 0002 und `scripts/stage_game_data.py`.
- Testumgebung: Emulator Azahar (`C:\Program Files\Azahar`, virtuelle SD `%APPDATA%\Azahar\sdmc`), später ein New 3DS / New 2DS XL mit Homebrew Launcher.

## Anleitung 3DS-Test (T4.5, für den Nutzer)

> **Ab dem Port-Build (`mausjagd.3dsx`) gilt die Struktur aus `docs/build-3ds.md`:** `SD:\3ds\mausjagd\mausjagd.3dsx` und Spieldaten in `SD:\3ds\mausjagd\game\`. Log unter `SD:\3ds\mausjagd\scummvm.log`. Die Schritte unten beschreiben noch das unveränderte Build.

Hardware: New 3DS / New 2DS XL mit Homebrew Launcher. Getestet wird das **unveränderte** Build aus `upstream-base`; die Touch-Anpassungen folgen erst in Phase 5.

1. **SD-Karte:**
   - `dist\3ds\scummvm.3dsx` nach `SD:\3ds\scummvm\scummvm.3dsx` kopieren. Liegt dort schon ein offizielles ScummVM, dieses vorher umbenennen, z. B. in `scummvm-offiziell.3dsx`.
   - Den **Inhalt** von `game\` (176 MB) nach `SD:\3ds\scummvm\games\mausjagd\` kopieren.
   - Für Ton braucht jede Homebrew-App `SD:\3ds\dspfirm.cdc`. Fehlt die Datei, einmal mit "DSP1" erzeugen.
2. **Starten:** Homebrew Launcher → ScummVM → "Spiel hinzufügen" → `games/mausjagd` wählen. Erwartet wird "The Great Green Mouse Disaster (Windows/German)".
3. **Notieren:**
   - Startbildschirm und Titelmusik? Menü? Läuft das Intro-Video flüssig und mit Ton?
   - Kommt man in einen Raum? Lässt sich eine Maus mit dem Stift fangen?
   - Ruckeln, Tonaussetzer, Abstürze? An welcher Stelle?
4. **Log zurück:** `SD:\3ds\scummvm\scummvm.log` nach `dist\3ds-logs\` im Repo kopieren (ignoriert). Der Agent wertet es aus.

Pfade laut `backends/platform/3ds/osystem.cpp`: Konfiguration `sdmc:/3ds/scummvm/scummvm.ini`, Log `sdmc:/3ds/scummvm/scummvm.log`, Spielstände `sdmc:/3ds/scummvm/saves/`. Themes, Engine-Daten und die virtuelle Tastatur liegen in der RomFS der `.3dsx`.

## Testmatrix

Wird in T3.4 angelegt.
