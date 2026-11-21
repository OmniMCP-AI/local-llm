"""Prepare and hand off one evidence-linked YouTube Short."""

from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import re
from zipfile import ZipFile, ZipInfo

from fastest_release.validation import plain_text

from .approval import create_approval, decode_sealed, instant, json_bytes, read_sealed, require_window, retain, seal
from .engagement_link import evidence_link, verified_link
from .package import require_current_story, retain_package, story_lineage, verify_story
from .shorts_render import SCENE_SECONDS, render


CHANNEL = "youtube-shorts"
CHANNEL_ID = re.compile(r"UC[A-Za-z0-9_-]{22}")
POST_COPY = "description.txt"
PAYLOAD_FILES = ("title.txt", POST_COPY, "captions.srt", "short.mp4")
ARCHIVE = "youtube-short.zip"
MEDIA_RIGHTS = {
    "visuals": "Original chart, title cards and captions generated from the pinned release",
    "third_party_media": [],
    "audio": "none",
    "channel_clearance": "Editor approval requires a YouTube use rights reference",
}
COPY = {
    "en": ("One benchmark for one tested setup.", "Source", "See the evidence in the description."),
    "zh-CN": ("这项基准测试针对一套配置。", "来源", "请在视频说明中查看证据。"),
    "zh-TW": ("這項基準測試針對一套配置。", "來源", "請在影片說明中查看證據。"),
}


def _copy(draft, engagement_key=None):
    setup, source, citation = COPY[draft["locale"]]
    story = draft["story"]
    title = story["copy"]["headline"]
    result = story["copy"]["body"]
    cues = (setup, result, citation)
    link = evidence_link(draft, engagement_key)
    description = f"{result}\n\n{source}: {story['attribution']['label']}\n{link}\n"
    if any(symbol in description for symbol in "<>"):
        raise ValueError("source attribution contains characters unsupported in a YouTube description")
    captions = []
    start = 0
    for index, (cue, seconds) in enumerate(zip(cues, SCENE_SECONDS, strict=True), start=1):
        end = start + seconds
        captions.append(f"{index}\n00:00:{start:02},000 --> 00:00:{end:02},000\n{cue}\n")
        start = end
    return cues, {
        "title.txt": (title + "\n").encode(),
        POST_COPY: description.encode(),
        "captions.srt": "\n".join(captions).encode(),
    }


def prepare(store, draft_path, output_dir, *, font_file=None, engagement_key=None):
    draft = read_sealed(draft_path, "draft_revision")
    maximum = verify_story(store, draft)
    cues, files = _copy(draft, engagement_key)
    files["short.mp4"] = render(draft, maximum, cues, font_file)
    package = seal({
        "schema_version": 1,
        "channel": CHANNEL,
        "draft": draft,
        **({"engagement_key": engagement_key} if engagement_key is not None else {}),
        "media_rights": MEDIA_RIGHTS,
        "files": {name: sha256(body).hexdigest() for name, body in files.items()},
    }, "payload_sha256")
    files["package.json"] = json_bytes(package)
    return retain_package(output_dir, package["payload_sha256"], files)


def _load_package(read):
    package = decode_sealed(read("package.json"), "payload_sha256", "package.json")
    if (
        package["schema_version"] != 1 or package["channel"] != CHANNEL
        or package["media_rights"] != MEDIA_RIGHTS or set(package["files"]) != set(PAYLOAD_FILES)
    ):
        raise ValueError("unsupported YouTube Shorts package")
    files = {name: read(name) for name in PAYLOAD_FILES}
    if any(sha256(body).hexdigest() != package["files"][name] for name, body in files.items()):
        raise ValueError("package bytes differ from the reviewed payload")
    return package, files


def approve(package_path, approval_dir, *, account, payload_sha256, window_start, window_end,
            approved_by, rights_reference):
    if not CHANNEL_ID.fullmatch(account):
        raise ValueError("account must be a YouTube channel ID beginning with UC")
    package, _ = _load_package(lambda name: (package_path / name).read_bytes())
    if payload_sha256 != package["payload_sha256"]:
        raise ValueError("reviewed payload digest differs from the requested approval")
    approval = create_approval(
        channel=CHANNEL, account=account, story_revision=package["draft"]["draft_revision"],
        payload_sha256=payload_sha256, window_start=window_start, window_end=window_end,
        approved_by=approved_by, rights_reference=rights_reference,
    )
    return retain(approval_dir / f"{approval['approval_id']}.json", json_bytes(approval))


def _read_approval(path):
    approval = read_sealed(path, "approval_id")
    if approval["channel"] != CHANNEL or not CHANNEL_ID.fullmatch(approval["account"]):
        raise ValueError("approval must name a YouTube channel ID")
    expected = create_approval(**{
        key: approval[key] for key in (
            "channel", "account", "story_revision", "payload_sha256", "window_start",
            "window_end", "approved_by", "rights_reference",
        )
    })
    if expected != approval:
        raise ValueError("invalid YouTube Shorts approval")
    return approval


def _check_coverage(approval, package):
    if (
        package["payload_sha256"] != approval["payload_sha256"]
        or package["draft"]["draft_revision"] != approval["story_revision"]
    ):
        raise ValueError("approval does not cover this package")


def _receipt_path(directory, approval):
    path = directory / "receipt.json"
    try:
        receipt = read_sealed(path, "receipt_id")
    except FileNotFoundError:
        return None
    if receipt["approval_id"] != approval["approval_id"]:
        raise ValueError("this story and channel already have a receipt for a different approval")
    return path.resolve()


def export(store, package_path, approval_path, delivery_dir):
    approval = _read_approval(approval_path)
    package, files = _load_package(lambda name: (package_path / name).read_bytes())
    _check_coverage(approval, package)
    directory = delivery_dir / approval["delivery_id"]
    confirmed = _receipt_path(directory, approval)
    if confirmed:
        return confirmed
    require_window(approval, datetime.now(timezone.utc))
    _, copy = _copy(package["draft"], package.get("engagement_key"))
    if any(files[name] != body for name, body in copy.items()):
        raise ValueError("approved text differs from the pinned public evidence")

    archive_bytes = BytesIO()
    files.update({"package.json": json_bytes(package), "approval.json": json_bytes(approval)})
    with ZipFile(archive_bytes, "w") as archive:
        for name, body in files.items():
            archive.writestr(ZipInfo(name), body)
    verify_story(store, package["draft"])
    require_current_story(store, package["draft"])
    require_window(approval, datetime.now(timezone.utc))
    handoff = retain(directory / ARCHIVE, archive_bytes.getvalue())
    return _receipt_path(directory, approval) or handoff


def record_receipt(approval_path, delivery_dir, *, account, url, published_at, operator, observed_engagement_url=None):
    approval = _read_approval(approval_path)
    if account != approval["account"]:
        raise ValueError("observed publication must use the approved channel ID")
    post = re.fullmatch(r"https://www\.youtube\.com/shorts/([A-Za-z0-9_-]{11})", url)
    if not post:
        raise ValueError("use the canonical YouTube Shorts URL")
    if not plain_text(operator):
        raise ValueError("receipt requires the operator who verified the live Short")
    when = instant(published_at)
    require_window(approval, when)
    if when > datetime.now(timezone.utc):
        raise ValueError("publication timestamp is in the future")

    directory = delivery_dir / approval["delivery_id"]
    with ZipFile(directory / ARCHIVE) as archive:
        if archive.read("approval.json") != json_bytes(approval):
            raise ValueError("the recorded handoff used a different approval")
        package, files = _load_package(archive.read)
    _check_coverage(approval, package)
    link = verified_link(package, files[POST_COPY], observed_engagement_url)
    draft = package["draft"]
    receipt = seal({
        "schema_version": 1,
        "status": "published",
        "channel": CHANNEL,
        "account": account,
        "approval_id": approval["approval_id"],
        "delivery_id": approval["delivery_id"],
        "payload_sha256": approval["payload_sha256"],
        "render_sha256": package["files"]["short.mp4"],
        "release_id": draft["release"]["release_id"],
        "claim_ids": [claim["claim_id"] for claim in draft["story"]["claims"]],
        "operator": operator,
        "published_at": when.isoformat(),
        "post_id": post[1],
        **link,
        "url": url,
    }, "receipt_id")
    return retain(directory / "receipt.json", json_bytes(receipt))


def corrections(store, delivery_dir):
    """Route withdrawn or superseded evidence to each live Short operator."""
    tasks = []
    for path in sorted(delivery_dir.glob("*/receipt.json")):
        receipt = read_sealed(path, "receipt_id")
        if receipt["channel"] != CHANNEL or receipt["status"] != "published":
            continue
        if receipt["delivery_id"] != path.parent.name:
            raise ValueError(f"receipt is in the wrong delivery directory: {path}")
        reason, replacement = story_lineage(store, receipt["release_id"])
        if reason is None:
            continue
        path_for_task = path.with_name("correction.json")
        if path_for_task.exists():
            prior = read_sealed(path_for_task, "correction_id")
            if prior["receipt_id"] != receipt["receipt_id"]:
                raise ValueError("correction does not match the recorded live receipt")
            if prior["reason"] == reason and prior.get("replacement_release_id") == replacement:
                tasks.append(path_for_task.resolve())
                continue
            # Keep the immutable original task when the evidence changes again.
            suffix = replacement or "withdrawn"
            path_for_task = path.with_name(f"correction-{suffix}.json")
        task = seal({
            "schema_version": 1,
            "status": "needs_correction",
            "reason": reason,
            **({"replacement_release_id": replacement} if replacement else {}),
            "action": "make_private_or_replace_with_approved_correction",
            **{key: receipt[key] for key in (
                "channel", "account", "delivery_id", "receipt_id", "release_id", "claim_ids", "post_id", "url",
            )},
        }, "correction_id")
        tasks.append(retain(path_for_task, json_bytes(task)))
    return tasks
