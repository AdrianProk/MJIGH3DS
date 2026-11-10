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

### Fortschritt

- 2026-11-09 23:00: Schritt 1 erledigt. `dism.log` meldet `Microsoft-Windows-Subsystem-Linux` als `Installed`, "Reboot required=yes".
- 2026-11-10 05:38: Neustart erledigt, WSL-Komponente aktiv.
- Die Ubuntu-App `CanonicalGroupLimited.Ubuntu` 2604.1.75.0 (Ubuntu 26.04) ist installiert, aber noch nicht registriert (`wsl -l -v`: keine Distribution).
- Die Standardversion stand noch auf 2. Der Agent hat `wsl --set-default-version 1` ausgeführt (Benutzereinstellung, ohne Admin).
- 2026-11-10: Ubuntu gestartet, Benutzer `adrian` angelegt. `wsl -l -v` zeigt `Ubuntu Stopped 1`, also WSL1.
- Bestand in Ubuntu:
  - Ubuntu 26.04.1 LTS ("resolute"), Kernel `4.4.0-19041-Microsoft`, 8 Kerne
  - vorhanden: `git`, `python3`, `curl`, `wget`; es fehlen `gcc`, `g++`, `make`, `pkg-config` und MinGW
  - `sudo` braucht ein Passwort, also stößt der Nutzer Paketinstallationen an
  - Die apt-Listen enthalten anfangs nur main und restricted. Universe (`mingw-w64`, `ccache`, `libsdl2-dev`) erscheint erst nach `sudo apt update`.

### Build-Pakete (führt der Nutzer aus, braucht das Ubuntu-Passwort)

```bash
sudo apt update && sudo apt install -y build-essential pkg-config ccache libsdl2-dev zlib1g-dev libpng-dev libfreetype-dev mingw-w64
```

- `build-essential`, `pkg-config`, `ccache` und `libsdl2-dev` sind für den nativen Linux-Build. Den startet der Agent ohne Fenster (SDL-Treiber `dummy`) für automatische Tests und Debug-Ausgaben.
- `mingw-w64` ist für den Windows-Build, den der Nutzer per GUI testet. SDL2 für MinGW gibt es nicht als apt-Paket; der Agent lädt es als Entwicklerpaket von den SDL-Releases nach `~/mingw-prefix`.
- **Stand 2026-11-10:**
  - `apt update` ist durchgelaufen. Jetzt bekannt: `mingw-w64` 13.0.0, `libsdl2-dev` 2.32.10, `ccache` 4.12.3.
  - Das `apt install` wurde **nicht** ausgeführt; in `/var/log/apt/history.log` stehen nur die Einträge vom Bau des Images. Es muss einzeln nachgeholt werden:
    ```bash
    sudo apt install -y build-essential pkg-config ccache libsdl2-dev zlib1g-dev libpng-dev libfreetype-dev mingw-w64
    ```

- **2026-11-10, Spiegel:** `apt install` blieb bei `Ign:8` hängen.
  - Ursache: Mehrere IPs von `archive.ubuntu.com` und `security.ubuntu.com` (z. B. `185.125.190.82`, `91.189.92.22`) antworten auf HTTP nicht, auch nicht unter Windows.
  - `de.archive.ubuntu.com` antwortet in 0,15 s, ebenso `ftp.fau.de` und `mirror.netcologne.de`.
  - Abhilfe: Die Quellen auf den deutschen Spiegel umstellen; er führt auch `resolute-security`:
    ```bash
    sudo sed -i 's|http://archive.ubuntu.com|http://de.archive.ubuntu.com|; s|http://security.ubuntu.com|http://de.archive.ubuntu.com|' /etc/apt/sources.list.d/ubuntu.sources
    ```

- **2026-11-10, Ergebnis:** Alle Build-Pakete sind installiert: gcc/g++ 15.2.0, GNU Make 4.4.1, ccache 4.12.3, SDL2 2.32.10, zlib 1.3.1, libpng 1.6.57, freetype2, MinGW-GCC 13.
- **systemd unter WSL1:** Die mitgezogenen Updates `systemd` 259.9 (`iF`), `udev`, `libpam-systemd`, `systemd-resolved` und `systemd-sysv` (`iU`) lassen sich nicht konfigurieren.
  - Ursache: `systemd.postinst` ruft ohne Bedingung `systemd-machine-id-setup` auf. Das scheitert unter WSL1 mit `Cannot open '/etc/machine-id': Bad file descriptor`; die Datei ist leer.
  - Für den Build ist das egal, systemd läuft unter WSL1 ohnehin nicht. Sonst würde aber jedes weitere `apt install` mit Fehlercode enden.
  - Abhilfe (Nutzer, mit `sudo`):
    ```bash
    sudo sh -c 'tr -d "-" < /proc/sys/kernel/random/uuid > /etc/machine-id'
    sudo sed -i 's#^\(systemd-machine-id-setup .*\)$#\1 || true#' /var/lib/dpkg/info/systemd.postinst
    sudo dpkg --configure -a
    ```
    Zeile 1 legt eine gültige Machine-ID an. Zeile 2 macht den Aufruf im Installationsskript fehlertolerant; das gilt nur bis zum nächsten systemd-Update, das das Skript neu mitbringt. Zeile 3 schließt die Konfiguration ab.
  - **Zweite Hürde:** Danach scheitert `systemd-sysusers` mit `Failed to read 'basic.conf'`; derselbe Aufruf steht in den Skripten von `udev` und `systemd-resolved`. Er legt nur Standardbenutzer an, die es im Image schon gibt, und darf deshalb übersprungen werden:
    ```bash
    sudo sed -i 's#^\(\s*systemd-sysusers .*\)$#\1 || true#' /var/lib/dpkg/info/systemd.postinst /var/lib/dpkg/info/udev.postinst /var/lib/dpkg/info/systemd-resolved.postinst
    sudo dpkg --configure -a
    ```
    Die Umstellung von `/etc/resolv.conf` in `systemd-resolved.postinst` greift nur bei einem Update von einer Version vor 251.4 und betrifft uns nicht (installiert war 259.5).
  - **Bedienhinweis:** Mehrere `sudo`-Zeilen nicht auf einmal einfügen, solange die Passwortabfrage aussteht; die weiteren Zeilen werden sonst als Passwort-Versuche gelesen. Erst `sudo -v` eingeben, dann den Block einfügen.

### SDL2 für MinGW

- `SDL2-devel-2.32.10-mingw.tar.gz` von `github.com/libsdl-org/SDL/releases`, SHA-256 `83a5d74012311edc3c0d40ea6faecbe57ad692aa033fa5dc273cc937e3938ff2`; das ist der Digest, den die GitHub-API ausweist, und er stimmt.
- Download nach `~/downloads/sdl2-mingw-2.32.10/`. Der Teil `x86_64-w64-mingw32` ist nach `~/mingw-prefix` kopiert, und das Präfix in `sdl2.pc` und `sdl2-config` ist umgeschrieben.
- `~/mingw-prefix/bin/sdl2-config --version` meldet `2.32.10`.

### WSL1-Eigenheiten

- **GNU tar 1.35** (Ubuntu 26.04) scheitert unter WSL1 beim SDL-Archiv (PAX, verschachtelte Pfade) mit `Cannot open: Function not implemented`, auch mit `--no-same-permissions`, `--touch` oder `--no-xattrs`. Ein flaches Mini-Archiv geht. Ersatz ist Pythons tarfile, was für fremde Archive ohnehin sicherer ist:
  ```bash
  python3 -I -c "import tarfile; tarfile.open('x.tar.gz').extractall('ziel', filter='data')"
  ```

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
- `wsl -- bash -lc '…'` aus PowerShell 5.1: Enthält der Befehl doppelte Anführungszeichen, zerlegt PowerShell ihn beim Übergeben, und die Ausgabe bricht ab. Befehle deshalb als Skriptdatei ablegen und `wsl -d Ubuntu -- bash /mnt/c/…/skript.sh` aufrufen. Die Ausgabe von `wsl.exe` selbst ist UTF-16 und braucht `-replace "`0", ''`.
