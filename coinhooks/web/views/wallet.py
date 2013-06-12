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

    w = api.wallet.create_wallet(request.bitcoin, request.redis, payout_address=payout_address, callback_url=callback_url)

    raise {
        'wallet_address': w,
    }


# Following are temporary in this branch, will ultimately live in a pluggable module.


@expose_api('wallet.deposit')
def wallet_deposit(request):
    callback_url, = get_many(request, ['callback_url'])

    w = api.wallet.create_wallet(request.bitcoin, request.redis, callback_url=callback_url)

    raise {
        'wallet_address': w,
    }


@expose_api('wallet.withdraw')
def wallet_withdraw(request):
    payout_address, amount, secret = get_many(request, ['payout_address', 'amount', 'secret'])

    # FIXME: This is silly-security. Will need something better if we want to
    # keep such functionality.
    expected_secret = request.registry.settings.get('withdraw_secret')
    if not expected_secret or expected_secret != secret:
        raise APIControllerError('Invalid withdraw secret.')

    request.bitcoin_rpc.sendtoaddress(payout_address, amount)
