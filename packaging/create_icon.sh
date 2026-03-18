#!/bin/bash
# Create icon.icns from icon.ico for macOS app
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

python3 -c "
from PIL import Image
img = Image.open('$PROJECT_DIR/icon.ico')
img = img.resize((1024, 1024), Image.LANCZOS)
img.save('$PROJECT_DIR/icon_1024.png', 'PNG')
"

mkdir -p "$PROJECT_DIR/icon.iconset"
sips -z 16 16     "$PROJECT_DIR/icon_1024.png" --out "$PROJECT_DIR/icon.iconset/icon_16x16.png"
sips -z 32 32     "$PROJECT_DIR/icon_1024.png" --out "$PROJECT_DIR/icon.iconset/icon_16x16@2x.png"
sips -z 32 32     "$PROJECT_DIR/icon_1024.png" --out "$PROJECT_DIR/icon.iconset/icon_32x32.png"
sips -z 64 64     "$PROJECT_DIR/icon_1024.png" --out "$PROJECT_DIR/icon.iconset/icon_32x32@2x.png"
sips -z 128 128   "$PROJECT_DIR/icon_1024.png" --out "$PROJECT_DIR/icon.iconset/icon_128x128.png"
sips -z 256 256   "$PROJECT_DIR/icon_1024.png" --out "$PROJECT_DIR/icon.iconset/icon_128x128@2x.png"
sips -z 256 256   "$PROJECT_DIR/icon_1024.png" --out "$PROJECT_DIR/icon.iconset/icon_256x256.png"
sips -z 512 512   "$PROJECT_DIR/icon_1024.png" --out "$PROJECT_DIR/icon.iconset/icon_256x256@2x.png"
sips -z 512 512   "$PROJECT_DIR/icon_1024.png" --out "$PROJECT_DIR/icon.iconset/icon_512x512.png"
sips -z 1024 1024 "$PROJECT_DIR/icon_1024.png" --out "$PROJECT_DIR/icon.iconset/icon_512x512@2x.png"
iconutil -c icns "$PROJECT_DIR/icon.iconset" -o "$PROJECT_DIR/icon.icns"

rm -rf "$PROJECT_DIR/icon.iconset" "$PROJECT_DIR/icon_1024.png"

echo "icon.icns created: $PROJECT_DIR/icon.icns"
