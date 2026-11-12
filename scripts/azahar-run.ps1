# Automatischer Startlauf im Emulator Azahar (für Messungen ohne Eingaben, siehe docs/performance.md):
# startet Azahar mit einer .3dsx, wartet auf zwei Marken im ScummVM-Log, nimmt jeweils ein Bild
# auf und beendet Azahar wieder.
#
#   powershell -File scripts/azahar-run.ps1                    # Port mit diag.txt auf der SD
#   powershell -File scripts/azahar-run.ps1 -ReadyPattern "Log opened" -GamePattern "3ds initsize w:640 h:480"
#
# Die Bilder entstehen mit PrintWindow und zeigen nur den Inhalt des Azahar-Fensters, auch wenn
# andere Fenster darüber liegen. Sie enthalten Spielgrafik und landen deshalb im ignorierten dist/.
# Das Log liegt unter %APPDATA%\Azahar\sdmc\3ds\mausjagd\scummvm.log.
param(
    [string]$Game = "$PSScriptRoot\..\dist\3ds\mausjagd.3dsx",
    [string]$OutDir = "$PSScriptRoot\..\dist\screens",
    [string]$Azahar = "C:\Program Files\Azahar\azahar.exe",
    [int]$AfterGameSeconds = 4,
    [int]$TimeoutSeconds = 180,
    # Marke 1 (Bild "1-startbildschirm"): Diagnosemodus "diag: backend ready", sonst "Log opened"
    [string]$ReadyPattern = "diag: backend ready",
    # Marke 2 (Bild "2-spiel" nach AfterGameSeconds): erstes Bild des Spiels
    [string]$GamePattern = "first frame at 640x480",
    # Optional weitere Bilder "3-spiel", "4-spiel", ... im Abstand ShotIntervalMs (z. B. für Blinken)
    [int]$MoreShots = 0,
    [int]$ShotIntervalMs = 250,
    # App-Ordner auf der virtuellen SD, in dem das Log liegt: mausjagd (deutsch) oder ggmd (englisch)
    [string]$AppFolder = "mausjagd"
)
$Game = (Resolve-Path $Game).Path

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win {
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
}
"@

function Shot([System.Diagnostics.Process]$p, [string]$name) {
    $p.Refresh()
    $r = New-Object Win+RECT
    [void][Win]::GetWindowRect($p.MainWindowHandle, [ref]$r)
    $w = $r.Right - $r.Left; $h = $r.Bottom - $r.Top
    if ($w -le 0 -or $h -le 0) { "kein Fenster für $name"; return }
    # PrintWindow mit PW_RENDERFULLCONTENT (2): nur der Inhalt dieses Fensters,
    # auch wenn andere Fenster darüber liegen (nie ein Bildschirmausschnitt)
    $bmp = New-Object System.Drawing.Bitmap $w, $h
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc()
    $ok = [Win]::PrintWindow($p.MainWindowHandle, $hdc, 2)
    $g.ReleaseHdc($hdc)
    if ($ok) { $bmp.Save("$OutDir\$name.png") } else { "PrintWindow fehlgeschlagen für $name" }
    $g.Dispose(); $bmp.Dispose()
}

New-Item -ItemType Directory -Force $OutDir | Out-Null
$log = "$env:APPDATA\Azahar\sdmc\3ds\$AppFolder\scummvm.log"
$start = Get-Date
$p = Start-Process -FilePath $Azahar -ArgumentList "`"$Game`"" -PassThru

function WaitFor([string]$pattern) {
    while (((Get-Date) - $start).TotalSeconds -lt $TimeoutSeconds) {
        if ((Test-Path $log) -and (Get-Item $log).LastWriteTime -gt $start) {
            if (Select-String -Path $log -Pattern $pattern -Quiet) { return $true }
        }
        if ($p.HasExited) { return $false }
        Start-Sleep -Milliseconds 100
    }
    return $false
}

$ok1 = WaitFor $ReadyPattern
"Marke 1 ($ReadyPattern): $ok1 nach $([int]((Get-Date) - $start).TotalMilliseconds) ms"
Start-Sleep -Milliseconds 300
Shot $p "1-startbildschirm"
$ok2 = WaitFor $GamePattern
"Marke 2 ($GamePattern): $ok2 nach $([int]((Get-Date) - $start).TotalMilliseconds) ms"
Start-Sleep -Seconds $AfterGameSeconds
Shot $p "2-spiel"
for ($i = 0; $i -lt $MoreShots; $i++) {
    Start-Sleep -Milliseconds $ShotIntervalMs
    Shot $p "$($i + 3)-spiel"
}
if (-not $p.HasExited) { Stop-Process -Id $p.Id }
"fertig"
