"""
Model Download Manager for VL-CAPTIONER Studio Pro.

Provides:
  - MODEL_REGISTRY: maps model combo display names to HF repo info
  - ModelDownloadWorker: QObject that downloads a GGUF in a background QThread
  - get_all_model_display_names(): returns ordered list of display names for combo
"""

import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional, Dict, Any, List

from PyQt6.QtCore import QObject, pyqtSignal


# ---------------------------------------------------------------------------
# Registry: combo text -> download info
#
# All models from: prithivMLmods/Qwen3-VL-8B-Instruct-abliterated-v1-GGUF
# Each key is the human-readable dropdown label:
#   "Qwen3-VL 8B Abliterated — <QUANT> (<SIZE>)"
# ---------------------------------------------------------------------------

MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    # ── Main model quants (smallest → largest) ──────────────────
    "Qwen3-VL 8B ABL — Q2_K (3.28 GB)": {
        "repo_id": "prithivMLmods/Qwen3-VL-8B-Instruct-abliterated-v1-GGUF",
        "filename": "Qwen3-VL-8B-Instruct-abliterated-v1.Q2_K.gguf",
        "size_gb": 3.28,
        "gated": False,
    },
    "Qwen3-VL 8B ABL — Q3_K_S (3.77 GB)": {
        "repo_id": "prithivMLmods/Qwen3-VL-8B-Instruct-abliterated-v1-GGUF",
        "filename": "Qwen3-VL-8B-Instruct-abliterated-v1.Q3_K_S.gguf",
        "size_gb": 3.77,
        "gated": False,
    },
    "Qwen3-VL 8B ABL — Q3_K_M (4.12 GB)": {
        "repo_id": "prithivMLmods/Qwen3-VL-8B-Instruct-abliterated-v1-GGUF",
        "filename": "Qwen3-VL-8B-Instruct-abliterated-v1.Q3_K_M.gguf",
        "size_gb": 4.12,
        "gated": False,
    },
    "Qwen3-VL 8B ABL — Q3_K_L (4.43 GB)": {
        "repo_id": "prithivMLmods/Qwen3-VL-8B-Instruct-abliterated-v1-GGUF",
        "filename": "Qwen3-VL-8B-Instruct-abliterated-v1.Q3_K_L.gguf",
        "size_gb": 4.43,
        "gated": False,
    },
    "Qwen3-VL 8B ABL — IQ4_XS (4.59 GB)": {
        "repo_id": "prithivMLmods/Qwen3-VL-8B-Instruct-abliterated-v1-GGUF",
        "filename": "Qwen3-VL-8B-Instruct-abliterated-v1.IQ4_XS.gguf",
        "size_gb": 4.59,
        "gated": False,
    },
    "Qwen3-VL 8B ABL — Q4_K_S (4.80 GB)": {
        "repo_id": "prithivMLmods/Qwen3-VL-8B-Instruct-abliterated-v1-GGUF",
        "filename": "Qwen3-VL-8B-Instruct-abliterated-v1.Q4_K_S.gguf",
        "size_gb": 4.80,
        "gated": False,
    },
    "Qwen3-VL 8B ABL — Q4_K_M (5.03 GB)": {
        "repo_id": "prithivMLmods/Qwen3-VL-8B-Instruct-abliterated-v1-GGUF",
        "filename": "Qwen3-VL-8B-Instruct-abliterated-v1.Q4_K_M.gguf",
        "size_gb": 5.03,
        "gated": False,
    },
    "Qwen3-VL 8B ABL — Q5_K_S (5.72 GB)": {
        "repo_id": "prithivMLmods/Qwen3-VL-8B-Instruct-abliterated-v1-GGUF",
        "filename": "Qwen3-VL-8B-Instruct-abliterated-v1.Q5_K_S.gguf",
        "size_gb": 5.72,
        "gated": False,
    },
    "Qwen3-VL 8B ABL — Q5_K_M (5.85 GB)": {
        "repo_id": "prithivMLmods/Qwen3-VL-8B-Instruct-abliterated-v1-GGUF",
        "filename": "Qwen3-VL-8B-Instruct-abliterated-v1.Q5_K_M.gguf",
        "size_gb": 5.85,
        "gated": False,
    },
    "Qwen3-VL 8B ABL — Q6_K (6.73 GB)": {
        "repo_id": "prithivMLmods/Qwen3-VL-8B-Instruct-abliterated-v1-GGUF",
        "filename": "Qwen3-VL-8B-Instruct-abliterated-v1.Q6_K.gguf",
        "size_gb": 6.73,
        "gated": False,
    },
    "Qwen3-VL 8B ABL — Q8_0 (8.71 GB)": {
        "repo_id": "prithivMLmods/Qwen3-VL-8B-Instruct-abliterated-v1-GGUF",
        "filename": "Qwen3-VL-8B-Instruct-abliterated-v1.Q8_0.gguf",
        "size_gb": 8.71,
        "gated": False,
    },
    "Qwen3-VL 8B ABL — F16 (16.4 GB)": {
        "repo_id": "prithivMLmods/Qwen3-VL-8B-Instruct-abliterated-v1-GGUF",
        "filename": "Qwen3-VL-8B-Instruct-abliterated-v1.f16.gguf",
        "size_gb": 16.4,
        "gated": False,
    },
}

# Ordered list for the dropdown — sorted by quant size ascending
_MODEL_ORDER = [
    "Qwen3-VL 8B ABL — Q2_K (3.28 GB)",
    "Qwen3-VL 8B ABL — Q3_K_S (3.77 GB)",
    "Qwen3-VL 8B ABL — Q3_K_M (4.12 GB)",
    "Qwen3-VL 8B ABL — Q3_K_L (4.43 GB)",
    "Qwen3-VL 8B ABL — IQ4_XS (4.59 GB)",
    "Qwen3-VL 8B ABL — Q4_K_S (4.80 GB)",
    "Qwen3-VL 8B ABL — Q4_K_M (5.03 GB)",
    "Qwen3-VL 8B ABL — Q5_K_S (5.72 GB)",
    "Qwen3-VL 8B ABL — Q5_K_M (5.85 GB)",
    "Qwen3-VL 8B ABL — Q6_K (6.73 GB)",
    "Qwen3-VL 8B ABL — Q8_0 (8.71 GB)",
    "Qwen3-VL 8B ABL — F16 (16.4 GB)",
]

# ---------------------------------------------------------------------------
# MLX models (Apple Silicon only) — folders of safetensors, no mmproj needed.
# Note: these are the standard (non-abliterated) Qwen3-VL Instruct weights;
# no MLX conversion of the abliterated variant has been published yet.
# ---------------------------------------------------------------------------

MLX_MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "Qwen3-VL 8B MLX — 4bit (5.4 GB)": {
        "repo_id": "lmstudio-community/Qwen3-VL-8B-Instruct-MLX-4bit",
        "folder": "Qwen3-VL-8B-Instruct-MLX-4bit",
        "size_gb": 5.38,
        "gated": False,
        "backend": "mlx",
    },
    "Qwen3-VL 8B MLX — 6bit (7.3 GB)": {
        "repo_id": "lmstudio-community/Qwen3-VL-8B-Instruct-MLX-6bit",
        "folder": "Qwen3-VL-8B-Instruct-MLX-6bit",
        "size_gb": 7.29,
        "gated": False,
        "backend": "mlx",
    },
    "Qwen3-VL 8B MLX — 8bit (9.2 GB)": {
        "repo_id": "lmstudio-community/Qwen3-VL-8B-Instruct-MLX-8bit",
        "folder": "Qwen3-VL-8B-Instruct-MLX-8bit",
        "size_gb": 9.19,
        "gated": False,
        "backend": "mlx",
    },
}

_MLX_MODEL_ORDER = list(MLX_MODEL_REGISTRY.keys())


def mlx_backend_supported() -> bool:
    """MLX models only make sense on Apple Silicon Macs."""
    import platform
    import sys
    return sys.platform == "darwin" and platform.machine() == "arm64"


def get_all_model_display_names() -> List[str]:
    """Return the ordered list of model display names for the dropdown combo.

    MLX entries are only offered on Apple Silicon, where they can run."""
    names = list(_MODEL_ORDER)
    if mlx_backend_supported():
        names.extend(_MLX_MODEL_ORDER)
    return names


def get_model_info(combo_text: str) -> Optional[Dict[str, Any]]:
    """Return registry entry for *combo_text*, or None if not downloadable.

    Entries carry a "backend" key: "gguf" (default) or "mlx"."""
    info = MODEL_REGISTRY.get(combo_text)
    if info is not None:
        return {**info, "backend": "gguf"}
    return MLX_MODEL_REGISTRY.get(combo_text)


def model_file_exists(model_dir: Path, filename: str) -> bool:
    """Check whether *filename* already exists in *model_dir*."""
    return (model_dir / filename).is_file()


def mlx_model_exists(model_dir: Path, folder: str) -> bool:
    """Check whether an MLX model folder is present and complete-looking."""
    path = model_dir / folder
    return (
        path.is_dir()
        and (path / "config.json").is_file()
        and any(path.glob("*.safetensors"))
    )


# ---------------------------------------------------------------------------
# Download worker
# ---------------------------------------------------------------------------

class _StripAuthOnRedirect(urllib.request.HTTPRedirectHandler):
    """Drop the Authorization header when HF redirects to its CDN.

    Storage backends (S3 etc.) reject requests that carry both their signed
    URL parameters and a Bearer token."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None:
            old_host = urllib.parse.urlparse(req.full_url).netloc
            new_host = urllib.parse.urlparse(newurl).netloc
            if old_host != new_host:
                new.headers.pop("Authorization", None)
        return new


class ModelDownloadWorker(QObject):
    """Downloads a single GGUF file from HuggingFace with streaming progress.

    Downloads to a .part file (resumable via HTTP Range) and renames it on
    completion, so a cancelled or interrupted download picks up where it
    left off the next time.

    Signals
    -------
    progress(message, fraction)   0.0-1.0 progress updates
    finished(local_path)          download complete — passes the local file path
    error(message)                something went wrong (or user cancelled)
    """

    progress = pyqtSignal(str, float)
    finished = pyqtSignal(str)      # str(local_path)
    error = pyqtSignal(str)

    _CHUNK_SIZE = 1024 * 1024  # 1 MiB reads — keeps cancel latency low

    def __init__(
        self,
        repo_id: str,
        filename: str,
        target_dir: Path,
        hf_token: str = "",
        snapshot_folder: Optional[str] = None,
    ):
        super().__init__()
        self.repo_id = repo_id
        self.filename = filename
        self.target_dir = target_dir
        self.hf_token = hf_token or None
        # When set, download the whole repo into target_dir/snapshot_folder
        # (used for MLX models, which are folders rather than single files)
        self.snapshot_folder = snapshot_folder
        self._cancelled = False

    def cancel(self):
        """Request cancellation of the download (takes effect within ~1 MiB)."""
        self._cancelled = True

    def _run_snapshot(self):
        """Download a whole model repo (MLX folder) via snapshot_download."""
        from huggingface_hub import snapshot_download

        dest = Path(self.target_dir) / self.snapshot_folder
        try:
            self.progress.emit(
                f"Downloading {self.repo_id} → {self.snapshot_folder}/ "
                "(folder download — this may take a while)...",
                0.0,
            )
            local = snapshot_download(
                self.repo_id,
                local_dir=str(dest),
                token=self.hf_token,
            )
            if self._cancelled:
                self.error.emit("Download cancelled.")
                return
            self.progress.emit("Download complete", 1.0)
            self.finished.emit(str(local))
        except Exception as exc:
            msg = str(exc)
            if "401" in msg or "403" in msg:
                msg = (
                    f"Authentication error ({msg[:120]}).\n\n"
                    "This model may require a HuggingFace token.\n"
                    "Add your token in Settings (gear icon) and try again."
                )
            self.error.emit(msg)

    def run(self):
        """Execute the download (call from a QThread)."""
        try:
            from huggingface_hub import hf_hub_url
        except ImportError:
            self.error.emit(
                "huggingface-hub is not installed.\n"
                "Run: pip install huggingface-hub"
            )
            return

        if self._cancelled:
            self.error.emit("Download cancelled before starting.")
            return

        if self.snapshot_folder:
            self._run_snapshot()
            return

        target = Path(self.target_dir) / self.filename
        part = target.with_name(target.name + ".part")

        try:
            url = hf_hub_url(repo_id=self.repo_id, filename=self.filename)

            headers = {"User-Agent": "qwen3vl-captioner"}
            if self.hf_token:
                headers["Authorization"] = f"Bearer {self.hf_token}"

            resume_pos = part.stat().st_size if part.exists() else 0
            if resume_pos:
                headers["Range"] = f"bytes={resume_pos}-"
                self.progress.emit(
                    f"Resuming {self.filename} at {resume_pos / 1024**3:.2f} GB...", 0.0
                )

            opener = urllib.request.build_opener(_StripAuthOnRedirect)
            request = urllib.request.Request(url, headers=headers)

            try:
                response = opener.open(request, timeout=30)
            except urllib.error.HTTPError as http_err:
                if http_err.code == 416 and resume_pos:
                    # Range beyond EOF — the .part file is already complete
                    part.rename(target)
                    self.progress.emit("Download complete", 1.0)
                    self.finished.emit(str(target))
                    return
                raise

            with response:
                if resume_pos and response.status == 206:
                    content_range = response.headers.get("Content-Range", "")
                    total = (
                        int(content_range.rsplit("/", 1)[-1])
                        if "/" in content_range else 0
                    )
                    mode = "ab"
                else:
                    # Server ignored the Range request — start over
                    total = int(response.headers.get("Content-Length") or 0)
                    resume_pos = 0
                    mode = "wb"

                downloaded = resume_pos
                last_emit = 0.0
                self.target_dir.mkdir(parents=True, exist_ok=True)

                with open(part, mode) as f:
                    while True:
                        if self._cancelled:
                            # Keep the .part file so the download can resume
                            self.error.emit(
                                "Download cancelled — progress kept, "
                                "download again to resume."
                            )
                            return
                        chunk = response.read(self._CHUNK_SIZE)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        now = time.monotonic()
                        if now - last_emit >= 0.5:
                            last_emit = now
                            if total:
                                fraction = downloaded / total
                                self.progress.emit(
                                    f"{self.filename} — "
                                    f"{downloaded / 1024**3:.2f} / {total / 1024**3:.2f} GB "
                                    f"({fraction * 100:.0f}%)",
                                    fraction,
                                )
                            else:
                                self.progress.emit(
                                    f"{self.filename} — {downloaded / 1024**3:.2f} GB...",
                                    0.0,
                                )

            if total and downloaded < total:
                self.error.emit(
                    f"Download incomplete ({downloaded / 1024**3:.2f} of "
                    f"{total / 1024**3:.2f} GB) — connection dropped. "
                    "Download again to resume."
                )
                return

            part.rename(target)
            self.progress.emit("Download complete", 1.0)
            self.finished.emit(str(target))

        except Exception as exc:
            if self._cancelled:
                self.error.emit(
                    "Download cancelled — progress kept, download again to resume."
                )
                return
            msg = str(exc)
            # Surface auth errors clearly
            if "401" in msg or "403" in msg:
                msg = (
                    f"Authentication error ({msg[:120]}).\n\n"
                    "This model may require a HuggingFace token.\n"
                    "Add your token in Settings (gear icon) and try again."
                )
            self.error.emit(msg)
