# Kompatibilitäts-Log

Testmatrix und Fehlerprotokoll. Neueste Einträge oben im Protokoll.

## Protokoll

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

## Anleitung Spieltest (für den Nutzer)

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

## Testmatrix

Wird in T3.4 angelegt.
