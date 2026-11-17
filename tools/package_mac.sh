#!/bin/sh
# SPDX-FileCopyrightText: 2026 K. S. Ernest (iFire) Lee
#
# SPDX-License-Identifier: MIT
#
# Package the obstacle course as a macOS arm64 app: the project's .pck, the engine's template_release binary and
# libfdb_c.dylib in a bundle, an ad-hoc signature, a zip. The guest ELFs and the clips must already be in the project
# (tools/fetch_guest_assets.sh) and the project imported once (godot --headless --import --path .).
#   ENGINE_DIR=<dir with godot.macos.editor.double.arm64, godot.macos.template_release.double.arm64, libfdb_c.dylib> \
#     tools/package_mac.sh <out dir> <version>
set -eu
out=$1 version=$2
here=$(cd "$(dirname "$0")/.." && pwd)
eng=${ENGINE_DIR:?set ENGINE_DIR}
app="$out/Obstacle Course.app"
rm -rf "$app" "$out/ObstacleCourse.pck"
mkdir -p "$out" "$app/Contents/MacOS" "$app/Contents/Resources" "$app/Contents/Frameworks"
"$eng/godot.macos.editor.double.arm64" --headless --path "$here" --export-pack "Mac" "$out/ObstacleCourse.pck"
cp "$eng/godot.macos.template_release.double.arm64" "$app/Contents/MacOS/ObstacleCourse"
cp "$eng/libfdb_c.dylib" "$app/Contents/Frameworks/"
# codesign takes every file in MacOS/ for code, so the pack sits in Resources/
cp "$out/ObstacleCourse.pck" "$app/Contents/Resources/"
cp "$here/LICENSE" "$here/NOTICE" "$here/README.md" "$app/Contents/Resources/"
cp -R "$here/LICENSES" "$app/Contents/Resources/LICENSES"
mkdir -p "$app/Contents/Resources/avatar-maro"
cp "$here/avatar/maro/LICENSE" "$here/avatar/maro/CITATION.cff" "$app/Contents/Resources/avatar-maro/"
cp -R "$here/avatar/maro/readme" "$app/Contents/Resources/avatar-maro/readme"
cat > "$app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>ObstacleCourse</string>
<key>CFBundleIdentifier</key><string>dev.vsekai.obstaclecourse</string>
<key>CFBundleName</key><string>Obstacle Course</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleShortVersionString</key><string>$version</string>
<key>CFBundleVersion</key><string>$version</string>
<key>LSMinimumSystemVersion</key><string>12.0</string>
<key>NSHighResolutionCapable</key><true/>
</dict></plist>
EOF
codesign --force --deep -s - "$app/Contents/Frameworks/libfdb_c.dylib"
codesign --force --deep -s - "$app"
codesign --verify --deep --strict "$app"
rm -f "$out/ObstacleCourse-macos-arm64.zip"
ditto -c -k --keepParent "$app" "$out/ObstacleCourse-macos-arm64.zip"
shasum -a 256 "$out/ObstacleCourse-macos-arm64.zip"
