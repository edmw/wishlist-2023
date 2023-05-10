"""Tests for encoding bytes to strings and decoding strings to bytes."""
from uuid import UUID

import pytest

from webapp.services.coding_services import Base62Service

INVALID_CHARACTER_IN_BASE62_STRING = "Invalid character in Base62 string"
INVALID_SIZE_FOR_BASE62_STRING = "Invalid size for Base62 string"


def test_base62_translation_byte_to_char() -> None:
    """Tests translation of a byte value to its base62 string character."""
    assert len(Base62Service.translation_byte_to_char) == 62
    assert len(set(Base62Service.translation_byte_to_char)) == 62
    assert Base62Service.translation_byte_to_char[10] == "A"


def test_base62_translation_char_to_byte() -> None:
    """Tests translation of a base62 string character to its byte value."""
    assert len(Base62Service.translation_char_to_byte) == 62
    assert len(set(Base62Service.translation_char_to_byte)) == 62
    assert Base62Service.translation_char_to_byte["A"] == 10


def test_base62_encode() -> None:
    """Tests encoding bytes to a base62 string."""
    assert Base62Service.encode(from_bytes=b"base62") == "UiP9AV6Y"


def test_base62_encode_long() -> None:
    """Tests encoding many bytes to a base62 string."""
    text = (
        b"O, but they say the tongues of dying men\n"
        b"Enforce attention like deep harmony.\n"
        b"Where words are scarce, they are seldom spent in vain,\n"
        b"For they breathe truth that breathe their words in pain.\n"
    )
    b62 = (
        "zRA9QMcCJEwiGgQbb1U1aAwq5BCxi4VT45TsGe3qGn5K4KuZ0MC7wora06rpuBwTv1zu97"
        "r2BFqnQDlvIUJrMFYdkBikTMQORacESaEzEY2rk4qssttYjrRiTndLhx6CxUBS1AP9aVA1"
        "IyQJGZXyOmyhwnRdZ1POhPCv8i2GAUqulWmB3bUuuTjL36xbLGp14KCIOX1RhxlqfSJcfT"
        "nHhVBWUFoYcCqCcLphiwx9at9IGTnktQlkYFOa602NDKM"
    )
    assert Base62Service.encode(from_bytes=text) == b62


def test_base62_encode_empty() -> None:
    """Tests encoding empty bytes to a base62 string."""
    assert Base62Service.encode(from_bytes=b"") == ""


def test_base62_decode() -> None:
    """Tests decoding a base62 encoded string to bytes."""
    assert Base62Service.decode(from_string="UiP9AV6Y") == b"base62"


def test_base62_decode_long() -> None:
    """Tests decoding an empty base62 string to bytes."""
    b62 = (
        "D0mhhtbYktt1FBm4AqlrG5DC54AYpbmH1xxxsnL4o1aJGHRhcVawVOgv1LGijCpTOUyDMU"
        "9xP1uKd4sWqd1fUNGPIhJ082KXUJNKkoblYGJxQ1T6DxsTciqpjHeAiPR8Fsbv6DTxRHGv"
        "9BvGqotmjaHJJXJquBDzjQVBPqdYqmvyvgslnkuXZue9mFi7Pjny3A1yDIC1pZC"
    )
    text = (
        b"Wer reitet so spaet durch Nacht und Wind?\n"
        b"Es ist der Vater mit seinem Kind;\n"
        b"Er hat den Knaben wohl in dem Arm,\n"
        b"Er fasst ihn sicher, er haelt ihn warm.\n"
    )
    assert Base62Service.decode(from_string=b62) == text


def test_base62_decode_empty() -> None:
    """Tests decoding an empty base62 string to bytes."""
    assert Base62Service.decode(from_string="") == b""


def test_decode_raises() -> None:
    """Tests decoding an invalid base62 string raises appropriate exceptions."""
    with pytest.raises(ValueError, match=INVALID_CHARACTER_IN_BASE62_STRING):
        # Invalid character in base62 string (it’s the 'ü').
        Base62Service.decode(from_string="00Lp4iüfOQ8Rlp9Ajg5SC")
    with pytest.raises(ValueError, match=INVALID_CHARACTER_IN_BASE62_STRING):
        # Invalid character in base62 string (it’s the 'А').
        Base62Service.decode(from_string="00Lp4i5fOQ8Rlp9Аjg5SC")


@pytest.fixture()
def uuid_base62_map() -> list[tuple[str, str]]:
    """Fixture for a mapping from UUID to its base62-encoded representation."""
    return [
        ("00000000-0000-0000-0000-000000000000", "0000000000000000"),
        ("00000000-0000-0000-0000-010000000001", "0000000000JMAIjoX"),
        ("0000c52d-e7bf-452a-ac0b-064f65f821e8", "00Lp4i5fOQ8Rlp9Ajg5SC"),
        ("86d5c52d-e7bf-452a-ac0b-064f65f821e8", "46QfEaPfUXMcvlP4dPgQJ6"),
        ("93fc6312-a557-41bb-85ce-e748b35bc626", "4VFDDjQEAu5WKj9g8cTjWw"),
        ("a71dc2a0-a158-41f3-bb0c-4b21bfd27e7a", "55LJmYwN5a2z0y5A0giXe6"),
        ("5291628d-759f-4547-b4ec-ab99b9301796", "2VnoL3jhh6mUqrWlDAChhW"),
        ("8b1a8064-28d9-4723-b539-b524a6ba4320", "4EU2llJTPTFKeKrip8mZIO"),
        ("c86542bd-bb5e-47ca-a753-dc0f911f894a", "668jyyjfZxLeaXnKJVz3P8"),
        ("11b441f7-cb5c-4d50-abdc-0ec35e4b04db", "XPFLab7Ln7qjwsjwU6Zhr"),
        ("895bdfca-b609-46fd-a2df-e87de6d429f6", "4BBvzkHZkc13VKpIDAUpjq"),
        ("4d5f3eda-044f-417f-b68e-5accec9601f3", "2Lzw3u4r3dK4Kg8xQIzgEl"),
        ("38c7fcae-0fab-4300-96f6-a2fbb097f276", "1j8xo4gTWaOUgb4kIQdVDi"),
        ("d5ac7e22-f786-47e9-997e-dafc471a6bb8", "6VCC5jyCdBgj2eg1z68mDI"),
    ]


def test_encode_uuid_to_base62(uuid_base62_map: list[tuple[str, str]]) -> None:
    """Tests encoding UUID to base62-encoded string."""
    for value in uuid_base62_map:
        uuid = UUID(value[0])
        assert Base62Service.uuid_encode(uuid=uuid) == value[1]


def test_decode_uuid_from_base62(uuid_base62_map: list[tuple[str, str]]) -> None:
    """Tests decoding UUID from a base62-encoded string."""
    for value in uuid_base62_map:
        uuid = Base62Service.uuid_decode(base62_string=value[1])
        assert str(uuid).lower() == value[0]


def test_decode_uuid_from_invalid_strings() -> None:
    """Tests decoding an invalid base62 string to UUID raises appropriate exceptions."""
    with pytest.raises(ValueError, match=INVALID_CHARACTER_IN_BASE62_STRING):
        # Invalid character in base62 string (it’s the 'ü').
        Base62Service.uuid_decode(base62_string="00Lp4iüfOQ8Rlp9Ajg5SC")
    with pytest.raises(ValueError, match=INVALID_CHARACTER_IN_BASE62_STRING):
        # Invalid character in base62 string (it’s the 'А').
        Base62Service.uuid_decode(base62_string="00Lp4i5fOQ8Rlp9Аjg5SC")
    with pytest.raises(ValueError, match=INVALID_SIZE_FOR_BASE62_STRING):
        # Invalid size for base62 string.
        Base62Service.uuid_decode(base62_string="46QfEaPfUXMcvlP4dPgQJ600Lp4i5fOQ8Rlp9Ajg5SC")
