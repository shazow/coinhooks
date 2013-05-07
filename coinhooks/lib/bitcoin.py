import re


RE_WALLET_ADDRESS = re.compile('^[a-zA-Z1-9]{27,35}$')


class NETWORK_VERSIONS:
    testnet = 0x6f
    main = 0x00


def get_address_version(addr_str):
    # TODO: ...
    pass


def assert_valid_address(addr_str, network_version=NETWORK_VERSIONS.main):
    if not RE_WALLET_ADDRESS.match(addr_str):
        raise ValueError('Invalid address format (regexp fail): %s' % addr_str)

    # TODO: ...
    #version = get_address_version(addr_str)
    #if version != network_version:
    #    raise ValueError('Invalid address format (version): %s' % addr_str)

    return True
