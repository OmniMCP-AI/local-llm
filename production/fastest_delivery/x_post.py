"""An X post card made from the editorial release's exact numeric claim."""

from datetime import date, datetime, timezone
from decimal import Decimal
import errno
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from unicodedata import normalize
from urllib.parse import urlsplit
from zipfile import ZipFile, ZipInfo

from fastest_editorial import generate_package
from fastest_release.validation import plain_text

from .approval import create_approval, instant, json_bytes, read_sealed, require_window, retain, seal


PAYLOAD_FILES = ("post.txt", "chart.png", "chart-alt.txt")
COPY = {
    "en": (
        "Median decode throughput: {value} {unit} ({samples} measurements)",
        "Correction: ", "Source: ",
        "Single bar on a scale from 0 to {maximum} {unit}.",
    ),
    "zh-CN": (
        "解码吞吐量中位数：{value} {unit}（{samples} 次测量）",
        "修订：", "来源：",
        "单柱图，刻度范围为 0 至 {maximum} {unit}。",
    ),
    "zh-TW": (
        "解碼吞吐量中位數：{value} {unit}（{samples} 次測量）",
        "修訂：", "來源：",
        "單柱圖，刻度範圍為 0 至 {maximum} {unit}。",
    ),
}


def verify_story(store, draft):
    if draft["outcome"] != "story":
        raise ValueError("draft contains no approved evidence story")
    citation = urlsplit(draft["story"]["evidence_destination"])
    checked = generate_package(
        store,
        editorial_date=date.fromisoformat(draft["editorial_date"]),
        locale=draft["locale"],
        public_origin=f"{citation.scheme}://{citation.netloc}",
        release_id=draft["release"]["release_id"],
    )
    if checked["outcome"] != "story":
        raise ValueError(f"evidence is ineligible: {checked['reason']}")
    if checked != draft:
        raise ValueError("draft differs from the pinned public evidence")
    chart = json.loads(store.artifact(draft["release"]["release_id"], "chart.json"))
    if chart["status"] != "published":
        raise ValueError("evidence is ineligible: withdrawn_release")
    return chart["scale"]["maximum"]


def _copy(draft, maximum):
    headline, correction, source_prefix, chart_description = COPY[draft["locale"]]
    story = draft["story"]
    claim, = story["claims"]
    result = headline.format(value=claim["value"], unit=claim["unit"], samples=claim["sample_count"])
    if story["kind"] == "correction":
        result = correction + result
    credit = source_prefix + story["attribution"]["label"]
    copy = normalize("NFC", f"{result}\n{credit}\n")
    link = story["evidence_destination"]
    # X v3 weights, conservatively counting emoji sequences per code point.
    single_weight = ((0, 4351), (8192, 8205), (8208, 8223), (8242, 8247))
    weight = sum(1 if any(low <= ord(char) <= high for low, high in single_weight) else 2 for char in copy)
    if weight + 23 > 280:
        raise ValueError("claim and full source attribution exceed X's 280-character limit")
    alt = f"{chart_description.format(maximum=maximum, unit=claim['unit'])} {result}. {credit}."
    return f"{copy}{link}\n".encode("utf-8"), f"{normalize('NFC', alt)}\n".encode("utf-8")


def _card(draft, maximum):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as error:
        raise ValueError("install Pillow to prepare the X chart") from error

    claim, = draft["story"]["claims"]
    value, unit = claim["value"], claim["unit"]
    image = Image.new("RGB", (1000, 500), "#f5f6f2")
    draw = ImageDraw.Draw(image)
    medium = ImageFont.load_default(size=30)
    small = ImageFont.load_default(size=24)
    label = f"{value} {unit}"
    large = ImageFont.load_default(size=64)
    if large.getlength(label) > 888:
        large = ImageFont.load_default(size=int(64 * 888 / large.getlength(label)))
    draw.text((56, 46), "Median decode throughput", font=medium, fill="#132927")
    draw.text((56, 113), label, font=large, fill="#132927")
    draw.text((56, 214), f"Measurements: {claim['sample_count']}", font=small, fill="#45615c")
    draw.rectangle((56, 284, 944, 337), fill="#dbe3dd")
    filled = round(888 * Decimal(value) / Decimal(maximum))
    if filled:
        draw.rectangle((56, 284, 56 + filled - 1, 337), fill="#087360")
    draw.text((56, 358), "0", font=small, fill="#132927")
    draw.text((944, 358), f"{maximum} {unit}", font=small, anchor="ra", fill="#132927")
    draw.text((56, 438), "fastest.ai  |  Evidence and attribution in the post", font=small, fill="#45615c")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def prepare(store, draft_path, output_dir):
    draft = read_sealed(draft_path, "draft_revision")
    maximum = verify_story(store, draft)
    post, alt = _copy(draft, maximum)
    files = {"post.txt": post, "chart.png": _card(draft, maximum), "chart-alt.txt": alt}
    package = seal({
        "schema_version": 1,
        "channel": "x",
        "draft": draft,
        "files": {name: sha256(body).hexdigest() for name, body in files.items()},
    }, "payload_sha256")
    files["package.json"] = json_bytes(package)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / package["payload_sha256"]
    with TemporaryDirectory(dir=output_dir, prefix=".review-") as staging:
        pending = Path(staging) / "package"
        pending.mkdir()
        for name, body in files.items():
            (pending / name).write_bytes(body)
        try:
            pending.rename(path)
        except OSError as error:
            if error.errno not in (errno.EEXIST, errno.ENOTEMPTY):
                raise
            if any((path / name).read_bytes() != body for name, body in files.items()):
                raise ValueError(f"existing candidate differs from {path.name}") from None
    return path.resolve()


def _load_package(path):
    package = read_sealed(path / "package.json", "payload_sha256")
    if package["schema_version"] != 1 or package["channel"] != "x" or set(package["files"]) != set(PAYLOAD_FILES):
        raise ValueError("unsupported X package")
    files = {name: (path / name).read_bytes() for name in PAYLOAD_FILES}
    if any(sha256(body).hexdigest() != package["files"][name] for name, body in files.items()):
        raise ValueError("package bytes differ from the reviewed payload")
    return package, files


def approve(package_path, approval_dir, *, account, payload_sha256, window_start, window_end,
            approved_by, rights_reference):
    if not re.fullmatch(r"@[a-zA-Z0-9_]{1,15}", account):
        raise ValueError("account must be an X @handle")
    package, _ = _load_package(package_path)
    if payload_sha256 != package["payload_sha256"]:
        raise ValueError("reviewed payload digest differs from the requested approval")
    approval = create_approval(
        channel="x", account=account.lower(), story_revision=package["draft"]["draft_revision"],
        payload_sha256=payload_sha256, window_start=window_start, window_end=window_end,
        approved_by=approved_by, rights_reference=rights_reference,
    )
    return retain(approval_dir / f"{approval['approval_id']}.json", json_bytes(approval))


def _read_approval(path):
    approval = read_sealed(path, "approval_id")
    if approval["channel"] != "x" or not re.fullmatch(r"@[a-z0-9_]{1,15}", approval["account"]):
        raise ValueError("approval must name an X @handle")
    expected = create_approval(**{
        key: approval[key] for key in (
            "channel", "account", "story_revision", "payload_sha256", "window_start",
            "window_end", "approved_by", "rights_reference",
        )
    })
    if expected != approval:
        raise ValueError("invalid X approval")
    return approval


def _receipt_path(directory, approval):
    path = directory / "receipt.json"
    try:
        receipt = read_sealed(path, "receipt_id")
    except FileNotFoundError:
        return None
    if receipt["approval_id"] != approval["approval_id"]:
        raise ValueError("this story and handle already have a receipt for a different approval")
    return path.resolve()


def export(store, package_path, approval_path, delivery_dir):
    approval = _read_approval(approval_path)
    package, files = _load_package(package_path)
    if (
        package["payload_sha256"] != approval["payload_sha256"]
        or package["draft"]["draft_revision"] != approval["story_revision"]
    ):
        raise ValueError("approval does not cover this package")
    directory = delivery_dir / approval["delivery_id"]
    confirmed = _receipt_path(directory, approval)
    if confirmed:
        return confirmed
    require_window(approval, datetime.now(timezone.utc))
    maximum = verify_story(store, package["draft"])
    if _copy(package["draft"], maximum) != (files["post.txt"], files["chart-alt.txt"]):
        raise ValueError("approved text differs from the pinned public evidence")

    output = BytesIO()
    files.update({"package.json": json_bytes(package), "approval.json": json_bytes(approval)})
    with ZipFile(output, "w") as archive:
        for name, body in files.items():
            archive.writestr(ZipInfo(name), body)
    require_window(approval, datetime.now(timezone.utc))
    handoff = retain(directory / "x-post.zip", output.getvalue())
    return _receipt_path(directory, approval) or handoff


def record_receipt(approval_path, delivery_dir, *, url, published_at, operator):
    approval = _read_approval(approval_path)
    account = approval["account"][1:]
    post = re.fullmatch(
        rf"https://x\.com/{re.escape(account)}/status/([1-9][0-9]{{0,19}})", url, re.ASCII | re.IGNORECASE,
    )
    if not post:
        raise ValueError("use the canonical X post URL for the approved handle")
    if not plain_text(operator):
        raise ValueError("receipt requires the operator who verified the live post")
    when = instant(published_at)
    require_window(approval, when)
    if when > datetime.now(timezone.utc):
        raise ValueError("publication timestamp is in the future")

    directory = delivery_dir / approval["delivery_id"]
    with ZipFile(directory / "x-post.zip") as archive:
        if archive.read("approval.json") != json_bytes(approval):
            raise ValueError("the recorded handoff used a different approval")
    post_id = post[1]
    receipt = seal({
        "schema_version": 1,
        "status": "published",
        "channel": "x",
        "account": approval["account"],
        "delivery_id": approval["delivery_id"],
        "approval_id": approval["approval_id"],
        "payload_sha256": approval["payload_sha256"],
        "operator": operator,
        "published_at": when.isoformat(),
        "post_id": post_id,
        "url": f"https://x.com/{account}/status/{post_id}",
    }, "receipt_id")
    return retain(directory / "receipt.json", json_bytes(receipt))
