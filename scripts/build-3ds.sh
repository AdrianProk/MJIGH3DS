#!/usr/bin/env bash
# Baut ScummVM mit nur der Director-Engine für den 3DS (WSL1/Ubuntu), siehe docs/build-3ds.md.
#
#   bash scripts/build-3ds.sh        -> dist/3ds/scummvm.3dsx
#
# Umgebungsvariablen (optional):
#   SCUMMVM_SRC   Quellcode, Standard ~/scummvm (Branch mausjagd)
#   BUILD_ROOT    Build-Ordner, Standard ~/build (gebaut wird in $BUILD_ROOT/3ds)
#   DEVKITPRO     Standard /opt/devkitpro (Symlink auf ~/devkitpro, siehe Doku)
#   JOBS          parallele Jobs, Standard nproc
#   RECONFIGURE=1 configure erzwingen
#   EXTRA_CONFIGURE  zusätzliche configure-Optionen
set -euo pipefail

SRC="${SCUMMVM_SRC:-$HOME/scummvm}"
BUILD="${BUILD_ROOT:-$HOME/build}/3ds"
JOBS="${JOBS:-$(nproc)}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export DEVKITPRO="${DEVKITPRO:-/opt/devkitpro}"
export DEVKITARM="$DEVKITPRO/devkitARM"
export CTRULIB="$DEVKITPRO/libctru"
export PORTLIBS="$DEVKITPRO/portlibs/3ds"
export PATH="$DEVKITPRO/tools/bin:$PORTLIBS/bin:$DEVKITARM/bin:$PATH"
# pkg-config darf nur die 3DS-Portlibs sehen
export PKG_CONFIG_LIBDIR="$PORTLIBS/lib/pkgconfig"
export PKG_CONFIG_PATH=

[ -x "$DEVKITARM/bin/arm-none-eabi-gcc" ] || { echo "devkitARM fehlt unter $DEVKITARM" >&2; exit 1; }

echo "=== 3DS-Build in $BUILD ($(arm-none-eabi-gcc --version | head -1))"
mkdir -p "$BUILD"
cd "$BUILD"
if [ "${RECONFIGURE:-0}" = 1 ] || [ ! -f config.mk ]; then
  # Cloud/libcurl aus: braucht sonst cacert.pem und ist für das Spiel unnötig
  # shellcheck disable=SC2086
  "$SRC/configure" --host=3ds --disable-all-engines --enable-engine=director \
    --disable-cloud --disable-libcurl ${EXTRA_CONFIGURE:-}
fi
make -j"$JOBS"
make scummvm.3dsx

dist="$REPO/dist/3ds"
mkdir -p "$dist"
cp scummvm.3dsx "$dist/"
git -C "$SRC" rev-parse HEAD > "$dist/SCUMMVM_COMMIT.txt"
ls -la "$dist/scummvm.3dsx"
echo "=== fertig: $dist/scummvm.3dsx"
