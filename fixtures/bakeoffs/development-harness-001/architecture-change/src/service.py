from transport import send


def get_status(request_id: str | None = None) -> dict[str, object]:
    return send("/status", request_id)
