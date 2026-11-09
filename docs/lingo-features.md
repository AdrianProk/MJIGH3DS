# Verwendete Lingo-Features

Generiert von `tools/lingo_stats.py` aus 543 dekompilierten Skripten (`analysis/lingo/`).
Eigene Handler des Spiels sind herausgefiltert. Die Spalte "ScummVM" wird in T3.3 ergänzt; in einer eigenen Datei, damit dieses Dokument generierbar bleibt.

## Event-Handler

| Name | Anzahl | Filme |
|---|---:|---|
| `exitFrame` | 398 | ARTIST, ATTIC, BALLROOM, BAR, BATHROOM, BUSINESS (+22) |
| `mouseDown` | 71 | ARTIST, ATTIC, BALLROOM, BAR, BATHROOM, BUSINESS (+17) |
| `mouseUp` | 53 | ARTIST, ATTIC, BALLROOM, BAR, BATHROOM, BUSINESS (+19) |
| `startMovie` | 1 | SHARED |

## Befehle und Funktionen (Aufrufe mit Klammern)

| Name | Anzahl | Filme |
|---|---:|---|
| `go` | 85 | ATTIC, BALLROOM, CREDITS, EXIT, FARMER, GGMDMENU (+5) |
| `puppetSound` | 81 | ARTIST, ATTIC, BALLROOM, BAR, BATHROOM, BUSINESS (+18) |
| `puppetSprite` | 81 | ATTIC, BALLROOM, CREDITS, EXIT, GGMDMENU, INSTRUM (+1) |
| `updateStage` | 59 | ATTIC, BALLROOM, CREDITS, EXIT, GGMDMENU, INSTRUM (+2) |
| `cursor` | 35 | ATTIC, BALLROOM, CREDITS, EXIT, GGMDMENU, GGMDSTRT (+4) |
| `value` | 28 | ATTIC, GGMDMENU, SHARED |
| `preLoad` | 23 | ARTIST, ATTIC, BALLROOM, BAR, BATHROOM, BUSINESS (+16) |
| `random` | 17 | ATTIC, CREDITS, EXIT, FARMER, GGMDMENU, SHARED |
| `preLoadCast` | 13 | INSTRUM |
| `myfile` | 12 | CREDITS, EXIT, GGMDMENU, GGMDSTRT |
| `puppetTempo` | 11 | ATTIC, BALLROOM, FARMER, ORCH, SHARED |
| `soundBusy` | 8 | CREDITS, EXIT, INSTRUM, ORCH |
| `objectp` | 7 | EXIT, GGMDMENU, GGMDSTRT |
| `FileIO` | 6 | CREDITS, EXIT, GGMDMENU, GGMDSTRT |
| `quit` | 5 | CREDITS, GGMDMENU, GGMDSTRT, SHARED |
| `getAt` | 5 | GGMDMENU, INSTRUM |
| `bg` | 5 | GGMDSTRT |
| `unLoad` | 4 | ATTIC, SHARED |
| `alert` | 4 | EXIT, GGMDMENU, GGMDSTRT |
| `count` | 4 | GGMDMENU |
| `rollOver` | 3 | ATTIC, GGMDMENU |
| `pass` | 2 | ATTIC, SHARED |
| `numToChar` | 2 | EXIT |
| `list` | 2 | GGMDMENU, GGMDSTRT |
| `string` | 2 | GGMDMENU, SHARED |
| `deleteAt` | 2 | GGMDMENU, SHARED |
| `continue` | 2 | SHARED |
| `unLoadCast` | 1 | ARTIST |
| `openXLib` | 1 | GGMDSTRT |
| `backdrop` | 1 | GGMDSTRT |
| `closeXLib` | 1 | GGMDSTRT |
| `add` | 1 | INSTRUM |
| `offset` | 1 | SHARED |
| `getPos` | 1 | SHARED |
| `integerp` | 1 | SHARED |
| `pause` | 1 | SHARED |
| `point` | 1 | SNOOKER |

## Anweisungen ohne Klammern

| Name | Anzahl | Filme |
|---|---:|---|
| `updateStage` | 59 | ATTIC, BALLROOM, CREDITS, EXIT, GGMDMENU, INSTRUM (+2) |
| `sound playFile` | 56 | ARTIST, ATTIC, BALLROOM, BAR, BATHROOM, BUSINESS (+17) |
| `play frame` | 39 | EXIT, INSTRUM, ORCH, SHARED |
| `quit` | 5 | CREDITS, GGMDMENU, GGMDSTRT, SHARED |
| `sound stop` | 4 | ARTIST, BALLROOM, INSTRUM, ORCH |
| `play movie` | 3 | ATTIC, INSTRUM, THEEND |
| `pass` | 2 | ATTIC, SHARED |
| `play done` | 2 | INSTRUM |
| `continue` | 2 | SHARED |
| `pause` | 1 | SHARED |

## Properties (`the …`)

| Name | Anzahl | Filme |
|---|---:|---|
| `number` | 54 | ATTIC, CREDITS, EXIT, GGMDMENU, INSTRUM, SHARED |
| `castNum` | 50 | ATTIC, CREDITS, EXIT, GGMDMENU, INSTRUM, SHARED |
| `locH` | 41 | ATTIC, CREDITS, EXIT, GGMDMENU, INSTRUM, SHARED |
| `machineType` | 40 | ARTIST, ATTIC, BALLROOM, BAR, BATHROOM, BUSINESS (+16) |
| `locV` | 39 | ATTIC, CREDITS, EXIT, GGMDMENU, INSTRUM, SHARED |
| `clickOn` | 32 | ATTIC, CREDITS, EXIT, FARMER, INSTRUM, SHARED |
| `visible` | 26 | ATTIC, CREDITS, EXIT, ORCH, SHARED |
| `frame` | 25 | ATTIC, GGMDMENU, INSTRUM, SHARED, THEEND |
| `timeoutScript` | 19 | ATTIC, CREDITS, EXIT, FARMER, INSTRUM, SHARED |
| `mouseDownScript` | 19 | ATTIC, EXIT, GGMDMENU, INSTRUM, SHARED, THEEND |
| `mouseDown` | 13 | SHARED |
| `ink` | 11 | CREDITS, EXIT, GGMDMENU, INSTRUM, SHARED |
| `mouseV` | 10 | ATTIC, GGMDMENU, SHARED |
| `mouseUpScript` | 10 | ATTIC, CREDITS, SHARED |
| `mouseH` | 9 | ATTIC, GGMDMENU, SHARED |
| `soundBusy` | 8 | BALLROOM, BAR, EXERCISE, GGMDMENU, NEWLYWED, SHARED (+1) |
| `type` | 8 | CREDITS, EXIT, INSTRUM, SHARED |
| `keyDownScript` | 8 | CREDITS, EXIT, GGMDMENU, GGMDSTRT, SHARED |
| `timeoutLapsed` | 8 | GGMDMENU, INSTRUM, SHARED |
| `movieRate` | 7 | GGMDMENU, INSTRUM, SHARED, THEEND |
| `stretch` | 6 | GGMDMENU, SHARED |
| `colorDepth` | 5 | CREDITS, GGMDSTRT |
| `pathName` | 4 | ATTIC, CREDITS, EXIT, GGMDSTRT |
| `mouseLine` | 4 | GGMDMENU |
| `key` | 4 | GGMDSTRT, SHARED |
| `exitLock` | 3 | CREDITS, EXIT, SHARED |
| `timeoutLength` | 3 | INSTRUM, SHARED |
| `puppet` | 3 | SHARED |
| `optionDown` | 2 | SHARED |
| `keyCode` | 2 | SHARED |
| `timer` | 2 | SHARED |
| `foreColor` | 1 | ATTIC |
| `editableText` | 1 | EXIT |
| `short` | 1 | EXIT |
| `time` | 1 | EXIT |
| `searchPath` | 1 | GGMDSTRT |
| `commandDown` | 1 | SHARED |
| `timeoutMouse` | 1 | SHARED |
| `regPoint` | 1 | SNOOKER |
