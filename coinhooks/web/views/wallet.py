from unstdlib import get_many

from coinhooks import api
from coinhooks.lib.exceptions import APIControllerError
from coinhooks.lib.bitcoin import assert_valid_address

from .api import expose_api


@expose_api('wallet.create')
def wallet_create(request):
    callback_url, payout_address = get_many(request, ['callback_url', 'payout_address'])

    try:
        assert_valid_address(payout_address)
    except ValueError, e:
        raise APIControllerError(e.message)

    # TODO: ...
    # - Generate a fresh wallet address
    # - Record w:<wallet> -> (<payout_address>, <callback_url>) in storage.
    # - Return new wallet object.

    raise NotImplementedError()
