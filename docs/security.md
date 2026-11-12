# Sicherheit und Robustheit (PLAN.md §10, S1–S7)

Stand: 2026-11-12. Fork `mausjagd`, Patches 0001–0027.

## Zusammenfassung

- **Kein Weg zum Brick im Binary.** Die `.3dsx` enthält keine Funktionen zum Installieren oder Löschen von Titeln, zum Schreiben der Systemkonfiguration oder zum Starten anderer Titel. Sie greift auf keine NAND-Archive zu und nutzt nur gewöhnliche Kernel-Aufrufe (Abschnitt 2).
- **Geschrieben wird nur im App-Ordner** `sdmc:/3ds/mausjagd/`. Belegt per Code-Durchsicht und Vorher-/Nachher-Vergleich der virtuellen SD-Karte. Drei Lücken, über die Schreibzugriffe nach außen möglich gewesen wären, sind geschlossen (Abschnitt 3).
- **Die Datei ist vollständig und unverändert:** Alle 442 eingebetteten Spieldateien stimmen bit-genau mit dem Inventar überein (Abschnitt 1).
- **Speicherfehler:** Statische Analyse ohne Befund im eigenen Code (Abschnitt 4). AddressSanitizer fand in 85 Läufen über alle Räume und Filme nichts. UBSan fand nur undefiniertes Verhalten im Zufallsgenerator der Engine, das ist mit Patch 0021 behoben (Abschnitt 5).
  - **Nachtrag:** Zwei Fehler lagen außerhalb dessen, was die Werkzeuge sehen; die CIA-Sitzung fand sie beim Spielen. Sie sind mit 0024 und 0025 behoben, die Lücken stehen in Abschnitt 5a.
- **Grenze:** Absolute Sicherheit liefert keine Analyse. Offene Restrisiken stehen in Abschnitt 8. Sie betreffen vor allem echte Hardware, die im Emulator nicht prüfbar ist.

## 1. Datei: `dist/3ds/mausjagd.3dsx` (`tools/inspect_3dsx.py`)

| Prüfung | Ergebnis |
|---|---|
| 3DSX-Kopf | gültig; Code 5,7 MB, Rodata 3,0 MB, Daten 0,1 MB, BSS 0,1 MB |
| SMDH | gültig, Titel "Mäusejagd im Grandhotel" |
| RomFS | 457 Dateien, 192 MB, alle Bereiche innerhalb der Datei |
| Spieldaten | 442 von 442 Dateien vorhanden, **alle SHA-1 korrekt**, keine zusätzlichen |
| übrige RomFS-Dateien | nur ScummVM-Dateien (Themes, Schriften, Engine-Daten, Tastatur); **keine `diag.txt`** |

Das Werkzeug erkennt eine eingebettete `diag.txt`: Bei `mausjagd-diag.3dsx` meldet es sie. Aufruf: `py -I tools/inspect_3dsx.py dist/3ds/mausjagd.3dsx docs/inventory.md`; der Exit-Code ist 0, wenn alles stimmt.

## 2. Binary: Dienste, Kernel-Aufrufe, Archive (S4)

Ausgewertet wurde `~/build/3ds/scummvm.elf` mit `arm-none-eabi-nm`, `objdump` und `strings`.

- **Mitgelinkte Systemfunktionen:**
  - `APT_*` (Anwendungsverwaltung);
  - lesend `CFGU_GetConfigInfoBlk`, `CFGU_GetSystemLanguage`, `CFGU_GetSystemModel`;
  - `DSP_*` (Ton), `FSUSER_*` (Dateisystem), `GSPGPU_*`/`GSPLCD_*` (Grafik, Displaybeleuchtung);
  - `PTMSYSM_ConfigureNew` (offizieller Taktmodus des New 3DS).
- **Nicht enthalten:** `AM_*` (Titel installieren oder löschen), `CFG_Set*`/`CFGI_*` (Konfiguration schreiben), `NS_*` (Titel starten), `MCU`, `PXI`, Netzwerk (`SOC`, `HTTPC`, `AC`), Kamera, Mikrofon.
- **Angeforderte Dienste:**
  - `fs:USER`, `gsp::Gpu`, `gsp::Lcd`, `hid:USER`, `dsp::DSP`, `APT:U/A/S`, `ptm:sysm`;
  - `cfg:u/s/i`: libctru probiert sie beim Verbinden der Reihe nach durch; genutzt werden nur Lesefunktionen;
  - `ir:rst` aus der Eingabe-Bibliothek.
- **Archive:**
  - `FSUSER_OpenArchive` wird nur in `archiveMountSdmc` aufgerufen, also nur für die SD-Karte.
  - `FSUSER_OpenFileDirectly` öffnet nur lesend die eigene RomFS und die DSP-Firmware.
  - **Kein Zugriff auf NAND-Archive.**
- **Kernel-Aufrufe:** 27 verschiedene, alle gewöhnliche Aufrufe für Anwendungen:
  - Speicher: `ControlMemory`, `QueryMemory`, `Map/UnmapMemoryBlock`;
  - Threads und Synchronisation;
  - `GetSystemTick`, IPC (`ConnectToPort`, `SendSyncRequest`), Ressourcenlimits, `Break`, `OutputDebugString`.

  Keine privilegierten Aufrufe (`0x7B` Backdoor, `0x7C` KernelSetState, Debug-Aufrufe ab `0x60`).
- **Fest eingebaute Pfade:** nur `sdmc:/3ds/mausjagd/…`, `romfs:/…` und `sdmc:/` (Arbeitsverzeichnis des Backends, siehe H1).

## 3. Schreibwege und Härtungen (S1, S4)

| Schreibweg | Ziel | Bewertung |
|---|---|---|
| Konfiguration, Log | `sdmc:/3ds/mausjagd/` | korrekt |
| Spielstände, FileIO (`saveinfo.txt`) | `sdmc:/3ds/mausjagd/saves/ggmd-…` | korrekt; seit **0022** atomar |
| Debug-Dumps der Engine (`dump_scripts`, hohe Debug-Stufen) | relativer Pfad | vorher SD-Wurzel, seit **0016** App-Ordner |
| Optionen aus `diag.txt` (`--savepath`, `--logfile`, `--config` …) | beliebig | seit **0017** nur noch Debug-Optionen |
| Lingo des Spiels | nur `FileIO` mit `read` und `append` | korrekt; kein `saveMovie` o. Ä. |

- **H1, Patch 0016:** Das Backend macht `sdmc:/` zum Arbeitsverzeichnis. Der Port wechselt nach `sdmc:/3ds/mausjagd/`.
  - **Test:** Mit `dump_scripts=true` hat die Engine 765 Dateien geschrieben, alle unter `\3ds\mausjagd\dumps\`.
- **H2, Patch 0017:** `diag.txt` nimmt nur `--debuglevel=`, `--debugflags=`, `--debug-channels-only` und `--start-movie=` an.
  - **Test:** `--savepath=sdmc:/evil` und `--logfile=sdmc:/evil.log` werden mit Warnung ignoriert, und es entsteht keine Datei.
  - Auf der ganzen SD-Karte änderte sich nur `scummvm.ini` im App-Ordner.
- **H3, Patch 0018 (S5):** Ein fataler Fehler öffnete die Debugger-Konsole, ohne Tastatur eine Sackgasse. Jetzt erscheint "Leider ist ein Fehler aufgetreten. Das Spiel wird beendet." mit dem Grund und OK; danach beendet sich die App.
  - **Test** im Emulator mit dem bekannten Fehler `Builtin 'getPos' did not return value`.
- **Atomare Spielstände, Patch 0022:**
  - **Problem:** Alle Spielstände stehen in einer Datei, die FileIO bei jedem Speichern komplett neu schreibt. Der Spielstand-Manager schrieb direkt (`createWriteStream(false)`). Ein Absturz oder Stromausfall dabei hätte alle Spielstände zerstören können.
  - **Jetzt:** Geschrieben wird in `….tmp`, umbenannt wird erst, wenn die Datei vollständig ist.
  - **Auf FAT** löscht ScummVM vor dem Umbenennen die alte Datei. In diesem winzigen Fenster liegt der neue Stand vollständig als `.tmp` vor.

## 4. Statische Analyse (S3)

GCC 15 (`-fanalyzer`) für die geänderten Engine-, Grafik-, Detection-, Engine- und Spielstand-Dateien, mit den Flags des Linux-Builds und `MAUSJAGD_PORT`. Dazu GCC 16 (devkitARM) für `mausjagd.cpp`, `main.cpp`, `osystem.cpp` und `osystem-graphics.cpp`.

- **Eigener Code:** keine Meldung.
- **Übriger ScummVM-Code:** Meldungen zu Speicherpools ("leak"), `Common::List` ("deref before check"), `Director::Object` ("uninitialized") und "`new` könnte Null liefern". Das sind bekannte Fehlalarme des C++-Analysators bzw. betreffen Pfade, die für D4 nicht laufen (`buildD6Score`).
- Compiler-Warnungen der eigenen Dateien im 3DS-Build: keine.

## 5. Sanitizer (S2)

**Aufbau:** Linux-Build mit `--enable-asan --enable-ubsan` (`~/build/linux-asan`, Director-Engine wie im Port), ohne Fenster. Skript `~/asan-sweep.sh`, 85 Läufe:
- jeder der 19 Räume ab Frame 1, ab der ersten Versteck-Animation, ab dem ersten Mauslauf und ab dem Label `caught` (Missgeschick-Video);
- dazu Menü mit Intro, Hotelübersicht, Startfilm, INSTRUM, ORCH, ATTIC, THEEND, CREDITS und EXIT.

Alle Läufe starteten die Engine. Die Direkteinstiege enden teils mit Lingo-Fehlern, weil Variablen aus dem normalen Ablauf fehlen; bis dahin laufen die jeweiligen Pfade.

| Werkzeug | Ergebnis |
|---|---|
| **AddressSanitizer** (Pufferüberläufe, Zugriffe auf freigegebenen Speicher, Stack-Überläufe) | **0 Funde** in 85 Läufen |
| **UBSan** (undefiniertes Verhalten) | Funde nur im Zufallsgenerator (`engines/director/util.cpp`, Zeilen 1239–1282): Überläufe vorzeichenbehafteter Ganzzahlen, Linksverschiebung negativer Werte, `1 << 32` |

- **Behoben mit Patch 0021:** gleiches Ergebnis Bit für Bit (Test über 20 Mio. Eingaben gegen den alten Code mit `-fwrapv`).
- **Gegenprobe** mit SNOOKER, ARTIST, SLOBS und Menü: ASan 0, UBSan 0.
- Eigener Port-Code (`MAUSJAGD_PORT`, 3DS-Backend) läuft nicht im Linux-Build. Ihn decken die statische Analyse (Abschnitt 4) und die Emulatortests ab.

## 5a. Lücken der Werkzeuge (Nachtrag 2026-11-12)

Zwei Fehler hat die CIA-Sitzung beim Spielen gefunden. Beide fallen in Bereiche, die die Werkzeuge aus den Abschnitten 4 und 5 nicht abdecken:

| Fehler | Patch | Warum unentdeckt |
|---|---|---|
| Doppelte Freigabe von Texturspeicher in `Sprite::free()`/`create()` des 3DS-Backends. Der Fehler steckt schon im ScummVM-Code; die Hotelkarte (0010) löst ihn bei jeder Aktualisierung aus. | 0024 | Das 3DS-Backend läuft nicht im Linux-Build, den die Sanitizer prüfen. Im Patch-Review zu 0010 fiel nicht auf, dass `free()` den Texturzeiger stehen lässt. |
| `_scaleX`/`_scaleY` nicht initialisiert bei Videos aus Cast-Daten. Dadurch wurden Video-Sprites bis 13100×23424 groß, mit Heap-Spitzen bis 65 MB und Stillstand (B8). | 0025 | ASan und UBSan erkennen das Lesen nicht initialisierter Werte nicht. Das könnten nur MemorySanitizer oder Valgrind. |

**Nachkontrolle:**
- **Nicht initialisierte Felder:** Die Konstruktoren aller Director-Cast-Klassen, von Sprite, Channel, Frame, Score, Cast, Movie, Window sowie von Sprite und OSystem im 3DS-Backend wurden heuristisch durchsucht (Felder ohne Vorgabewert, die ein Konstruktor nicht setzt). Jeder Treffer wurde von Hand geprüft. Für dieses Spiel bleibt kein Fall, in dem ein solches Feld gelesen wird:
  - Viele Felder setzen `reset()`, die Zuweisung im Kopier-Konstruktor oder das Laden vor der ersten Nutzung (z. B. die Score-Felder für D4).
  - `TextCastMember::_height`/`_ascent` liest nur das Speichern eines Films.
  - `_alphaThreshold` gibt es erst ab D7, RichText ab D5.
  - Die Kopier-Konstruktoren bei `_emptyFile` und `_bgCol` sowie `_needsReload` bei `importFileInto` kommen nur über `duplicate` bzw. `importFileInto` zum Zug; beides nutzt das Spiel nicht.
- **Freigeben und neu anlegen** im eigenen Port-Code: Alle übrigen Stellen nutzen `Graphics::Surface::free()`, das den Zeiger zurücksetzt, oder `Sprite::free()` (seit 0024 sicher).
- **Offen:** Ein Lauf mit Valgrind (Memcheck) über den Linux-Build würde nicht initialisierte Werte zur Laufzeit finden. Valgrind ist in WSL nicht installiert; die Installation braucht eine Freigabe.

## 6. Speicher und Stack (S6)

Gemessen mit dem Diagnosemodus (Patch 0020: Timer alle 20 ms, Spitzenwerte), Azahar im New- und Old-3DS-Modus. Build `cd8d6fa151` (Patches 0001–0025), 2026-11-12:

| Szene | Heap (Spitze) | linearer Speicher frei (Minimum) New / Old |
|---|---:|---:|
| SNOOKER | 27,4 MB | 15,0 / 4,8 MB |
| ATTIC (größter Cast) | 36,0 MB | 15,0 / 4,8 MB |
| THEEND (Endvideo) | 10,2 MB | 16,0 / 5,8 MB |
| Hotelübersicht mit Karte | 10,8 / 11,1 MB | 15,0 / 4,8 MB |
| Fang-Video Fitness (B8) | 22,4 MB | 15,0 / 4,8 MB |
| Fang-Video Hochzeitspaar (B8) | 23,3 MB | 15,0 / 4,8 MB |
| Fang-Video Speisesaal (B8) | 26,9 MB | 15,0 / 4,8 MB |

Die Fang-Videos laufen in beiden Modi mit 640×480 und 13–16 fps. Die Werte der ersten vier Szenen gleichen der Messung vom 2026-11-11 vor Patch 0025 auf 0,1 MB genau.

- **Linearer Speicher** (Texturen, Old 3DS 10 MB): auch im Old-3DS-Modus 4,8 MB Reserve.
- **Heap:** Azahar gibt der App im Old-3DS-Modus 79 MB, ein echter Old 3DS hat nach Abzug von Code und linearem Speicher etwa 44 MB. Mit der Spitze von 36 MB bleiben dort geschätzt 8 MB Reserve. Das muss auf echter Hardware gemessen werden.
- **B8:** Vor Patch 0025 konnten Video-Sprites je nach zufälligem Speicherinhalt riesig werden. Die CIA-Sitzung maß dabei Heap-Spitzen bis 65,8 MB und 2 fps; auf einem echten Old 3DS wäre das ein Absturz. Mit 0025 bleiben dieselben Videos unter 27 MB. Ein Prüflauf der CIA-Sitzung über alle 19 Räume mit Fangen (New-Modus) kam auf höchstens 35,0 MB.
- **Stack:** Der Hauptthread hat seit Patch 0019 256 KB statt 64 KB. Das schafft Reserve für FreeType beim Fehlerdialog (bekanntes Problem laut README) und für verschachtelte Lingo-Aufrufe.

## 7. Patch-Review (S1)

Prüfpunkte: Puffer und Längen, begrenzte Zeichenoperationen, Dateipfade, Fehlerbehandlung, Dienste.

| Patch | Inhalt | Befund |
|---|---|---|
| 0001 | Direktstart, App-Ordner | Pfade fest im App-Ordner; keine Puffer |
| 0002 | Spieldaten aus der RomFS | nur lesend; Existenzprüfung vor Nutzung |
| 0003 | Null-Prüfung im Destruktor | unbedenklich |
| 0004 | App-Ordner anlegen | nur `sdmc:/3ds/mausjagd/`; Fehler beim Anlegen werden toleriert |
| 0005 | Diagnosemodus | Datei zeilenweise mit `Common::String`; Zeitmessung ohne Puffer |
| 0006 | Startwarnung aus | nur ein Konfigurations-Default |
| 0007 | Erkennung nur für `ggmd` | nur ein Filter, keine Speicherzugriffe |
| 0008 | Startbildschirm | feste Größe 400×240; alle Rechtecke innerhalb; Text über die begrenzende `drawString` |
| 0009 | normaler Bildschirmmodus | ein Systemaufruf weniger |
| 0010 | Hotelkarte | Skalierung mit Grenzprüfung in jeder Schleife; Palettenindex gegen die Palettenlänge geprüft; Divisionen nur durch geprüfte Werte ≥ 2; Rahmen auf den Bildschirm zugeschnitten; keine Dateizugriffe |
| 0011 | gelöschte Palette | nur Steuerlogik |
| 0012 | nicht doppelt rendern | nur Steuerlogik; identisches Ergebnis |
| 0013 | schneller Blit | nur, wenn Quelle, Maske und Ziel vollständig in Grenzen liegen; sonst alter Pfad |
| 0014 | `transBlit` | gleiche Grenzprüfungen wie der alte Pfad pro Zeile und Pixel |
| 0015 | `FloodFill` mit Array | Kopie des Punkts vor dem Wachsen des Arrays; gleiche Grenzprüfung in `addSeed` |
| 0016 | Arbeitsverzeichnis | schränkt Schreibwege ein |
| 0017 | Optionsfilter | schränkt Schreibwege ein |
| 0018 | Fehlerdialog | Wiedereintritt verhindert (bei einem Fehler im Dialog endet die App direkt) |
| 0019 | Stack 256 KB | kostet 192 KB Heap |
| 0020 | Speicherstatistik | nur lesend; Timer-Thread schreibt nur eigene Zähler |
| 0021 | Zufallsgenerator ohne undefiniertes Verhalten | bit-gleich (Test mit 20 Mio. Eingaben) |
| 0022 | atomare Spielstände | nutzt den vorhandenen Mechanismus von ScummVM |
| 0023 | `play done` aus Ereignis-Skripten (B7, CIA-Sitzung) | nur Steuerlogik, ein neues Feld mit Vorgabewert; keine Puffer, Pfade oder Dienste. Im Spiel ändert sich nur der Handler `bored` (INSTRUM, EXIT); alle anderen `play`-Aufrufe stehen in Frame-, Sprite- oder Cast-Skripten |
| 0024 | Texturzeiger nach dem Freigeben löschen (CIA-Sitzung) | behebt eine doppelte Freigabe von linearem Speicher (Abschnitt 5a); `create()` legt die Textur danach neu an, weil es `!texture.data` prüft |
| 0025 | Skalierung von Videos aus Cast-Daten (B8, CIA-Sitzung) | behebt einen nicht initialisierten Wert (Abschnitt 5a); der Kopier-Konstruktor übernimmt den Wert schon, der Standard-Konstruktor setzt ihn auf 100 |
| 0026 | Erkennungseintrag der englischen Windows-CD (CIA-Sitzung) | nur eine Tabellenzeile (Dateinamen, MD5, Größen) |
| 0027 | englische Fassung `MAUSJAGD_LANG_EN` (CIA-Sitzung) | Alle Schreibwege nutzen weiter das Makro `MAUSJAGD_APP_DIR`, das jetzt `sdmc:/3ds/ggmd/` ist; im Binary steht kein anderer SD-Pfad (Abschnitt 10). Texte sind feste Konstanten; die Formatzeichenkette `"of %d"` hat genau einen Platzhalter für `kNumRooms`. Ohne den Schalter bleibt der Code gleich. |

## 8. Vergessene Winkel und Restrisiken

**Geprüft und in Ordnung:**
- **Sleep, HOME, Beenden:**
  - Deckel zu und HOME pausieren die Engine samt Ton und setzen sie fort.
  - "Beenden" im HOME-Menü erzeugt ein normales `EVENT_QUIT`, ScummVM fährt geordnet herunter.
- **Bedienung:** Tastenkombinationen für Debugger und Beenden sind auf dem 3DS keiner Taste zugeordnet (laut Log nicht belegbar).
- **Speicher im Old-3DS-Modus:** siehe Abschnitt 6.

**Offen bzw. nur auf echter Hardware prüfbar:**
- **Heap auf dem Old 3DS:** geschätzt 8 MB Reserve in ATTIC; messen mit `diag.txt` auf der SD-Karte (S6, T5.6). Im Emulator ist mit Patch 0025 neu gemessen (Abschnitt 6), die größte Spitze bleibt ATTIC.
- **Nicht initialisierte Werte zur Laufzeit:** nur heuristisch geprüft (Abschnitt 5a); ein Valgrind-Lauf steht aus.
- **Start als Applet:** Wird die `.3dsx` aus einem Einstieg gestartet, der nur Applet-Speicher bekommt (manche Homebrew-Einstiege), reicht der Speicher nicht. Unterstützt ist nur der Start über den Homebrew Launcher mit vollem Anwendungsspeicher; das gehört ins README (T6.4).
- **DSP-Firmware:** Ohne `sdmc:/3ds/dspfirm.cdc` gibt es keinen Ton; die App läuft weiter (Fix aus dem ersten Lauf). Wie man die Firmware sichert, gehört ins README.
- **SD-Karte voll oder schreibgeschützt:** Speichern schlägt fehl, das Spiel läuft weiter; Spielstände gehen nicht verloren (atomar). Nicht getestet.
- **SD-Karte im Betrieb entfernt:** Absturz der App ist möglich und nicht abfangbar; Spielstände bleiben durch das atomare Schreiben erhalten.
- **Lingo-Warteschleifen:** In `repeat while the soundBusy` (Raumstart) reagiert die App einige Sekunden lang nicht auf "Beenden"; danach beendet sie sich normal.
- **Debug-Ausgabe über GDB-HIO:** Jede Log-Zeile geht zusätzlich per `printf` an eine HIO-Schnittstelle, die ohne Debugger ins Leere läuft. Das ist harmlos und kostet nur im Diagnosemodus etwas Zeit.
- **CIA (S7):** Rechte gekürzt und eigene Title-ID, siehe Abschnitt 9. Offen: Start und Deinstallation auf echter Hardware.

## 9. CIA: `dist/3ds/mausjagd.cia` (S7)

Gebaut mit `CIA=1 bash scripts/build-3ds.sh` und `config/mausjagd.rsf`, geprüft mit `ctrtool -p` (Project_CTR, aus dem Quellcode gebaut, siehe `docs/build-3ds.md`).

| Prüfung | Ergebnis |
|---|---|
| Title-ID | `000400000F8D4A00` (UniqueId `0xF8D4A`), nicht die von ScummVM (`0xFF321`); Produktcode `CTR-H-MJGH`, Prozessname `Mausjagd` |
| Inhalt | ein Content (NCCH), unverschlüsselt; dieselbe ELF, dasselbe SMDH und dieselbe RomFS wie in der `.3dsx` |
| Dienste | nur `APT:U`, `cfg:u`, `dsp::DSP`, `fs:USER`, `gsp::Gpu`, `gsp::Lcd`, `hid:USER`, `ir:rst` (Vorlage: 30), also genau die aus Abschnitt 2 |
| Dateisystem | nur Direct SDMC; kein NAND, keine ExtData, kein Spielstand-Archiv (`SaveDataSize` 0) |
| Kernel-Aufrufe | Liste der Vorlage ohne `0x7B` Backdoor; alle 27 im Binary benutzten sind enthalten |
| Speicher, Takt | wie bei ScummVM: Old 3DS 64 MB, New 3DS 124 MB, 804 MHz und L2-Cache |

- **`ptm:sysm`** ist nicht freigegeben: `osSetSpeedupEnable` scheitert beim CIA ohne Folgen, Takt und Cache setzt die RSF.
- **Emulator** (Azahar 2126.2, 2026-11-11):
  - `azahar.exe -i …\mausjagd.cia` installiert nach `title/00040000/0f8d4a00/content/` (`.tmd` und `.app`, 202 MB). Der Prozess beendet sich danach nicht selbst und muss geschlossen werden.
  - Der installierte Inhalt (`.app`, mit den Rechten aus dem CIA) startet über `scripts/azahar-run.ps1 -Game …` bis zum Titelbild; das Log gleicht dem der `.3dsx`.
- **Nicht geprüft:** Azahar setzt die Dienst-Liste nicht durch. Ob die gekürzten Rechte reichen, zeigt erst echte Hardware. Die rückstandsfreie Deinstallation ist ebenfalls noch offen.
- **Banner und Icon** stammen bei eingebetteten Spieldaten aus Titelbild und Titelmelodie des Spiels (`scripts/make_app_art.py`, `docs/build-3ds.md`). Sie entstehen nur im Build-Ordner, nicht im Repo (PLAN.md §7).
- **Vorteil gegenüber der `.3dsx`:** Das CIA startet immer als Anwendung mit vollem Speicher; das Applet-Risiko aus Abschnitt 8 entfällt.

## 10. Englische Fassung: `dist/3ds/ggmd.3dsx` (S1, S4)

Build `ffeab9aab1` (`GAME_LANG=en`, Patches 0001–0027), geprüft am 2026-11-12:

| Prüfung | Ergebnis |
|---|---|
| `tools/inspect_3dsx.py` mit `docs/inventory-en.md` | gültig; SMDH "The Great Green Mouse Disaster"; 443 von 443 Spieldateien per SHA-1 korrekt; keine `diag.txt` |
| Pfade im Binary | nur `sdmc:/3ds/ggmd/…`, `romfs:/…` und `sdmc:/`; `3ds/mausjagd` kommt nur als Quelldateiname vor |
| Dienste | dieselben wie in Abschnitt 2 |
| RSF `config/ggmd.rsf` | wie `config/mausjagd.rsf`, nur Name `GGMD`, Produktcode `CTR-H-GGMD` und UniqueId `0xF8D4B` (Title-ID `000400000F8D4B00`). Beide Fassungen können also nebeneinander installiert sein. |
| Kaltstart in Azahar, SD-Karte vorher/nachher | Geändert haben sich nur `\3ds\ggmd\scummvm.ini` und `\3ds\ggmd\scummvm.log`. Log: "Running The Great Green Mouse Disaster (Windows/English)", Startbildschirm auf Englisch, erstes Spielbild nach 6,7 s. |

- **Getrennte Spielstände:** Die deutsche Fassung schreibt nach `sdmc:/3ds/mausjagd/`, die englische nach `sdmc:/3ds/ggmd/`. Keine liest oder überschreibt Dateien der anderen.
- **Nicht gemessen:** der Speicher der englischen Fassung. Die Daten sind fast gleich groß (183 statt 192 MB RomFS), der Code ist derselbe. Eine eigene Messung lohnt sich vor dem Hardware-Test der englischen Fassung.
