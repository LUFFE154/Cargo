from __future__ import annotations

import secrets


BASE32_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"


class TransferCodeGenerator:
    def generate(self, length: int = 6) -> str:
        value = secrets.randbelow(32**length)
        chars: list[str] = []
        for _ in range(length):
            value, remainder = divmod(value, 32)
            chars.append(BASE32_ALPHABET[remainder])
        return "".join(reversed(chars))
