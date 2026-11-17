# SPDX-FileCopyrightText: 2026 K. S. Ernest (iFire) Lee
#
# SPDX-License-Identifier: MIT
#
# Convert an imported FBX to a GLB with its skin kept, for the walk (it takes .glb and .vrm only).
#   godot --headless --path . --script tools/fbx_to_glb.gd -- res://avatar/maro/MarocchinoLP.fbx avatar/maro/MarocchinoLP.glb
extends SceneTree


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var packed := ResourceLoader.load(args[0]) as PackedScene
	if packed == null:
		printerr("FBX-FAIL cannot load ", args[0])
		quit(1)
		return
	var root := packed.instantiate()
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	var err := doc.append_from_scene(root, state)
	if err == OK:
		err = doc.write_to_filesystem(
			state, ProjectSettings.globalize_path("res://").path_join(args[1])
		)
	var skeletons := root.find_children("*", "Skeleton3D", true, false)
	print(
		(
			"FBX-GLB err=%d skeletons=%d bones=%d out=%s"
			% [
				err,
				skeletons.size(),
				(skeletons[0] as Skeleton3D).get_bone_count() if skeletons.size() > 0 else 0,
				args[1]
			]
		)
	)
	quit(0 if err == OK else 1)
