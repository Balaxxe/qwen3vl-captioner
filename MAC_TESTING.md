# 🍎 macOS Burn Test — v1.4.0 (Metal + MLX)

## Why this test exists
v1.4.0 added macOS support, but the validation so far has been **Windows/CUDA
only** (see [WINDOWS_TESTING.md](WINDOWS_TESTING.md) — passed). The macOS side
has two GPU backends that have **not** been exercised on real Apple Silicon:

- **Tier 1 — llama.cpp Metal** (GGUF models + mmproj, same models as Windows,
  via the Metal wheel).
- **Tier 2 — MLX** (`mlx-vlm`, MLX-converted model *folders*, no mmproj).

The download/cancel improvements and the vision-encoder mismatch fix from
v1.4.0 are platform-agnostic and benefit the Metal (GGUF) path too, but the
goal here is to confirm both backends actually load and caption on a Mac.

## Prereqs
- **Apple Silicon Mac** (M1/M2/M3/M4). Intel Macs work CPU-only (slow; the MLX
  backend is Apple-Silicon-only).
- **Xcode Command Line Tools** (`xcode-select --install`) — only required on
  Intel Macs, which build llama.cpp from source.
- **Git**. Python is installed by `setup.sh` via `uv`.

## Steps

### 1. Get the branch
```bash
git clone https://github.com/GitDonkeyHubbed/qwen3vl-captioner.git
cd qwen3vl-captioner
git checkout main        # v1.4.0 is now on main (tag V1.4.0)
```

### 2. Run setup
```bash
chmod +x setup.sh run.sh   # if needed
./setup.sh
```
Watch for:
- **`[4/5]`** — on Apple Silicon it installs the **Metal** llama-cpp-python
  wheel (`0.3.40 … macosx_11_0_arm64`).
- **`[5/5]`** — installs `mlx-vlm` for the MLX backend.
- A final **`Engine OK - llama_cpp 0.3.40`**-style line proving the Metal wheel
  imports.

### 3. Launch
```bash
./run.sh
```

### 4. In-app walkthrough — **test BOTH backends**

**A) Metal / GGUF (Tier 1)**
- Pick **Qwen3-VL 8B ABL v2 — Q6_K (6.26 GB)**, click **⬇ download** (confirm
  it auto-pulls the matching `…v2.mmproj-f16.gguf`), then **Load Model**.
- Import an image → **Regenerate Caption** → confirm tokens stream.
- Watch **Activity Monitor → Window → GPU History**: GPU should engage (Metal),
  not pure CPU.

**B) MLX (Tier 2)**
- The dropdown should show **MLX** entries on Apple Silicon (e.g.
  **Qwen3-VL 8B MLX ABL — 4bit (5.4 GB)**). Pick one, **⬇ download** (this is a
  *folder* snapshot — watch it land), then **Load Model**.
- The status bar should indicate the **MLX** engine (not llama.cpp). Caption an
  image and confirm it streams.

### 5. Specifically watch for (v1.4.0 macOS risk areas)
1. Does the **Metal wheel** load cleanly on arm64? (`Engine OK 0.3.40`)
2. Does **MLX** load via `mlx-vlm` and caption?
3. Is inference **GPU-fast** (Metal / MLX), not CPU-slow?
4. Do downloads behave (parallel for GGUF, snapshot for MLX) and does the
   **Stop** button cancel cleanly?

## If something fails
Run `python doctor.py` from the repo (inside the venv) and capture the output;
it reports the engine/backends detected. Note that the
`fix/wheel-rollback-0.3.24` branch is a pre-staged rollback to the
community-tested 0.3.24 wheel if 0.3.40 misbehaves.
