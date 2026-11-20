"""Run the research contract tests in a disposable checkout of pinned llmfit."""
import argparse
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import sys

# Reuse the importer's source pin and seed location.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastest_release.llmfit_build import pinned_workspace, run_owned
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain", help="Optional Rust toolchain name passed to rustup.")
    args = parser.parse_args()
    with pinned_workspace(args.toolchain) as (upstream, cargo, environment):
        for path in CONTRACT_INPUTS:
            digest = sha256((upstream / path).read_bytes()).hexdigest()
            print(f"{digest}  {UPSTREAM}/blob/{UPSTREAM_COMMIT}/{path}", flush=True)

        test = Path(__file__).with_name("fastest_research_contract.rs")
        shutil.copyfile(test, upstream / "llmfit-core" / "tests" / test.name)
        run_owned(
            [cargo, "test", "--locked", "-q", "-p", "llmfit-core", "--test", test.stem],
            cwd=upstream,
            env={
                **environment,
                "FASTEST_RESEARCH_LLMFIT_SEED": str(SEED_ROOT / "llmfit"),
            },
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
