# Third-party parts of the app

`Obstacle Course.app` holds these parts besides this project's own code (MIT, `LICENSE`). Their licence texts are in the app
under `Contents/Resources/LICENSES/`: `third-party/` for the rows below that name a file there (it is `LICENSES/third-party/`
here), and `texts/` for the ones copied from each part's own repository (it is `tools/licences/src/` here).

| Part | Where it is in the app | Licence | Text |
|---|---|---|---|
| Godot Engine, the entities build [`4.8.beta.double.gh.2bb0aa622`](https://github.com/V-Sekai-fire/entities-zone/releases/tag/v0.0.0-20261113200510-2bb0aa62247c) | the executable | MIT | `texts/Godot_Engine.md` |
| godot-sandbox and libriscv | in the engine | BSD-3-Clause | `texts/godot_sandbox.md`, `texts/libriscv.md` |
| Godot VRM and MToon shader addons | the project | MIT | `texts/godot_vrm_and_Godot_MToon_Shader.md` |
| FoundationDB client library | `Frameworks/libfdb_c.dylib` | Apache-2.0 | `third-party/foundationdb-LICENSE` |
| `mm.elf`: [interactor-motion-matching-guest](https://github.com/V-Sekai-fire/interactor-motion-matching-guest), a port of godot-motion-matching by Guilherme Sousa | the project | MIT | `third-party/interactor-motion-matching-guest-LICENSE` |
| `mujoco.elf`: [interactor-mujoco-sandbox-demo](https://github.com/V-Sekai-fire/interactor-mujoco-sandbox-demo) with MuJoCo | the project | MIT; MuJoCo is Apache-2.0 | `third-party/interactor-mujoco-sandbox-demo-LICENSE`, `third-party/mujoco-LICENSE` |
| `skintokens.elf`: [interactor-skintokens-guest](https://github.com/V-Sekai-fire/interactor-skintokens-guest) and the parts it vendors | the project | MIT or Apache-2.0; the vendored parts keep their own | `texts/interactor_skintokens_guest.md`, `texts/SkinTokens.md`, `texts/ggml.md`, `texts/nlohmann_json.md`, `texts/skin_tokens_ggml_NOTICE.md`, `texts/skin_tokens_ggml_and_oneTBB.md` |
| 21 motion-capture clips from the O3DE MotionMatching gem | `motion/mm/` | Apache-2.0 or MIT | `third-party/o3de-motionmatching-LICENSE.txt` and the two texts it names |
| 54 clips generated with NVIDIA Kimodo-SOMA-RP-v1.1 | `motion/mm/` | NVIDIA Open Model License: the clips are outputs of the model, and NVIDIA claims no ownership of outputs | [the model's licence](https://huggingface.co/nvidia/Kimodo-SOMA-RP-v1.1/blob/main/LICENSE) |
| Maro, by Mohka Noir | `avatar/maro/` | Apache-2.0 | `Contents/Resources/avatar-maro/LICENSE`, beside `LICENSES/` |

The 75 clips are the `data/` of interactor-motion-matching-guest, which lists the generated ones with their prompts. The app
holds outputs of the Kimodo model, not the model.
