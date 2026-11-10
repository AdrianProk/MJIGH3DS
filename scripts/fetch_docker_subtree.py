#!/usr/bin/env python3
"""Lädt ein Image von Docker Hub ohne Docker und entpackt einen Teilbaum daraus.

Zweck (T4.1): devkitpro.org sperrt automatisierte Downloads (Cloudflare, HTTP 403).
Das offizielle Image ``devkitpro/devkitarm`` auf Docker Hub enthält dieselbe
3DS-Toolchain unter ``/opt/devkitpro``. Dieses Skript holt es über die
Registry-API und entpackt nur diesen Teilbaum, ohne Docker und ohne root.

Aufruf in WSL/Linux, nur Standardbibliothek (Python >= 3.12; für zstd-Schichten 3.14):

    python3 -I scripts/fetch_docker_subtree.py devkitpro/devkitarm 20260610 \\
        --blobs ~/downloads/devkitarm-20260610 --subtree opt/devkitpro --dest ~/devkitpro

- Jede Schicht wird gegen ihren SHA-256-Digest geprüft. Vorhandene und korrekte
  Schichten werden nicht erneut geladen.
- Manifeste werden im Blob-Ordner zwischengespeichert, um die Pull-Limits von
  Docker Hub zu schonen.
- Docker-Whiteouts (``.wh.<name>``, ``.wh..wh..opq``) werden innerhalb des
  Teilbaums angewendet.
- Absolute Symlinks in den Teilbaum werden in relative umgeschrieben. Alles, was
  aus dem Teilbaum herauszeigt, wird übersprungen und gemeldet.
- Entpackt wird mit ``tarfile`` und ``filter='data'``. GNU tar scheitert unter WSL1.
"""
import argparse
import hashlib
import json
import os
import posixpath
import shutil
import sys
import tarfile
import urllib.request

REGISTRY = 'https://registry-1.docker.io'
AUTH = 'https://auth.docker.io/token'
UA = 'mjigh3ds-fetch/1.0 (python-urllib)'
INDEX_TYPES = (
    'application/vnd.oci.image.index.v1+json',
    'application/vnd.docker.distribution.manifest.list.v2+json',
)
MANIFEST_TYPES = (
    'application/vnd.oci.image.manifest.v1+json',
    'application/vnd.docker.distribution.manifest.v2+json',
)
ACCEPT = ', '.join(INDEX_TYPES + MANIFEST_TYPES)


def get_token(repo):
    url = f'{AUTH}?service=registry.docker.io&scope=repository:{repo}:pull'
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)['token']


def open_url(url, repo, accept=None):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    # Nicht an Weiterleitungen (CDN) mitschicken
    req.add_unredirected_header('Authorization', f'Bearer {get_token(repo)}')
    if accept:
        req.add_header('Accept', accept)
    return urllib.request.urlopen(req, timeout=120)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def get_manifest(repo, ref, cache_dir):
    """Manifest laden (oder aus dem Cache) und bei Digest-Referenzen prüfen."""
    safe = ref.replace(':', '_').replace('/', '_')
    path = os.path.join(cache_dir, f'manifest-{safe}.json')
    if os.path.exists(path):
        with open(path, 'rb') as f:
            data = f.read()
    else:
        with open_url(f'{REGISTRY}/v2/{repo}/manifests/{ref}', repo, ACCEPT) as r:
            data = r.read()
        with open(path, 'wb') as f:
            f.write(data)
    digest = 'sha256:' + hashlib.sha256(data).hexdigest()
    if ref.startswith('sha256:') and digest != ref:
        os.remove(path)
        sys.exit(f'Manifest-Digest stimmt nicht: {digest} != {ref}')
    return json.loads(data), digest


def fetch_blob(repo, digest, size, blobs_dir):
    algo, hexd = digest.split(':', 1)
    if algo != 'sha256':
        sys.exit(f'Unbekannter Digest-Typ: {digest}')
    path = os.path.join(blobs_dir, hexd)
    if os.path.exists(path) and sha256_file(path) == hexd:
        print(f'  vorhanden und geprüft: {hexd[:12]} ({size >> 20} MiB)')
        return path
    tmp = path + '.part'
    h = hashlib.sha256()
    done = 0
    step = max(size // 4, 1)
    next_report = step
    print(f'  lade {hexd[:12]} ({size >> 20} MiB)', flush=True)
    with open_url(f'{REGISTRY}/v2/{repo}/blobs/{digest}', repo) as r, open(tmp, 'wb') as f:
        for chunk in iter(lambda: r.read(1 << 20), b''):
            f.write(chunk)
            h.update(chunk)
            done += len(chunk)
            if done >= next_report:
                print(f'    {done * 100 // max(size, 1):3d} %', flush=True)
                next_report += step
    if h.hexdigest() != hexd or done != size:
        os.remove(tmp)
        sys.exit(f'Prüfung fehlgeschlagen für {digest}: sha256 {h.hexdigest()}, {done} von {size} Bytes')
    os.replace(tmp, path)
    return path


def norm(name):
    name = name.lstrip('/')
    while name.startswith('./'):
        name = name[2:]
    return posixpath.normpath(name) if name else ''


def remove_path(p):
    if os.path.islink(p) or os.path.isfile(p):
        os.remove(p)
    elif os.path.isdir(p):
        shutil.rmtree(p)


def open_layer(path, media):
    if 'zstd' in media:
        return tarfile.open(path, 'r:zst')
    return tarfile.open(path, 'r:*')


def extract_subtree(layers, subtree, dest):
    prefix = subtree.strip('/') + '/'
    root = prefix[:-1]

    def rel_of(name):
        n = norm(name)
        if n == root:
            return '.'
        if n.startswith(prefix):
            return n[len(prefix):]
        return None

    skipped = []

    def safe_filter(member, path):
        try:
            return tarfile.data_filter(member, path)
        except tarfile.FilterError as e:
            skipped.append(f'{member.name}: {e}')
            return None

    os.makedirs(dest, exist_ok=True)
    count = 0
    for i, (path, media) in enumerate(layers, 1):
        with open_layer(path, media) as tf:
            members = tf.getmembers()
            # 1. Whiteouts dieser Schicht auf die unteren Schichten anwenden
            for m in members:
                n = norm(m.name)
                base, parent = posixpath.basename(n), posixpath.dirname(n)
                if base == '.wh..wh..opq':
                    r = rel_of(parent)
                    if r is not None:
                        d = os.path.join(dest, r)
                        if os.path.isdir(d):
                            for e in os.listdir(d):
                                remove_path(os.path.join(d, e))
                elif base.startswith('.wh.'):
                    r = rel_of(posixpath.join(parent, base[4:]))
                    if r == '.':
                        for e in os.listdir(dest):
                            remove_path(os.path.join(dest, e))
                    elif r is not None:
                        remove_path(os.path.join(dest, r))
            # 2. Einträge im Teilbaum umbenennen und entpacken
            todo = []
            for m in members:
                n = norm(m.name)
                if posixpath.basename(n).startswith('.wh.'):
                    continue
                r = rel_of(n)
                if r is None or r == '.':
                    continue
                if m.issym() and m.linkname.startswith('/'):
                    t = rel_of(m.linkname)
                    if t is None:
                        skipped.append(f'{n}: absoluter Symlink nach außen ({m.linkname})')
                        continue
                    m.linkname = posixpath.relpath(t, posixpath.dirname(r) or '.')
                elif m.islnk():
                    t = rel_of(m.linkname)
                    if t is None or t == '.':
                        skipped.append(f'{n}: Hardlink nach außen ({m.linkname})')
                        continue
                    m.linkname = t
                p = os.path.join(dest, r)
                if os.path.lexists(p) and not (m.isdir() and os.path.isdir(p) and not os.path.islink(p)):
                    remove_path(p)
                m.name = r
                todo.append(m)
            tf.extractall(dest, members=todo, filter=safe_filter)
            count += len(todo)
            print(f'  Schicht {i}/{len(layers)}: {len(todo)} Einträge im Teilbaum', flush=True)
    return count, skipped


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('repo', help='z. B. devkitpro/devkitarm')
    ap.add_argument('tag', help='z. B. 20260610')
    ap.add_argument('--arch', default='amd64')
    ap.add_argument('--blobs', required=True, help='Ordner für Manifeste und Schichten')
    ap.add_argument('--subtree', required=True, help='z. B. opt/devkitpro')
    ap.add_argument('--dest', required=True, help='Zielordner für den Teilbaum')
    a = ap.parse_args()

    blobs = os.path.expanduser(a.blobs)
    dest = os.path.expanduser(a.dest)
    os.makedirs(blobs, exist_ok=True)

    print(f'Manifest {a.repo}:{a.tag}')
    m, top_digest = get_manifest(a.repo, a.tag, blobs)
    index_digest = None
    if m.get('mediaType') in INDEX_TYPES or 'manifests' in m:
        index_digest = top_digest
        cands = [x for x in m['manifests']
                 if x.get('platform', {}).get('os') == 'linux'
                 and x.get('platform', {}).get('architecture') == a.arch]
        if not cands:
            sys.exit(f'Keine linux/{a.arch}-Variante im Index')
        m, man_digest = get_manifest(a.repo, cands[0]['digest'], blobs)
    else:
        man_digest = top_digest
    print(f'  Index:    {index_digest}')
    print(f'  Manifest: {man_digest}')

    cfg_path = fetch_blob(a.repo, m['config']['digest'], m['config']['size'], blobs)
    with open(cfg_path, 'rb') as f:
        cfg = json.load(f)
    env = cfg.get('config', {}).get('Env', [])

    layers = []
    total = sum(x['size'] for x in m['layers'])
    print(f'{len(m["layers"])} Schichten, {total >> 20} MiB komprimiert')
    for x in m['layers']:
        layers.append((fetch_blob(a.repo, x['digest'], x['size'], blobs), x['mediaType']))

    print(f'Entpacke /{a.subtree.strip("/")} nach {dest}')
    count, skipped = extract_subtree(layers, a.subtree, dest)

    record = {
        'image': f'{a.repo}:{a.tag}', 'arch': a.arch,
        'index_digest': index_digest, 'manifest_digest': man_digest,
        'layers': [x['digest'] for x in m['layers']],
        'subtree': a.subtree, 'env': env, 'skipped': skipped,
    }
    with open(os.path.join(dest, '.mjigh3ds-source.json'), 'w', encoding='utf-8') as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    print(f'Fertig: {count} Einträge, {len(skipped)} übersprungen')
    for s in skipped[:20]:
        print('  übersprungen:', s)
    print('Image-Umgebung:')
    for e in env:
        print('  ', e)


if __name__ == '__main__':
    main()
