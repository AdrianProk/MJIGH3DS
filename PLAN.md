# Plan: "Mäusejagd im Grandhotel" auf dem Nintendo 3DS

Ziel: Die deutsche Windows-Version von *Mäusejagd im Grandhotel* (engl. *The Great Green Mouse Disaster*) läuft auf dem Nintendo 3DS. Die Mäuse fängt man, indem man sie direkt auf dem Touchscreen antippt (siehe §3). Gestartet wird die App direkt aus dem HOME-Menü. Die Spieldaten stammen immer aus der eigenen Original-CD. Dieses Repo enthält nur Werkzeuge, Patches und Doku.

Die abzuarbeitenden Aufgaben stehen in [TODO.md](TODO.md).

---

## 1. Befunde aus der ersten Analyse (2026-11-09)

Das ISO wurde bereits nur lesend untersucht. Diese Fakten gelten als gesichert:

| Punkt | Befund |
|---|---|
| ISO | `original/The-Great-Green-Mouse-Disaster_Win_DE_ISO/GGMDCD_Ger.iso`, 609.390.592 Bytes, reines ISO9660 ohne Joliet, Volume `MAEUSEJAGD`, Dateinamen im 8.3-Format |
| Engine | **Macromedia Director for Windows 4.0.4**. Der Projektor ist `MAUSJAGD.EXE` (1,3 MB). |
| Filme | 27 × `.DXR`. Das Format ist `RIFX`, Big-Endian, Codec `MV93`, fileVersion `0x045d`. Es sind *geschützte* Filme: Der Lingo-Quelltext ist entfernt, der Bytecode (`Lscr`, `Lctx`, `Lnam`) ist vorhanden. |
| Bühne | 640×480 mit 8-Bit-Paletten (`CLUT`-Chunks) |
| Shared Cast | `SHARED.DXR` |
| Videos | 27 × QuickTime `.MOV`: 20 im Wurzelverzeichnis, 6 in `GERHELP/`, 1 in `GERVIDEO/`. Video-Codec **SMC (Apple Graphics)**, Audio `raw ` (8 Bit) bzw. `twos` (16 Bit PCM). Größte Datei: `ENDSEQ.MOV` mit 18 MB. |
| Sounds | ca. 400 × AIFF (72 MB) in `SOUNDS/` (215), `MUSIC/BUILD1-3`, `MUSIC8/BUILD1-3` (8-Bit-Varianten), `SOLOS/`, `SOLOS8/`, `STARTSND/`, `ENDSOUNG/`, dazu `START.WAV` und `SILENT.WAV` |
| Xlib | `FILEIO.DLL`, wird in `LINGO.INI` per `openXlib "FileIO"` geladen |
| `LINGO.INI` | setzt `theHDpath`/`theCDpath` = `"D:\"`, `gCPU` = `"486"`, `gMusicPath` = `"music\"`, `gSolosPath` = `"solos\"`, `centreStage` |
| Spieldaten gesamt | ca. 180 MB (DXR + MOV ≈ 107 MB, AIFF ≈ 72 MB) |
| Beilagen (ignorieren) | `AC/` (Acrobat), `IE/` (IE5), `NC/` (Netscape), `NORMAN/` (Virenscanner), `DBEVALCD/`, `PRONTO/`, `PACKER/`, `PMEASY/`, `NTSP/`, `QT/`, `SETUP/`, `SHOPPING/`, `MEDI8OR/` (Autorun-Launcher der CD) |
| Noch unklar | `GALLERY.EXE` (5,1 MB), `PEARL.EXE` (8 MB), `ONLINE.EXE`, `BILDER/*.BMP`, `AUFTRAG.PDF`, `KONFIG.PDF` |
| Spielmechanik (aus den Lingo-Namenstabellen `Lnam`) | Alle Raum-Filme kennen `mouseDown`/`mouseUp`, `clicked` und `caught`. Dazu kommen `mymouse`, `waitmouse`, `holdmouse`, `movemouse`, Verstecke (`hideplaces`, `hidepos`), Fallen (`settraps`, `selecttrap`, `checktrap`, `trapsdone`), der Zähler `miceCaught`/`countup` und der Orchesteraufbau (`buildorchestra`, `instrument`, `ORCH.DXR`, `INSTRUM.DXR`). **Damit ist bestätigt, dass man die Mäuse per Klick fängt.** Details nach der Dekompilierung in `docs/mouse-catching.md`: Gefangen wird beim `mouseDown` auf die laufende Maus. Die Maus misst etwa 39×28 px, also 19×14 auf dem Touchscreen, und läuft im Median 4,2 s (Level 1) bis 1,5 s (Level 3, spät im Spiel). |
| Hover und Tasten | `rollOver` in `GGMDMENU` und `ATTIC` (`rollovermap`); `keyCode`, `commandDown`, `optionDown` in `SHARED.DXR` |
| Speichern | `GGMDMENU` nutzt `FileIO` (`mReadString`, `loadgame`, `savelist`) |

Liste der DXR-Filme: ARTIST, ATTIC, BALLROOM, BAR, BATHROOM, BUSINESS, CREDITS, DINING, EXERCISE, EXIT, FARMER, GGMDMENU, INSTRUM, KITCHEN, LIBRARY, MADSCI, NEWLYWED, ORCH, PLAYROOM, PLUMBER, PRESBED, PRESLIV, SHARED, SLOBS, SNOOKER, THEEND, WITCHES.

---

## 2. Grundsatzentscheidung: ScummVM-Director-Engine statt Neuschreiben

**Weg: Wir setzen auf die Director-Engine von ScummVM und den offiziellen 3DS-Port von ScummVM. Das Spiel selbst wird nicht nachprogrammiert.**

Begründung:

- ScummVM liest Director-4-Dateien direkt: DXR, Casts, Bitmaps, Paletten, Sounds. Den Lingo-Bytecode führt es selbst aus. Die Assets müssen also **nicht** konvertiert werden, und der Lingo-Code muss nicht neu kompiliert werden.
- Director 4 ist die Version, die ScummVM am besten unterstützt. Mehrere D4-Titel laufen dort offiziell.
- Die QuickTime-Codecs (SMC, raw, twos) und AIFF kann ScummVM bereits dekodieren.
- `FileIO` gibt es in ScummVM als eingebautes XObject.
- ScummVM hat einen gepflegten 3DS-Port mit GPU-Skalierung, Touch als Maus und CIA/3DSX-Builds.

Daraus folgen drei Arbeitsfelder:

1. ScummVM so weit bringen, dass genau dieses Spiel auf dem PC fehlerfrei durchläuft: Erkennungseintrag, Fixes an Engine und Lingo, eventuell spielspezifische Quirks.
2. Diesen Stand für den 3DS bauen und dort anpassen: Touch-Steuerung zum Mäusefangen, Bildschirm, Performance, Speicher.
3. Alles als eigenständige 3DS-App verpacken, die das Spiel direkt startet.

**Rolle der Dekompilierung:** Der Lingo-Bytecode wird mit ProjectorRays und den Debug-Funktionen von ScummVM nur zur Analyse lesbar gemacht. So lassen sich der Spielablauf verstehen und Fehler in ScummVM gegen das erwartete Verhalten prüfen. Aus dem dekompilierten Code wird nichts gebaut.

**Ausweichplan (nur bei Gate G1, siehe unten):** ScummVM könnte grundlegende, nicht behebbare Lücken zeigen. Das ist unwahrscheinlich, weil fehlende Features in der Engine sonst einfach ergänzt werden. Dann stoppt der Agent und legt dem Nutzer die Alternativen schriftlich vor, z. B. einen eigenen, minimalen D4-Player für den 3DS. Das wäre ein neues, deutlich größeres Projekt mit eigenem Plan.

---

## 3. Bedienung: Mäuse fangen per Touchscreen

**Kernanforderung:** Man fängt die Mäuse, indem man sie direkt auf dem Touchscreen antippt. Ein Cursor, den man erst hinsteuern muss, ist nicht gewünscht.

**Was die Namenstabellen schon zeigen** (siehe §1): In jedem Raum zeigt sich eine Maus (`mymouse`) an einem Versteck (`hideplaces`, `hidepos`), wartet kurz (`waitmouse`, `waittime`) und wird beim Klick gefangen (`clicked`, `caught`). Dazu kommen Fallen und ein Zähler, mit dem sich offenbar ein Orchester aufbaut. Wie das genau abläuft, klärt T2.6. Wichtig für den Touchscreen: Die Maus ist nur kurz sichtbar, also zählen Reaktionszeit und Treffgenauigkeit.

| Thema | Entscheidung |
|---|---|
| Spielbild | **Unterer Bildschirm (Touchscreen).** 640×480 → 320×240 ist genau der Faktor 0,5. Das Bild füllt den Bildschirm ohne Ränder und ohne Verzerrung, und ein Touch-Pixel entspricht genau 2×2 Spielpixeln. |
| Touch-Modus | **Direkt:** Die Tippposition ist die Mausposition, kein Touchpad-Modus. Beim Aufsetzen springt der Zeiger zuerst auf die Tippposition, im selben Frame folgt `mouseDown`. Beim Loslassen folgt `mouseUp` an der letzten Position. So liefern `the mouseH`/`the mouseV`, `rollOver` und `the clickOn` auch bei kurz sichtbaren Mäusen die richtige Stelle. |
| Treffhilfe | Eine Maus ist bei halber Auflösung klein und nur kurz zu sehen. Deshalb bekommt die Director-Engine eine **abschaltbare Treffhilfe:** Trifft ein Tipp keine Maus, sucht sie im Umkreis nach der nächsten sichtbaren Maus und lenkt den Klick auf sie um. Startwert für den Umkreis sind etwa 16 Spielpixel (= 8 Touch-Pixel); der endgültige Wert wird per Test abgestimmt. Die Hilfe gilt nur für Sprites, die laut T2.6 Mäuse sind. Alle anderen Klickflächen bleiben exakt, damit nichts versehentlich ausgelöst wird. |
| Hover/Rollover | Touch hat kein Hover. `rollOver` wird mindestens im Menü (`GGMDMENU`) und auf der Dachboden-Karte (`ATTIC`, `rollovermap`) benutzt. Ersatz: Solange der Stift aufliegt und gezogen wird, folgt der Zeiger; Rollover-Effekte erscheinen also beim Ziehen. Die genaue Lösung hängt von der Skriptlogik ab (T2.6, T5.2). |
| Cursor | Auf dem Touchscreen ausgeblendet, denn der Stift ist der Zeiger. In der Lupe oben ist er sichtbar. |
| Oberer Bildschirm | **Lupe:** ein 1:1-Ausschnitt (400×240) der Originalgrafik um den letzten Tippunkt, für Details und Texte. Optional später: eine Anzeige der gefangenen Mäuse aus `miceCaught` (Phase 7). |
| Tasten | Zusätzlich, für das Spielen ohne Stift: Circle Pad/Steuerkreuz = Zeiger, A = Klick, START = ScummVM-Menü, SELECT = Lupe an/aus. Falls das Spiel Tasten abfragt (`keyCode`, `commandDown`, `optionDown`), werden diese auf freie Tasten gelegt. |

Was das 3DS-Backend von ScummVM davon schon kann (Bildschirmwahl, Touch-Modus, Lupe), prüft T5.1. Fehlendes wird im Backend (`backends/platform/3ds/`) oder in der Director-Engine ergänzt. Beides wird als Patch nach `patches/` exportiert.

---

## 4. Repo-Struktur (Zielzustand)

```
MJIGH3DS/
├── PLAN.md, TODO.md          dieser Plan und die Aufgabenliste
├── README.md                 Anleitung für Endnutzer (Phase 6)
├── .gitignore
├── tools/                    eigene Python-Skripte (Extraktion, Inventar, Analyse)
├── scripts/                  Build-Skripte (Desktop, 3DS, Packaging)
├── patches/                  ScummVM-Änderungen als `git format-patch`-Serie
├── config/                   vorkonfigurierte scummvm.ini, Autorun-Datei, Icon/Banner
├── docs/                     Befunde, Kompatibilitäts-Log, Build-Doku
│
├── original/   (ignoriert)   ISO + ZIP
├── game/       (ignoriert)   aus dem ISO extrahierte Spieldaten
├── analysis/   (ignoriert)   dekompilierter Lingo-Code, Dumps
├── scummvm/    (ignoriert)   Klon von github.com/scummvm/scummvm, Branch `mausjagd`
└── dist/       (ignoriert)   Build-Ausgaben (.3dsx, .cia)
```

---

## 5. Phasen und Gates

| Phase | Inhalt | Ergebnis |
|---|---|---|
| 0 | Repo und Umgebung | Struktur steht, Werkzeuge geprüft |
| 1 | ISO extrahieren und inventarisieren | `game/` mit allen Spieldaten, `docs/inventory.md` |
| 2 | Analyse und Lingo-Dekompilierung | Spielablauf, Abhängigkeiten und benutzte Lingo-Features dokumentiert |
| 3 | ScummVM auf dem PC | Spiel läuft auf dem Desktop komplett durch |
| **G1** | **Gate** | Ist das Spiel auf dem PC von Anfang bis Ende spielbar? Nein, mit grundlegenden Blockern → Nutzer fragen. |
| 4 | 3DS-Build | ScummVM mit unserem Branch läuft im Emulator und auf echter Hardware |
| 5 | 3DS-Anpassung | Spiel auf dem Touchscreen, Mäuse per Antippen fangbar (mit Treffhilfe), Lupe oben, flüssige Videos, kein Speichermangel |
| **G2** | **Gate** | Lassen sich die Mäuse per Touch zuverlässig fangen? Ist es auf dem New 3DS gut spielbar? Status des Old 3DS ist dokumentiert. |
| 6 | Packaging | CIA/3DSX, die direkt ins Spiel startet, plus Endnutzer-README |
| 7 | optional | Upstream-PR an ScummVM, englische Version |

---

## 6. Technische Eckpunkte

**Build-Umgebung:** **WSL1** mit Ubuntu. WSL2 geht nicht, weil VT-x im BIOS aus ist; siehe `docs/environment.md`.

**Desktop-Build (Phase 3):** in WSL1 per MinGW-w64-Cross-Compile zu einer Windows-EXE (`./configure --host=x86_64-w64-mingw32 --disable-all-engines --enable-engine=director`). Für den ersten Smoke-Test reicht das offizielle ScummVM-Release 2026.4.0 für Windows.

**ScummVM-Erkennung:** Den Eintrag in `engines/director/detection_tables.h` nach dem Muster bestehender D4-Windows-Einträge anlegen (Version 404, Sprache `DE_DEU`, Projektor `MAUSJAGD.EXE`). Vorher prüfen, ob die englische Version schon einen Eintrag hat und welche Game-ID sie nutzt.

**Debugging:** Die Debug-Kanäle der Director-Engine (`scummvm --list-debugflags`, z. B. `lingo`, `loading`, `score`, `sound`, `video`) und das Dumpen der Skripte nutzen. Dann mit der Ausgabe von ProjectorRays vergleichen.

**3DS-Toolchain (Phase 4):** devkitPro mit devkitARM, libctru, citro3d und den 3DS-Portlibs, die `backends/platform/3ds/README.md` von ScummVM verlangt. Dazu `bannertool` und `makerom` für die CIA. Die Installation erfolgt in WSL1 über das devkitPro-pacman; das ScummVM-Projekt `dockerized-bb` enthält ein Rezept für die 3DS-Toolchain.

**3DS-Build:** `./configure --host=3ds --disable-all-engines --enable-engine=director`, dann `make scummvm.3dsx` bzw. `make scummvm.cia`. Die Flags sind gegen das aktuelle README zu prüfen.

**Testen:** zuerst im Emulator **Azahar** (Nachfolger von Citra/Lime3DS), dann auf echter Hardware per `3dslink` (Homebrew-Launcher-Netloader) oder als CIA.

**Hardware-Grenzen:**

- Unterer Bildschirm 320×240 (Touch), oberer 400×240. Das Spiel läuft unten in genau halber Auflösung, oben ist die Lupe (siehe §3). Lesbarkeit und Treffsicherheit beim Antippen sind das Hauptthema.
- Old 3DS: 268 MHz und ca. 64 MB App-Speicher. New 3DS: 804 MHz und mehr Speicher. **Zielplattform ist der New 3DS.** Der Old 3DS ist Best Effort mit dokumentiertem Status.
- Mögliche Performance-Engpässe: SMC-Videodekodierung in voller Auflösung, Konvertierung der 8-Bit-Palette, Audio-Resampling. Als Hebel gibt es die 8-Bit-Musik in `MUSIC8/` und `SOLOS8/`, die das Spiel über `gCPU` offenbar selbst auswählt; das ist zu prüfen.

**Autostart (Phase 6):** eine vorkonfigurierte `scummvm.ini` mit dem Spieleintrag und dem Spielpfad auf der SD-Karte, z. B. `sdmc:/3ds/mausjagd/game/`. Dazu ein Direktstart, etwa über eine `scummvm-autorun`-Datei; ob ScummVM das unterstützt, ist zu prüfen. Die App bekommt eine eigene Title-ID sowie ein selbst gestaltetes Icon und Banner.

---

## 7. Regeln (Recht und Repo)

- Spieldaten, das ISO, extrahierte Dateien und dekompilierter Lingo-Code kommen **nie** ins Git oder in ein Release. Sie bleiben in den ignorierten Ordnern. Endnutzer extrahieren ihre eigene CD mit `tools/`.
- Ins Repo kommen nur eigene Skripte, Doku und ScummVM-Patches. ScummVM steht unter GPLv3+; damit stehen auch unsere Patches und Binaries unter der GPL, und für verteilte Binaries muss der Quellcode verfügbar sein.
- Icon und Banner der 3DS-App selbst gestalten und keine Grafiken aus dem Spiel verwenden, falls die App je weitergegeben wird.
- Nach außen wirkende Schritte nur nach Freigabe durch den Nutzer: Push nach GitHub, PR an ScummVM, Veröffentlichung von Builds.

---

## 8. Risiken

| Risiko | Gegenmaßnahme |
|---|---|
| Lücken oder Fehler der Director-Engine bei genau diesem Spiel | Szene für Szene testen (Phase 3), dekompilierten Lingo-Code als Referenz nutzen, Fixes in der Engine, spielspezifische Quirks in `engines/director/game-quirks.cpp` |
| Kein Referenzverhalten verfügbar: der 16-Bit-Projektor startet nicht unter Windows 10 x64 | Optional eine Win9x-VM (86Box/VirtualBox) oder ein Longplay-Video als Referenz |
| Mäuse bei halber Auflösung zu klein oder zu kurz sichtbar zum Antippen | Treffhilfe mit Fangradius (§3), Trefferquote auf echter Hardware messen und den Radius abstimmen (T5.4) |
| Das Spiel braucht Hover/Rollover, den Touch nicht liefert | In T2.6 klären; Ersatz durch Ziehen mit dem Stift (§3, T5.2) |
| Schlechte Lesbarkeit bei 320×240 | Lupe auf dem oberen Bildschirm mit 1:1-Ausschnitt; Skalierungsfilter vergleichen (T5.1) |
| Videos auf dem 3DS zu langsam | Auf echter Hardware messen; Optimierung oder notfalls vorab umkodierte Videos (nur als lokaler Konvertierungsschritt für den Nutzer, nicht im Repo) |
| Speichermangel auf dem Old 3DS | Speicher messen; New 3DS als Ziel, Old 3DS als Best Effort |
| `LINGO.INI`-Pfade (`D:\`) oder CD-Prüfungen | Prüfen, wie ScummVM `LINGO.INI` und Laufwerkspfade behandelt; bei Bedarf ein Quirk. Die Anforderungen stehen in `docs/dependencies.md` |
| Warteschleifen in Lingo (`wait` über `the timer`, leere Zählschleifen, `the mouseDown`/`the soundBusy`/`the movieRate` innerhalb von Schleifen) | Gezielt in T3.4 testen (Fallen, Hilfe des Katers, Raumstart). Bei Hängern die Event-Verarbeitung in der Engine nachbessern |
