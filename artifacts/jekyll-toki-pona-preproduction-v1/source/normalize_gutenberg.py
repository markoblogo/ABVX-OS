"""Bounded Project Gutenberg #42 normalizer for the Jekyll pre-production sample."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path


RAW = Path("gutenberg-42-2026-09-21.txt")
OUT = Path("jekyll-hyde-gutenberg-42-normalized.txt")
START = "STORY OF THE DOOR"
END = "*** END OF THE PROJECT GUTENBERG EBOOK"


def main() -> None:
    raw = RAW.read_text(encoding="utf-8")
    start = raw.index(START, raw.index("*** START OF THE PROJECT GUTENBERG EBOOK"))
    end = raw.index(END)
    body = raw[start:end].strip() + "\n"
    OUT.write_text(body, encoding="utf-8")
    print(f"words={len(body.split())}")
    print(f"sha256={sha256(body.encode()).hexdigest()}")


if __name__ == "__main__":
    main()
