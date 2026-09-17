import sys
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "pigeon" / "tools"))

from publish_gate import publish_allowed, check_precedence, check_transaction


def test_publish_requires_all_gates():
    assert publish_allowed(build_ok=True, precedence_ok=True, transaction_ok=True)
    assert not publish_allowed(build_ok=False, precedence_ok=True, transaction_ok=True)
    assert not publish_allowed(build_ok=True, precedence_ok=False, transaction_ok=True)
    assert not publish_allowed(build_ok=True, precedence_ok=True, transaction_ok=False)


def test_check_precedence_stub(tmp_path):
    # Create a dummy RPM
    rpm = tmp_path / "test-1.0-1.x86_64.rpm"
    rpm.write_text("dummy")
    # Stub always passes if RPMs exist
    assert check_precedence(tmp_path, "quay.io/hummingbird-community/bootc-os:latest", ".hum1.pigeon")


def test_check_precedence_no_rpms(tmp_path):
    # Should fail when no RPMs
    assert not check_precedence(tmp_path, "quay.io/hummingbird-community/bootc-os:latest", ".hum1.pigeon")


def test_check_transaction_stub(tmp_path):
    # Stub always passes
    assert check_transaction(tmp_path, "quay.io/hummingbird-community/bootc-os:latest", ".hum1.pigeon")