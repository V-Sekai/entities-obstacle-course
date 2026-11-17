#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 K. S. Ernest (iFire) Lee
#
# SPDX-License-Identifier: MIT
"""Normalise a rigged GLB: Y-up, metres, and optionally a given height, with no scale or rotation on the skeleton's parent node.

An FBX import leaves the unit scale (here 100) and the Z-up turn (-90 degrees about X) on the Armature node. The
retargeter reads the skeleton's own numbers, so it sees a rig in the wrong units and guesses a scale. This bakes the
Armature's rotation and a uniform scale into the bones, the vertices, normals, tangents, morph targets and the inverse
bind matrices, and sets the Armature to identity, so the file means what it says.
    tools/glb_normalize.py IN.glb OUT.glb [HEIGHT_M] [--t-pose]   (no height: keep the model's own size)
Checks before writing: at bind pose every joint times its inverse bind matrix is the identity. Exit 1 when it is not."""
import json, struct, sys
import numpy as np

COMP = {5126: np.float32, 5123: np.uint16, 5121: np.uint8, 5125: np.uint32}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def quat_to_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return [aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz]


def trs(node):
    m = np.eye(4)
    if "matrix" in node:
        return np.array(node["matrix"]).reshape(4, 4).T
    s = node.get("scale", [1, 1, 1])
    m[:3, :3] = quat_to_mat(node.get("rotation", [0, 0, 0, 1])) @ np.diag(s)
    m[:3, 3] = node.get("translation", [0, 0, 0])
    return m


class Glb:
    def __init__(self, path):
        g = open(path, "rb").read()
        jl = struct.unpack("<I", g[12:16])[0]
        self.doc = json.loads(g[20:20 + jl])
        bl = struct.unpack("<I", g[20 + jl:24 + jl])[0]
        self.bin = bytearray(g[28 + jl:28 + jl + bl])
        self.parent = {c: i for i, n in enumerate(self.doc["nodes"]) for c in n.get("children", [])}

    def view(self, ai):
        a = self.doc["accessors"][ai]
        bv = self.doc["bufferViews"][a["bufferView"]]
        n, k = a["count"], NCOMP[a["type"]]
        dt = np.dtype(COMP[a["componentType"]])
        stride = bv.get("byteStride") or k * dt.itemsize
        base = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        assert "sparse" not in a, "sparse accessors are not handled"
        raw = np.frombuffer(self.bin, dtype=np.uint8)
        idx = base + np.arange(n)[:, None] * stride + np.arange(k * dt.itemsize)[None, :]
        return a, dt, k, idx, raw

    def read(self, ai):
        a, dt, k, idx, raw = self.view(ai)
        return raw[idx].copy().view(dt).reshape(a["count"], k)

    def write(self, ai, arr):
        a, dt, k, idx, _ = self.view(ai)
        raw = np.frombuffer(self.bin, dtype=np.uint8)
        arr = np.ascontiguousarray(arr.astype(dt).reshape(a["count"], k))
        raw_w = np.frombuffer(self.bin, dtype=np.uint8)
        # frombuffer on a bytearray is writable
        raw_w[idx] = arr.view(np.uint8).reshape(a["count"], k * dt.itemsize)
        if a["type"] == "VEC3" and a["componentType"] == 5126 and "min" in a:
            a["min"], a["max"] = arr.min(0).tolist(), arr.max(0).tolist()

    def global_of(self, i, nodes=None):
        nodes = nodes or self.doc["nodes"]
        m = trs(nodes[i])
        while i in self.parent:
            i = self.parent[i]
            m = trs(nodes[i]) @ m
        return m

    def save(self, path):
        body = json.dumps(self.doc, separators=(",", ":")).encode()
        body += b" " * (-len(body) % 4)
        b = bytes(self.bin) + b"\0" * (-len(self.bin) % 4)
        self.doc["buffers"][0]["byteLength"] = len(b)
        body = json.dumps(self.doc, separators=(",", ":")).encode()
        body += b" " * (-len(body) % 4)
        total = 12 + 8 + len(body) + 8 + len(b)
        open(path, "wb").write(b"glTF" + struct.pack("<II", 2, total) + struct.pack("<I", len(body)) + b"JSON" + body
                               + struct.pack("<I", len(b)) + b"BIN\0" + b)


def bind_error(glb):
    """Largest |J * IBM - M| over the skin's joints, where M is the identity for a normalised file."""
    skin = glb.doc["skins"][0]
    ibm = glb.read(skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    return [glb.global_of(j) @ ibm[n] for n, j in enumerate(skin["joints"])]


def mat_to_quat(m):
    t = m[0, 0] + m[1, 1] + m[2, 2]
    if t > 0:
        r = np.sqrt(1 + t) * 2
        q = [(m[2, 1] - m[1, 2]) / r, (m[0, 2] - m[2, 0]) / r, (m[1, 0] - m[0, 1]) / r, r / 4]
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        r = np.sqrt(1 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        q = [r / 4, (m[0, 1] + m[1, 0]) / r, (m[0, 2] + m[2, 0]) / r, (m[2, 1] - m[1, 2]) / r]
    elif m[1, 1] > m[2, 2]:
        r = np.sqrt(1 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        q = [(m[0, 1] + m[1, 0]) / r, r / 4, (m[1, 2] + m[2, 1]) / r, (m[0, 2] - m[2, 0]) / r]
    else:
        r = np.sqrt(1 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        q = [(m[0, 2] + m[2, 0]) / r, (m[1, 2] + m[2, 1]) / r, r / 4, (m[1, 0] - m[0, 1]) / r]
    q = np.array(q, dtype=np.float64)
    return (q / np.linalg.norm(q)).tolist()


def rotation_between(a, b):
    """The rotation matrix that turns unit vector a onto unit vector b."""
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-12:
        return np.eye(3)
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k * (1 / (1 + c))


def weights_of(glb, prim):
    """(joints (n, 8) int, weights (n, 8) float) from JOINTS_0/1 and WEIGHTS_0/1, normalised-integer weights read as floats."""
    def get(name):
        ai = prim["attributes"].get(name)
        if ai is None:
            return None
        a = glb.doc["accessors"][ai]
        arr = glb.read(ai).astype(np.float64)
        if a.get("normalized"):
            arr = arr / {5121: 255.0, 5123: 65535.0}[a["componentType"]]
        return arr
    j = [get("JOINTS_0"), get("JOINTS_1")]
    w = [get("WEIGHTS_0"), get("WEIGHTS_1")]
    j = np.concatenate([x for x in j if x is not None], axis=1).astype(np.int64)
    w = np.concatenate([x for x in w if x is not None], axis=1)
    return j, w


def t_pose(glb, report=True):
    """Rotate each arm, about its upper-arm joint, until the upper arm to hand direction is horizontal (a T-pose), and
    bake that into the mesh by skinning, so the surface is unchanged and only the rest pose moves. Needs the VRM
    humanoid map (leftUpperArm, leftHand and the right ones). Returns the largest bind error afterwards."""
    doc = glb.doc
    nodes = doc["nodes"]
    skin = doc["skins"][0]
    hb = doc["extensions"]["VRMC_vrm"]["humanoid"]["humanBones"]
    old = {j: glb.global_of(j) for j in skin["joints"]}
    moved = {}
    for side in ("left", "right"):
        upper, hand = hb[f"{side}UpperArm"]["node"], hb[f"{side}Hand"]["node"]
        v = old[hand][:3, 3] - old[upper][:3, 3]
        v = v / np.linalg.norm(v)
        t = np.array([v[0], 0.0, v[2]])
        t = t / np.linalg.norm(t)
        R = rotation_between(v, t)  # world rotation about the upper arm joint
        parent = glb.parent[upper]
        Pr = glb.global_of(parent)[:3, :3]
        Lo = quat_to_mat(nodes[upper].get("rotation", [0, 0, 0, 1]))
        nodes[upper]["rotation"] = mat_to_quat((Pr.T @ R @ Pr) @ Lo)
        moved[side] = float(np.degrees(np.arccos(np.clip(np.dot(v, t), -1, 1))))
    new = {j: glb.global_of(j) for j in skin["joints"]}
    S = [new[j] @ np.linalg.inv(old[j]) for j in skin["joints"]]  # skinning matrix of each joint: old rest -> new rest
    S = np.array(S)
    prim = doc["meshes"][0]["primitives"][0]
    J, W = weights_of(glb, prim)
    W = W / W.sum(1, keepdims=True)
    blend = np.einsum("nk,nkab->nab", W, S[J])  # per-vertex blended 4x4
    R3 = blend[:, :3, :3]

    def apply(ai, mat_fn):
        arr = glb.read(ai).astype(np.float64)
        out = mat_fn(arr[:, :3])
        glb.write(ai, np.concatenate([out, arr[:, 3:]], axis=1) if arr.shape[1] == 4 else out)

    apply(prim["attributes"]["POSITION"], lambda p: np.einsum("nab,nb->na", blend[:, :3, :3], p) + blend[:, :3, 3])
    for name in ("NORMAL", "TANGENT"):
        if name in prim["attributes"]:
            def f(x):
                y = np.einsum("nab,nb->na", R3, x)
                return y / np.linalg.norm(y, axis=1, keepdims=True).clip(1e-12)
            apply(prim["attributes"][name], f)
    for target in prim.get("targets", []):
        for name, ai in target.items():
            a = doc["accessors"][ai]
            if "sparse" in a:
                sp = a["sparse"]
                ib = doc["bufferViews"][sp["indices"]["bufferView"]]
                off = ib.get("byteOffset", 0) + sp["indices"].get("byteOffset", 0)
                dt = np.dtype(COMP[sp["indices"]["componentType"]])
                idx = np.frombuffer(glb.bin, dtype=dt, count=sp["count"], offset=off).astype(np.int64)
                vb = doc["bufferViews"][sp["values"]["bufferView"]]
                voff = vb.get("byteOffset", 0) + sp["values"].get("byteOffset", 0)
                vals = np.frombuffer(glb.bin, dtype=np.float32, count=sp["count"] * 3, offset=voff).reshape(-1, 3).astype(np.float64)
                out = np.einsum("nab,nb->na", R3[idx], vals)
                if name == "NORMAL" or name == "TANGENT":
                    pass
                np.frombuffer(glb.bin, dtype=np.float32, count=sp["count"] * 3, offset=voff)[:] = out.astype(np.float32).reshape(-1)
                a.pop("min", None)
                a.pop("max", None)
            elif "bufferView" in a:
                apply(ai, lambda d: np.einsum("nab,nb->na", R3, d))
    glb.write(skin["inverseBindMatrices"], np.array([np.linalg.inv(new[j]).T.reshape(16) for j in skin["joints"]]))
    err = max(np.abs(m - np.eye(4)).max() for m in bind_error(glb))
    if report:
        print(f"T-POSE raised left {moved['left']:.1f} deg, right {moved['right']:.1f} deg, bind_err={err:.2g}")
    return err


def main(src, dst, height=0.0, make_t_pose=False):
    glb = Glb(src)
    doc = glb.doc
    nodes = doc["nodes"]
    skin = doc["skins"][0]
    joint_set = set(skin["joints"])
    root_joints = [j for j in skin["joints"] if glb.parent.get(j) not in joint_set]
    arm = glb.parent[root_joints[0]]
    A = trs(nodes[arm])
    # The mesh's place in the world is M = J * IBM, the same for every joint: here a turn and a uniform scale. The
    # bones' own scale (the Armature's) may differ from it; both are baked separately.
    ms = bind_error(glb)
    spread = max(np.abs(m - ms[0]).max() for m in ms)
    M = ms[0]
    s_mesh = float(np.linalg.norm(M[:3, 0]))
    s_bones = float(np.linalg.norm(A[:3, 0]))
    rot = M[:3, :3] / s_mesh
    if spread > 1e-3 or np.abs(rot - A[:3, :3] / s_bones).max() > 1e-4:
        print(f"unexpected bind pose: spread {spread:.3g}, turn differs from the Armature's", file=sys.stderr)
        return 1
    prim = doc["meshes"][0]["primitives"][0]
    up = (glb.read(prim["attributes"]["POSITION"]) @ rot.T)[:, 1] * s_mesh
    f = height / float(up.max() - up.min()) if height else 1.0  # optional uniform resize to HEIGHT metres

    def transform(ai, mat):
        a = doc["accessors"][ai]
        if "bufferView" in a:
            arr = glb.read(ai).astype(np.float64)
            out = arr[:, :3] @ mat.T
            glb.write(ai, np.concatenate([out, arr[:, 3:]], axis=1) if arr.shape[1] == 4 else out)
        if "sparse" in a:  # the deltas of a morph target are stored for the vertices that move; a linear map keeps the rest at zero
            sv = a["sparse"]["values"]
            bv = doc["bufferViews"][sv["bufferView"]]
            k = NCOMP[a["type"]]
            off = bv.get("byteOffset", 0) + sv.get("byteOffset", 0)
            vals = np.frombuffer(glb.bin, dtype=np.float32, count=a["sparse"]["count"] * k, offset=off).reshape(-1, k).astype(np.float64)
            out = vals[:, :3] @ mat.T
            out = np.concatenate([out, vals[:, 3:]], axis=1) if k == 4 else out
            np.frombuffer(glb.bin, dtype=np.float32, count=a["sparse"]["count"] * k, offset=off)[:] = out.astype(np.float32).reshape(-1)
            a.pop("min", None)
            a.pop("max", None)

    for name, ai in prim["attributes"].items():
        if name == "POSITION":
            transform(ai, rot * s_mesh * f)
        elif name in ("NORMAL", "TANGENT"):
            transform(ai, rot)
    for target in prim.get("targets", []):
        for name, ai in target.items():
            transform(ai, rot * s_mesh * f if name == "POSITION" else rot)
    # Every joint, and every node hanging under one, is local: only translations change. The skeleton roots take the turn.
    below = {i for i in range(len(nodes)) if any(p in joint_set for p in _ancestors(glb, i))} | joint_set
    for i in below:
        if "translation" in nodes[i]:
            nodes[i]["translation"] = (np.array(nodes[i]["translation"], dtype=np.float64) * s_bones * f).tolist()
    q_arm = [float(v) for v in nodes[arm].get("rotation", [0, 0, 0, 1])]
    for r in root_joints:
        n = nodes[r]
        n["rotation"] = qmul(q_arm, n.get("rotation", [0, 0, 0, 1]))
        n["translation"] = (rot @ np.array(n.get("translation", [0, 0, 0]), dtype=np.float64)).tolist()
    for key in ("scale", "rotation", "translation"):
        nodes[arm].pop(key, None)
    glb.write(skin["inverseBindMatrices"], np.array([np.linalg.inv(glb.global_of(j)).T.reshape(16) for j in skin["joints"]]))
    err = max(np.abs(m - np.eye(4)).max() for m in bind_error(glb))
    if err > 1e-4:
        print(f"bind pose is not the identity after the rewrite: {err:.3g}", file=sys.stderr)
        return 1
    if make_t_pose:
        err = max(err, t_pose(glb))
        if err > 1e-4:
            print(f"bind pose is not the identity after the T-pose: {err:.3g}", file=sys.stderr)
            return 1
    pos = glb.read(prim["attributes"]["POSITION"])
    hips = glb.global_of(root_joints[0])[:3, 3]
    print(f"NORMALISED mesh_scale={s_mesh:g} bone_scale={s_bones:g} height={pos[:, 1].max() - pos[:, 1].min():.4f} m "
          f"hips_y={hips[1]:.3f} bind_err={err:.2g} out={dst}")
    glb.save(dst)
    return 0


def _ancestors(glb, i):
    while i in glb.parent:
        i = glb.parent[i]
        yield i


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x != "--t-pose"]
    sys.exit(main(a[0], a[1], float(a[2]) if len(a) > 2 else 0.0, "--t-pose" in sys.argv) if len(a) >= 2 else print(__doc__) or 2)
