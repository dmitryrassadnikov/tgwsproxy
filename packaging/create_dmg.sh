#!/bin/bash
# Create a DMG installer for TG WS Proxy macOS app
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_DIR/dist"

APP_NAME="TG WS Proxy"
DMG_NAME="TgWsProxy"

if [ ! -d "$DIST_DIR/$APP_NAME.app" ]; then
    echo "Error: $DIST_DIR/$APP_NAME.app not found"
    echo "Build the app first:"
    echo "  pyinstaller packaging/macos.spec --noconfirm"
    exit 1
fi

# Create temp dir for DMG contents
DMG_TEMP="$DIST_DIR/dmg_temp"
rm -rf "$DMG_TEMP"
mkdir -p "$DMG_TEMP"

# Copy app bundle
cp -R "$DIST_DIR/$APP_NAME.app" "$DMG_TEMP/"

# Create symlink to /Applications for drag-and-drop install
ln -s /Applications "$DMG_TEMP/Applications"

# Create DMG
hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$DMG_TEMP" \
    -ov \
    -format UDZO \
    "$DIST_DIR/$DMG_NAME.dmg"

# Cleanup
rm -rf "$DMG_TEMP"

echo ""
echo "DMG created: $DIST_DIR/$DMG_NAME.dmg"
