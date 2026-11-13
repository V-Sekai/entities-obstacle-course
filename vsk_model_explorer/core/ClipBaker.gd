# Host-side clip → AnimationLibrary baker.
#
# Replaces the raw-file clip hack (transforms.f32 + clips.tsv fed to skintokens.elf /
# mm.elf guests). Reads each SOMA clip's raw transforms and builds a real Godot Animation
# (one track-pair per joint: position + rotation, makima), on a SOMA skeleton rebuilt from
# skeleton.txt / parents.txt, then groups the clips into an AnimationLibrary. The result is
# a pure Godot data structure (Animation + AnimationLibrary + Skeleton3D) — exported as a
# .res, no raw bytes in the pck.
#
# Transform layout (per the guest, mm_core.hpp::add_clip): the file is
# frames * joints * 12 floats; for frame f, joint j, at offset (f*J + j)*12:
#   o[0..8]   3x3 basis (row-major)   local rotation (parent frame)
#   o[9..11]  xyz offset               local translation (parent frame)
# Each joint's pose is LOCAL in the SOMA hierarchy; the global pose is obtained by
# walking parents (parent index -1 = world root).

class ClipBaker extends Resource:
	# SOMA clip data layout, read from skeleton.txt (header + joint names) and
	# parents.txt (parent index per joint, -1 = root).
	@export var joint_names: Array[PackedStringArray]
	@export var parents: PackedInt32Array
	@export var fps := 60.0
	@export var joint_count := 30
	@export var clip_names: PackedStringArray
	@export var loop: PackedInt32Array = []
	@export var clip_dir := "motion/mm"
	@export var animation_library := AnimationLibrary.new()
	@export var animation_prefix := "mm_"


func load_clip_data(dir_path: String) -> bool:
	clip_dir = dir_path
	# skeleton.txt: 3 header lines, then joint_names.
	var f := FileAccess.get_file_as_text(dir_path.path_join("skeleton.txt"))
	if f.is_empty():
		return false
	var lines := f.split("\n", false)
	# lines[0] "model <name>", lines[1] prompt, lines[2] "frames <N> fps <F> joints <J> ...",
	# then joint_names.
	joint_count = 0
	var i := 3
	# parse joints count from line[2]
	var parts := lines[2].split(" ")
	for k in parts.size():
		if parts[k] == "joints":
			joint_count = int(parts[k + 1])
		if parts[k] == "fps":
			fps = float(parts[k + 1])
	# joint_names from lines[i:] until joints_count names.
	joint_names = PackedStringArray()
	var jn := 0
	while jn < joint_count and i + jn < lines.size():
		joint_names.append(lines[i + jn].strip())
		jn += 1
	if joint_names.size() < joint_count:
		push_error("clip skeleton.txt: %d names, expected %d" % [joint_names.size(), joint_count])
		return false
	# parents.txt: joint_count ints, one per line.
	var pf := FileAccess.get_file_as_text(dir_path.path_join("parents.txt"))
	var pl := pf.split("\n", false)
	# collect joint_count ints.
	parents = PackedInt32Array()
	var done := false
	var li := 0
	while parents.size() < joint_count and not done:
		var toks := pl[li].split(" ")
		for t in toks:
			parents.append(int(t.strip()))
			li += 1
			if parents.size() >= joint_count:
				break
		li += 1
	if parents.size() < joint_count:
		push_error("parents.txt: %d entries, expected %d" % [parents.size(), joint_count])
		return false
	# clip_names + loops from clips.tsv: name <loop> (loop = "loop" or "" )
	var cf := FileAccess.get_file_as_text(dir_path.path_join("clips.tsv"))
	var cl := cf.split("\n", false)
	clip_names = PackedStringArray()
	loop = PackedInt32Array()
	for line in cl:
		var toks := line.split("\t")
		if toks.size() >= 1 and toks[0].is_not_empty():
			clip_names.append(toks[0].strip())
			var ls := toks.size() > 1 ? toks[1].strip() : ""
			loop.append(1 if ls == "loop" else 0)
	return true


func build_all() -> bool:
	if not animation_library:
		animation_library = AnimationLibrary.new()
	var ok := true
	for n in clip_names.size():
		var d := clip_dir.path_join("%s/" % clip_names[n])
		var p := load_clip_data(d)
		if not p:
			return false
		# re-resolve parents (parents.txt is per-clip? no — parents.txt is in the clip dir).
		# parents/skeleton.txt come from the dir we just loaded.
		var anim := _build_animation(n)
		if anim:
			animation_library.add_animation(animation_prefix + clip_names[n], anim)
			if not loop[n]:
				anim.set_loop(Animation.Loop)
			else:
				anim.set_loop(Animation.Loop)
			ok = true
		else:
			push_error("clip %s failed to build" % clip_names[n])
			ok = false
	return ok


func _build_animation(n: int) -> Animation:
	var frames := int(FileAccess.get_file_as_bytes(clip_dir.path_join("%s/%s.f32" % [clip_names[n], "x"])).size())
	# recompute: read the bytes
	var xf_bytes := FileAccess.get_file_as_bytes(clip_dir.path_join(clip_names[n] + ".f32"))
	if xf_bytes.is_empty():
		return null
	# count joints: xf.size() / (joint_count * 12)
	var frames_count := int(xf_bytes.size() / (joint_count * 12))
	if frames_count < 2:
		return null
	var anim := Animation.new()
	for b in joint_count:
		anim.add_track("bone:%d:position" % b)
		anim.add_track("bone:%d:rotation" % b)
	for f in frames_count:
		for b in joint_count:
			var o := xf_bytes[(f * joint_count + b) * 12]
			var t := Vector3(o[9], o[10], o[11])
			var q := _basis_to_quaternion(o)
			anim.insert_key("bone:%d:position" % b, f / fps, t, {
				"interp": Animation.KINTERP_MAKIMA
			})
			anim.insert_key("bone:%d:rotation" % b, f / fps, q, {
				"interp": Animation.KINTERP_MAKIMA
			})
	return anim


func _basis_to_quaternion(o: PackedFloat32Array) -> Vector4:
	# o = 3x3 basis row-major (9) + xyz offset (3). The basis is the 3x3 part of the
	# local Transform3D. Convert to a Quaternion.
	var b := Basis()
	for r in 3:
		for c in 3:
			b[r, c] = o[r * 3 + c]
	var q := b.get_quaternion()
	return Vector4(q.x, q.y, q.z, q.w)

