"""Run the research contract tests in a disposable checkout of pinned llmfit."""
import argparse
from contextlib import suppress
from hashlib import sha256
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory

# Reuse the importer's source pin and seed location.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastest_release.research import SEED_ROOT, UPSTREAM_COMMIT

UPSTREAM = "https://github.com/AlexsJones/llmfit"
CONTRACT_INPUTS = (
    "Cargo.lock",
    "LICENSE",
    "llmfit-core/src/hwprofile.rs",
    "llmfit-core/src/models.rs",
    "llmfit-core/src/benchmarks.rs",
    "llmfit-core/data/hardware/schema.json",
    "llmfit-core/data/hf_models.json",
    "llmfit-core/data/community/schema.json",
)


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


def interrupted(_signum, _frame):
    raise KeyboardInterrupt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain", help="Optional Rust toolchain name passed to rustup.")
    args = parser.parse_args()
    toolchain = [] if not args.toolchain else ["--toolchain", args.toolchain]

    def rust(tool):
        return subprocess.check_output(["rustup", "which", *toolchain, tool], text=True).strip()

    cargo, rustc, rustdoc = (rust(tool) for tool in ("cargo", "rustc", "rustdoc"))
    signal.signal(signal.SIGTERM, interrupted)
    with TemporaryDirectory(prefix="fastest-research-llmfit-") as temp:
        print(f"Verifier workspace {temp}", flush=True)
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

        for path in CONTRACT_INPUTS:
            digest = sha256((upstream / path).read_bytes()).hexdigest()
            print(f"{digest}  {UPSTREAM}/blob/{UPSTREAM_COMMIT}/{path}", flush=True)

        test = Path(__file__).with_name("fastest_research_contract.rs")
        shutil.copyfile(test, upstream / "llmfit-core" / "tests" / test.name)
        run_owned(
            [cargo, "test", "--locked", "-q", "-p", "llmfit-core", "--test", test.stem],
            cwd=upstream,
            env={
                **os.environ,
                "CARGO_HOME": str(root / "cargo"),
                "CARGO_TARGET_DIR": str(root / "target"),
                "RUSTC": rustc,
                "RUSTDOC": rustdoc,
                "FASTEST_RESEARCH_LLMFIT_SEED": str(SEED_ROOT / "llmfit"),
            },
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except (OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
