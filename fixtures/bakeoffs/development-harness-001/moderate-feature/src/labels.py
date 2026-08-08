def normalize_label(value: str) -> str:
    return "-".join(value.strip().lower().split())


def display_labels(values: list[str]) -> str:
    return ", ".join(normalize_label(value) for value in values)
