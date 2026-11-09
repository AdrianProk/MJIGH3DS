# Startablauf

Stand: T1.5. Quellen: Strings und Lingo-Namenstabellen aus `MAUSJAGD.EXE` (eingebetteter Film) und `GGMDMENU.DXR`, dazu `INSTALL.WRI` und `SETUP.LST`. Der Ablauf ist aus Namen und Literalen erschlossen; den genauen Code bestätigt T2.2.

## 1. Projektor `MAUSJAGD.EXE`

- Macromedia Director for Windows 4.0.4, 16-Bit-Windows-Projektor ("Director Player 4.0").
- Ab Offset 729500 liegt ein `XFIR`-Container (`APPL`, little-endian) mit den Chunks `List`, `Dict` und `File`, also der Dateiliste des Projektors.
- Ab Offset 729822 folgt der eingebettete Film **`C:\GGMD\GGMDSTRT.DIR`** (`XFIR`/`MV93`, fileVersion `0x045d`, 12 Cast-Member, 5 Lingo-Skripte). Die Chunk-Offsets in seiner `mmap` beziehen sich auf den **Dateianfang der EXE**, nicht auf den Filmanfang.
- `GALLERY.EXE` hat denselben Projektor-Code (identische Offsets); eingebettet ist dort `C:\PCFILES\GALLERY.DIR`.

## 2. `LINGO.INI`

Der Windows-Projektor von Director 4 führt `LINGO.INI` aus dem Programmverzeichnis beim Start aus. Inhalt:

```lingo
on startup
   global theHDpath, theCDpath, gCPU
   global gMusicPath, gSolosPath, gSoundDrive
   put "D:\" into theHDpath
   put "D:\" into theCDpath
   put "486" into gCPU
   put "music\" into gMusicPath
   put "solos\" into gSolosPath
   put "d:\" into gSoundDrive
   set centreStage to true
   openXlib "FileIO"
end startup
```

- Bei einer Installation kopierte das Setup laut `SETUP.LST` `MAUSJAGD.EXE`, `LINGO.INI`, `FILEIO.DLL`, `README.WRI` und `SOUNDS\*.AIF` nach `C:\Mausjagd`. Alles andere wurde von der CD gelesen. `theHDpath` und `theCDpath` zeigen auf die beiden Orte; auf der CD selbst stehen beide auf `D:\`.
- **Musikvariante:** Laut `INSTALL.WRI` wird die 8-Bit-Musik gewählt, indem man `gMusicPath` auf `music8\` und `gSolosPath` auf `solos8\` ändert. `gCPU` wählt die Variante also nicht.

## 3. Startfilm `GGMDSTRT` (eingebettet)

Lingo-Namen: `startit`, `machineType`, `thecdpath`, `thehdpath`, `checkifcd`, `openXLib`, `closeXLib`, `FileIO`, `mnew`, `backdrop`, `mHideInBack`, `mSetPicture`, `mShow`, `mSetColor`, `mSetPattern`, `mregister`, `playFile`, `puppetSound`, `whenexit`, `wayout`, `quit` …

Daraus ergibt sich, mit Lingo-Literalen belegt:

1. **Prüfung der Farbtiefe:** Bei weniger als 256 Farben erscheint der Hinweis "…'Mäusejagd im Grandhotel' ist am schönsten mit 256 Farben … ändere die Monitoreinstellung".
2. **Plattformweiche** über `the machineType` mit Mac-Pfaden (`ggmdcd:`, `music:`, `solos:`) und Windows-Pfaden.
3. **CD-Prüfung** (`checkifcd`): FileIO öffnet eine Datei zum Lesen (`read`). Literale: `lingo.ini` und `sounds:sndtext.txt`, dazu die Fehlermeldung "Finde das CD-ROM Laufwerk nicht." `SOUNDS/SNDTEXT.TXT` existiert als leere Datei.
4. **XObject "Backdrop"** (`backdrop xobj` plus Registrierungscode) mit den Methoden `mSetPicture`, `mSetColor`, `mSetPattern`, `mShow`, `mHide` und `mHideInBack`. Es füllt vermutlich den Bildschirmhintergrund um die 640×480-Bühne. Noch offen ist, ob es nur auf dem Mac verwendet wird (Windows hat `centreStage`); das klärt T2.4. In ScummVM ist es möglicherweise nicht implementiert.
5. Abspielen des Sounds `theme.aif`; das ist ein interner Sound-Cast, keine Datei auf der CD.
6. Wechsel zum Film **`ggmdmenu`** (`GGMDMENU.DXR`).

## 4. Menü `GGMDMENU`

- Hier wählt man Level 1–3 (`fast`/`medium`/`slow`, `mytempo`) und Musik an/aus (`musicon`/`musicoff`) und startet das Spiel (`startmenu`, `mainstart`).
- Spielstände laden: `loadgame` und `savelist` über FileIO (`mReadString`, `mReadFile`, `mdispose`).
- Intro-Video `GGMDCD:gervideo:gerintro.MoV` (Mac-Pfad im Cast) und Hilfevideo `cathelp6.mov`.
- `rollOver` und `mouseLine` werden in der Speicherstandsliste und im Menü benutzt.

## Folgen für ScummVM und den 3DS

- **CD-Pfade:** ScummVM muss `D:\…` und `GGMDCD:…` auf das Spielverzeichnis abbilden (T3.6).
- **CD-Prüfung:** `checkifcd` muss erfolgreich sein. Es öffnet Dateien unter `theCDpath` per FileIO.
- **Backdrop:** Das XObject braucht mindestens einen Stub, falls es unter Windows aufgerufen wird.
- **8-Bit-Musik:** Für den 3DS kann die 8-Bit-Musik über eine angepasste `LINGO.INI` gewählt werden, ohne Änderung an der Engine.
