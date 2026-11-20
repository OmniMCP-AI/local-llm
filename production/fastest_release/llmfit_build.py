"""Build against a disposable, locked checkout of the approved llmfit revision."""

from contextlib import contextmanager, suppress
from hashlib import sha256
import os
from pathlib import Path
import signal
import subprocess
from tempfile import TemporaryDirectory

from .research import UPSTREAM_COMMIT


LOCK_SHA256 = "d7eca4e943ca37285eba1a4dc3a8e65aa6f8f21b89fe95cd6837b654cad2470a"


def run_owned(command, **options):
    with subprocess.Popen(command, start_new_session=True, **options) as process:
        try:
            status = process.wait()
        except BaseException:
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            finally:
                with suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise
        if status:
            raise subprocess.CalledProcessError(status, command)


def verify_sha256(path, expected):
    actual = sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f"Unexpected SHA-256 for {path.name}: {actual}")


def interrupted(_signum, _frame):
    raise KeyboardInterrupt


@contextmanager
def pinned_workspace(toolchain=None):
    options = ["--toolchain", toolchain] if toolchain else []

    def rust(tool):
        return subprocess.check_output(["rustup", "which", *options, tool], text=True).strip()

    cargo, rustc, rustdoc = (rust(tool) for tool in ("cargo", "rustc", "rustdoc"))
    previous_handler = signal.signal(signal.SIGTERM, interrupted)
    try:
        with TemporaryDirectory(prefix="fastest-llmfit-") as temp:
            print(f"llmfit workspace {temp}", flush=True)
            root = Path(temp)
            archive = root / "upstream.tar.gz"
            upstream = root / "upstream"
            upstream.mkdir()
            run_owned([
                "curl", "-fLsS", "--max-time", "90",
                f"https://codeload.github.com/AlexsJones/llmfit/tar.gz/{UPSTREAM_COMMIT}",
                "-o", str(archive),
            ])
            run_owned(["tar", "--strip-components=1", "-xzf", str(archive), "-C", str(upstream)])
            archive.unlink()
            verify_sha256(upstream / "Cargo.lock", LOCK_SHA256)
            yield upstream, cargo, {
                **os.environ,
                "CARGO_HOME": str(root / "cargo"),
                "CARGO_TARGET_DIR": str(root / "target"),
                "TMPDIR": str(root),
                "RUSTC": rustc,
                "RUSTDOC": rustdoc,
            }
    finally:
        signal.signal(signal.SIGTERM, previous_handler)
