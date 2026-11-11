# Leistung

Messwerte zu Startzeit, Bildrate und Speicher. Neueste Einträge oben. Werte aus dem Emulator Azahar sind Näherungen; verbindlich sind Messungen auf echter Hardware (T4.5, T5.5).

## Messverfahren

- **Diagnosemodus** (`docs/build-3ds.md`): Mit einer `diag.txt` im App-Ordner beginnt jede Log-Zeile mit `[+s.mmm]`, der Zeit seit App-Start. Dazu kommen Startmarken und alle 5 s eine Zeile zur Bildrate. Die Optionen in der Datei schalten weitere Kanäle zu, z. B. `--debuglevel=3 --debugflags=detection` für die Spielerkennung.
- **Automatischer Lauf im Emulator:** `scripts/azahar-run.ps1` startet Azahar mit der `.3dsx`, wartet auf zwei Log-Marken, nimmt je ein Bild des Azahar-Fensters auf (nach `dist/screens/`) und beendet Azahar wieder. Die ausgegebenen Zeiten sind Wanduhr-Zeiten ab dem Start von Azahar, also einschließlich des Emulatorstarts (etwa 2,5 s).
- **Desktop zum Vergleich:** eigener Linux-Build ohne Fenster (`docs/build-desktop.md`).

## T4.12 – Raumanimationen in SNOOKER: 5 fps und Farbrauschen (2026-11-11, Azahar 2126.2)

**Befund des Nutzers:**
- Im zweiten Raum (SNOOKER) wird das Bild verrauscht und bunt, "sobald man was anklickt".
- Die Bildrate fällt auf 5 fps; das Rauschen verschwindet danach wieder, die 5 fps bleiben.
- Damit war B2 nicht behoben: Die frühere Messung lief in ARTIST, das diese Animationen nicht hat.

**Zwei Ursachen:**

1. **Farbrauschen: gelöschte Palette (Patch 0011).**
   - Mehrere Animationsframes von SNOOKER verweisen im Palettenkanal auf Cast-Member 301; SNOOKER hat nur Member bis 246.
   - `Score::setLastPalette()` fiel dann über die zwischengespeicherte Palette (ebenfalls 301) auf die Standardpalette des Films zurück, die Mac-Systempalette. Alle Bitmaps des Raums wurden per Dithering auf sie umgerechnet.
   - Fix: Bei gelöschter Palette bleibt die aktuelle. Danach ist das Bild farbtreu, die 5 fps bleiben aber.
2. **5 fps: Zeichenaufwand der Leerlauf-Animationen (Patches 0012–0014).**
   - Der Film-Loop in Kanal 20 (523×317) wird in jedem Frame neu zusammengesetzt, aus 20 überlappenden Kanälen.
   - Direkteinstieg in die Leerlauf-Schleifen (`SNOOKER.DXR@12` und `@51`): auch ohne Palette 301 sofort 3–5 fps. Die Palette war also nur zeitlich zufällig beteiligt.
   - Messung auf dem 3DS (Stufe 7, `images`): **ein Zeichendurchgang 123–185 ms**.
   - Profil am Desktop (gprof mit Aufrufzählern; die Zeitmessung geht unter WSL1 nicht) für rund 25 s:
     - `Graphics::transBlit<byte, byte>`: 97,7 Mio. Pixel, pro Pixel `colorToRGB()` (Ergebnis ungenutzt) und `hasTransparentColor()`. `MacWindow::draw()` setzt damit bei jeder Änderung das ganze Bühnenfenster zusammen.
     - `DirectorPlotData::inkBlitSurface()`: 65,8 Mio. Pixel über den virtuellen `InkPrimitives::drawPoint()`, für alle maskierten Sprites (Matte).
     - Dazu wurde jeder Kanal, der sich an Ort und Stelle ändert, doppelt gerendert (alte und neue Position sind gleich).

**Fixes:**
- **0012:** Alte Position nicht neu zeichnen, wenn die neue sie abdeckt.
- **0013:** Schneller 8-Bit-Pfad für Copy mit Maske, Matte, Mask, Blend ohne Alpha und Background Transparent. Er greift nur bei vollständig gültigen Grenzen, sonst gilt der alte Pfad.
- **0014:** `transBlit` dekodiert Farben nur noch bei Bedarf; 8 Bit nach 8 Bit kopiert direkt.
- Alle drei liefern dasselbe Bild und sind allgemeine Verbesserungen (upstream-Kandidaten).

| SNOOKER, Leerlauf-Animation | vorher | nachher |
|---|---:|---:|
| Zeichendurchgang (`Window::render`) | 123–185 ms | **11 ms** |
| Durchläufe der Hauptschleife | 4,5–4,9/s | **43/s** |
| Score-Tempo | ca. 4–5 fps | **12 fps** (Original) |
| übertragene Fläche pro Durchlauf | 307.200 px | 79.000 px im Schnitt |

- **Gegenprobe:** Missgeschick-Video ARTIST jetzt 15,8 Durchläufe/s bei 12 fps Video (vorher 11,4–12,3/s); Bild unverzerrt. Hotelkarte unverändert.
- **Noch möglich:** `MacWindow::draw()` kopiert bei jeder Änderung das ganze Fenster (7 ms im Backend). Nur geänderte Bereiche zu übertragen, wäre der nächste Schritt, falls der Old 3DS es braucht.

## T4.12 – Bildrate der Missgeschick-Videos (2026-11-10, Azahar 2126.2)

**Verfahren:** Ohne Eingaben über die Diag-Datei direkt ins Video springen: `--debuglevel=2 --debugflags=images --start-movie=ARTIST.DXR@1203` (Label `caught`), Lauf mit `scripts/azahar-run.ps1 -AfterGameSeconds 25`. `artist.mov` hat 12 fps, 640×480, SMC.

| Modus in Azahar | Bildrate im Video | umgerechnete Fläche pro Frame | Umrechnung (flush) | `updateScreen` gesamt |
|---|---:|---:|---:|---:|
| New 3DS | 11,4 / 12,3 fps | 307.200 px (Vollbild) | 7,0 ms | 7,6 ms |
| Old 3DS (`is_new_3ds=false`) | 11,3 / 12,3 fps | 307.200 px | 7,0 ms | 7,6 ms |

- Das Video läuft in **Originalgeschwindigkeit**; B2 ("5 FPS beim Fangen") tritt im Emulator nicht mehr auf (auch laut Nutzer). Die erste 5-s-Zeile (9,1 fps) enthält noch den Raumstart.
- Das Backend braucht pro Videoframe 7,6 ms von 83 ms; der Rest bleibt für Dekodieren und Engine.
- **Old 3DS:** Azahar liefert in beiden Modi dieselben Werte, bildet den Taktunterschied (268 MHz statt 804 MHz) also nicht ab. Aussagekräftig ist hier nur echte Hardware.
- Nebeneffekt der Methode: Ohne `startsequence` fehlen Variablen, nach dem Video bricht ein fataler Fehler (`Builtin 'getPos' did not return value`) ab und öffnet die Debugger-Konsole. Im normalen Spiel tritt das nicht auf.

## T4.8 – Startzeit (2026-11-10, Azahar 2126.2)

**Ziel** laut PLAN.md §3: Startbildschirm des Spiels nach höchstens 10 s.

| Phase (Zeit ab App-Start) | vorher (Fork `215225f512`) | nachher (Fork `2022c2c09f`) |
|---|---:|---:|
| Backend bereit (`diag: backend ready`) | 0,7 s | 0,8 s |
| Beginn der Erkennung (`Starting detection`) | 1,5 s | 1,4 s |
| Erkennung fertig (`Totally found`) | 76,2 s | **1,6 s** |
| Engine startet (`Starting v404 Director game`) | 77,5 s | 2,9 s |
| erstes Spielbild 640×480 (`first frame at 640x480`) | 78,6 s | **4,1 s** |
| Wanduhr ab Start von Azahar bis zum ersten Spielbild | ca. 81 s | **6,0–6,9 s** |
| Menü `GGMDMENU` (Startfilm mit den Original-Pausen) | 93,3 s | ca. 19 s (Startfilm unverändert, etwa 15 s) |

- **Ursache:** `AdvancedMetaEngineDetectionBase::detectGame()` schlägt die Dateien **aller** Einträge der Director-Erkennungstabelle nach. Viele davon sind Mac-Einträge, die `MacResManager` unter mehreren Namen sucht (`.rsrc`, `.bin`, `._name`, `__MACOSX`). Mit `--debugflags=detection` lag die Zeit vollständig in diesem Durchlauf (+1,45 s → +76,1 s). Die Prüfsummen der fünf vorhandenen Dateien kosten dagegen nur Millisekunden.
- **Am Desktop** dauert dieselbe Erkennung 0,07 s CPU-Zeit. Der emulierte 3DS ist hier um den Faktor 1000 langsamer, weit mehr als bei normalem Code (die Vorverarbeitung derselben Tabelle braucht dort nur 20 ms). Der genaue Grund ist offen, vermutlich Speicherverwaltung oder Hashing der Pfade; er spielt nach dem Fix keine Rolle mehr.
- **Fix (Patch 0007):** Im Port prüft `identifyGame()` nur noch die Einträge der gesuchten Game-ID `ggmd`. `identifyGame()` akzeptiert ohnehin nur einen Treffer mit dieser ID.
- **Restliche Zeit** bis zum ersten Spielbild (etwa 2,5 s ab Ende der Erkennung):
  - 1,2 s zwischen `Running` und `Starting v404`: ScummVM lädt dort `gui-icons.dat` (3,3 MB) und richtet die GUI ein, obwohl kein Launcher erscheint.
  - 1,2 s Engine-Start: Laden der Mac-Schriften (`MacResManager: Extracted original filename …`, etwa 0,3 s), danach `MAUSJAGD.EXE` und `SHARED.DXR`.
  - 0,4 s beim Backend-Start für die virtuelle Tastatur (`vkeybd_small`).
  - Mögliche nächste Schritte, falls auf echter Hardware nötig: GUI-Icons und virtuelle Tastatur erst bei Bedarf laden.
- **Startfilm:** Die etwa 15 s bis zum Menü sind die Frame-Pausen des Original-Startfilms (`GGMDSTRT`) und bleiben (PLAN.md §9).
- **Offen:** Messung auf dem New 3DS (T4.5). Dort kommt das Laden der `.3dsx` durch den Homebrew Launcher dazu.
