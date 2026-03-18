#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/macos"
ICONSET_DIR="$BUILD_DIR/TgWsProxy.iconset"
ICNS_PATH="$BUILD_DIR/TgWsProxy.icns"
APP_PATH="$ROOT_DIR/dist/TgWsProxy.app"
BIN_PATH="$APP_PATH/Contents/MacOS/TgWsProxy"
ZIP_PATH="$ROOT_DIR/dist/TgWsProxy-macos-universal.zip"
VENV_DIR="$ROOT_DIR/.venv-macos-build"
PYTHON_BIN="${PYTHON_BIN:-python3}"

PYTHON_EXE="$("$PYTHON_BIN" -c 'import sys; print(sys.executable)')"
if [[ "$(uname -s)" == "Darwin" ]] && ! file "$PYTHON_EXE" | grep -q "universal binary"; then
  if file /usr/bin/python3 | grep -q "universal binary"; then
    PYTHON_BIN="/usr/bin/python3"
    PYTHON_EXE="/usr/bin/python3"
  fi
fi

mkdir -p "$BUILD_DIR"

rm -rf "$VENV_DIR"
"$PYTHON_BIN" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

if [[ "$(uname -s)" == "Darwin" ]]; then
  export ARCHFLAGS="-arch arm64 -arch x86_64"
  export CFLAGS="$ARCHFLAGS"
  export LDFLAGS="$ARCHFLAGS"
  export MACOSX_DEPLOYMENT_TARGET=11.0
  export _PYTHON_HOST_PLATFORM="macosx-11.0-universal2"
  export SDKROOT="$(xcrun --sdk macosx --show-sdk-path)"
fi

echo "Using build Python: $(python --version) [$PYTHON_EXE]"
python -m pip install --upgrade pip
python -m pip install \
  --no-binary cffi,Pillow,psutil \
  -r "$ROOT_DIR/requirements.txt" \
  "pyinstaller==6.13.0"

if command -v iconutil >/dev/null 2>&1; then
  if [[ ! -d "$ICONSET_DIR" || -z "$(find "$ICONSET_DIR" -maxdepth 1 -name '*.png' -print -quit 2>/dev/null)" ]]; then
    if [[ ! -f "$ROOT_DIR/icon.ico" ]]; then
      echo "Missing icon source: $ROOT_DIR/icon.ico" >&2
      exit 1
    fi
    rm -rf "$ICONSET_DIR"
    mkdir -p "$ICONSET_DIR"
    python3 - "$ROOT_DIR/icon.ico" "$ICONSET_DIR" <<'PY'
from pathlib import Path
import sys
from PIL import Image

src = Path(sys.argv[1])
iconset = Path(sys.argv[2])
img = Image.open(src).convert("RGBA")

for base in (16, 32, 128, 256, 512):
    for scale in (1, 2):
        size = base * scale
        resized = img.resize((size, size), Image.LANCZOS)
        suffix = "" if scale == 1 else "@2x"
        resized.save(iconset / f"icon_{base}x{base}{suffix}.png")
PY
  fi
  iconutil -c icns "$ICONSET_DIR" -o "$ICNS_PATH"
fi

rm -rf "$ROOT_DIR/build/pyinstaller" "$ROOT_DIR/dist"
pyinstaller "$ROOT_DIR/packaging/macos.spec" \
  --noconfirm \
  --clean \
  --workpath "$ROOT_DIR/build/pyinstaller"

if [[ ! -f "$BIN_PATH" ]]; then
  echo "Missing app binary: $BIN_PATH" >&2
  exit 1
fi

ARCHS="$(lipo -archs "$BIN_PATH")"
echo "Built architectures: $ARCHS"
if [[ "$ARCHS" != *"x86_64"* ]] || [[ "$ARCHS" != *"arm64"* ]]; then
  echo "Expected a universal binary containing x86_64 and arm64" >&2
  exit 1
fi

codesign --force --deep --sign - "$APP_PATH"
codesign --verify --deep --strict "$APP_PATH"
spctl --assess --type execute "$APP_PATH" || true

rm -f "$ZIP_PATH"
ditto -c -k --keepParent "$APP_PATH" "$ZIP_PATH"

echo "Built app: $APP_PATH"
echo "Built zip: $ZIP_PATH"
