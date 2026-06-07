"""Derivazione locale di indirizzi Bitcoin da una WIF compressa."""

from __future__ import annotations

import hashlib


BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
FIELD_PRIME = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
CURVE_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
GENERATOR = (
    55066263022277343669578718895168534326250603453777594175500187360389116729240,
    32670510020758816978083085130507043184471273380659243275938904335757337482424,
)


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def hash160(data: bytes) -> bytes:
    return hashlib.new("ripemd160", sha256(data)).digest()


def base58_decode(value: str) -> bytes:
    number = 0
    for character in value:
        try:
            digit = BASE58_ALPHABET.index(character)
        except ValueError as error:
            raise ValueError("WIF non valida: carattere Base58 non riconosciuto.") from error
        number = number * 58 + digit

    decoded = number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b""
    leading_zeroes = len(value) - len(value.lstrip("1"))
    return (b"\x00" * leading_zeroes) + decoded


def base58_encode(data: bytes) -> str:
    number = int.from_bytes(data, "big")
    encoded = ""

    while number:
        number, remainder = divmod(number, 58)
        encoded = BASE58_ALPHABET[remainder] + encoded

    leading_zeroes = len(data) - len(data.lstrip(b"\x00"))
    return ("1" * leading_zeroes) + encoded


def base58check(payload: bytes) -> str:
    checksum = sha256(sha256(payload))[:4]
    return base58_encode(payload + checksum)


def decode_compressed_wif(wif: str) -> int:
    raw = base58_decode(wif.strip())

    if len(raw) != 38:
        raise ValueError("La WIF deve essere una chiave mainnet compressa.")

    payload, checksum = raw[:-4], raw[-4:]
    if checksum != sha256(sha256(payload))[:4]:
        raise ValueError("Checksum WIF non valido.")
    if payload[0] != 0x80:
        raise ValueError("Sono supportate solo chiavi Bitcoin mainnet.")
    if payload[-1] != 0x01:
        raise ValueError("Sono supportate solo WIF compresse.")

    private_key = int.from_bytes(payload[1:33], "big")
    if not 1 <= private_key < CURVE_ORDER:
        raise ValueError("Chiave privata fuori dall'intervallo secp256k1.")

    return private_key


def inverse(value: int) -> int:
    return pow(value, FIELD_PRIME - 2, FIELD_PRIME)


def point_add(
    first: tuple[int, int] | None,
    second: tuple[int, int] | None,
) -> tuple[int, int] | None:
    if first is None:
        return second
    if second is None:
        return first

    x1, y1 = first
    x2, y2 = second

    if x1 == x2 and (y1 + y2) % FIELD_PRIME == 0:
        return None

    if first == second:
        slope = (3 * x1 * x1) * inverse(2 * y1) % FIELD_PRIME
    else:
        slope = (y2 - y1) * inverse(x2 - x1) % FIELD_PRIME

    x3 = (slope * slope - x1 - x2) % FIELD_PRIME
    y3 = (slope * (x1 - x3) - y1) % FIELD_PRIME
    return x3, y3


def scalar_multiply(value: int) -> tuple[int, int]:
    result = None
    addend = GENERATOR

    while value:
        if value & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        value >>= 1

    if result is None:
        raise ValueError("Impossibile derivare la chiave pubblica.")
    return result


def bech32_polymod(values: list[int]) -> int:
    generators = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    checksum = 1

    for value in values:
        top = checksum >> 25
        checksum = ((checksum & 0x1FFFFFF) << 5) ^ value
        for index, generator in enumerate(generators):
            if (top >> index) & 1:
                checksum ^= generator

    return checksum


def bech32_hrp_expand(hrp: str) -> list[int]:
    return [ord(character) >> 5 for character in hrp] + [0] + [
        ord(character) & 31 for character in hrp
    ]


def convert_bits(data: bytes, from_bits: int, to_bits: int) -> list[int]:
    accumulator = 0
    bit_count = 0
    result = []
    maximum = (1 << to_bits) - 1

    for value in data:
        accumulator = (accumulator << from_bits) | value
        bit_count += from_bits
        while bit_count >= to_bits:
            bit_count -= to_bits
            result.append((accumulator >> bit_count) & maximum)

    if bit_count:
        result.append((accumulator << (to_bits - bit_count)) & maximum)

    return result


def segwit_address(program: bytes) -> str:
    data = [0] + convert_bits(program, 8, 5)
    values = bech32_hrp_expand("bc") + data + [0, 0, 0, 0, 0, 0]
    polymod = bech32_polymod(values) ^ 1
    checksum = [(polymod >> (5 * (5 - index))) & 31 for index in range(6)]
    return "bc1" + "".join(BECH32_CHARSET[value] for value in data + checksum)


def derive_addresses(wif: str) -> list[str]:
    private_key = decode_compressed_wif(wif)
    x_coordinate, y_coordinate = scalar_multiply(private_key)
    prefix = b"\x02" if y_coordinate % 2 == 0 else b"\x03"
    public_key = prefix + x_coordinate.to_bytes(32, "big")
    public_key_hash = hash160(public_key)

    legacy = base58check(b"\x00" + public_key_hash)
    redeem_script = b"\x00\x14" + public_key_hash
    nested_segwit = base58check(b"\x05" + hash160(redeem_script))
    native_segwit = segwit_address(public_key_hash)
    return [legacy, nested_segwit, native_segwit]
