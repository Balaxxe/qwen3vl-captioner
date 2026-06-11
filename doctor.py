"""
Installation diagnostics for Qwen3-VL Captioner.

Run via diagnose.bat (Windows) or:  python doctor.py

Prints a report of the Python / CUDA / llama-cpp-python install state with
specific remediation steps. If you open a GitHub issue about installation
problems, please paste this report into it.
"""

import sys
from pathlib import Path

# Allow running from the repo root without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.cuda_setup import diagnose  # noqa: E402


OK = "[ OK ]"
WARN = "[WARN]"
FAIL = "[FAIL]"
INFO = "[ -- ]"


def main() -> int:
    print("=" * 64)
    print("  Qwen3-VL Captioner — Install Diagnostics")
    print("=" * 64)

    report = diagnose()
    problems: list[str] = []

    print(f"{INFO} Platform:        {report['platform']}")
    print(f"{INFO} Python:          {report['python']}")

    if report["gpu_name"]:
        print(f"{OK} GPU:             {report['gpu_name']} (driver {report['driver_version']})")
    else:
        print(f"{WARN} GPU:             could not query NVML — NVIDIA driver missing or no NVIDIA GPU")
        problems.append(
            "Install/update the NVIDIA GPU driver: https://www.nvidia.com/drivers"
        )

    if report["toolkit_version"]:
        print(f"{OK} CUDA Toolkit:    v{report['toolkit_version']}  ({report['toolkit_path']})")
    else:
        print(f"{FAIL} CUDA Toolkit:    NOT FOUND (the GPU driver alone is not enough)")
        problems.append(
            "Install the CUDA Toolkit:  winget install Nvidia.CUDA\n"
            "         (or https://developer.nvidia.com/cuda-downloads), then re-run setup.bat"
        )

    if report["llama_cpp_installed"]:
        print(f"{OK} llama-cpp-python: {report['llama_cpp_version']}")
    else:
        print(f"{FAIL} llama-cpp-python: NOT INSTALLED")
        problems.append("Run setup.bat to install all dependencies")

    wheel_tag = report["wheel_cuda_tag"]
    rec_tag = report["recommended_tag"]
    if wheel_tag:
        if report["tags_match"] is False:
            print(f"{FAIL} Wheel/CUDA match: wheel is '{wheel_tag}' but your toolkit needs '{rec_tag}'")
            problems.append(
                f"Re-run setup.bat — it will replace the {wheel_tag} wheel with the {rec_tag} build"
            )
        elif report["tags_match"]:
            print(f"{OK} Wheel/CUDA match: wheel '{wheel_tag}' matches toolkit (needs '{rec_tag}')")
        else:
            print(f"{WARN} Wheel/CUDA match: wheel is '{wheel_tag}' but no toolkit found to compare")
    elif report["llama_cpp_installed"]:
        print(f"{WARN} Wheel build:      CPU build detected (no CUDA tag) — GPU acceleration disabled")

    if report["llama_cpp_installed"]:
        if report["llama_cpp_importable"]:
            print(f"{OK} Engine import:   llama_cpp loads successfully")
        else:
            print(f"{FAIL} Engine import:   {report['import_error']}")
            if not problems:
                problems.append(
                    "llama_cpp failed to load even though versions look right.\n"
                    "         Re-run setup.bat; if it persists, open a GitHub issue with this report."
                )

    print("-" * 64)
    if problems:
        print("  PROBLEMS FOUND — suggested fixes (in order):")
        for i, p in enumerate(problems, 1):
            print(f"  {i}. {p}")
        print()
        print("  After fixing, run diagnose.bat again to verify.")
        result = 1
    else:
        print("  All checks passed. If the app still fails, open a GitHub")
        print("  issue and include this report.")
        result = 0
    print("=" * 64)
    return result


if __name__ == "__main__":
    sys.exit(main())
