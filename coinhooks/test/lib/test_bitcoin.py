from nose.tools import assert_true, assert_raises

from coinhooks.lib.bitcoin import assert_valid_address, NETWORK_VERSIONS


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


def test_validate_bitcoin_address():
    for addr_str in BITCOIN_ADDRESSES.good:
        assert_true(assert_valid_address(addr_str))

    for addr_str in BITCOIN_ADDRESSES.good:
        assert_true(assert_valid_address(addr_str, network_version=NETWORK_VERSIONS.testnet))

    for addr_str in BITCOIN_ADDRESSES.good:
        assert_raises(ValueError, assert_valid_address, addr_str)
