# entities-obstacle-course

The walk and the obstacle course of the Model Explorer, as an app of their own for testing locomotion. A plain launch opens Maro and walks her on the course.
The Model Explorer no longer carries them ([V-Sekai/entities-model-explorer#49](https://github.com/V-Sekai/entities-model-explorer/pull/49)).

| Path | What it is |
|---|---|
| `vsk_model_explorer/core/MotionMatch.gd`, `MotionMatchNode.gd` | The walk: motion matching on `mm.elf`, driven by keyboard or pad. |
| `vsk_model_explorer/core/ObstacleCourse.gd`, `WalkBar.gd` | The course and its button bar. |
| `vsk_model_explorer/core/ClipBaker.gd`, `MMClipLibraryBaker.gd` | Bake clips into the motion-matching library. |
| `vsk_model_explorer/course/` | Course data (colliders). |
| `tools/course/` | Course baking and checking scripts. |
| `motion/` | The motion list `clips.tsv` and the prompt embeddings (see `NOTICE`). |

The history was cut from [V-Sekai/entities-model-explorer](https://github.com/V-Sekai/entities-model-explorer) with `git filter-repo`.
The auto-rig path is gone: a model with no rig now fails with a message.

## Run it

1. `tools/fetch_guest_assets.sh` fetches the build products (needs `gh` and `python3`): the guest programs `mm.elf`, `mujoco.elf` and `skintokens.elf`, and the 72 clips under `motion/mm/`. Git ignores them.
2. Run the project with the entities engine, the Godot 4.8 double build of [V-Sekai/entities-zone](https://github.com/V-Sekai/entities-zone) (tried with `4.8.beta.double.gh.2bb0aa622`):
   - `godot --path .` opens Maro with the clips already on her and shows the course. W A S D walks.
   - `godot --path . -- model.glb` walks another skinned model. Only Maro has been tried here. The first run puts the clips on the model and keeps the result in the app's user data.

`Bintr.gd`, `CardStyle.gd` and `Motion.gd` also live in [V-Sekai/entities-explorer-core](https://github.com/V-Sekai/entities-explorer-core).

## Make the app (macOS, arm64)

```sh
export ENGINE_DIR=<folder with godot.macos.editor.double.arm64, godot.macos.template_release.double.arm64 and libfdb_c.dylib>
tools/bake_moves.sh                          # puts the clips on Maro once: avatar/maro/Maro.moves.glb (53 MB, not in git)
tools/package_mac.sh <out folder> <version>  # Obstacle Course.app and a zip
```

The app is ad-hoc signed, not notarized. macOS blocks it on the first launch: choose Open Anyway in System Settings > Privacy & Security, or run `xattr -dr com.apple.quarantine "Obstacle Course.app"`.

## Maro

The default avatar is Maro, a free model by Mohka Noir (Apache-2.0) from [chibifire-stages/character-marocchino](https://github.com/chibifire-stages/character-marocchino) at `dcd38ff7f6f2ea10a584dca383a6b7c3fab27d36`. Her licence and credit are in `avatar/maro/` and `NOTICE`.
The walk needs a VRM humanoid bone map and a T-pose rest. `avatar/maro/Maro.glb` is made from her low-poly FBX in three steps:

1. `tools/fbx_to_glb.gd` turns the imported FBX into a GLB.
2. `tools/glb_add_vrm_humanoid.py` adds the VRM 1.0 bone map from the author's Unity bone map (`Marocchino.fbx.meta` in the source repository).
3. `tools/glb_normalize.py --t-pose` bakes the unit scale and the turn that the FBX left on the Armature into the data (Y-up, metres), then raises her arms to a T-pose without changing the surface.

## Licence

MIT, see `LICENSE` (Copyright (c) 2022 K. S. Ernest (iFire) Lee and Allen Dang).
`NOTICE` and `LICENSES/` carry the Meta Llama 3 notice for the embeddings.
