# 🔥 Windows GPU Burn Test — v1.4.0 (`feature/macos-metal-mlx`)

> This file lives on the `feature/macos-metal-mlx` branch so it travels to the
> Windows machine via `git pull`. It is the hands-on test plan for validating
> v1.4.0 on a **real NVIDIA GPU** before merging to `main`.

## Why this test exists

| Branch | Version | State |
|--------|---------|-------|
| `main` | **v1.3.0** | Merged & live. CUDA wheel auto-detection (#8/#10), custom model loading (#7), `diagnose.bat`, download resume/cancel, VRAM-aware dropdown, CI green. The community is testing this now. |
| `feature/macos-metal-mlx` | **v1.4.0** | Pushed, **NOT merged**. Adds macOS Metal (Tier 1) + MLX (Tier 2) backends, the 2026 model refresh (abliterated **v2** default, **Caption-it**, **Huihui/noctrex**), and bumps the Windows wheel **0.3.24 → 0.3.40** (adds Qwen3.5/3.6 support + a new `cu131` tag). |

**Validated already (on an M4 Mac):** GGUF via Metal, standard MLX, abliterated
MLX q4, Qwen3.5-4B VLM, offscreen GUI test, pyflakes clean.

**The untested path = this test.** CI proved the Windows install *logic* on a
real Windows box, but CI has **no GPU**, so actual CUDA model loading +
captioning has never run. That's the burn test.

**⚠️ Highest-risk change to validate:** the Windows wheel jumps from `0.3.24`
(community-tested) to **`0.3.40`** (untested on a Windows GPU). Testing this
branch validates the **new wheel** *and* the **new models** in one pass.

---

## Prereqs on the Windows machine

If you already run ComfyUI you almost certainly have these:

- **NVIDIA GPU** + current driver
- **CUDA Toolkit installed** — *this is the whole point of the fix.* Confirm
  `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\` contains a `v12.x` or
  `v13.x` folder. If it's missing: `winget install Nvidia.CUDA`
  *(the driver alone is not enough — `ggml-cuda.dll` needs the Toolkit's runtime DLLs).*
- **Git** (to pull the branch). You do **not** need Python pre-installed —
  `setup.bat` installs Python 3.12 itself via `uv`.

---

## Steps

### 1. Get the branch
Pulling is read-only and needs no push credentials:

```bat
git clone https://github.com/GitDonkeyHubbed/qwen3vl-captioner.git
cd qwen3vl-captioner
git checkout feature/macos-metal-mlx
```

If you already cloned it:

```bat
git fetch origin feature/macos-metal-mlx
git checkout feature/macos-metal-mlx
git pull
```

### 2. Run `setup.bat` (double-click) — watch two lines
- **`[4/6] Detecting CUDA Toolkit`** → should print your version and pick a
  wheel tag. Toolkit → tag mapping (all five exist for the pinned `0.3.40` release):

  | CUDA Toolkit | Wheel tag |
  |--------------|-----------|
  | 13.1+ | `cu131` |
  | 13.0  | `cu130` |
  | 12.8 – 12.9 | `cu128` |
  | 12.6 – 12.7 | `cu126` |
  | 12.4 – 12.5 | `cu124` |

- **`[6/6] Verifying the engine loads`** → must print
  **`Engine OK - llama_cpp 0.3.40`**. (This is the single most important line —
  it proves the new wheel loaded.)

### 3. If setup fails → `diagnose.bat`
Double-click it, copy the full report. It tells us exactly what broke (missing
Toolkit, wheel/CUDA mismatch, import failure). Paste it into the chat / a GitHub
issue.

### 4. Launch the app
Double-click `run.bat`. (It adds the newest CUDA Toolkit `bin` to `PATH` so the
DLLs resolve — prevents the "access violation" failure mode.)

### 5. In-app walkthrough
- Dropdown default = **Qwen3-VL 8B ABL v2 — Q6_K (~6.26 GB)**
  (`prithivMLmods/Qwen3-VL-8B-Instruct-abliterated-v2-GGUF`). Click the
  **⬇ download** button → watch the **real % / GB progress bar**, and confirm it
  **auto-downloads the matching mmproj** (`...abliterated-v2.mmproj-f16.gguf`)
  right after.
- **Models land one level *above* the app folder.** If the repo is at
  `E:\qwen3vl-captioner\`, the `.gguf` files go to `E:\`.
- Click **Load Model** → watch the **GPU pill / VRAM** climb. This confirms CUDA
  engaged (GPU), not a silent CPU fallback (slow).
- Import a test image → **Regenerate Caption** → confirm tokens **stream out**.
- Run **Batch Caption All** on 2–3 images.
- *(Optional)* try **Qwen3-VL 8B Caption-it**
  (`prithivMLmods/Qwen3-VL-8B-Abliterated-Caption-it-GGUF`) and
  **Huihui Qwen3-VL 8B ABL** (`noctrex/Huihui-Qwen3-VL-8B-Instruct-abliterated-GGUF`).

### 6. Specifically watch for (the v1.4.0 risk areas)
1. Does the **`0.3.40` wheel load cleanly**? (`Engine OK - llama_cpp 0.3.40`)
2. Does the **new v2 model + mmproj** download and load?
3. Is inference **GPU-fast**, not CPU-slow?

---

## After the test

### ✅ If it all works — promote to a release
```bat
git checkout main
git merge feature/macos-metal-mlx
git push
git tag v1.4.0 && git push origin v1.4.0
```
That's a real cross-platform release: Windows + macOS, MLX backend, 2026 model
lineup, Qwen3.5/3.6 support.

### ⚠️ If the `0.3.40` wheel misbehaves (but everything else is fine)

**Fastest path — a rollback is already pre-staged.** Branch
`fix/wheel-rollback-0.3.24` is this branch with the wheel reverted to the
community-tested `0.3.24` (and the `cu131` tag removed), keeping the 2026 model
refresh + macOS backends. To use it:

```bat
git checkout fix/wheel-rollback-0.3.24
setup.bat
```

You keep the model refresh but lose Qwen3.5/3.6 support until the `0.3.40` wheel
issue is sorted. Send me the `diagnose.bat` output and I'll pinpoint the cause.

<details><summary>Or apply the rollback by hand (two edits)</summary>

Roll the wheel back to the community-tested `0.3.24` while keeping the model
refresh. Two edits:

1. **`setup.bat`** — replace the v1.4.0 `WHEEL_URL` line with the v1.3.0 form.
   Note the URL *format* changed between releases (not just the version number),
   so replace the whole line:

   ```bat
   REM v1.4.0 (current):
   set "WHEEL_URL=https://github.com/JamePeng/llama-cpp-python/releases/download/v0.3.40-!CUDA_WHEEL!-win-20260608/llama_cpp_python-0.3.40%%2B!CUDA_WHEEL!-cp312-cp312-win_amd64.whl"

   REM v1.3.0 rollback:
   set "WHEEL_URL=https://github.com/JamePeng/llama-cpp-python/releases/download/v0.3.24-!CUDA_WHEEL!-Basic-win-20260208/llama_cpp_python-0.3.24%%2B!CUDA_WHEEL!.basic-cp312-cp312-win_amd64.whl"
   ```

2. **`engine/cuda_setup.py`** — drop the `((13, 1), "cu131"),` row from
   `_WHEEL_TAGS` (the `0.3.24` release set has no `cu131` build, so a CUDA 13.1
   box must fall back to `cu130`). Leave the rest of the file alone — in
   particular keep the `pynvml` FutureWarning suppression in `diagnose()`.

> Note: `git checkout main -- setup.bat` cleanly grabs the `0.3.24` `setup.bat`,
> but do **not** do the same for `engine/cuda_setup.py` — `main`'s copy also
> lacks the `pynvml` fix, so edit that file by hand (or just use the pre-staged
> `fix/wheel-rollback-0.3.24` branch above, which already does this correctly).

</details>

### 🧹 Optional cleanup
`fix/cuda-custom-models-qol` is fully merged into `main` — safe to delete once
`main` looks right: `git branch -d fix/cuda-custom-models-qol` (and delete on GitHub).

---

## Quick reference — what each script does
| Script | Role |
|--------|------|
| `setup.bat` | Installs `uv` → Python 3.12 → deps → the CUDA-matched `0.3.40` wheel, then verifies the engine imports. Re-run it if you install/upgrade CUDA. |
| `run.bat` | Adds newest CUDA Toolkit `bin` to `PATH`, then launches `app.py`. |
| `diagnose.bat` | One-click full report (GPU, driver, Toolkit, wheel build, engine import) with fixes. First stop for any problem. |
