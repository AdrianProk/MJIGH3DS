# Spielmechanik (Zusammenfassung der Anleitung)

Eigene Zusammenfassung von `README.WRI` (Spielanleitung) und `INSTALL.WRI`. Sie dient als Grundlage für T2.6 (Fangmechanik), die Testmatrix (T3.4) und das Touch-Design (PLAN.md §3).

## Ablauf

1. **Menü:** Level 1–3 wählen. Das Level bestimmt die Geschwindigkeit der Mäuse; je mehr gefangen sind, desto schneller laufen sie. Außerdem Musik an oder aus, dann "Start". Gespeicherte Spiele lassen sich hier laden.
2. **Hotelübersicht:** Das **Mausometer** wird über das Bild bewegt, bis es Alarm gibt. Der Raum darunter enthält eine Maus und wird angeklickt.
   → **Touch:** Das ist reines Hovern; es muss durch Ziehen mit dem Stift funktionieren.
3. **Im Raum:** Gegenstände anklicken, bis die grüne Maus aufgescheucht wird. Sie läuft dann zu einem anderen Versteck. **Die Maus muss angeklickt werden, während sie läuft.**
   → **Touch:** Das Ziel bewegt sich. Treffhilfe und geringe Eingabelatenz sind entscheidend.
4. **Gefangen:** Der Hotelboy kommt mit einem Netz, dabei passiert oft ein Missgeschick. Das ist eine Animation bzw. ein Video (`<RAUM>.MOV`).
5. **Musikzimmer** (nur mit Musik): Für die Maus ein Instrument auswählen und so lange suchen, bis das richtige gefunden ist (`INSTRUM.DXR`, Soli aus `SOLOS/`).
6. **Tanzsaal:** Die Maus probt mit dem Orchester (`ORCH.DXR`/`BALLROOM.DXR`, Musik aus `MUSIC/BUILD1-3`).
7. Ende, wenn alle Mäuse gefangen sind (`ENDSEQ.MOV`, `CREDITS.DXR`, `THEEND.DXR`).

## Bedienelemente auf dem Bildschirm

| Element | Position | Funktion |
|---|---|---|
| Korb des Hotelkaters | rechts unten | Hilfe: Der Kater gibt einen (nicht immer nützlichen) Rat; Videos in `GERHELP/` |
| Blaue Fallen-Tasche | neben dem Katzenkorb | Falle wählen; sie wird auf den Boden gestellt. Läuft die Maus vorbei, ist sie kurz langsamer und muss dann angeklickt werden. Level 1: 10 Fallen, Level 2: 5, Level 3: keine. |
| Hotel-Symbol | links unten | Beenden: Abfrage, dann Frage nach dem Speichern, dann **Namen per Tastatur eingeben**. Datum und Uhrzeit werden automatisch ergänzt. |

→ **Touch:** Die Namenseingabe braucht auf dem 3DS eine Bildschirmtastatur (T5.2).

## Weitere Inhalte der CD

- **Gallery** (`GALLERY.EXE`): eine eigene kleine App, die die Bilder aus den Hotelzimmern mit passender Musik zeigt (`STARTSND/`). Sie gehört nicht zum Spiel und ist ein Kandidat für Phase 7.
- **Bilder** (`BILDER/`): sechs Ausmalbilder zum Ausdrucken.

## Musikoptionen

16-Bit-Musik ist der Standard. Die 8-Bit-Variante wird über `LINGO.INI` gewählt: `music8\` und `solos8\` statt `music\` und `solos\`.
