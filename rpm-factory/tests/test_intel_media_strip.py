"""Regression tests for the generated Intel media-driver source archive."""
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STRIP = ROOT / "rpm-factory" / "packages" / "intel-media-driver-free" / "strip.py"


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("fixture\n")


def test_generation_directories_match_fedora_strip_semantics(tmp_path):
    strip = runpy.run_path(str(STRIP), run_name="intel_media_strip")

    for relative in (
        "media_driver/agnostic/gen12/codec/kernel/nonfree.bin",
        "media_driver/agnostic/gen9_bxt/cm/cm_gpucopy_kernel.bin",
        "media_driver/agnostic/gen11/cm/cmrt_kernel/nonfree.bin",
    ):
        _touch(tmp_path / relative)
    for relative in (
        "media_driver/agnostic/gen12/codec/kernel_free/free.bin",
        "media_driver/agnostic/other/kernel/keep.bin",
        "README.md",
    ):
        _touch(tmp_path / relative)

    strip["_strip_non_free_sources"](tmp_path)

    assert (tmp_path / "media_driver/agnostic/gen12/codec/kernel_free/free.bin").is_file()
    assert (tmp_path / "media_driver/agnostic/other/kernel/keep.bin").is_file()
    assert (tmp_path / "README.md").is_file()
    assert not (tmp_path / "media_driver/agnostic/gen12/codec/kernel").exists()
    assert not (tmp_path / "media_driver/agnostic/gen9_bxt/cm/cm_gpucopy_kernel.bin").exists()
    assert not (tmp_path / "media_driver/agnostic/gen11/cm/cmrt_kernel").exists()
