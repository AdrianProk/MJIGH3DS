# Fangmechanik der Mäuse

Stand: T2.6. Quellen: dekompilierter Lingo-Code (vor allem `SHARED.DXR`, MovieScript 761), Cast-Listen (`analysis/cast/`), `docs/room-stats.md` (generiert von `tools/room_stats.py`). Die Annahme des Nutzers ist **bestätigt**: Mäuse fängt man durch Anklicken, und zwar während sie laufen.

## Ablauf in einem Fangraum

1. **Raumstart** (`startsequence`): Das Feld `movieinfo` liefert Sound-Präfix, Anzahl der Leerlauf-Animationen, Puppet-Kanal, Netzposition (`mloc`) und Fallenposition (`trappos`). Das Feld `hidelist` enthält eine Zeile pro Versteck, z. B. `1:10,4,6` für Versteck 1 mit den möglichen Laufzielen 10, 4 und 6. Ein Startversteck wird zufällig gewählt (`hidepos`).
2. **Suchen:** Die Verstecke sind die Sprites **30 bis 29+n** mit dem Skript `on mouseUp clicked()`, ausgelöst also **beim Loslassen**. Ein Klick auf ein falsches Versteck spielt dessen Animation `A<nr>` und einen Sound. Bei einem Klick auf das richtige Versteck (`the clickOn - 29 = hidepos`) passiert Folgendes:
   - Das Tempo wird auf `mytempo` gesetzt.
   - Der Film springt zur **Laufanimation** `MA<versteck>:<ziel>`.
   - Der Cursor wird zum animierten Netz (Cast 823/824).
   - Ein Fehlklick ins Leere (`mouseUpScript = "miss"`) spielt `miss.aif`.
3. **Fangen:** Die laufende Maus ist ein **Sprite in der Score-Animation**, sein Skript lautet `on mouseDown caught()`. Ausgelöst wird beim **Aufsetzen**, und ein Treffer zählt nur, wenn das Sprite unter dem Zeiger liegt.
4. **Verpasst:** Am Ende der Laufanimation (`endOfRun`) sitzt die Maus im neuen Versteck (`newdest`), und man muss sie dort erneut aufscheuchen. Nach 4800 Ticks (80 s) ohne Aktion springt sie von selbst (`timeoutScript = nothingatstart`).
5. **Gefangen** (`caught`): Die Maus (Sprite 39, Bilder `m1`–`m5`) hängt am Zeiger und wird zum Netz bewegt (`hanging`, `movetonet`, `checkmove`). Danach folgt die Missgeschick-Animation bzw. das Video (`<RAUM>.MOV`), dann `endofRoom`: `miceCaught + 1`, Raum aus `spritelist` entfernen, weiter ins Musikzimmer oder Menü.

## Fallen

- Die Fallen-Tasche hat die Sprites **41–45** (Auswahl), Sprite **46** ist die Markierung (`trapmark`, `traphilite`).
- **Auswahl** (`runtraps`, `selecttrap`): Die gewählte Falle wird zu `trappos` animiert. Anzahl: Level 1: 10, Level 2: 5, Level 3: 0.
- **Auslösen** (`checktrap msprite`): Läuft die Maus über die Falle, spielt eine Fallen-Animation mit den Cast-Membern `1.1`–`1.10`, `2.1`–`2.11`, `3.1`–`3.5`, `4.1`–`4.6` bzw. `5.1`–`5.9`. Diese tragen **selbst** das Skript `on mouseDown caught()`. Die Schleife fragt `the mouseDown` ab und bricht bei einem Klick ab (`trapsoff` → `pass`), sodass der Klick zum Sprite durchgereicht wird.

## Größen und Zeiten

| Ziel | Größe bei 640×480 | auf dem Touchscreen (×0,5) |
|---|---|---|
| Laufende Maus (`mice0xxx`, 312 Bilder) | Median 39×28 px (min 14×10, max 67×74) | ca. 19×14 px ≈ 3,5×2,5 mm |
| Falle (`trap1`–`trap5`) | 35×31 px | ca. 17×15 px |
| Markierung (`trapmark`) | 10×10 px | 5×5 px |

**Laufdauer der Maus** (Median aller Laufwege, 34 Frames; Details pro Raum in `room-stats.md`):

| Level | Tempo | Median | kürzester Weg (8 Frames) |
|---|---:|---:|---:|
| 1 | 8 fps | 4,2 s | 1,0 s |
| 2 | 12 fps | 2,8 s | 0,7 s |
| 3 | 16 fps | 2,1 s | 0,5 s |
| 3, nach 15 Mäusen | 22 fps | 1,5 s | 0,36 s |

Die Maus bewegt sich **pro Frame** sprunghaft weiter, nicht flüssig. Bei 8 fps springt sie z. B. alle 125 ms.

## Folgen für die Touch-Steuerung (PLAN.md §3, T5.2/T5.3)

1. **Fangen erfolgt beim Aufsetzen** (`mouseDown`). Der Zeiger muss vor dem `mouseDown` auf der Tippstelle stehen, sonst prüft Director die alte Position. Das ist die wichtigste Anforderung an das Eingabe-Backend.
2. **Verstecke reagieren beim Loslassen** (`mouseUp`). Ein Tippen (Aufsetzen und Loslassen an derselben Stelle) funktioniert ohne Sonderbehandlung.
3. **Ziele der Treffhilfe:** Sprites, deren Score-Skript `caught()` beim `mouseDown` aufruft, sowie Sprites mit den Cast-Membern `1.x`–`5.x` (Fallen-Animationen). Robuste Erkennung in der Engine: "Hat das Sprite (bzw. sein Cast-Member) einen `mouseDown`-Handler, der `caught` aufruft?" Alternativ der Name des Cast-Members (`mice*`, `[1-5].*`).
4. **Exaktes Hit-Testing:** Ist die Maus mit Matte-Ink gezeichnet, zählen in Director nur deckende Pixel. Das macht Treffer zusätzlich schwerer; die Treffhilfe sollte deshalb auf das Bounding-Rect plus Radius prüfen. Die Ink der Maus-Sprites wird in T3.4 im Debugger geprüft.
5. **Eingabelatenz:** Bei 22 fps hat ein Frame 45 ms. Die Verzögerung zwischen Touch und `mouseDown` sollte unter einem Frame bleiben, sonst ist die Maus schon weiter. Das wird in T5.5 gemessen.
6. **Mausometer** (GGMDMENU, `detecter`): Es folgt `the mouseH`/`the mouseV`, und `rollOver` löst den Alarm aus. Per Touch funktioniert es durch Ziehen. Die Raumwahl (`select`) erfolgt beim `mouseDown` per `rollOver`, also gilt auch hier: Zeiger zuerst auf die Tippstelle setzen.
7. **Dachboden** (ATTIC): Eine eigene Karte mit 6 Bereichen und `rollovermap`; das in T3.4 gesondert testen.
