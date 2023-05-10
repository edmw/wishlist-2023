"""Provides service functions for codings."""

import uuid


def _divide(source: bytearray, from_base: int, to_base: int) -> tuple[bytearray, int]:
    quotient = bytearray()
    remainder = 0
    for byte in source:
        accumulator = byte + remainder * from_base
        remainder = accumulator % to_base  # noqa: S001
        value = int(accumulator / to_base)
        if quotient or value > 0:
            quotient.append(value)
    remainder = int(remainder)
    return (quotient, remainder)


def _pad(target: bytearray, using: bytes) -> bytearray:
    source = using
    for byte in source:
        if byte == 0:
            target.append(0)
        else:
            break
    return target


def from_base_to_base(from_bytes: bytes, from_base: int, to_base: int) -> bytes:
    # This is a sanity check while developing which can be safely removed in production.
    assert from_base > 0 and from_base <= 256  # nosec
    assert to_base > 0 and to_base <= 256  # nosec

    source = bytearray(from_bytes)
    target = bytearray()
    while source:
        quotient, remainder = _divide(source, from_base, to_base)
        if quotient or remainder > 0:
            target.append(remainder)
        source = quotient

    target = _pad(target, using=from_bytes)

    return bytes(reversed(target))


class Base62Service:
    """Service class providing a collection of static functions for codings."""

    translation_byte_to_char = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    translation_char_to_byte = {char: index for index, char in enumerate(translation_byte_to_char)}

    @staticmethod
    def encode(*, from_bytes: bytes | bytearray) -> str:
        b62_bytes = from_base_to_base(from_bytes, from_base=256, to_base=62)
        char_array = [Base62Service.translation_byte_to_char[byte] for byte in b62_bytes]
        return "".join(char_array)

    @staticmethod
    def uuid_encode(*, uuid: uuid.UUID) -> str:
        return Base62Service.encode(from_bytes=uuid.bytes)

    @staticmethod
    def decode(*, from_string: str) -> bytes:
        try:
            byte_array = [Base62Service.translation_char_to_byte[char] for char in from_string]
        except KeyError:
            raise ValueError(f"Invalid character in Base62 string '{from_string}'.") from KeyError
        b62_bytes = bytes(byte_array)
        b256_bytes = from_base_to_base(b62_bytes, from_base=62, to_base=256)
        return b256_bytes

    @staticmethod
    def uuid_decode(*, base62_string: str) -> uuid.UUID:
        to_bytes = Base62Service.decode(from_string=base62_string)
        if len(to_bytes) != 16:
            raise ValueError(f"Invalid size for Base62 string '{base62_string}'.")
        return uuid.UUID(bytes=to_bytes)
