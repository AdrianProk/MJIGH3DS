# Kompatibilitäts-Log

Testmatrix und Fehlerprotokoll. Neueste Einträge oben im Protokoll.

## Protokoll

### 2026-11-12 – B8: Absturz bei Maus 14/15 (Agent, Log des Nutzers, Desktop und Azahar)

- **Befund des Nutzers (New 3DS, CIA mit Stand 2026-11-11 18:17, noch ohne B7-Korrektur):** Nach 14 gefangenen Mäusen stürzt das Spiel ab und friert den ganzen 3DS ein.
- **Log des Nutzers** (`SD:\3ds\mausjagd\scummvm.log`, lokal in `crashfiles/`, nicht im Repo):
  - Die `put`-Ausgaben zeigen den Verlauf: `spritelist` (noch offene Räume) schrumpft von 19 auf 5.
  - Reihenfolge der Räume: Ballsaal, Snooker, Hochzeitspaar, Bad, Klempner, Schlampen, Bauer, Spielzimmer, Bibliothek, Büro, Hexen, Künstler, Fitness, Bar. Maus 14 ist um 22:23:35 gefangen.
  - Der 15. Raum (Mad Scientist, Präsidenten-Schlafzimmer, Präsidenten-Wohnzimmer, Speisesaal oder Küche) startet um 22:23:37. Bis 22:23:53 folgen nur Warnungen `Sprite::getShape(): kCastMemberSprite has no cast defined!`, die auch in Räumen ohne Absturz zu Hunderten vorkommen (Treffertests beim Tippen). Danach endet das Log.
  - Der Luma-Absturzbericht im selben Ordner (`crash_dump_00000004.dmp`, Prefetch Abort im Kernel) stammt vom 01.12.2025 und vom Systemdienst `news`, gehört also nicht dazu. Für B8 gibt es keinen Bericht. Das spricht für ein Einfrieren, nicht für eine Ausnahme im Spiel.
- **Testhilfe:** `tools/scummvm-test-patches/movie-tour.patch`, eine Rundtour durch alle 19 Räume in einem Prozess. Die Test-`LINGO.INI` dafür:
  - `buildList` (Variante 1), `theBuild` `"BUILD1"`, `miceCaught` 0, `playList` `[]`, `music` 1, `mytempo` 12, `numtraps` 0, `trapsdone` `EMPTY`
  - `spritelist` 25 × 5, `shortlist` 5–23, `theselsprite` 5, `WhereAmI` `"menu"`
  - `the searchPath` wie im Startfilm, dazu die Pfade aus der Original-INI
- **Ergebnisse:**

  | Lauf | Ergebnis |
  |---|---|
  | Desktop, ohne Fangen | 19 Räume, kein Absturz; Heap +0,34 MB pro Raum |
  | Desktop, mit Fangen (Video, `endofRoom`) | 19 Räume, kein Absturz; Heap 14,1 → 20,9 MB (+0,35 MB pro Raum); nur PLAYROOM erreichte `endofRoom` nicht innerhalb von 90 s |
  | Desktop mit ASan/UBSan, Hilfevideo der Katze jedes Mal mittendrin per Filmwechsel abgebrochen | 19 Durchgänge, **kein Befund** |
  | Azahar, ohne Fangen | 19 Räume, kein Absturz; Heap 12,2 → 16,8 MB; linearer Speicher konstant 16 MB frei |
  | Azahar, mit Fangen, Spieldaten in der RomFS | 19 Räume, kein Absturz |
  | Azahar, mit Fangen, Spieldaten auf der SD (schlanker Build) | sporadischer Stillstand beim Start des Fang-Videos (Maus 17, Maus 7), einmal im Menü (Maus 4); zwei weitere Läufe ohne Stillstand |

- **Stillstand im SD-Build (GDB über Azahars Stub):** Kein Thread steckt in einer Sperre. Die Hauptschleife läuft weiter (`DirectorEngine::run` → `delayMillis(10)`), Azahar braucht kaum Rechenzeit, aber der Score rückt nicht vor, und die Tour schaltet nicht weiter. Ursache noch offen; ein Fehler der SD-Emulation von Azahar ist möglich.
- **Gefunden und behoben, Patch 0024 (3DS-Backend):**
  - `Sprite::free()` ließ nach `C3D_TexDelete()` den Texturzeiger stehen; citro3d setzt ihn nicht zurück. Das nächste `create()` gab die alte Adresse ein zweites Mal frei. War sie inzwischen neu vergeben, zum Beispiel an den direkt davor angelegten Pixelpuffer, teilten sich Grafikchip und Programm fremden linearen Speicher.
  - Die Hotelkarte (Patch 0010) löst `free()` + `create()` bei jedem Filmwechsel und jeder neuen Mauszahl aus.
  - Ein Stresstest mit 300 Aktualisierungen löste den Fehler im Emulator nicht aus; als Ursache von B8 ist er damit nicht belegt.
- **Lücke der Tour:** Bis 2026-11-12 nachmittags sprang die Tour an den Anfang des Menüs, nie in die Hotelübersicht. Die Hotelkarte war deshalb in keinem dieser Läufe aktiv (Hinweis des Nutzers: oben dasselbe Bild wie unten). Seitdem führt die Tour über Frame 14 (Hotelübersicht).
- **Reproduziert in Azahar** (RomFS, Hotelkarte aktiv, ohne Patch 0024): Stillstand bei **Maus 14** (Fitness), wieder direkt nach dem Parsen des Fang-Videos. Danach lief kein Herzschlag und keine Diagnose-Zeile mehr, und das Azahar-Fenster antwortete nicht mehr.
- **Auffällige Räume:** In einem weiteren Lauf ohne Stillstand liefen die Fang-Videos von drei Räumen mit 1,8–2,6 fps statt 11–16 fps. Der Heap stieg dabei auf Spitzen von 48,8 MB (Hochzeitspaar) und 65,8 MB (Fitness), alle anderen Räume blieben unter 35 MB. Diese drei Räume kamen vor jedem Stillstand vor, auch im Spiel des Nutzers (Maus 3, 8, 13).
- **Ursache (Desktop, Messzeilen am Video):**
  - Das Dekodieren kostet 0–1 ms pro Bild. Die **Zielbox des Video-Sprites** war aber zufällig: 640×480, 11 545–15 401 × 480 oder 13 100 × 23 424.
  - `DigitalVideoCastMember` multipliziert in `getInitialRect()` die Videogröße mit `_scaleX`/`_scaleY` (D7-Eigenschaft, upstream seit Commit `6c8a0e45f1`, 2026-06-30). Nur der Standard-Konstruktor setzte sie auf 100, der Konstruktor, der das Cast-Member aus den Filmdaten liest, ließ sie uninitialisiert.
  - Das Widget wird in Sprite-Größe angelegt und jedes Videobild hineingestreckt: bis zu mehrere hundert MB pro Bild. Am Desktop fiel das kaum auf; auf dem 3DS führte es zu 2 fps, Heap-Spitzen und schließlich zu einer Anforderung, die nicht mehr zu erfüllen war.
  - Welche Räume betroffen sind, hängt vom Zufall im Speicher ab. Deshalb trat der Stillstand mal bei Maus 4, 7, 14 oder 17 auf. Beim Nutzer kam er im 15. Raum, wahrscheinlich dem Speisesaal, dessen Video am Desktop einmal 13 100 × 23 424 groß wurde.
- **Behoben mit Patch 0025:** Initialisierung im Lese-Konstruktor. Danach haben am Desktop alle Fang-Videos (Künstler, Bauer, Hochzeitspaar, Spielzimmer, Fitness, Speisesaal) 640×480.
- **Prüflauf in Azahar mit allen Korrekturen** (Patches 0001–0025, RomFS, Hotelkarte aktiv, 2026-11-12 20:17–20:35):
  - Alle 19 Räume mit Fangen, ohne Stillstand; die Karte wurde 97-mal aktualisiert.
  - Die Fang-Videos laufen überall mit 11–16 fps; vorher hatten Hochzeitspaar, Spielzimmer und Fitness 1,8–2,6 fps.
  - Die Heap-Spitze liegt bei höchstens 35,0 MB, vorher bei bis zu 65,8 MB.
- **Auf dem 3DS bestätigt** (2026-11-12, Nutzer): neue CIA per QR-Code installiert, das ganze Spiel ohne Absturz durchgespielt.

### 2026-11-11 – B7: Katze redet im Instrumentenraum von selbst (Agent, Desktop ohne Fenster)

- **Befund des Nutzers (3DS):** Im Instrumentenraum (INSTRUM) fängt die Katze an zu reden. Nach etwa 3/4 bricht sie ab, und ihr Bild bleibt unten in der Ecke, bis man 2–3 Instrumente antippt. Meist ab Maus 2.
- **Aufbau des Tests:** eigener Linux-Build, `--start-movie=INSTRUM.DXR`, keine Eingaben. Eine eigene `LINGO.INI` in einem Testordner mit Verweisen auf die Spieldaten setzt den Zustand "Maus 2 gefangen":
  - `buildList` (Variante 1), `miceCaught`, `playList`, `music`, `WhereAmI`
  - `the timeoutMouse` = 0 wie in den Räumen und `the searchPath` wie im Startfilm
- **Ablauf in INSTRUM** (Labels: `Select` 4, `help` 7, `Done` 11, `Bored` 1397):
  - Frame 2 setzt `the timeoutLength` auf 4 s und `the timeoutScript` auf `"Bored"`, Frame 4 wartet mit `go the frame`.
  - Nach 4 s ohne Eingabe: `bored` → `play frame "bored"`, kurze Animation (Frames 1397–1413), dann `play done`.
  - **Fehler:** ScummVM kehrte zu **Frame 5** statt 4 zurück. Der Film lief über 5 und 6 in die Hilfe-Sequenz (Frame 7): Das Katzenvideo `cathel11.mov` startete von selbst (26 s). Danach sprang `go(myhelpframe)` ins Leere, weil die Variable nur der Hilfe-Knopf setzt, und der Film fiel über `Done` bis nach ORCH durch.
  - Im Original kommt diese Sequenz nur über den Hilfe-Knopf. Während des Videos überspringt jedes Antippen den Rest (`mouseDownScript` = `"go frame the frame + 1"`). Abbruch und stehenbleibendes Bild beim Antippen von Instrumenten passen dazu.
- **Ursache:** `Lingo::func_play` lässt `play done` zum nächsten Frame zurückkehren, wenn `play` aus dem Skriptkanal kam (Kanal 0). Ereignis-Skripte wie `timeoutScript` und `mouseDownScript` laufen ebenfalls mit Kanal 0 und wurden deshalb wie Frame-Skripte behandelt.
- **Behoben mit Patch 0023:** Die Engine merkt sich den Skripttyp des laufenden Ereignisses. Primäre Ereignis-Handler (`kEventScript`: `timeoutScript`, `mouseDownScript`, `keyDownScript` …) kehren nach `play done` zum selben Frame zurück. Alles andere verhält sich wie vorher, auch `on exitFrame` in Movie-Skripten.
  - Eine erste Fassung prüfte auf `kScoreScript`. Sie hätte auch `play` aus `on exitFrame` in Movie-Skripten zum selben Frame zurückgeschickt und dort eine Endlosschleife ermöglicht; Hinweis aus dem Review der Sicherheits-Sitzung. Deshalb jetzt die engere Bedingung `!= kEventScript`.
  - **Test:** Danach alle 4 s Bored-Animation und Rückkehr zu Frame 4, kein Video, kein Sprung nach ORCH.
  - **Gegenprobe im ganzen Spiel:** Nur `bored` ruft `play` aus einem Ereignis-Skript auf: INSTRUM, dazu eine unbenutzte Kopie in EXIT, wo kein Skript `"Bored"` setzt. Die übrigen Ereignis-Handler (`nothingatstart`, `checkexit`, `whenexit`, `select` …) nutzen `go`. Frame- und Sprite-Skripte verhalten sich wie bisher.
- **Nebenbefund:** `getMovieCurrentTime()` liefert bei Zeit 0 durch einen vorzeichenlosen Unterlauf die Gesamtlänge (`STARTING VIDEO … 1560/1560`). Das betrifft nur `the movieTime` bei Zeit 0, das Spiel fragt es nicht ab. Nicht behoben.
- **Offen:** Bestätigung auf dem 3DS.

### 2026-11-11 – Alle Räume durchgeprüft: Verweise ins Leere (Agent, statisch)

- **Wunsch des Nutzers:** alle Räume auf Fehler wie in SNOOKER durchgehen.
- **Werkzeug:** `tools/scummvm-test-patches/score-lint.patch` (nur Testbranch `lint-tmp`, nicht im Port). Es prüft nach dem Laden eines Films **jeden Frame** des Scores und alle Film-Loops: Palettenkanal, beide Sounds, Frame-Skript, Übergang, Cast-Member und Skripte aller Sprite-Kanäle. So werden auch Animationen erfasst, die erst auf Klick laufen.
- **Umfang:** alle 27 Filme (19 Räume, GGMDMENU, INSTRUM, ORCH, ATTIC, THEEND, CREDITS, EXIT, Startfilm), zusammen über 30.000 Frames und 60 Film-Loops.
- **Ergebnis:**

  | Film | Fund | Frames | Bewertung |
  |---|---|---|---|
  | SNOOKER | Palette 301 und Bitmap 302 fehlen (Kanal 4) | 26 | bekannt; der Palettenfix (Patch 0011) greift, das fehlende Bitmap wird wie in Director nicht gezeichnet |
  | PLUMBER | Sprite-Skript 226 fehlt (Kanal 4) | 738 | harmlos: Ein Klick auf dieses Sprite löst in diesem Frame nichts aus |
  | ORCH | Kanal 27 verweist auf die Bitmaps 102–122 (Ink 36) | 38–58 | Die Member fehlen in der Datei selbst (ORCH hat 100–101 "MOUSE CON .11/.12", dann erst wieder 123+; ProjectorRays sieht dieselbe Lücke). Director zeichnet fehlende Member nicht, ScummVM ebenso. Kein Engine-Fehler |

  Alle übrigen 24 Filme: keine Verweise ins Leere. **Eine gelöschte Palette wie in SNOOKER gibt es sonst nirgends.**

### 2026-11-11 – Alle Räume durchgeprüft: Leistung im Emulator (Agent)

- **Messreihe:** 63 Läufe in Azahar: jeder Raum ab Frame 1, ab der ersten Versteck-Animation und ab dem ersten Mauslauf, dazu INSTRUM, ORCH, ATTIC, CREDITS, EXIT, THEEND. Tabelle in `docs/performance.md`.
- **Ergebnis:**
  - Kein Raum hat einen Dauer-Engpass wie zuvor SNOOKER; das normale Zeichnen dauert überall 3–18 ms.
  - Nirgends werden Bitmaps in eine andere Palette umgerechnet, also gibt es kein Rauschen.
- **Gefunden und behoben:** Ruckler beim **ersten** Erscheinen großer Matte-Bilder. Am stärksten war SLOBS mit 132 ms pro Bild, weil `Graphics::FloodFill` pro Pixel Speicher anforderte. Patch 0015 senkt das auf 48 ms, damit bleibt der erste Durchlauf auf dem New 3DS im Budget.
- **Im echten Ablauf noch zu prüfen:**
  - INSTRUM und ORCH; der Direkteinstieg bricht dort wegen fehlender Variablen ab.
  - Das Hilfevideo des Katers (Suchpfad `GERHELP`).
  - Der Old 3DS (Hardware).

### 2026-11-11 – SNOOKER: Farbrauschen und 5 fps behoben (B1/B2, Agent)

### 2026-11-11 – SNOOKER: Farbrauschen und 5 fps behoben (B1/B2, Agent)

- **Nutzer:**
  - Die Karte im echten Spiel funktioniert: Zähler auf 1, Rahmen um den Raum.
  - Im zweiten Raum (SNOOKER) wird das Bild beim Anklicken verrauscht und bunt (Screenshot), die Bildrate fällt auf 5 fps und bleibt dort.
- **Ursachen und Fixes** (Details in `docs/performance.md`):
  - **Farbrauschen:** Animationsframes verweisen auf die gelöschte Palette 301. Die Engine fiel auf die Mac-Systempalette zurück und rechnete alle Bitmaps um. Patch 0011 behält die aktuelle Palette, auch am Desktop reproduziert.
  - **5 fps:** Die Leerlauf-Animationen kosteten auf dem 3DS 123–185 ms pro Zeichendurchgang: doppeltes Rendern, Pixel-für-Pixel-Ink-Blits und ein ineffizientes `transBlit`. Mit den Patches 0012–0014 sind es **11 ms**, der Raum läuft mit 12 fps.
- **Damit ist B1/B2 vermutlich erklärt:** Rauschen und 5 fps aus dem ersten Lauf passen genau zu diesem Muster. Damals wurde es dem Fangen zugeschrieben; tatsächlich trat es in Räumen mit diesen Animationen auf.
- **Geprüft in Azahar:**
  - SNOOKER von Frame 1 mit Animationen: farbtreu, 43 Durchläufe/s.
  - ARTIST-Video unverzerrt (15,8/s).
  - Hotelkarte unverändert.
- **Offen:** Rückmeldung aus dem echten Spiel; der Old 3DS braucht echte Hardware.

### 2026-11-11 – Hotelkarte auf dem oberen Bildschirm (T5.1, Agent)

- **Build:** `mausjagd.3dsx`, Fork `1ab81ca9da`, Patches 0001–0010.
- **Wunsch des Nutzers:** oben die Hotelkarte, ein blinkender Rahmen um den aktuellen Raum und ein Mäusezähler; die Lupe kommt später (T7.4).
- **Befund beim Bauen:** Die Hotelübersicht ist **kein** Fassadenbild (`hotlpicdull.256`), sondern der Querschnitt `interfinalfordir0001` (582×429) mit 19 Zimmern und dem Dachboden.
  - Seine Pixel beziehen sich auf die eigene Palette (Cast 23); mit der Bühnenpalette waren die Farben falsch.
  - Die Klickflächen des Mausometers (Sprites 5–23) liegen etwa 12 Pixel tiefer als die Zimmerbilder. Die Umrisse der Zimmerbilder wurden einmalig im Bild gemessen und als Tabelle hinterlegt.
- **Test in Azahar** (Direkteinstieg `GGMDMENU.DXR@14`, Testschlüssel `mausjagd_debug_room`):
  - Karte in Originalfarben, "Mäuse 0 von 19".
  - Rahmen um ARTIST (oben links) und SNOOKER (unten rechts) genau auf dem Zimmerbild.
  - Das Blinken ist belegt: Von sieben Bildern im Abstand von 170 ms zeigen vier den Rahmen.
- **Normaler Start** ohne Testschlüssel: unverändert, bis zur ersten Hotelübersicht zeigt der obere Bildschirm das Spiel; keine neuen Warnungen.
- **Offen:** Rückmeldung aus dem echten Spiel (Rahmen beim Raumwechsel, Zähler nach dem Fangen).

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
