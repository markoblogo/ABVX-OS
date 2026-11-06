"""Synthetic in-memory Keychain fixture; never used by the production broker."""

SERVICE = "ABVX Credential Broker"


class FakeKeychain:
    def __init__(self):
        self.items: dict[tuple[str, str], str] = {}

    def put(self, account: str, value: str) -> None:
        self.items[(SERVICE, account)] = value

    def update(self, account: str, value: str) -> None:
        if (SERVICE, account) not in self.items:
            raise RuntimeError("credential unavailable")
        self.items[(SERVICE, account)] = value

    def get(self, account: str) -> str:
        try:
            return self.items[(SERVICE, account)]
        except KeyError as error:
            raise RuntimeError("credential unavailable") from error

    def _read_for_provider(self, account: str) -> str:
        return self.get(account)

    def delete(self, account: str) -> None:
        self.items.pop((SERVICE, account), None)

    def exists(self, account: str) -> bool:
        return (SERVICE, account) in self.items
