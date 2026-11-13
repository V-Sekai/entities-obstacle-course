# All-Godot motion-matching data: build the clip AnimationLibrary from the raw clip transforms,
# so the clips live in Godot's own animation data structures (Animation / AnimationLibrary) and
# export into the pck — no more skintokens.elf baking the clips onto a GLB.
#
# Transform file layout (from the clip repo's add_clip: c.frames = xf.size() / (J * 12)):
#   frames * J * 12 floats, per frame, per bone (in `names` order): a local Transform3D =
#   basis 3x3 (9 floats) + local translation (3 floats, parent-relative).
# The root bone (parents[i] < 0) is world-space; the others are parent-relative.
# We feed those local transforms straight into Godot's per-bone position/rotation Animation
# tracks (makima), move the hips' floor travel to a root motion track, and loop per clip.
class_name MMClipLibraryBaker

@export var dir: String = "res://motion/mm"
const SKELETON := "skeleton.txt"
const PARENTS := "parents.txt"

# Root motion node, created as a sibling of the hips in the owner.
const ROOT := "MMRoot"
const HIPS := "pelvis"  # the hips bone (last in the skeleton order, per mm_core's `want.back()`)

var library: AnimationLibrary = null
var root_node_path: StringName = null  # set before build(); the AnimationPlayer's root_node
var bone_names: PackedStringArray = []
var parents: PackedInt32Array = null

func build() -> bool:
	var t = Dir.open(dir)
	if t == null:
		return false
	bone_names = t.get_contents()
	bone_names.erase("clips.tsv")  # not a bone
	var n: int = bone_names.size()
	var s: String = t.get(SKELETON)
	t.close()
	bone_names = s.split("\n")
	# Drop empty trailing lines.
	while bone_names.is_empty() or bone_names[bone_names.size() - 1] == "":
		bone_names.pop_back()
	bone_names.erase("")
	parents = _parents_from_file()
	if bone_names.size() == 0 or parents == null or parents.size() != bone_names.size():
		return false
	var clips: Array[String] = []
	t = Dir.open(dir)
	t = t if t else false
	return _add_all(t)

func _parents_from_file() -> PackedInt32Array:
	var f = File.new()
	var p = Path.join(dir, PARENTS)
	if not f.open_read(p):
		return null
	var t: String = f.read_all()
	f.close()
	var lines: Array[String] = t.split("\n")
	# Skip a possible header (bone names) line: parents are the joint indices, one per line.
	# Detect: if a line is all-integers, that's the parent array (header may be bone names).
	var ints: PackedInt32Array
	for l in lines:
		if l == "" or not _is_int(l):
			continue
		ints.append_int(l)
	return ints

func _is_int(s: String) -> bool:
	return s.matches_regex("-?[0-9]+")

func _add_all(t) -> bool:
	var clips: Array[String] = t.get_contents()
	clips.erase("clips.tsv")
	clips.erase("skeleton.txt")
	clips.erase("parents.txt")
	for f in clips:
		if f.ends_with(".tsv") or f.ends_with(".txt") or f.ends_with(".phase.f32") or f.ends_with(".f32"):
			var k := f
			k = k if not k.ends_with(".phase.f32") else k
		# one clip per base .f32 file name (clip names are the .f32 filenames)
		var base := f
		if base.ends_with(".phase.f32"):
			base = base.rsplit(".phase.f32", 1)[0]
		if base.ends_with(".f32"):
			if _add_clip(t, base):
				clips.erase(base)
	return true

func _add_clip(t, k: String) -> bool:
	var xf: PackedFloat32Array
	f = t.get(k + ".f32")
	if f == null:
		return false
	xf = f
	var J: int = bone_names.size()
	if xf.size() % (J * 12) != 0:
		return false
	var frames: int = int(xf.size() / (J * 12))
	# fps: read from the clip file's clip metadata, or default to 30.0 (the clips are 30fps).
	var anim := _build_animation(k, xf, frames, frames, 30.0, true)
	library.add_animation(k, anim)
	return true