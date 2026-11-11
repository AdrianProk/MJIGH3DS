#!/usr/bin/env bash
# Baut makerom und bannertool aus dem Quellcode (WSL1/Ubuntu). Beide braucht nur das CIA,
# siehe docs/build-3ds.md. Dazu ctrtool, um ein fertiges CIA zu prüfen.
#
#   bash scripts/build-ctr-tools.sh   -> ~/ctr-tools/bin/{makerom,bannertool,ctrtool}
#
# Die Quellen kommen per git von GitHub, mit festem Tag; danach prüft das Skript den Commit.
# Netzwerkzugriff gibt es nur beim Klonen. Das optionale Ziel "update-libs" von bannertool
# (lädt Bibliotheken nach) wird nicht benutzt, die Bibliotheken liegen im Repo.
#
# Umgebungsvariablen (optional):
#   CTR_TOOLS_SRC  Quellordner, Standard ~/src/ctr-tools
#   CTR_TOOLS      Zielordner, Standard ~/ctr-tools (Binaries in bin/)
#   JOBS           parallele Jobs, Standard nproc
set -euo pipefail

SRC_ROOT="${CTR_TOOLS_SRC:-$HOME/src/ctr-tools}"
PREFIX="${CTR_TOOLS:-$HOME/ctr-tools}"
JOBS="${JOBS:-$(nproc)}"

MAKEROM_REPO=https://github.com/3DSGuy/Project_CTR.git
MAKEROM_TAG=makerom-v0.19.0
MAKEROM_COMMIT=e8f5f529c54ff9b22a2491a480ffa69206bf7b19
BANNERTOOL_REPO=https://github.com/carstene1ns/3ds-bannertool.git
BANNERTOOL_TAG=1.2.3
BANNERTOOL_COMMIT=da573b13418acd0ac1803b43b30e8a155e5f83e2

# fetch <ordner> <repo> <tag> <commit>: klonen (falls nötig) und Commit prüfen
fetch() {
  local dir="$SRC_ROOT/$1"
  if [ ! -d "$dir/.git" ]; then
    mkdir -p "$SRC_ROOT"
    git clone -q --depth 1 --branch "$3" "$2" "$dir"
  fi
  local head
  head="$(git -C "$dir" rev-parse HEAD)"
  [ "$head" = "$4" ] || { echo "$1: Commit $head, erwartet $4 ($3)" >&2; exit 1; }
  [ -z "$(git -C "$dir" status --porcelain --untracked-files=no)" ] \
    || { echo "$1: geänderte Dateien im Quellordner" >&2; exit 1; }
  echo "=== $1 $3 ($head)"
}

fetch Project_CTR "$MAKEROM_REPO" "$MAKEROM_TAG" "$MAKEROM_COMMIT"
fetch 3ds-bannertool "$BANNERTOOL_REPO" "$BANNERTOOL_TAG" "$BANNERTOOL_COMMIT"

# makerom: eigenes Makefile, Abhängigkeiten (mbedtls, libyaml, libblz) liegen im Repo
MR="$SRC_ROOT/Project_CTR/makerom"
make -C "$MR" deps -j"$JOBS"
make -C "$MR" -j"$JOBS"
# ctrtool aus demselben Commit (Tag ctrtool-v1.3.0): zeigt Title-ID und Rechte eines CIA
CT="$SRC_ROOT/Project_CTR/ctrtool"
make -C "$CT" deps -j"$JOBS"
make -C "$CT" -j"$JOBS"

# bannertool: CMakeLists.txt von Hand nachgebildet (kein cmake nötig). Die Defines der
# Bibliotheken gelten dort nur für die Nutzer (INTERFACE), nicht für die Bibliotheken selbst.
BT="$SRC_ROOT/3ds-bannertool"
BTB="$SRC_ROOT/build-bannertool"
rm -rf "$BTB"
mkdir -p "$BTB"
CXX="${CXX:-g++}"
CXXFLAGS=(-std=c++17 -O2)
for lib in stb_image stb_vorbis dr_wav; do
  "$CXX" "${CXXFLAGS[@]}" -c "$BT/source/pc/$lib.cpp" -o "$BTB/$lib.o"
done
"$CXX" "${CXXFLAGS[@]}" -Wall -Wextra -DVERSION='"1.2.3"' \
  -DSTBI_ONLY_PNG -DSTBI_NO_LINEAR -DSTBI_NO_STDIO \
  -DSTB_VORBIS_NO_PUSHDATA_API -DSTB_VORBIS_NO_STDIO -DDR_WAV_NO_STDIO \
  -I"$BT/source" -I"$BT/source/pc" \
  "$BT"/source/*.cpp "$BT"/source/3ds/*.cpp \
  "$BTB"/stb_image.o "$BTB"/stb_vorbis.o "$BTB"/dr_wav.o \
  -o "$BTB/bannertool"

mkdir -p "$PREFIX/bin"
install -m 755 "$MR/bin/makerom" "$PREFIX/bin/makerom"
install -m 755 "$CT/bin/ctrtool" "$PREFIX/bin/ctrtool"
install -m 755 "$BTB/bannertool" "$PREFIX/bin/bannertool"
cat > "$PREFIX/SOURCES.txt" <<EOF
makerom    $MAKEROM_REPO $MAKEROM_TAG $MAKEROM_COMMIT
ctrtool    $MAKEROM_REPO ctrtool-v1.3.0 $MAKEROM_COMMIT
bannertool $BANNERTOOL_REPO $BANNERTOOL_TAG $BANNERTOOL_COMMIT
EOF
"$PREFIX/bin/makerom" 2>&1 | head -2 || true
"$PREFIX/bin/ctrtool" 2>&1 | head -1 || true
"$PREFIX/bin/bannertool" 2>&1 | head -2 || true
sha256sum "$PREFIX/bin/makerom" "$PREFIX/bin/ctrtool" "$PREFIX/bin/bannertool"
echo "=== fertig: $PREFIX/bin"
