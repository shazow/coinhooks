from nose.tools import assert_true, assert_equal, assert_raises

from coinhooks.lib.bitcoin import assert_valid_address, NETWORK_VERSIONS
from coinhooks.lib import bitcoin
from coinhooks.test.fixtures import BITCOIN_ADDRESSES


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
