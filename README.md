# entities-obstacle-course

The walk and the obstacle course of the Model Explorer, as a twin app for testing locomotion.
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

## What this repository does not have

- No `project.godot`: it is not a Godot project yet, and none of it has run under Godot here.
- `Bintr.gd`, `CardStyle.gd` and `Motion.gd` come from [V-Sekai/entities-explorer-core](https://github.com/V-Sekai/entities-explorer-core).
- `mm.elf` (interactor-motion-matching-guest) and `mujoco.elf` (interactor-mujoco-sandbox-demo) are build products, and so are the clip folders under `res://motion/mm/`.
- Walking a model needs a skinned model: `skintokens.elf` puts the clips on it.

## Licence

MIT, see `LICENSE` (Copyright (c) 2022 K. S. Ernest (iFire) Lee and Allen Dang).
`NOTICE` and `LICENSES/` carry the Meta Llama 3 notice for the embeddings.
