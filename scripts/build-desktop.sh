#!/usr/bin/env bash
# Baut ScummVM mit nur der Director-Engine in WSL1 (Ubuntu), siehe docs/build-desktop.md.
#
#   bash scripts/build-desktop.sh linux    nativer Linux-Build (für Agenten-Tests ohne Fenster)
#   bash scripts/build-desktop.sh win64    MinGW-Cross-Build, Windows-EXE nach dist/scummvm-win64/
#   bash scripts/build-desktop.sh all      beides (Standard)
#
# Umgebungsvariablen (optional):
#   SCUMMVM_SRC   Quellcode, Standard ~/scummvm (Branch mausjagd)
#   BUILD_ROOT    Build-Ordner, Standard ~/build
#   MINGW_PREFIX  SDL2 für MinGW, Standard ~/mingw-prefix
#   JOBS          parallele Jobs, Standard nproc
#   RECONFIGURE=1 configure erzwingen
set -euo pipefail

SRC="${SCUMMVM_SRC:-$HOME/scummvm}"
BUILD="${BUILD_ROOT:-$HOME/build}"
MINGW_PREFIX="${MINGW_PREFIX:-$HOME/mingw-prefix}"
JOBS="${JOBS:-$(nproc)}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMON=(--disable-all-engines --enable-engine=director)
MINGW_HOST=x86_64-w64-mingw32

# ccache über die Masquerade-Links, falls vorhanden
if [ -d /usr/lib/ccache ]; then
  export PATH="/usr/lib/ccache:$PATH"
fi

log() { printf '\n=== %s\n' "$*"; }

need_configure() {
  [ "${RECONFIGURE:-0}" = 1 ] || [ ! -f config.mk ]
}

build_linux() {
  log "Linux-Build in $BUILD/linux"
  mkdir -p "$BUILD/linux"
  cd "$BUILD/linux"
  if need_configure; then
    "$SRC/configure" "${COMMON[@]}"
  fi
  make -j"$JOBS"
  log "fertig: $BUILD/linux/scummvm"
}

build_win64() {
  log "Windows-Build (MinGW) in $BUILD/win64"
  [ -x "$MINGW_PREFIX/bin/sdl2-config" ] || { echo "SDL2 für MinGW fehlt in $MINGW_PREFIX" >&2; exit 1; }
  mkdir -p "$BUILD/win64"
  cd "$BUILD/win64"
  # pkg-config darf nur die MinGW-Bibliotheken sehen, nicht die von Linux
  export PKG_CONFIG_LIBDIR="$MINGW_PREFIX/lib/pkgconfig"
  export PKG_CONFIG_PATH=
  if need_configure; then
    "$SRC/configure" --host="$MINGW_HOST" --with-sdl-prefix="$MINGW_PREFIX" "${COMMON[@]}"
  fi
  make -j"$JOBS"

  local dist="$REPO/dist/scummvm-win64"
  log "Distribution nach $dist"
  mkdir -p "$dist"
  "$MINGW_HOST-strip" scummvm.exe -o "$dist/scummvm.exe"
  # DLL-Abhängigkeiten aus dem MinGW-Sysroot bzw. dem SDL-Präfix mitkopieren
  local dll path
  for dll in $("$MINGW_HOST-objdump" -p scummvm.exe | awk '/DLL Name:/ {print $3}'); do
    for path in "$MINGW_PREFIX/bin/$dll" \
                "/usr/$MINGW_HOST/lib/$dll" \
                $(ls -d /usr/lib/gcc/$MINGW_HOST/*-posix/"$dll" 2>/dev/null); do
      if [ -f "$path" ]; then
        cp "$path" "$dist/"
        echo "  DLL: $dll"
        break
      fi
    done
  done
  # Portabler Modus: Konfiguration und Log bleiben neben der EXE (dist/ ist ignoriert)
  [ -f "$dist/scummvm.ini" ] || : > "$dist/scummvm.ini"
  cp "$SRC/COPYING" "$dist/COPYING.txt"
  git -C "$SRC" rev-parse HEAD > "$dist/SCUMMVM_COMMIT.txt"
  log "fertig: $dist/scummvm.exe"
}

case "${1:-all}" in
  linux) build_linux ;;
  win64) build_win64 ;;
  all)   build_linux; build_win64 ;;
  *)     echo "Aufruf: $0 [linux|win64|all]" >&2; exit 2 ;;
esac
