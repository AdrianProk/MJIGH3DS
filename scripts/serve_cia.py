#!/usr/bin/env python3
"""Ein CIA im Heimnetz anbieten und als QR-Code für FBI zeigen (Remote Install -> Scan QR Code).

Der PC liefert nur diese eine Datei aus, ohne Verzeichnisliste, und nur im lokalen Netz. Die
Datei verlässt das WLAN also nicht. Nach dem ersten vollständigen Download beendet sich der
Server (mit --keep nicht), spätestens nach --minutes Minuten.

Aufruf (Windows, braucht segno für den QR-Code). Abweichend von Regel 8 der TODO mit -P statt
-I: segno liegt in den Benutzer-Paketen, die -I ausblendet. -P verhindert weiterhin, dass Module
aus dem Skriptordner geladen werden; gelesen wird nur unser eigenes CIA.
    py -P scripts/serve_cia.py dist/3ds/mausjagd.cia [--ip 192.168.0.135] [--port 8080]

Danach auf dem 3DS: FBI -> Remote Install -> Scan QR Code, den Code auf dem Bildschirm scannen.
3DS und PC müssen im selben WLAN sein. Beim ersten Start fragt die Windows-Firewall nach.
"""
import argparse
import http.server
import ipaddress
import os
import shutil
import socket
import sys
import tempfile
import threading
import time
import urllib.parse


def lan_ip():
    """Adresse der Netzwerkkarte, über die der PC ins Netz geht (es wird nichts gesendet)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(('192.0.2.1', 9))  # TEST-NET-1, nur zur Wahl der Route
        return s.getsockname()[0]


def make_handler(path, name, done, keep):
    size = os.path.getsize(path)

    class Handler(http.server.BaseHTTPRequestHandler):
        def _head(self):
            if urllib.parse.unquote(self.path.split('?')[0]) != '/' + name:
                self.send_error(404)
                return False
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(size))
            self.end_headers()
            return True

        def do_HEAD(self):
            self._head()

        def do_GET(self):
            if not self._head():
                return
            t0 = time.time()
            self.log_message('Download beginnt (%.1f MB)', size / 1e6)
            try:
                with open(path, 'rb') as fh:
                    shutil.copyfileobj(fh, self.wfile, 256 * 1024)
            except (BrokenPipeError, ConnectionResetError):
                self.log_message('Download abgebrochen')
                return
            secs = time.time() - t0
            self.log_message('Download fertig: %.1f MB in %.0f s (%.2f MB/s)', size / 1e6, secs, size / 1e6 / max(secs, 0.001))
            if not keep:
                done.set()

    return Handler


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('cia')
    ap.add_argument('--ip', default=None, help='Adresse des PCs im WLAN (Standard: automatisch)')
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--minutes', type=float, default=30, help='spätestens dann beenden (Standard 30)')
    ap.add_argument('--keep', action='store_true', help='nach einem Download weiterlaufen')
    ap.add_argument('--no-open', action='store_true', help='QR-Bild nicht automatisch öffnen')
    args = ap.parse_args()

    path = os.path.abspath(args.cia)
    if not os.path.isfile(path):
        sys.exit(f'{path} fehlt')
    name = os.path.basename(path)
    ip = args.ip or lan_ip()
    # Nur private Adressen (10/8, 172.16/12, 192.168/16): Das CIA enthält das Spiel und darf
    # nicht aus dem Internet erreichbar sein, falls der PC direkt eine öffentliche Adresse hat
    addr = ipaddress.ip_address(ip)
    if not addr.is_private or addr.is_loopback:
        sys.exit(f'{ip} ist keine Adresse im Heimnetz; mit --ip angeben')
    url = f'http://{ip}:{args.port}/{urllib.parse.quote(name)}'

    done = threading.Event()
    server = http.server.ThreadingHTTPServer((ip, args.port), make_handler(path, name, done, args.keep))
    threading.Thread(target=server.serve_forever, daemon=True).start()

    print(f'Biete {name} ({os.path.getsize(path) / 1e6:.1f} MB) an: {url}')
    try:
        import segno
    except ImportError:
        print('segno fehlt, kein QR-Code. In FBI die URL von Hand eingeben (Remote Install -> Enter URL).')
    else:
        qr = segno.make(url, error='m')
        png = os.path.join(tempfile.gettempdir(), 'mausjagd-cia-qr.png')
        qr.save(png, scale=12, border=4)
        print(f'QR-Code: {png}')
        if not args.no_open and hasattr(os, 'startfile'):
            os.startfile(png)
    print('3DS: FBI -> Remote Install -> Scan QR Code. Beenden mit Strg+C.', flush=True)

    try:
        finished = done.wait(args.minutes * 60)
        print('Fertig, Server beendet.' if finished else f'Nach {args.minutes:g} Minuten beendet.')
    except KeyboardInterrupt:
        print('Abgebrochen.')
    server.shutdown()


if __name__ == '__main__':
    main()
