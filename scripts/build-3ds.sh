#!/usr/bin/env bash
# Baut ScummVM mit nur der Director-Engine für den 3DS (WSL1/Ubuntu), siehe docs/build-3ds.md.
#
#   bash scripts/build-3ds.sh                  -> dist/3ds/mausjagd.3dsx (eigenständiger Port)
#   MAUSJAGD_PORT=0 bash scripts/build-3ds.sh  -> dist/3ds/scummvm.3dsx  (normales ScummVM mit Launcher)
#
# Umgebungsvariablen (optional):
#   SCUMMVM_SRC   Quellcode, Standard ~/scummvm (Branch mausjagd)
#   BUILD_ROOT    Build-Ordner, Standard ~/build (Port: 3ds, normal: 3ds-vanilla)
#   DEVKITPRO     Standard /opt/devkitpro (Symlink auf ~/devkitpro, siehe Doku)
#   JOBS          parallele Jobs, Standard nproc
#   RECONFIGURE=1 configure erzwingen
#   EXTRA_CONFIGURE  zusätzliche configure-Optionen
#   EMBED_GAME    nur Port: 1 = Spieldaten in die RomFS der .3dsx (Standard), 0 = Daten auf der SD-Karte
#   GAME_DIR      Spielordner, Standard <repo>/game
#
# Achtung: Mit EMBED_GAME=1 enthält die .3dsx das Spiel. Nur für den eigenen Gebrauch,
# nicht weitergeben (dist/ ist ignoriert).
set -euo pipefail

SRC="${SCUMMVM_SRC:-$HOME/scummvm}"
PORT="${MAUSJAGD_PORT:-1}"
JOBS="${JOBS:-$(nproc)}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "$PORT" = 1 ]; then
  BUILD="${BUILD_ROOT:-$HOME/build}/3ds"
  OUT=mausjagd.3dsx
  # Port-Patches im Fork sind mit #ifdef MAUSJAGD_PORT geschützt
  export CPPFLAGS="-DMAUSJAGD_PORT"
  APP_VARS=(APP_TITLE="Mäusejagd im Grandhotel"
            APP_DESCRIPTION="3DS-Port mit ScummVM (Director-Engine)"
            APP_AUTHOR="ScummVM Team")
else
  BUILD="${BUILD_ROOT:-$HOME/build}/3ds-vanilla"
  OUT=scummvm.3dsx
  export CPPFLAGS=
  APP_VARS=()
fi

export DEVKITPRO="${DEVKITPRO:-/opt/devkitpro}"
export DEVKITARM="$DEVKITPRO/devkitARM"
export CTRULIB="$DEVKITPRO/libctru"
export PORTLIBS="$DEVKITPRO/portlibs/3ds"
export PATH="$DEVKITPRO/tools/bin:$PORTLIBS/bin:$DEVKITARM/bin:$PATH"
# pkg-config darf nur die 3DS-Portlibs sehen
export PKG_CONFIG_LIBDIR="$PORTLIBS/lib/pkgconfig"
export PKG_CONFIG_PATH=

[ -x "$DEVKITARM/bin/arm-none-eabi-gcc" ] || { echo "devkitARM fehlt unter $DEVKITARM" >&2; exit 1; }

echo "=== 3DS-Build ($([ "$PORT" = 1 ] && echo Port || echo normal)) in $BUILD ($(arm-none-eabi-gcc --version | head -1))"
mkdir -p "$BUILD"
cd "$BUILD"
if [ "${RECONFIGURE:-0}" = 1 ] || [ ! -f config.mk ]; then
  # Cloud/libcurl aus: braucht sonst cacert.pem und ist für das Spiel unnötig
  # shellcheck disable=SC2086
  "$SRC/configure" --host=3ds --disable-all-engines --enable-engine=director \
    --disable-cloud --disable-libcurl ${EXTRA_CONFIGURE:-}
fi
make -j"$JOBS"

ROMFS_VARS=()
if [ "$PORT" = 1 ] && [ "${EMBED_GAME:-1}" = 1 ]; then
  GAME_DIR="${GAME_DIR:-$REPO/game}"
  STAGE="$BUILD/romfs-extra/game"
  echo "=== Spieldaten laut docs/inventory.md nach $STAGE (geprüft)"
  python3 -I "$REPO/scripts/stage_game_data.py" "$GAME_DIR" "$REPO/docs/inventory.md" "$STAGE"
  ROMFS_VARS=(DIST_3DS_EXTRA_FILES="$STAGE")
fi

# RomFS und SMDH immer neu erzeugen: make sieht Änderungen in Unterordnern bzw. an
# Titel/Beschreibung sonst nicht
rm -rf romfs scummvm.smdh scummvm.3dsx
make scummvm.3dsx "${APP_VARS[@]}" "${ROMFS_VARS[@]}"
if [ ${#ROMFS_VARS[@]} -gt 0 ]; then
  echo "RomFS-Spieldaten: $(find romfs/game -type f | wc -l) Dateien, $(du -sh romfs/game | cut -f1)"
fi

dist="$REPO/dist/3ds"
mkdir -p "$dist"
cp scummvm.3dsx "$dist/$OUT"
git -C "$SRC" rev-parse HEAD > "$dist/SCUMMVM_COMMIT.txt"
ls -la "$dist/$OUT"
echo "=== fertig: $dist/$OUT"
