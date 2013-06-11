from nose.tools import assert_true, assert_equal, assert_raises
from mock import Mock

from coinhooks import api
from coinhooks.test.fixtures import BITCOIN_ADDRESSES


FakeBitcoinRpc = Mock()
FakeRedis = Mock()

def test_create_wallet():
    w = api.bitcoin.create_wallet(
        FakeBitcoinRpc, FakeRedis,
        payout_address=BITCOIN_ADDRESSES.good[0],
        callback_url=u'http://localhost/webhook',
    )

    assert_true(w)
