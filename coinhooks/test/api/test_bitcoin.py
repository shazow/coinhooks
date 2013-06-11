from nose.tools import assert_true, assert_equal, assert_raises
from mock import Mock

from coinhooks import api
from coinhooks.test.fixtures import BITCOIN_ADDRESSES


class FakeBitcoinRPC(object):
    def getnewaddress(self, account=''):
        return BITCOIN_ADDRESSES.good[0]

    def gettransaction(self, tx_id):
        return {
            u'account': u'',
            u'address': unicode(BITCOIN_ADDRESSES.good[0]),
            u'amount': 0.5,
            u'category': u'receive',
            u'confirmations': 265,
            u'time': 1309047735,
            u'txid': u'40a18541d6f16dc823f91b572c126bd2deadf490d34be9761e2137fe27b2f6e9',
        }

    def sendtoaddress(payout_address, amount):
        return


class FakeRedis(Mock):
    pass


def test_create_wallet():
    expected_address = BITCOIN_ADDRESSES.good[0]

    w = api.bitcoin.create_wallet(
        FakeBitcoinRPC(),
        Mock(**{'spop.return_value': None}),
        payout_address=BITCOIN_ADDRESSES.good[1],
        callback_url=u'http://localhost/webhook',
    )

    assert_equal(w, expected_address)
