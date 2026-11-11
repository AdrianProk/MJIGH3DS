#!/usr/bin/env bash
# Baut ScummVM mit nur der Director-Engine für den 3DS (WSL1/Ubuntu), siehe docs/build-3ds.md.
#
#   bash scripts/build-3ds.sh                  -> dist/3ds/mausjagd.3dsx (eigenständiger Port)
#   DIAG=1 bash scripts/build-3ds.sh           -> dist/3ds/mausjagd-diag.3dsx (Port mit Diagnosemodus)
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
#   DIAG          nur Port: 1 = Diagnosemodus, legt diag.txt in die RomFS; Ausgabe dist/3ds/mausjagd-diag.3dsx.
#                 Gleiches Binary wie ohne DIAG. Ohne Neubau geht es auch mit sdmc:/3ds/mausjagd/diag.txt.
#   DIAG_ARGS     Startoptionen für den Diagnosemodus, Standard leer = Vorgabe im Code
#                 (MAUSJAGD_DIAG_DEFAULT_ARGS: --debuglevel=1 --debugflags=loading)
#   CIA           nur Port: 1 = zusätzlich dist/3ds/mausjagd.cia (bzw. mausjagd-diag.cia) mit
#                 config/mausjagd.rsf. Braucht makerom und bannertool (scripts/build-ctr-tools.sh).
#   CTR_TOOLS     Ordner mit bin/makerom und bin/bannertool, Standard ~/ctr-tools
#   APP_ART       nur Port mit EMBED_GAME=1: 1 = Icon, Banner und Banner-Ton aus Titelbild und
#                 Titelmelodie des Spiels (scripts/make_app_art.py, Standard), 0 = Vorgaben von ScummVM.
#                 Ohne eingebettete Spieldaten gelten immer die Vorgaben von ScummVM.
#
# Achtung: Mit EMBED_GAME=1 enthalten .3dsx und .cia das Spiel. Nur für den eigenen Gebrauch,
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

DIAG="${DIAG:-0}"
if [ "$DIAG" = 1 ]; then
  [ "$PORT" = 1 ] || { echo "DIAG=1 gibt es nur für den Port-Build" >&2; exit 1; }
  OUT=mausjagd-diag.3dsx
fi

CIA="${CIA:-0}"
if [ "$CIA" = 1 ]; then
  # Das normale ScummVM hätte die UniqueId des offiziellen CIA und würde es überschreiben
  [ "$PORT" = 1 ] || { echo "CIA=1 gibt es nur für den Port-Build" >&2; exit 1; }
  CTR_TOOLS="${CTR_TOOLS:-$HOME/ctr-tools}"
  CIA_TOOLS=(MAKEROM="$CTR_TOOLS/bin/makerom" BANNERTOOL="$CTR_TOOLS/bin/bannertool")
  for t in makerom bannertool; do
    [ -x "$CTR_TOOLS/bin/$t" ] || { echo "$t fehlt unter $CTR_TOOLS/bin (scripts/build-ctr-tools.sh)" >&2; exit 1; }
  done
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

ROMFS_EXTRA=()
EMBEDDED=0
if [ "$PORT" = 1 ] && [ "${EMBED_GAME:-1}" = 1 ]; then
  GAME_DIR="${GAME_DIR:-$REPO/game}"
  STAGE="$BUILD/romfs-extra/game"
  echo "=== Spieldaten laut docs/inventory.md nach $STAGE (geprüft)"
  python3 -I "$REPO/scripts/stage_game_data.py" "$GAME_DIR" "$REPO/docs/inventory.md" "$STAGE"
  ROMFS_EXTRA+=("$STAGE")
  EMBEDDED=1
  if [ "${APP_ART:-1}" = 1 ]; then
    # Icon, Banner und Banner-Ton aus dem Titelbild und der Titelmelodie des Spiels. Nur bei
    # eingebetteten Spieldaten: Dieser Build ist ohnehin nur für den eigenen Gebrauch (PLAN.md §7).
    ART="$BUILD/app-art"
    echo "=== App-Grafik aus den Spieldaten nach $ART"
    python3 -I "$REPO/scripts/make_app_art.py" "$GAME_DIR" "$ART"
    APP_VARS+=(APP_ICON="$ART/icon.png" APP_BANNER_IMAGE="$ART/banner.png" APP_BANNER_AUDIO="$ART/banner.wav")
  fi
fi
if [ "$DIAG" = 1 ]; then
  # Diagnosemodus, siehe backends/platform/3ds/mausjagd.h im Fork
  DIAG_FILE="$BUILD/romfs-extra/diag.txt"
  mkdir -p "$(dirname "$DIAG_FILE")"
  printf '# Diagnosemodus (scripts/build-3ds.sh DIAG=1), leer = Vorgabe im Code\n%s\n' "${DIAG_ARGS:-}" > "$DIAG_FILE"
  ROMFS_EXTRA+=("$DIAG_FILE")
  echo "=== Diagnosemodus: Optionen '${DIAG_ARGS:-<Vorgabe>}'"
fi
ROMFS_VARS=()
if [ ${#ROMFS_EXTRA[@]} -gt 0 ]; then
  ROMFS_VARS=(DIST_3DS_EXTRA_FILES="${ROMFS_EXTRA[*]}")
fi

# RomFS und SMDH immer neu erzeugen: make sieht Änderungen in Unterordnern bzw. an
# Titel/Beschreibung sonst nicht
rm -rf romfs scummvm.smdh scummvm.3dsx
make scummvm.3dsx "${APP_VARS[@]}" "${ROMFS_VARS[@]}"
if [ "$EMBEDDED" = 1 ]; then
  echo "RomFS-Spieldaten: $(find romfs/game -type f | wc -l) Dateien, $(du -sh romfs/game | cut -f1)"
fi

if [ "$CIA" = 1 ]; then
  # Gleiche RomFS und gleiches SMDH wie die .3dsx; Banner wie das Icon (siehe APP_ART)
  echo "=== CIA mit $REPO/config/mausjagd.rsf"
  rm -f scummvm.bnr scummvm.cia
  make scummvm.cia "${APP_VARS[@]}" "${ROMFS_VARS[@]}" "${CIA_TOOLS[@]}" \
    APP_RSF="$REPO/config/mausjagd.rsf"
fi

dist="$REPO/dist/3ds"
mkdir -p "$dist"
cp scummvm.3dsx "$dist/$OUT"
git -C "$SRC" rev-parse HEAD > "$dist/SCUMMVM_COMMIT.txt"
ls -la "$dist/$OUT"
if [ "$CIA" = 1 ]; then
  cp scummvm.cia "$dist/${OUT%.3dsx}.cia"
  ls -la "$dist/${OUT%.3dsx}.cia"
fi
echo "=== fertig: $dist/$OUT$([ "$CIA" = 1 ] && echo " und ${OUT%.3dsx}.cia")"
