from __future__ import annotations

from app.application.transfer_codes import TransferCodeGenerator


def test_transfer_code_generator_returns_base32_code() -> None:
    generator = TransferCodeGenerator()

    code = generator.generate()

    assert len(code) == 6
    assert code.isupper()
    assert all(character in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for character in code)
