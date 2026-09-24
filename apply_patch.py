"""Build the ECHO NANO V1.7.0 ID3-title patch.

This tool only reads and writes image files supplied by the user. It never
accesses the player itself and accepts only the exact supported stock image.
"""

from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path


SOURCE_SHA256 = "54a45d233a23c3ce142d1da9c093cc40c46eba417aa91fe915ee867726f4a116"
OUTPUT_SHA256 = "9576d6af3cf0e07a8e1b49a168ece09b55e4afa40275c3c1827c103715e9ca61"
IMAGE_SIZE = 11_534_340
PATCH_OFFSET = 0x53390
MIRROR_HEADER_OFFSET = 0xA58000
HEADER_SIZE = 512

ORIGINAL_PATCH = bytes.fromhex(
    "ddf86c05c4f80005ddf870050025c4f82055c4f804054ff48072214604f58070"
    "dcf781fcc4f82855c4f82c55"
)
REPLACEMENT_PATCH = bytes.fromhex(
    "ddf86c0504f5a0610860ddf87005486000250d628d62cd6204f5807002881ab9"
    "2146421adcf77ffc00bf00bf"
)


class InvalidFirmware(ValueError):
    """Raised when the input is not the exact supported stock image."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crc32_rknano(data: bytes) -> int:
    """Return the non-reflected CRC-32 used by this RKnano image."""
    table = []
    for byte in range(256):
        value = byte << 24
        for _ in range(8):
            value = ((value << 1) ^ (0x04C10DB7 if value & 0x80000000 else 0)) & 0xFFFFFFFF
        table.append(value)

    value = 0
    for byte in data:
        value = ((value << 8) & 0xFFFFFFFF) ^ table[(value >> 24) ^ byte]
    return value


def validate_source(image: bytes) -> None:
    if len(image) != IMAGE_SIZE:
        raise InvalidFirmware(f"unexpected image size: {len(image)} bytes")
    if sha256(image) != SOURCE_SHA256:
        raise InvalidFirmware("input SHA-256 does not match ECHO NANO V1.7.0 stock firmware")
    if image[504:512] != b"RKnanoFW":
        raise InvalidFirmware("RKnano firmware marker is missing")
    if image[:HEADER_SIZE] != image[MIRROR_HEADER_OFFSET:MIRROR_HEADER_OFFSET + HEADER_SIZE]:
        raise InvalidFirmware("duplicate firmware headers do not match")
    stored_crc = struct.unpack_from("<I", image, len(image) - 4)[0]
    if crc32_rknano(image[:-4]) != stored_crc:
        raise InvalidFirmware("stock firmware checksum is invalid")
    actual_patch = image[PATCH_OFFSET:PATCH_OFFSET + len(ORIGINAL_PATCH)]
    if actual_patch != ORIGINAL_PATCH:
        raise InvalidFirmware("expected stock instructions are not present")


def build_image(source: bytes) -> bytes:
    validate_source(source)
    result = bytearray(source)
    result[PATCH_OFFSET:PATCH_OFFSET + len(REPLACEMENT_PATCH)] = REPLACEMENT_PATCH
    struct.pack_into("<I", result, len(result) - 4, crc32_rknano(result[:-4]))
    output = bytes(result)
    if sha256(output) != OUTPUT_SHA256:
        raise RuntimeError("internal verification failed: generated image hash is unexpected")
    return output


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print("usage: python apply_patch.py STOCK.IMG OUTPUT.IMG", file=sys.stderr)
        return 2

    source_path, output_path = map(Path, args)
    if output_path.exists():
        print(f"refusing to overwrite existing file: {output_path}", file=sys.stderr)
        return 1

    try:
        output = build_image(source_path.read_bytes())
        with output_path.open("xb") as destination:
            destination.write(output)
    except (OSError, InvalidFirmware, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"wrote {output_path}")
    print(f"SHA-256: {sha256(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
