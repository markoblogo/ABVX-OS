"""Prepare an ABVXsite intake from ready JSON-frontmatter Markdown; no publication."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date as calendar_date, datetime, timezone
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from abvx_harness.content_ops import prepare_content_item
from abvx_harness.harness import ValidationError, now_iso


def publication_fixture(source: str, item_id: str, source_uri: str, assets: list[dict]) -> dict:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item_id):
        raise ValidationError("id must be a safe lowercase identifier")
    match = re.match(r"\A---\s*\n(.*?)\n---(?:\n|$)(.*)\Z", source, re.S)
    if not match:
        raise ValidationError("source must use ABVXsite JSON frontmatter")
    data = json.loads(match[1])
    body = match[2].strip()
    story = data.get("type") == "working-story"
    if not story and data.get("primarySection") != "writing":
        raise ValidationError("only native Writing and Working Stories are supported")
    for field in ("title", "slug", "summary"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValidationError(f"source requires {field}")
    if not body:
        raise ValidationError("body must not be empty")
    date = data.get("date" if story else "publishedAt")
    if not date:
        raise ValidationError("explicit publication date required")
    if not isinstance(date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValidationError("publication date must be YYYY-MM-DD")
    if calendar_date.fromisoformat(date) > datetime.now(timezone.utc).date():
        raise ValidationError("future publication requires a later reviewed release")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", data["slug"]):
        raise ValidationError("slug must be a safe lowercase URL slug")
    if not story and (data.get("visibility") != "public" or data.get("status") != "live"):
        raise ValidationError("native Writing must explicitly be ready, public and live")
    if not story and data.get('id') != data['slug']:
        raise ValidationError("native Writing id must match its slug")
    if not story and bool(data.get('videoUrl')) != bool(data.get('videoUploadedAt')):
        raise ValidationError('video URL and upload date must be provided together')
    if not story and data.get('videoUrl'):
        if not re.fullmatch(r'https://www\.youtube\.com/watch\?v=[\w-]{11}', data['videoUrl']):
            raise ValidationError('native Writing supports a reviewed YouTube watch URL')
        uploaded = data.get('videoUploadedAt')
        try:
            uploaded_date = datetime.fromisoformat(uploaded.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            raise ValidationError('video requires a valid non-future upload date') from None
        if uploaded_date.tzinfo is None or uploaded_date > datetime.now(timezone.utc):
            raise ValidationError('video requires a valid non-future upload date')
    image = data.get("coverImage" if story else "media") or {}
    images = [image, *(data.get('illustrations') or [])] if story else [image, data.get('heroImage')]
    if not story:
        for entry in filter(None, images):
            if not entry.get('alt') or not isinstance(entry.get('width'), int) or not isinstance(entry.get('height'), int) or min(entry['width'], entry['height']) <= 0:
                raise ValidationError('native image requires alt text and positive dimensions')
            if entry['src'].startswith('https://') and (not data.get('videoUrl') or entry['src'] != f"https://i.ytimg.com/vi/{data['videoUrl'].partition('?v=')[2]}/hqdefault.jpg"):
                raise ValidationError('only a matching YouTube thumbnail may be remote')
    referenced = {entry['src'] for entry in images if entry and not entry['src'].startswith('https://')}
    targets = [asset["target"] for asset in assets]
    if set(targets) != referenced or len(targets) != len(set(targets)):
        raise ValidationError("every referenced image requires its own asset mapping, including existing site files")
    payload = {
        "excerpt": data["summary"], "body_lines": [body],
        "tags": data.get("topics" if story else "tags", []),
        "asset_refs": [asset["source"] for asset in assets],
        "source_refs": [source_uri], "media_event_candidate": None,
        "date_published": date, "language": data.get("language", "en"),
        "cover_image": image.get("src"), "image_alt": image.get("alt"),
        **({"seo_title": data["seoTitle"]} if data.get("seoTitle") else {}),
        "source_markdown": source,
        "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "media_assets": assets,
    }
    return {
        "schema_version": "v1", "id": item_id, "project": "abvxsite",
        "surface": "working-stories" if story else "writing",
        "kind": "working-story" if story else data.get("type", "note"),
        "title": data["title"], "slug": data["slug"], "summary": data["summary"],
        "locales": [payload["language"]],
        "adapter_id": "abvx.working-story" if story else "abvx.writing",
        "payload": payload,
        "provenance": {"recorded_by": "ABVX-PUBLISHING-004", "source_uri": source_uri, "observed_at": now_iso()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--asset", action="append", default=[], help="/absolute/image.webp=/media/path/image.webp")
    args = parser.parse_args()
    assets = []
    for entry in args.asset:
        source, separator, target = entry.partition("=")
        if not separator or not Path(source).is_file() or not target.startswith("/media/"):
            parser.error("asset must identify an existing local file and a /media/ destination")
        assets.append({"source": str(Path(source).resolve()), "target": target,
                       "sha256": hashlib.sha256(Path(source).read_bytes()).hexdigest()})
    fixture = publication_fixture(args.source.read_bytes().decode("utf-8"), args.id, str(args.source.resolve()), assets)
    # This input is a local operational artifact, not a committed public fixture.
    intake = ROOT / ".tmp" / "abvx-publication-intakes" / f"{args.id}.json"
    intake.parent.mkdir(parents=True, exist_ok=True)
    intake.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    item = prepare_content_item(ROOT, str(intake))
    print(json.dumps({"id": item["id"], "status": item["status"], "adapter": item["adapter"]["id"],
                      "next": f"./bin/abvx content inspect {item['id']} --json"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
