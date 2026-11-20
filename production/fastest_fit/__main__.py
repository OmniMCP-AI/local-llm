import argparse
import json
from pathlib import Path
import shutil
from subprocess import CalledProcessError
import sys
from tempfile import TemporaryDirectory

from fastest_release.llmfit_build import pinned_workspace, run_owned, verify_sha256

from . import CATALOG, MODEL_DATA, MODEL_DATA_SHA256, UPSTREAM_COMMIT


def main():
    parser = argparse.ArgumentParser(description="Build or verify the pinned llmfit executable.")
    parser.add_argument("--toolchain", default="1.98.0", help="An installed Rust toolchain.")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="Build and retain the native executable.")
    build.add_argument("destination", type=Path)
    commands.add_parser("verify", help="Build the native executable and run the public request fixtures.")
    args = parser.parse_args()
    hardware = json.loads((CATALOG / "catalog-hardware-sources.json").read_bytes())["upstream"]
    if hardware["commit"] != UPSTREAM_COMMIT:
        parser.error("hardware catalog and engine pins disagree")

    with pinned_workspace(args.toolchain) as (upstream, cargo, environment):
        verify_sha256(upstream / MODEL_DATA, MODEL_DATA_SHA256)
        for profile in hardware["presets"]:
            verify_sha256(upstream / profile["path"], profile["sha256"])

        adapter = upstream / "llmfit-core/src/bin/fastest-fit.rs"
        adapter.parent.mkdir(exist_ok=True)
        shutil.copyfile(Path(__file__).with_name("engine.rs"), adapter)
        environment["FASTEST_LLMFIT_COMMIT"] = UPSTREAM_COMMIT
        run_owned(
            [cargo, "build", "--locked", "--release", "-q", "-p", "llmfit-core", "--bin", "fastest-fit"],
            cwd=upstream,
            env=environment,
        )
        binary = Path(environment["CARGO_TARGET_DIR"]) / "release/fastest-fit"
        if args.command == "build":
            destination = args.destination.absolute()
            with TemporaryDirectory(prefix="fastest-fit-install-", dir=destination.parent) as temp:
                staged = Path(temp) / binary.name
                shutil.copy2(binary, staged)
                staged.replace(destination)
            print(destination)
        else:
            environment["FASTEST_FIT_TEST_ENGINE"] = str(binary)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            run_owned(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_fit.py", "-v"],
                cwd=Path(__file__).resolve().parents[1],
                env=environment,
            )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except (OSError, ValueError, CalledProcessError) as error:
        sys.exit(str(error))
