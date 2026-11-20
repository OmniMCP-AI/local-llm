"""Check production discovery and both PostgreSQL readers over HTTP."""

import argparse
import json
import sys
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import urlopen


def check(origin):
    catalog_url = origin.rstrip("/") + "/.well-known/api-catalog"
    with urlopen(catalog_url, timeout=3) as response:
        catalog = json.load(response)
    description = catalog["linkset"][0]["service-desc"][0]["href"]
    with urlopen(urljoin(catalog_url, description), timeout=3) as response:
        specification = json.load(response)

    empty_id = "00000000-0000-0000-0000-000000000000"
    for path, query in (
        ("/api/v1/evidence", "evidence_id"),
        ("/api/v1/evidence", "release"),
        ("/api/v1/historical-offers", "release"),
    ):
        if path not in specification["paths"]:
            raise ValueError(f"{path} is missing from public discovery")
        try:
            with urlopen(urljoin(catalog_url, path) + f"?{query}={empty_id}", timeout=3) as response:
                payload = json.load(response)
        except HTTPError as error:
            with error:
                # An empty lookup still exercises the configured PostgreSQL reader.
                if error.code not in (404, 410):
                    raise
                payload = json.load(error)
        if payload["api_version"] != specification["info"]["version"]:
            raise ValueError(f"{path} did not return a versioned API response")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("origin", help="Release origin, for example http://127.0.0.1:8000")
    args = parser.parse_args()
    try:
        check(args.origin)
    except (OSError, KeyError, IndexError, TypeError, ValueError) as error:
        print(f"Release origin is unavailable: {error}", file=sys.stderr)
        return 1
    print("Release origin is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
