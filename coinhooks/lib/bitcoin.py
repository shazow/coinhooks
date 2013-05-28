import re
import hashlib
import unstdlib


RE_WALLET_ADDRESS = re.compile('^[a-zA-Z1-9]{27,35}$')
ALPHABET_BASE58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


class NETWORK_VERSIONS:
    testnet = 0x6f
    main = 0x00


def encode_address(b):
    '''Encode a string of bytes into a base58 Bitcoin address.'''
    # Convert to base58
    n = unstdlib.bytes_to_number(b)
    s = unstdlib.number_to_string(n, alphabet=ALPHABET_BASE58)

    # Replace leading \x00 with equivalent of \x01
    num_pad = next(i for i, ch in enumerate(b) if ch != '\x00')
    return ALPHABET_BASE58[0] * num_pad + s


def decode_address(addr_str):
    '''Decode a base58 Bitcoin address into a string of bytes.'''
    # Convert from base58
    n = unstdlib.string_to_number(addr_str, alphabet=ALPHABET_BASE58)
    b = unstdlib.number_to_bytes(n)

    # Replace leading \x01 equivalents with \x00
    num_pad = next(i for i, ch in enumerate(addr_str) if ch != ALPHABET_BASE58[0])
    return '\x00' * num_pad + b


def address_checksum(body):
    return hashlib.sha256(hashlib.sha256(body).digest()).digest()[:4]


def assert_valid_address(addr_str, network_version=NETWORK_VERSIONS.main):
    if not RE_WALLET_ADDRESS.match(addr_str):
        raise ValueError('Invalid address format (regexp fail): %s' % addr_str)

    addr = decode_address(addr_str)
    version, body, checksum = addr[0], addr[:-4], addr[-4:]

    if address_checksum(body) != checksum:
        raise ValueError('Invalid address format (checksum fail): %s' % addr_str)

    if ord(version) != network_version:
        raise ValueError('Invalid address format (version): %s' % addr_str)

    return True
