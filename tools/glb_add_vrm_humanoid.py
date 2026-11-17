#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 K. S. Ernest (iFire) Lee
#
# SPDX-License-Identifier: MIT
"""Add the VRM 1.0 humanoid bone map and licence metadata to a rigged GLB, from a Unity .fbx.meta humanDescription.
The walk's retargeter (skintokens.elf) maps SOMA onto a model by these roles; without them it falls back to matching
the skeleton's shape, which refuses a root with more than a trunk and two legs (Maro has tail-side Butt bones).
    tools/glb_add_vrm_humanoid.py IN.glb Marocchino.fbx.meta OUT.glb
Exit 0 on success; exits 1 and writes nothing when a required bone has no node."""
import json, re, struct, sys

# Unity humanName -> VRM 1.0 humanBones key. VRM 1.0 renamed the thumb: Unity's Proximal is VRM's Metacarpal.
BODY = {
    "Hips": "hips", "Spine": "spine", "Chest": "chest", "UpperChest": "upperChest", "Neck": "neck", "Head": "head",
    "LeftEye": "leftEye", "RightEye": "rightEye", "Jaw": "jaw",
    "LeftShoulder": "leftShoulder", "RightShoulder": "rightShoulder",
    "LeftUpperArm": "leftUpperArm", "RightUpperArm": "rightUpperArm",
    "LeftLowerArm": "leftLowerArm", "RightLowerArm": "rightLowerArm",
    "LeftHand": "leftHand", "RightHand": "rightHand",
    "LeftUpperLeg": "leftUpperLeg", "RightUpperLeg": "rightUpperLeg",
    "LeftLowerLeg": "leftLowerLeg", "RightLowerLeg": "rightLowerLeg",
    "LeftFoot": "leftFoot", "RightFoot": "rightFoot", "LeftToes": "leftToes", "RightToes": "rightToes",
}
FINGER = {"Thumb": "Thumb", "Index": "Index", "Middle": "Middle", "Ring": "Ring", "Little": "Little"}
SEGMENT = {"Proximal": "Proximal", "Intermediate": "Intermediate", "Distal": "Distal"}
REQUIRED = ["hips", "spine", "head", "leftUpperArm", "leftLowerArm", "leftHand", "rightUpperArm", "rightLowerArm",
            "rightHand", "leftUpperLeg", "leftLowerLeg", "leftFoot", "rightUpperLeg", "rightLowerLeg", "rightFoot"]


def vrm_key(human: str):
    if human in BODY:
        return BODY[human]
    m = re.fullmatch(r"(Left|Right) (Thumb|Index|Middle|Ring|Little) (Proximal|Intermediate|Distal)", human)
    if not m:
        return None
    side, finger, seg = m.group(1).lower(), m.group(2), m.group(3)
    if finger == "Thumb":
        seg = {"Proximal": "Metacarpal", "Intermediate": "Proximal", "Distal": "Distal"}[seg]
    return f"{side}{finger}{seg}"


def main(src: str, meta: str, dst: str) -> int:
    g = open(src, "rb").read()
    jlen = struct.unpack("<I", g[12:16])[0]
    doc = json.loads(g[20:20 + jlen])
    rest = g[20 + jlen:]
    node_of = {n.get("name"): i for i, n in enumerate(doc["nodes"])}
    text = open(meta, encoding="utf-8").read()
    pairs = re.findall(r"- boneName: (.+)\n\s+humanName: (.+)", text[text.find("human:"):])
    bones = {}
    for bone, human in pairs:
        key = vrm_key(human.strip())
        node = node_of.get(bone.strip().replace(".", "_"))
        if key and node is not None:
            bones[key] = {"node": node}
    missing = [k for k in REQUIRED if k not in bones]
    if missing:
        print("missing required bones:", missing, file=sys.stderr)
        return 1
    doc.setdefault("extensions", {})["VRMC_vrm"] = {
        "specVersion": "1.0",
        "meta": {
            "name": "Marocchino (Maro)", "version": "1", "authors": ["Mohka Noir"],
            "copyrightInformation": "Marocchino, free original 3D model by Mohka Noir (Cafemohka)",
            "contactInformation": "https://cafemohka.booth.pm/",
            "references": ["https://github.com/chibifire-stages/character-marocchino"],
            "licenseUrl": "https://vrm.dev/licenses/1.0/", "avatarPermission": "everyone",
            "allowExcessivelyViolentUsage": False, "allowExcessivelySexualUsage": False,
            "commercialUsage": "corporation", "allowPoliticalOrReligiousUsage": False,
            "allowAntisocialOrHateUsage": False, "creditNotation": "required", "allowRedistribution": True,
            "modification": "allowModificationRedistribution",
            "otherLicenseUrl": "https://www.apache.org/licenses/LICENSE-2.0",
        },
        "humanoid": {"humanBones": bones},
    }
    used = doc.setdefault("extensionsUsed", [])
    if "VRMC_vrm" not in used:
        used.append("VRMC_vrm")
    body = json.dumps(doc, separators=(",", ":")).encode()
    body += b" " * (-len(body) % 4)
    out = b"glTF" + struct.pack("<II", 2, 12 + 8 + len(body) + len(rest)) + struct.pack("<I", len(body)) + b"JSON" + body + rest
    open(dst, "wb").write(out)
    print(f"VRM-HUMANOID bones={len(bones)} out={dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]) if len(sys.argv) == 4 else print(__doc__) or 2)
