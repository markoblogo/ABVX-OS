def parse_timeout(value: int | None, default: int = 30) -> int:
    if value is None:
        return default
    if value < 0:
        raise ValueError("timeout must be non-negative")
    return value
