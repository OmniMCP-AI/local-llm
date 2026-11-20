"""Capture a private four-user workload against a dedicated pinned llama-server."""

import argparse
import asyncio
from contextlib import suppress
from datetime import datetime, timezone
from ipaddress import ip_address
import json
from pathlib import Path
import platform
from time import monotonic_ns

from fastest_serving import (INPUT_TOKENS, INTERVAL_MS, OUTPUT_TOKENS, PROTOCOL, REQUESTS,
                             START_TOLERANCE_MS, TIMEOUT_MS, USERS, WINDOW_MS)


NS_PER_MS = 1_000_000
MAX_RESPONSE_BYTES = 1_048_576
WARMUP_TIMEOUT_MS = 180_000
ERASE_TIMEOUT_MS = 15_000


def _payload(user):
    prompt = [1000 + ((index + 251 * user) % 1000) for index in range(INPUT_TOKENS)]
    return json.dumps({"prompt": prompt, **PROTOCOL["request_options"]}).encode()


def _response_object(body):
    try:
        data = json.loads(body)
    except (ValueError, UnicodeError):
        return None
    return data if isinstance(data, dict) else None


async def _post(host, port, path, payload, started_ns, timeout_ms):
    """Read the pinned non-streaming response under one end-to-end deadline."""
    authority = f"[{host}]" if ":" in host else host
    request = (f"POST {path} HTTP/1.1\r\nHost: {authority}:{port}\r\nConnection: close\r\n"
               f"Content-Type: application/json\r\nContent-Length: {len(payload)}\r\n\r\n").encode() + payload
    deadline = started_ns + timeout_ms * NS_PER_MS
    writer = None
    body = bytearray()
    response = {"started_ns": started_ns, "http_status": None, "response_headers": None}
    try:
        async with asyncio.timeout((deadline - monotonic_ns()) / 1_000_000_000):
            reader, writer = await asyncio.open_connection(host, port)
            writer.write(request)
            await writer.drain()
            headers = await reader.readuntil(b"\r\n\r\n")
            response["response_headers"] = headers.decode("latin-1")
            first, *fields = headers.split(b"\r\n")
            version, status, *_ = first.split(b" ")
            response["http_status"] = int(status)
            if version not in (b"HTTP/1.0", b"HTTP/1.1") or not 100 <= int(status) < 600:
                raise ValueError("Invalid HTTP status line.")
            headers = [field.lower().split(b":", 1) for field in fields if field]
            lengths = [value for key, value in headers if key == b"content-length"]
            if len(lengths) != 1 or any(key == b"transfer-encoding" for key, _ in headers):
                raise ValueError("Expected a fixed-length llama-server response.")
            length = int(lengths[0])
            if not 0 <= length <= MAX_RESPONSE_BYTES:
                raise ValueError("HTTP body exceeds the capture size limit.")
            while len(body) < length:
                chunk = await reader.read(length - len(body))
                if not chunk:
                    raise ValueError("HTTP body ended before its declared length.")
                body.extend(chunk)
    except (TimeoutError, OSError, ValueError, asyncio.IncompleteReadError, asyncio.LimitOverrunError) as error:
        response["transport_error"] = type(error).__name__
        response["transport_detail"] = str(error)
        if isinstance(error, TimeoutError):
            response["timeout"] = True
    finally:
        response["finished_ns"] = monotonic_ns()
        if writer is not None:
            writer.close()
            with suppress(ConnectionError):
                await writer.wait_closed()
    if response["finished_ns"] > deadline:
        response["timeout"] = True
    return response, body


def _outcome(response, body):
    if response.get("timeout"):
        return "timeout", 0, "Client deadline elapsed."
    if error := response.get("transport_error"):
        return "failed", 0, f"Client transport failed ({error})."
    status = response["http_status"]
    if not 200 <= status < 300:
        return "failed", 0, f"Server returned HTTP {status}."
    data = _response_object(body)
    tokens = data.get("tokens") if data is not None else None
    if not isinstance(tokens, list) or any(type(token) is not int or not 0 <= token < 2**31 for token in tokens):
        return "rejected", 0, "Response did not contain valid token IDs."
    if data.get("stop") is not True or "error" in data:
        return "rejected", len(tokens), "Response did not report a complete non-streaming completion."
    if len(tokens) != OUTPUT_TOKENS:
        return "rejected", len(tokens), f"Response contained {len(tokens)} token IDs, expected {OUTPUT_TOKENS}."
    return "accepted", len(tokens), None


def _save_ledger(output, ledger):
    staging = output / "capture.next.json"
    staging.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    staging.replace(output / "capture.json")


async def _sleep_until(target_ns):
    # A timer can fire just ahead of its monotonic target.
    while (remaining := target_ns - monotonic_ns()) > 0:
        await asyncio.sleep(remaining / 1_000_000_000)


async def capture(output, host, port, *, diagnostic_reason=None, notes=None):
    address = ip_address(host)
    endpoint = address.ipv4_mapped if address.version == 6 and address.ipv4_mapped else address
    if endpoint.is_loopback and not diagnostic_reason:
        raise ValueError("Loopback requires an explicit diagnostic reason. Use a separate client for a serving run.")
    if not 1 <= port <= 65535:
        raise ValueError("Invalid llama-server port.")

    output.mkdir(mode=0o700)
    payloads = {user: _payload(user) for user in USERS}
    for user, payload in payloads.items():
        (output / f"request-{user}.json").write_bytes(payload)
    attempts = []
    ledger = {
        "kind": "diagnostic" if diagnostic_reason else "private-capture",
        "protocol": PROTOCOL["id"], "diagnostic_reason": diagnostic_reason, "operator_notes": notes,
        "server": {"ip": host, "port": port},
        "client": {"host": platform.node(), "platform": platform.platform(), "python": platform.python_version()},
        "duration_ms": 0, "attempts": attempts, "status": "starting",
        "power": {"status": "missing", "reason": "No calibrated cumulative AC input meter evidence was supplied."},
    }
    started_ns = None
    with (output / "trace.jsonl").open("x", encoding="utf-8", buffering=1) as trace:
        def retain(event, name=None, body=None):
            if body is not None:
                (output / name).write_bytes(body)
                event["response_file"] = name
            trace.write(json.dumps(event, separators=(",", ":")) + "\n")

        async def complete(user, request=None):
            now = monotonic_ns()
            event = {"phase": "warmup" if request is None else "timed", "user": user}
            timeout = WARMUP_TIMEOUT_MS
            if request is not None:
                scheduled_ms = (request - 1) * INTERVAL_MS
                event.update(request=request, scheduled_ms=scheduled_ms)
                start_offset = now - started_ns
                if start_offset > (scheduled_ms + START_TOLERANCE_MS) * NS_PER_MS:
                    retain({**event, "outcome": "unrecorded", "started_ns": now,
                            "reason": "Client missed the scheduled arrival slot."})
                    return False
                timeout = TIMEOUT_MS
            response, body = await _post(host, port, "/completion", payloads[user], now, timeout)
            outcome, tokens, reason = _outcome(response, body)
            elapsed = response["finished_ns"] - now
            attempt = {"user": user, "outcome": outcome, "output_tokens": tokens,
                       "elapsed_ms": timeout if outcome == "timeout" else max(1, (elapsed + NS_PER_MS - 1) // NS_PER_MS)}
            if reason:
                attempt["reason"] = reason
            if request is not None:
                attempt.update(request=request, started_ms=start_offset // NS_PER_MS)
                attempts.append(attempt)
            name = f"response-{request:02d}-{user}.bin" if request is not None else f"warmup-{user}.bin"
            retain({**event, **response, **attempt}, name, body)
            return outcome == "accepted"

        _save_ledger(output, ledger)
        try:
            if not all(await asyncio.gather(*(complete(user) for user in USERS))):
                raise ValueError("Warmup did not complete successfully. See the private trace.")
            for slot in range(len(USERS)):
                path = f"/slots/{slot}?action=erase"
                response, body = await _post(host, port, path, b"{}", monotonic_ns(), ERASE_TIMEOUT_MS)
                retain({"phase": "erase", "slot": slot, **response}, f"erase-{slot}.bin", body)
                data = _response_object(body)
                if (response.get("timeout") or response.get("transport_error") or response["http_status"] != 200
                        or data is None or type(data.get("id_slot")) is not int or data["id_slot"] != slot
                        or type(data.get("n_erased")) is not int or data["n_erased"] < 0):
                    raise ValueError(f"Could not confirm KV erasure for slot {slot}. See the private trace.")

            ledger["window_started_utc"] = datetime.now(timezone.utc).isoformat()
            started_ns = monotonic_ns()
            ledger["window_started_ns"] = started_ns
            ledger["status"] = "capturing"
            for request in range(1, REQUESTS + 1):
                await _sleep_until(started_ns + (request - 1) * INTERVAL_MS * NS_PER_MS)
                await asyncio.gather(*(complete(user, request) for user in USERS))
                ledger["duration_ms"] = min(WINDOW_MS, (monotonic_ns() - started_ns) // NS_PER_MS)
                attempts.sort(key=lambda attempt: (attempt["request"], attempt["user"]))
                _save_ledger(output, ledger)
            await _sleep_until(started_ns + WINDOW_MS * NS_PER_MS)
            ledger["status"] = "complete" if len(attempts) == len(USERS) * REQUESTS else "partial"
        except BaseException as error:
            ledger.update(status="interrupted" if isinstance(error, asyncio.CancelledError) else "failed",
                          error=str(error) or type(error).__name__)
            raise
        finally:
            if started_ns is not None:
                ledger["duration_ms"] = min(WINDOW_MS, (monotonic_ns() - started_ns) // NS_PER_MS)
                ledger["capture_finished_utc"] = datetime.now(timezone.utc).isoformat()
            attempts.sort(key=lambda attempt: (attempt["request"], attempt["user"]))
            _save_ledger(output, ledger)
    return ledger


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New directory for the private trace and response bodies.")
    parser.add_argument("--host", required=True, help="IP address of the dedicated serving host.")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--diagnostic-reason", help="Record a protocol deviation, including use of loopback.")
    parser.add_argument("--notes", help="Private notes identifying the client and its network boundary.")
    args = parser.parse_args()
    try:
        ledger = asyncio.run(capture(args.output, args.host, args.port,
                                     diagnostic_reason=args.diagnostic_reason, notes=args.notes))
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    if ledger["status"] != "complete":
        parser.exit(1, f"The scheduled window was incomplete. Private evidence retained in {args.output}\n")


if __name__ == "__main__":
    main()
