def parse_timeout(value: int | None, default: int = 30) -> int:
    # Historical regression: truthiness incorrectly discarded an explicit zero.
    return value or default
