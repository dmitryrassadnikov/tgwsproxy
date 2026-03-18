#!/bin/bash
# Merge arm64 and x86_64 .app bundles into a universal2 .app and create DMG
set -e

ARM_APP="$1"
INTEL_APP="$2"
OUT_APP="$3"

if [ -z "$ARM_APP" ] || [ -z "$INTEL_APP" ] || [ -z "$OUT_APP" ]; then
    echo "Usage: $0 <arm64.app> <x86_64.app> <output.app>"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_DIR/dist"
APP_NAME="$(basename "$OUT_APP" .app)"
DMG_NAME="TgWsProxy"

# --- Merge ---

echo "Merging '$ARM_APP' + '$INTEL_APP' -> '$OUT_APP'"

rm -rf "$OUT_APP"
cp -R "$ARM_APP" "$OUT_APP"

find "$OUT_APP" -type f | while read -r file; do
    rel="${file#"$OUT_APP"/}"
    intel_file="$INTEL_APP/$rel"

    [ -f "$intel_file" ] || continue

    if file "$file" | grep -qE "Mach-O (64-bit )?executable|Mach-O (64-bit )?dynamically linked|Mach-O (64-bit )?bundle"; then
        arm_arch=$(lipo -archs "$file" 2>/dev/null || echo "")
        intel_arch=$(lipo -archs "$intel_file" 2>/dev/null || echo "")
        if [ "$arm_arch" = "$intel_arch" ]; then
            # same arch (e.g. local test with two arm64 copies) — skip
            continue
        fi
        lipo -create "$file" "$intel_file" -output "$file"
    fi
done

echo "Merge done: $OUT_APP"

# --- Create DMG ---

DMG_TEMP="$DIST_DIR/dmg_temp"
rm -rf "$DMG_TEMP"
mkdir -p "$DMG_TEMP"

cp -R "$OUT_APP" "$DMG_TEMP/"
ln -s /Applications "$DMG_TEMP/Applications"

hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$DMG_TEMP" \
    -ov \
    -format UDZO \
    "$DIST_DIR/$DMG_NAME.dmg"

rm -rf "$DMG_TEMP"

echo "DMG created: $DIST_DIR/$DMG_NAME.dmg"
