def build_headers(request_id: str | None = None) -> dict[str, str]:
    headers = {"accept": "application/json"}
    if request_id:
        headers["x-request-id"] = request_id
    return headers


def send(path: str, request_id: str | None = None) -> dict[str, object]:
    return {"path": path, "headers": build_headers(request_id)}
