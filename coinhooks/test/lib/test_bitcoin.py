from nose.tools import assert_true, assert_equal, assert_raises

from coinhooks.lib.bitcoin import assert_valid_address, NETWORK_VERSIONS
from coinhooks.lib import bitcoin


class BITCOIN_ADDRESSES:
    good = [
        '15VjRaDX9zpbA8LVnbrCAFzrVzN7ixHNsC',
    ]

    bad = [
        'asdf',
        '0'*34,
        'n3swQ1Gm1HrNuzA8B4KJtzxqwXt1zEhhNJ',
    ]

    good_testnet = [
        'n3swQ1Gm1HrNuzA8B4KJtzxqwXt1zEhhNJ',
    ]

    encoding = [
        ('15VjRaDX9zpbA8LVnbrCAFzrVzN7ixHNsC', '\x001O\x90Eg\x8d2\xfdBj\xa03+\xc1\x86\x9dE\x9a\x86suR\xa5\xe3'),
        ('n3swQ1Gm1HrNuzA8B4KJtzxqwXt1zEhhNJ', 'o\xf5J\xc0\xda\xcd\xb1\x12\x0f3[\x19\xcf\x95\xa9\xb0\x87\xa9\xc2R7R\x9b|\xa3'),
    ]


def test_bitcoin_encoding():
    for encoded, decoded in BITCOIN_ADDRESSES.encoding:
        assert_equal(bitcoin.decode_address(encoded), decoded)
        assert_equal(bitcoin.encode_address(decoded), encoded)


def test_validate_bitcoin_address():
    for addr_str in BITCOIN_ADDRESSES.good:
        assert_true(assert_valid_address(addr_str))

    for addr_str in BITCOIN_ADDRESSES.good_testnet:
        assert_true(assert_valid_address(addr_str, network_version=NETWORK_VERSIONS.testnet))

    for addr_str in BITCOIN_ADDRESSES.bad:
        assert_raises(ValueError, assert_valid_address, addr_str)
