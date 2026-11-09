# Kompatibilitäts-Log

Testmatrix und Fehlerprotokoll. Neueste Einträge oben im Protokoll.

## Protokoll

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
- **Folge:** Der eigentliche Spieltest (GUI) läuft durch den Nutzer, siehe "Anleitung Spieltest" unten. Das Log liest der Agent danach aus `%APPDATA%\ScummVM\Logs\scummvm.log`.
- **Status:** Erkennung ok (Fallback), Spieltest offen.

## Anleitung Spieltest (für den Nutzer)

1. `vendor\scummvm-release\scummvm-2026.4.0-win32-x86_64\scummvm.exe` per Doppelklick starten.
2. **Spiel hinzufügen…** und den Ordner `C:\Users\Alphe\Documents\GitHub\MJIGH3DS\game` wählen. ScummVM meldet eine unbekannte Variante (Fallback-Erkennung); trotzdem hinzufügen.
3. Spiel starten und notieren:
   - Erscheint das Menü? Läuft das Intro-Video mit Ton?
   - Lässt sich ein Level wählen und "Start" drücken? Erscheint die Hotelübersicht?
   - Reagiert das Mausometer beim Bewegen und gibt es Alarm?
   - Kommt man in einen Raum? Lässt sich die Maus aufscheuchen und **fangen**?
   - Läuft das Missgeschick-Video danach?
   - Fehlermeldungen oder Abstürze? An welcher Stelle?
4. ScummVM beenden. Das Log liegt dann unter `%APPDATA%\ScummVM\Logs\scummvm.log`, der Agent wertet es aus.

## Testmatrix

Wird in T3.4 angelegt.
