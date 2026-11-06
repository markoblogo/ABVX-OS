"""Prepare a reviewed ABVXsite intake from ready Markdown or a supported draft; no publication."""
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


def normalize_draft(text: str, publication_date: str, supplement: dict) -> tuple[str, dict]:
    """Normalize only the documented H1 + SEO suffix; never interpret recipe prose."""
    if not isinstance(supplement, dict) or set(supplement) - {"recipe", "media"}:
        raise ValidationError("supplement supports only reviewed recipe/media fields")
    text = text.replace("\r\n", "\n")
    title = re.search(r"(?m)^# ([^\n]+)\n", text)
    separators = list(re.finditer(
        r"(?m)^---[ \t]*\n[ \t\n]*### (?:SEO и метаданные для ABVX|SEO and metadata for ABVX)[ \t]*\n", text))
    if not title or len(separators) != 1 or title.end() >= separators[0].start():
        raise ValidationError("draft requires one article H1 and one supported SEO suffix; use --source for other formats")
    body = text[title.end():separators[0].start()].strip()
    fields = {}
    allowed = {"title", "seo title", "slug", "meta description", "excerpt", "collection", "content type", "topics", "language", "preparation time", "cooking time", "cooling time", "servings", "yield"}
    for line in text[separators[0].end():].splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"\*\*([^*]+):\*\*[ \t]*(.+)", line.strip())
        if not match:
            raise ValidationError("unsupported SEO suffix line; review source rather than dropping it")
        key, value = match[1].strip().casefold(), match[2].strip()
        if key not in allowed or key in fields:
            raise ValidationError("unknown or duplicate SEO field: " + key)
        fields[key] = value[1:-1] if value.startswith("`") and value.endswith("`") and key != "topics" else value
    for key in ("slug", "excerpt", "meta description", "language"):
        if not fields.get(key):
            raise ValidationError("draft requires SEO field: " + key)
    if fields.get("title", title[1]) != title[1] or not body:
        raise ValidationError("title disagreement or empty article body")
    slug = fields["slug"]
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValidationError("safe lowercase slug required")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", publication_date) or calendar_date.fromisoformat(publication_date) > datetime.now(timezone.utc).date():
        raise ValidationError("explicit non-future publication date required")
    topics = fields.get("topics", "")
    if topics and not re.fullmatch(r"`[^`\n]+`(?:\s*,\s*`[^`\n]+`)*", topics):
        raise ValidationError("topics must be comma-separated backtick labels")
    collection = fields.get("collection")
    if collection and collection != "Kitchen Notes":
        raise ValidationError("new collections are outside draft normalization")
    data = {"id": slug, "slug": slug, "title": title[1], "summary": fields["excerpt"],
            "seoDescription": fields["meta description"], "primarySection": "writing", "appearsIn": ["writing"],
            "type": fields.get("content type", "note"), "visibility": "public", "status": "live",
            "language": fields["language"], "publishedAt": publication_date, "updatedAt": publication_date,
            "tags": re.findall(r"`([^`]+)`", topics), "links": [], "featured": False,
            "sortRank": 500, "needsReview": False, "homepageEligible": True}
    if fields.get("seo title"):
        data["seoTitle"] = fields["seo title"]
    if collection:
        data["collection"] = "kitchen-notes"
    if data["type"] == "recipe":
        recipe = supplement.get("recipe")
        if collection != "Kitchen Notes" or not isinstance(recipe, dict) or not recipe.get("ingredients") or not recipe.get("instructions"):
            raise ValidationError("recipes need reviewed ingredients/instructions in --supplement; no quantities are inferred")
        recipe = dict(recipe)
        if fields.get("yield") and fields.get("servings") and fields["yield"] != fields["servings"]:
            raise ValidationError("supplied yield and servings disagree")
        yield_text = fields.get("yield") or fields.get("servings")
        if yield_text:
            if recipe.get("recipeYield", yield_text) != yield_text:
                raise ValidationError("recipe yield disagrees with supplied servings")
            recipe["recipeYield"] = yield_text
        timing_keys = ("preparation time", "cooking time", "cooling time")
        timing = " ".join(key.capitalize() + ": " + fields[key] for key in timing_keys if fields.get(key))
        if timing:
            if recipe.get("timingText") and any(fields[key] not in recipe["timingText"] for key in timing_keys if fields.get(key)):
                raise ValidationError("reviewed timing must retain all supplied timing details")
            recipe.setdefault("timingText", timing)
        data["recipe"] = recipe
    elif "recipe" in supplement or any(key in fields for key in ("preparation time", "cooking time", "cooling time", "servings", "yield")):
        raise ValidationError("recipe metadata needs recipe content type")
    report = {"bodyPreserved": True, "bodySha256": hashlib.sha256(body.encode()).hexdigest(),
              "titleMovedToMetadata": True, "serviceSuffixRemoved": True, "metadataFields": sorted(fields)}
    return "---\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n---\n\n" + body + "\n", report


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
    images = [image, *(data.get('illustrations') or [])] if story else [image, data.get('heroImage'), *(data.get('illustrations') or [])]
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
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--source", type=Path, help="Ready JSON-frontmatter Markdown (unchanged existing path)")
    inputs.add_argument("--draft", type=Path, help="Article H1/body plus the supported SEO suffix")
    parser.add_argument("--id", required=True)
    parser.add_argument("--asset", action="append", default=[], help="/absolute/image.webp=/media/path/image.webp")
    parser.add_argument("--run", help="Existing active publication cycle; mandatory with --draft")
    parser.add_argument("--date", default=datetime.now(timezone.utc).date().isoformat())
    parser.add_argument("--supplement", type=Path, help="Reviewed recipe and optional media dimensions/alt JSON")
    parser.add_argument("--cover", type=Path, help="Supplied cover; PNG dimensions are read without changing bytes")
    parser.add_argument("--image-alt", help="Reviewed alt text for supplied cover")
    args = parser.parse_args()
    source_path = args.source
    source = source_path.read_bytes().decode("utf-8") if source_path else None
    report = None
    if args.draft:
        from abvx_harness.publication_learning import folder
        if not args.run or args.asset:
            parser.error("--draft needs --run and uses --cover instead of --asset")
        cycle_dir = folder(ROOT, args.run)
        cycle = json.loads((cycle_dir / "cycle.json").read_text())
        if args.id not in cycle.get("itemIds", []) or (cycle_dir / "outcome.json").exists() or (cycle_dir / "aborted.json").exists():
            parser.error("draft requires membership in an active, uncompleted cycle")
        supplement = json.loads(args.supplement.read_text()) if args.supplement else {}
        source, report = normalize_draft(args.draft.read_bytes().decode("utf-8"), args.date, supplement)
        front, _, body = source[4:].partition("\n---")
        data = json.loads(front)
        if args.cover:
            media = dict(supplement.get("media") or {})
            if set(media) - {"width", "height", "alt", "role"}:
                parser.error("cover supplement cannot override the generated media path")
            raw = args.cover.read_bytes()
            extension = args.cover.suffix.lower()
            if extension not in {".png", ".jpg", ".jpeg", ".webp"}:
                parser.error("unsupported cover format")
            if extension == ".png":
                if len(raw) < 24 or raw[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR":
                    parser.error("invalid or truncated PNG header")
                import struct
                width, height = struct.unpack(">II", raw[16:24])
                if any(media.get(key, actual) != actual for key, actual in (("width", width), ("height", height))):
                    parser.error("reviewed dimensions disagree with supplied PNG")
                media.update(width=width, height=height)
            media["alt"] = args.image_alt or media.get("alt")
            media.setdefault("role", "generic-thumbnail")
            media["src"] = "/media/writing/" + data["slug"] + extension
            data["media"] = media
            args.asset = [str(args.cover.resolve()) + "=" + media["src"]]
        elif supplement.get("media") or args.image_alt or data["type"] == "recipe":
            parser.error("recipe/media metadata requires the supplied --cover")
        source = "---\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n---" + body
        source_path = cycle_dir / "article.md"
    elif any((args.run, args.supplement, args.cover, args.image_alt)):
        parser.error("draft options cannot silently alter ready --source Markdown")
    assets = []
    for entry in args.asset:
        asset_source, separator, target = entry.partition("=")
        if not separator or not Path(asset_source).is_file() or not target.startswith("/media/"):
            parser.error("asset must identify an existing local file and a /media/ destination")
        assets.append({"source": str(Path(asset_source).resolve()), "target": target,
                       "sha256": hashlib.sha256(Path(asset_source).read_bytes()).hexdigest()})
    fixture = publication_fixture(source, args.id, str((args.draft or source_path).resolve()), assets)
    if report is not None:
        if source_path.exists() and source_path.read_bytes() != source.encode():
            parser.error("normalized source already exists with different content; review instead of overwriting")
        source_path.write_bytes(source.encode())
        (source_path.parent / "normalization.json").write_text(json.dumps(report, indent=2) + "\n")
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
