# Entwicklungsumgebung

Stand: 2026-11-09 (T0.2)

| Werkzeug | Status |
|---|---|
| Betriebssystem | Windows 10 Pro 10.0.19045 |
| CPU / RAM | Intel Core i7-1165G7, 32 GB |
| Freier Platz C: | ca. 410 GB |
| Python | 3.13.17, Aufruf über `py` (`python` ist nur ein Store-Platzhalter) |
| Git | 2.36.1 (Git for Windows, mit Git Bash) |
| WSL2 | **nicht eingerichtet** (`wsl -l -v` zeigt nur die Hilfe) |
| Docker | **nicht installiert** |
| make / gcc | **nicht vorhanden** |
| MSYS2 | **nicht vorhanden** |
| devkitPro | **nicht vorhanden** |
| 7-Zip | nicht vorhanden (wird nicht gebraucht: `tools/iso_extract.py`) |

## Folgen für den Plan

- Phase 1 und 2 laufen vollständig mit Python, ohne weitere Installation.
- Für Phase 3 (ScummVM-Desktop-Build) und Phase 4 (3DS-Toolchain) braucht es eine Build-Umgebung.
- Für den ersten Smoke-Test (T3.1) genügt ein offizielles ScummVM-Release für Windows, ohne Build-Umgebung.

## Build-Umgebung: WSL1 (Entscheidung 2026-11-09)

- **Befund:** WSL2 ist nicht möglich. `systeminfo` meldet "Virtualisierung in Firmware aktiviert: **Nein**"; Intel VT-x ist im BIOS/UEFI aus.
- **Entscheidung des Nutzers:** **WSL1** ohne BIOS-Änderung. WSL1 braucht keine Hardware-Virtualisierung.
- **Einschränkungen von WSL1:**
  - Dateizugriffe sind langsamer. Deshalb bauen wir im Linux-Dateisystem (`~/…`), nicht unter `/mnt/c/…`.
  - Es gibt keine Linux-GUI. Der Desktop-Build von ScummVM wird deshalb per MinGW-w64 als **Windows-EXE** cross-kompiliert (`--host=x86_64-w64-mingw32`) und unter Windows gestartet.

### Installation (führt der Nutzer aus, braucht Admin-Rechte)

1. PowerShell **als Administrator** öffnen und ausführen:
   ```powershell
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
   ```
2. **Windows neu starten.**
3. Normale PowerShell:
   ```powershell
   wsl --set-default-version 1
   wsl --install -d Ubuntu --web-download
   ```
   Beim ersten Start fragt Ubuntu nach einem Linux-Benutzernamen und Passwort. Die sind frei wählbar; das Passwort wird später für `sudo` gebraucht.
4. Falls Ubuntu mit Fehler `0x80370102` (Virtualisierung fehlt) startet:
   ```powershell
   wsl --set-version Ubuntu 1
   ```
5. Prüfen: `wsl -l -v` muss `Ubuntu … VERSION 1` zeigen.

## Hinweise

- In Git Bash vor Aufrufen mit `/`-Pfaden `export MSYS_NO_PATHCONV=1` setzen. Sonst schreibt MSYS Pfade wie `/ATTIC.DXR` zu `C:/Program Files/Git/ATTIC.DXR` um.
