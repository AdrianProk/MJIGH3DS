# Externe Abhängigkeiten

Stand: T2.4. Quelle: dekompilierter Lingo-Code (`analysis/lingo/`), `docs/dxr-inventory.md`.

## XObjects und Xlibs

| XObject | Wo | Methoden | Unter Windows? | ScummVM |
|---|---|---|---|---|
| `FileIO` (`FILEIO.DLL`, geladen per `openXlib` in `LINGO.INI`) | GGMDSTRT (`checkifcd`), GGMDMENU (`mainstart`, `loadgame`), EXIT (`saveinfo`) | `mnew` mit `"read"` bzw. `"append"`, `mReadFile`, `mReadString`, `mWriteString`, `mdispose`; Prüfung über `objectp()` | ja | eingebaut; in T3.3 prüfen, ob `append` unterstützt wird |
| `Backdrop` (`backdrop xobj`) | GGMDSTRT (`startit`) | `mnew`, `mregister`, `mHideInBack`, `mSetColor`, `mSetPattern`, `mShow` | **nein**: nur im Mac-Zweig (`the machineType <> 256`) | nicht nötig |

## Dateien, die das Spiel zur Laufzeit öffnet

| Zugriff | Pfad (Windows-Zweig) | Datei im Spielordner |
|---|---|---|
| CD-Prüfung (FileIO read) | `thecdpath & "lingo.ini"` = `D:\lingo.ini` | `LINGO.INI` |
| Spielstände (FileIO read/append) | `thehdpath & "saveinfo.txt"` = `D:\saveinfo.txt` | neu, ScummVM-Savefile |
| Startmusik | `puppetSound "theme.aif"` | interner Sound-Cast |
| Raum-Sounds | `gsounddrive & "sounds\" & <Präfix aus Feld movieinfo> & <Nr>` | `SOUNDS/KN1.AIF` usw. |
| Effekte | `gsounddrive & "sounds\car.aif"` (auch `plane`, `rocket`, `bike`, `silent`) | `SOUNDS/*.AIF` |
| Abschluss-Sounds | `thecdpath & "endsoung\random<1–7>.aif"`, `endsoung\atticend.aif` | `ENDSOUNG/` |
| Orchester | `thecdpath & gmusicpath & theBuild & "\" & instrument & ".aif"` | `MUSIC/BUILD1–3/` (bzw. `MUSIC8/`) |
| Soli | `thecdpath & gsolospath & instrument & ".aif"` | `SOLOS/` (bzw. `SOLOS8/`) |
| Videos | verknüpfte QuickTime-Casts mit Mac-Pfaden (`PixelMagic1:GGMD:kitchen.mov`, `GGMDCD:gervideo:gerintro.MoV`, `PixelMagic1:ENGhelp:cathel10.mov` …), aufgelöst über `the searchPath` = Hauptordner, `gervideo`, `gerhelp` | `*.MOV`, `GERVIDEO/`, `GERHELP/` |
| Filmwechsel | `go to frame 1 of movie thecdpath & <name>`, `play movie the pathName & "theend"`, `play frame "Options" of movie thehdpath & "GGMDmenu"` | `*.DXR` (ohne Endung referenziert, teils mit `.dir`: `"credits.dir"`) |

**Nicht referenziert:** `STARTSND/` (nur von `GALLERY.EXE` benutzt), `MUSIC/BUILD*.TXT` (die Instrumentenlisten sind im Code fest verdrahtet, siehe `buildorchestra`), alle Beilagen.

## Pfadauflösung: Anforderungen an ScummVM (für T3.6)

1. **Laufwerksbuchstaben:** `D:\` und `d:\` müssen auf das Spielverzeichnis zeigen.
2. **Mischpfade:** Windows-Pfade mit `\` in Ordnernamen (`sounds\`, `endsoung\`, `music\BUILD1\`) auflösen, ohne Rücksicht auf Groß- und Kleinschreibung (`GGMDmenu` → `GGMDMENU.DXR`).
3. **Filmnamen ohne Endung:** `ggmdmenu` → `GGMDMENU.DXR`; `credits.dir` → `CREDITS.DXR`.
4. **Verknüpfte Videos:** Mac-Pfade der Entwickler über den Dateinamen und `the searchPath` finden (`GGMDCD:gervideo:gerintro.MoV` → `GERVIDEO/GERINTRO.MOV`, `cathel10.mov` liegt auf der deutschen CD in `GERHELP/`, nicht in `ENGhelp`).
5. **FileIO:** `D:\lingo.ini` muss lesbar sein (CD-Prüfung), `D:\saveinfo.txt` auf einen Savefile umgeleitet werden.

## Systemabfragen

| Abfrage | Wo | Erwarteter Wert |
|---|---|---|
| `the machineType` (40×) | überall: Weiche Windows/Mac für Pfade | 256 (IBM PC); ScummVM muss für die Windows-Version 256 liefern |
| `the colorDepth` | GGMDSTRT | 8, sonst Warnhinweis |
| `the timer`, `wait` | SHARED (`wait n` als Warteschleife über `the timer`), GGMDMENU (`wait n` als **leere Zählschleife** `1 to n*60`, CPU-abhängig) | Die Warteschleifen müssen in ScummVM weiterlaufen (Timer, Events) und dürfen nicht hängen |
| `the mouseDown` in Schleifen | SHARED (`checktrap`, `help`) | Eingaben müssen auch innerhalb laufender Lingo-Schleifen ankommen |
| `the soundBusy of 1` in Schleifen | SHARED (`startsequence`: `repeat while the soundBusy of 1`) | Der Sound-Status muss sich innerhalb der Schleife aktualisieren |
| `the movieRate of sprite 48` in Schleifen | SHARED (`help`) | Der Abspielstatus des QuickTime-Sprites muss sich aktualisieren |
| Tasten | SHARED `checkexit`: Esc (keyCode 53) bzw. Cmd/Option + Q/F4 → Beenden-Dialog; GGMDSTRT: `q` → Ende; EXIT: Return (keyCode 36) bestätigt den Namen | auf 3DS-Tasten legen |
