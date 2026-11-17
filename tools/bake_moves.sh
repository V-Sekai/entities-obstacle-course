#!/bin/sh
# SPDX-FileCopyrightText: 2026 K. S. Ernest (iFire) Lee
#
# SPDX-License-Identifier: MIT
#
# Bake the motion-matching clips onto the default avatar once, at build time, so the app opens it already walking:
# a walk-mode test run writes <name>.moves.glb into the app's user data; this copies it into the project as the
# default avatar and marks it "keep" so the export ships the file as it is.
#   ENGINE_DIR=<dir with godot.macos.editor.double.arm64> tools/bake_moves.sh
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
eng=${ENGINE_DIR:?set ENGINE_DIR}
rm -f "$HOME"/Library/Application\ Support/Godot/app_userdata/*/moves/Maro.moves.glb
MOVE_STEPS=walk "$eng/godot.macos.editor.double.arm64" --path "$here" -- "$here/avatar/maro/Maro.glb" --move-quit | grep -E "^MOVE-(BAKE|STEP|FAIL)"
baked=$(ls -t "$HOME"/Library/Application\ Support/Godot/app_userdata/*/moves/Maro.moves.glb | head -1)
cp "$baked" "$here/avatar/maro/Maro.moves.glb"
cat > "$here/avatar/maro/Maro.moves.glb.import" <<'IMP'
[remap]

importer="keep"
IMP
ls -l "$here/avatar/maro/Maro.moves.glb" | awk '{printf "BAKED %.1f MB\n", $5/1048576}'
