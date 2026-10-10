"""Build serverless LongImageOCR Lite distribution packages."""

from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path


VERSION = "0.1.0"


def _write_zip(zip_path: Path, files: list[tuple[Path, str]]) -> Path:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for source, archive_name in files:
            zf.write(source, archive_name)
    return zip_path


def _sync_chatgpt_policy(repo_root: Path) -> Path:
    canonical = repo_root / "skills" / "lite" / "common"
    refs = (
        repo_root
        / "plugins"
        / "longimageocr-lite"
        / "skills"
        / "long-image-ocr-lite"
        / "references"
    )
    refs.mkdir(parents=True, exist_ok=True)
    for name in ("CORE_POLICY.md", "OUTPUT_RULES.md"):
        shutil.copyfile(canonical / name, refs / name)
    return refs


def build_chatgpt_package(repo_root: Path, dist_dir: Path) -> Path:
    """Build the skills-only ChatGPT Agent Plugin ZIP with plugin files at ZIP root."""
    repo_root = Path(repo_root).resolve()
    dist_dir = Path(dist_dir).resolve()
    _sync_chatgpt_policy(repo_root)
    plugin_root = repo_root / "plugins" / "longimageocr-lite"
    files: list[tuple[Path, str]] = []
    for source in sorted(p for p in plugin_root.rglob("*") if p.is_file()):
        files.append((source, source.relative_to(plugin_root).as_posix()))
    return _write_zip(
        dist_dir / f"LongImageOCR-Lite-ChatGPT-v{VERSION}.zip",
        files,
    )


def build_gemini_package(repo_root: Path, dist_dir: Path) -> Path:
    """Build the paste-ready Gemini Workspace Studio skill ZIP."""
    repo_root = Path(repo_root).resolve()
    dist_dir = Path(dist_dir).resolve()
    gemini_root = repo_root / "skills" / "lite" / "gemini"
    canonical = repo_root / "skills" / "lite" / "common"
    files = [
        (gemini_root / "SKILL.md", "SKILL.md"),
        (gemini_root / "README.md", "README.md"),
        (canonical / "CORE_POLICY.md", "CORE_POLICY.md"),
        (canonical / "OUTPUT_RULES.md", "OUTPUT_RULES.md"),
    ]
    return _write_zip(
        dist_dir / f"LongImageOCR-Lite-Gemini-v{VERSION}.zip",
        files,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build LongImageOCR Lite ChatGPT and Gemini packages.")
    parser.add_argument("--dist", default="dist", help="Output directory (default: dist).")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    dist_dir = (repo_root / args.dist).resolve() if not Path(args.dist).is_absolute() else Path(args.dist)
    chatgpt = build_chatgpt_package(repo_root, dist_dir)
    gemini = build_gemini_package(repo_root, dist_dir)
    print(chatgpt)
    print(gemini)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
