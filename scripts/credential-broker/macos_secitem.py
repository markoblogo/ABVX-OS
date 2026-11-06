"""Broker-internal macOS SecItem bridge. No command-line or IPC entry point."""
from __future__ import annotations

import ctypes as C
import sys


class SecItemStore:
    def __init__(self, service: str, test_keychain: str | None = None):
        if sys.platform != "darwin":
            raise RuntimeError("macOS Keychain unavailable")
        self.cf = C.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        self.sec = C.CDLL("/System/Library/Frameworks/Security.framework/Security")
        self.service = service
        self.test_keychain = test_keychain
        self._configure()

    def _configure(self):
        p = C.c_void_p
        self.cf.CFStringCreateWithCString.argtypes = [p, C.c_char_p, C.c_uint32]
        self.cf.CFStringCreateWithCString.restype = p
        self.cf.CFDataCreate.argtypes = [p, p, C.c_long]
        self.cf.CFDataCreate.restype = p
        self.cf.CFDataGetLength.argtypes = [p]
        self.cf.CFDataGetLength.restype = C.c_long
        self.cf.CFDataGetBytePtr.argtypes = [p]
        self.cf.CFDataGetBytePtr.restype = p
        self.cf.CFDictionaryCreateMutable.argtypes = [p, C.c_long, p, p]
        self.cf.CFDictionaryCreateMutable.restype = p
        self.cf.CFDictionarySetValue.argtypes = [p, p, p]
        self.cf.CFArrayCreate.argtypes = [p, C.POINTER(p), C.c_long, p]
        self.cf.CFArrayCreate.restype = p
        self.cf.CFRelease.argtypes = [p]
        for name in ("SecItemAdd", "SecItemCopyMatching", "SecItemUpdate", "SecItemDelete"):
            getattr(self.sec, name).restype = C.c_int32
        self.sec.SecItemAdd.argtypes = [p, C.POINTER(p)]
        self.sec.SecItemCopyMatching.argtypes = [p, C.POINTER(p)]
        self.sec.SecItemUpdate.argtypes = [p, p]
        self.sec.SecItemDelete.argtypes = [p]
        self.sec.SecKeychainOpen.argtypes = [C.c_char_p, C.POINTER(p)]
        self.sec.SecKeychainOpen.restype = C.c_int32

    def _constant(self, name: str, library=None) -> int:
        return C.c_void_p.in_dll(library or self.sec, name).value

    def _string(self, value: str) -> int:
        return self.cf.CFStringCreateWithCString(None, value.encode(), 0x08000100)

    def _data(self, value: bytes) -> int:
        buffer = C.create_string_buffer(value)
        return self.cf.CFDataCreate(None, C.cast(buffer, C.c_void_p), len(value))

    def _query(self, account: str, *, add: bool = False, return_data: bool = False, value: bytes | None = None):
        p = C.c_void_p
        owned = []
        d = self.cf.CFDictionaryCreateMutable(None, 0,
            C.addressof(C.c_byte.in_dll(self.cf, "kCFTypeDictionaryKeyCallBacks")),
            C.addressof(C.c_byte.in_dll(self.cf, "kCFTypeDictionaryValueCallBacks")))
        owned.append(d)
        def put(key, item): self.cf.CFDictionarySetValue(d, self._constant(key), item)
        service = self._string(self.service)
        acct = self._string(account)
        owned.extend((service, acct))
        put("kSecClass", self._constant("kSecClassGenericPassword"))
        put("kSecAttrService", service)
        put("kSecAttrAccount", acct)
        if self.test_keychain:
            ref = p()
            status = self.sec.SecKeychainOpen(self.test_keychain.encode(), C.byref(ref))
            if status != 0:
                self._release(owned)
                raise RuntimeError(f"test Keychain open failed: {status}")
            owned.append(ref.value)
            if add:
                put("kSecUseKeychain", ref.value)
            else:
                array_values = (p * 1)(ref.value)
                search = self.cf.CFArrayCreate(None, array_values, 1,
                    C.addressof(C.c_byte.in_dll(self.cf, "kCFTypeArrayCallBacks")))
                owned.append(search)
                put("kSecMatchSearchList", search)
        if value is not None:
            data = self._data(value)
            owned.append(data)
            put("kSecValueData", data)
        if return_data:
            put("kSecReturnData", self._constant("kCFBooleanTrue", self.cf))
            put("kSecMatchLimit", self._constant("kSecMatchLimitOne"))
        return d, owned

    def _release(self, refs):
        for ref in reversed(refs):
            if ref: self.cf.CFRelease(ref)

    def exists(self, account: str) -> bool:
        query, refs = self._query(account)
        try:
            status = self.sec.SecItemCopyMatching(query, None)
        finally:
            self._release(refs)
        if status not in (0, -25300):
            raise RuntimeError(f"Keychain status: {status}")
        return status == 0

    def add_synthetic(self, account: str, value: str) -> None:
        query, refs = self._query(account, add=True, value=value.encode())
        try: status = self.sec.SecItemAdd(query, None)
        finally: self._release(refs)
        if status != 0: raise RuntimeError(f"Keychain add status: {status}")

    def update_synthetic(self, account: str, value: str) -> None:
        query, refs = self._query(account)
        attrs = self.cf.CFDictionaryCreateMutable(None, 0,
            C.addressof(C.c_byte.in_dll(self.cf, "kCFTypeDictionaryKeyCallBacks")),
            C.addressof(C.c_byte.in_dll(self.cf, "kCFTypeDictionaryValueCallBacks")))
        data = self._data(value.encode())
        try:
            self.cf.CFDictionarySetValue(attrs, self._constant("kSecValueData"), data)
            status = self.sec.SecItemUpdate(query, attrs)
        finally:
            self._release((data, attrs, *refs))
        if status != 0: raise RuntimeError(f"Keychain update status: {status}")

    def delete_synthetic(self, account: str) -> None:
        query, refs = self._query(account)
        try: status = self.sec.SecItemDelete(query)
        finally: self._release(refs)
        if status not in (0, -25300): raise RuntimeError(f"Keychain delete status: {status}")

    def _read_for_provider(self, account: str) -> str:
        query, refs = self._query(account, return_data=True)
        result = C.c_void_p()
        try:
            status = self.sec.SecItemCopyMatching(query, C.byref(result))
            if status != 0 or not result.value:
                raise RuntimeError(f"credential unavailable status: {status}")
            size = self.cf.CFDataGetLength(result)
            data = C.string_at(self.cf.CFDataGetBytePtr(result), size)
            return data.decode("utf-8")
        finally:
            if result.value: self.cf.CFRelease(result)
            self._release(refs)
