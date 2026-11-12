#!/usr/bin/env python3
"""Icon, Banner und Banner-Ton der 3DS-App aus den eigenen Spieldaten (scripts/build-3ds.sh).

Quelle ist der Startfilm GGMDSTRT, der im Projektor eingebettet ist (MAUSJAGD.EXE bzw. GGMD.EXE):
  - Cast 9 "german splashscreen" bzw. "english splashscreen" (640x480, 8 Bit, Palette Cast 8):
    Titelbild -> Banner und Icon
  - Cast 6 "Theme.aif" (snd): Titelmelodie -> Banner-Ton (die ersten Sekunden, ausgeblendet)

Die Ausgaben enthalten Spielgrafik und -ton. Sie entstehen nur im Build-Ordner und landen nie
im Repo (PLAN.md §7); gedacht für Builds mit eingebetteten Spieldaten, die ohnehin nur für den
eigenen Gebrauch sind. Nur Python-Standardbibliothek; liest die Spieldaten nur.

Aufruf:
    python3 -I scripts/make_app_art.py <game> <ausgabeordner> [--full]

    <game>           Ordner mit MAUSJAGD.EXE oder GGMD.EXE
    <ausgabeordner>  bekommt banner.png (256x128), icon.png (48x48), banner.wav
    --full           zusätzlich splash.png (ganzes Titelbild, zum Prüfen der Ausschnitte)
"""
import os
import struct
import sys
import wave
import zlib

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
import dxr_inventory  # noqa: E402  (Chunk-Lesung der Director-Filme)

PROJECTORS = ('MAUSJAGD.EXE', 'GGMD.EXE')   # deutsche, englische Fassung
SPLASH_MEMBER = 9   # "german splashscreen" bzw. "english splashscreen"
THEME_MEMBER = 6
# Ausschnitte im 640x480-Titelbild (x, y, Breite, Höhe), am Bild ausgesucht (2026-11-11):
BANNER_CROP = (0, 0, 640, 320)    # obere zwei Drittel: Logo, Hotelfassade, Portier (2:1 wie der Banner)
ICON_CROP = (334, 314, 66, 66)    # die grünen Mäuse in der Hand des Pagen
BANNER_SECONDS = 3.0              # Banner-Ton: höchstens etwa 3 s
BANNER_FADE = 0.35                # Ausblenden am Ende; die Phrase endet bei etwa 3,25 s
BANNER_PEAK = 0.9                 # Spitzenpegel nach dem Anheben (Anteil von Vollaussteuerung)


# --- Director-Film -------------------------------------------------------------------------

class StartMovie:
    """Der in MAUSJAGD.EXE eingebettete Startfilm mit Cast-Zuordnung über KEY*."""

    def __init__(self, exe_path):
        movies = dxr_inventory.find_movies(exe_path)
        if not movies:
            raise ValueError(f'{exe_path}: kein eingebetteter Director-Film')
        self.m = m = movies[0]
        cfg = m.chunk_data(m.first('VWCF'))
        min_member = struct.unpack('>H', cfg[12:14])[0] or 1
        ids = m.chunk_data(m.first('CAS*'))
        self.member_chunk = {}
        for i in range(len(ids) // 4):
            cid = struct.unpack('>I', ids[4 * i:4 * i + 4])[0]
            if cid:
                self.member_chunk[min_member + i] = cid
        key = m.chunk_data(m.first('KEY*'))
        _, _, _, used = struct.unpack(m.fmt + 'HHII', key[:12])
        self.resources = {}  # (CASt-Chunk, Tag) -> Daten-Chunk
        for i in range(used):
            sec, cast, tag = struct.unpack(m.fmt + 'II4s', key[12 + i * 12:24 + i * 12])
            tag = (tag[::-1] if m.le else tag).decode('latin-1')
            self.resources[(cast, tag)] = sec

    def cast_specific(self, num):
        c = self.m.chunk_data(self.member_chunk[num])
        size = struct.unpack('>H', c[0:2])[0]
        return c[6:6 + size]

    def resource(self, num, tag):
        return self.m.chunk_data(self.resources[(self.member_chunk[num], tag)])


def decode_palette(clut):
    """CLUT: 6 Byte pro Farbe (R, G, B je 16 Bit, oberes Byte zählt)."""
    return [(clut[i], clut[i + 2], clut[i + 4]) for i in range(0, len(clut) - 5, 6)]


def decode_bitmap(movie, num):
    """8-Bit-Bitmap (Director 4) -> (Breite, Höhe, Zeilen mit RGB-Tupeln)."""
    # Typ(1) Flags(1) Pitch mit Flag 0x8000(2) initialRect(8) boundingRect(8) regY(2) regX(2)
    # 0(1) Bits pro Pixel(1) Palette(2, Cast-Nummer; <= 0 eingebaute Palette)
    spec = movie.cast_specific(num)
    pitch_flags = struct.unpack('>H', spec[2:4])[0]
    top, left, bottom, right = struct.unpack('>hhhh', spec[4:12])
    width, height = right - left, bottom - top
    if not pitch_flags & 0x8000 or len(spec) < 28:
        raise ValueError(f'Cast {num}: keine 8-Bit-Bitmap')
    bpp = spec[25]
    clut_id = struct.unpack('>h', spec[26:28])[0]
    if bpp != 8 or clut_id <= 0:
        raise ValueError(f'Cast {num}: {bpp} Bit, Palette {clut_id} nicht unterstützt')
    pitch = pitch_flags & 0x0fff
    palette = decode_palette(movie.resource(clut_id, 'CLUT'))
    data = movie.resource(num, 'BITD')
    if len(data) < pitch * height:
        # PackBits: n < 0x80 -> n+1 Bytes übernehmen, sonst nächstes Byte 257-n mal
        out = bytearray()
        i = 0
        while i < len(data) and len(out) < pitch * height:
            n = data[i]
            i += 1
            if n < 0x80:
                out += data[i:i + n + 1]
                i += n + 1
            else:
                out += bytes([data[i]]) * (257 - n)
                i += 1
        data = bytes(out)
    if len(data) < pitch * height:
        raise ValueError(f'Cast {num}: Bilddaten zu kurz')
    rows = []
    for y in range(height):
        row = data[y * pitch:y * pitch + width]
        rows.append([palette[p] if p < len(palette) else (0, 0, 0) for p in row])
    return width, height, rows


# --- Bilder --------------------------------------------------------------------------------

def crop(rows, x, y, w, h):
    return [r[x:x + w] for r in rows[y:y + h]]


def _resample_1d(line, out_len):
    """Flächenmittel (Box-Filter) einer Zeile aus RGB-Tupeln auf out_len Werte."""
    n = len(line)
    scale = n / out_len
    out = []
    for o in range(out_len):
        a, b = o * scale, (o + 1) * scale
        acc = [0.0, 0.0, 0.0]
        i = int(a)
        while i < b and i < n:
            wgt = min(b, i + 1) - max(a, i)
            px = line[i]
            acc[0] += px[0] * wgt
            acc[1] += px[1] * wgt
            acc[2] += px[2] * wgt
            i += 1
        out.append((acc[0] / scale, acc[1] / scale, acc[2] / scale))
    return out


def resize(rows, w, h):
    horiz = [_resample_1d(r, w) for r in rows]
    cols = [_resample_1d([r[x] for r in horiz], h) for x in range(w)]
    return [[tuple(min(255, max(0, round(c))) for c in cols[x][y]) for x in range(w)] for y in range(h)]


def write_png(path, rows, alpha=False):
    h, w = len(rows), len(rows[0])
    raw = bytearray()
    for r in rows:
        raw.append(0)
        for px in r:
            raw += bytes(px[:3])
            if alpha:
                raw.append(255)
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 6 if alpha else 2, 0, 0, 0)
    with open(path, 'wb') as fh:
        fh.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(bytes(raw), 9))
                 + chunk(b'IEND', b''))


# --- Ton -----------------------------------------------------------------------------------

def decode_snd(snd):
    """Mac-'snd '-Ressource (Format 1 oder 2, ein Sampled-Sound-Header) -> (Rate, Kanäle, Bits, PCM)."""
    fmt = struct.unpack('>H', snd[0:2])[0]
    pos = 2
    if fmt == 1:
        count = struct.unpack('>H', snd[pos:pos + 2])[0]
        pos += 2 + count * 6
    elif fmt == 2:
        pos += 2
    else:
        raise ValueError(f'snd-Format {fmt} nicht unterstützt')
    ncmd = struct.unpack('>H', snd[pos:pos + 2])[0]
    pos += 2
    header = None
    for i in range(ncmd):
        cmd, _, param2 = struct.unpack('>HHI', snd[pos + i * 8:pos + i * 8 + 8])
        if cmd in (0x8050, 0x8051):  # soundCmd / bufferCmd mit Offset des Headers
            header = param2
    if header is None:
        raise ValueError('snd ohne Sound-Header')
    _, length, rate, _, _, encode, _ = struct.unpack('>IIIIIBB', snd[header:header + 22])
    rate = rate >> 16
    data = header + 22
    if encode == 0x00:  # Standard-Header: 8 Bit mono, unsigned
        return rate, 1, 8, snd[data:data + length]
    if encode == 0xFF:  # erweiterter Header
        channels = length
        frames = struct.unpack('>I', snd[data:data + 4])[0]
        bits = struct.unpack('>H', snd[data + 26:data + 28])[0]
        start = header + 64
        pcm = snd[start:start + frames * channels * bits // 8]
        if bits == 16:  # big-endian -> little-endian für WAV
            pcm = b''.join(pcm[i + 1:i + 2] + pcm[i:i + 1] for i in range(0, len(pcm), 2))
        return rate, channels, bits, pcm
    raise ValueError(f'snd-Kodierung 0x{encode:02x} nicht unterstützt')


def write_banner_wav(path, rate, channels, bits, pcm, seconds, fade, peak):
    """Die ersten `seconds` Sekunden als 16-Bit-PCM, auf `peak` angehoben (höchstens 2-fach),
    die letzten `fade` Sekunden ausgeblendet."""
    if bits == 8:
        samples = [(b - 128) << 8 for b in pcm]
    elif bits == 16:
        samples = list(struct.unpack('<%dh' % (len(pcm) // 2), pcm[:len(pcm) // 2 * 2]))
    else:
        raise ValueError(f'{bits} Bit nicht unterstützt')
    frames = min(len(samples) // channels, int(rate * seconds))
    samples = samples[:frames * channels]
    level = max((abs(s) for s in samples), default=0)
    boost = min(2.0, peak * 32767 / level) if level else 1.0
    fade_frames = int(rate * fade)
    out = []
    for f in range(frames):
        gain = boost * (min(1.0, (frames - f) / fade_frames) if fade_frames else 1.0)
        for c in range(channels):
            out.append(max(-32768, min(32767, int(samples[f * channels + c] * gain))))
    with wave.open(path, 'wb') as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(struct.pack('<%dh' % len(out), *out))
    return frames / rate


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 2:
        sys.exit(__doc__)
    game, out = args
    os.makedirs(out, exist_ok=True)
    # Projektor der deutschen bzw. englischen Fassung; der Startfilm ist in beiden gleich aufgebaut
    exe = next((os.path.join(game, n) for n in PROJECTORS if os.path.isfile(os.path.join(game, n))), None)
    if not exe:
        sys.exit(f'{game}: kein Projektor ({", ".join(PROJECTORS)})')
    movie = StartMovie(exe)
    w, h, splash = decode_bitmap(movie, SPLASH_MEMBER)
    if (w, h) != (640, 480):
        raise ValueError(f'Titelbild {w}x{h}, erwartet 640x480')
    if '--full' in sys.argv:
        write_png(os.path.join(out, 'splash.png'), splash)
    write_png(os.path.join(out, 'banner.png'), resize(crop(splash, *BANNER_CROP), 256, 128), alpha=True)
    write_png(os.path.join(out, 'icon.png'), resize(crop(splash, *ICON_CROP), 48, 48))
    rate, ch, bits, pcm = decode_snd(movie.resource(THEME_MEMBER, 'snd '))
    secs = write_banner_wav(os.path.join(out, 'banner.wav'), rate, ch, bits, pcm,
                            BANNER_SECONDS, BANNER_FADE, BANNER_PEAK)
    print(f'App-Grafik aus dem Titelbild: banner.png 256x128, icon.png 48x48; '
          f'banner.wav {secs:.2f} s aus "Theme.aif" ({rate} Hz, {bits} Bit) -> {out}')


if __name__ == '__main__':
    main()
