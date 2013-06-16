import time

from nose.tools import assert_equal, assert_true

from coinhooks import api
from coinhooks.test import TestWeb
from coinhooks.test.fixtures import BITCOIN_ADDRESSES


class FakeBitcoinRPC(object):
    # TODO: Move this into its own lib?

    def __init__(self):
        self._transactions = {}

    def getnewaddress(self, account=''):
        return BITCOIN_ADDRESSES.good[0]

    def gettransaction(self, txid):
        return self._transactions[txid]

    def sendtoaddress(self, payout_address, amount):
        return

    def _inject_transaction(self, **params):
        r = {
            u'account': u'',
            u'address': unicode(BITCOIN_ADDRESSES.good[0]),
            u'amount': 0.5,
            u'category': u'receive',
            u'confirmations': 0,
            u'time': int(time.time()),
            u'txid': u'000defaulttransaction',
        }
        r.update(params)
        self._transactions[r['txid']] = r
        return r


class TestBitcoin(TestWeb):
    def test_create_wallet(self):
        expected_address = BITCOIN_ADDRESSES.good[0]

        w = api.bitcoin.create_wallet(
            FakeBitcoinRPC(),
            self.redis,
            payout_address=BITCOIN_ADDRESSES.good[1],
        )

        assert_equal(w, expected_address)

    def test_queue_transaction(self):
        fake_bitcoin = FakeBitcoinRPC()

        w = api.bitcoin.create_wallet(
            fake_bitcoin,
            self.redis,
            payout_address=BITCOIN_ADDRESSES.good[1],
        )

        txid = u'foo'
        fake_bitcoin._inject_transaction(amount=0.5, txid=txid, address=w)

        api.bitcoin.queue_transaction(self.redis, txid)
        t = api.bitcoin.deque_transaction(fake_bitcoin, self.redis)

        assert_true(t)
        assert_equal(t['txid'], txid)
        assert_equal(t['address'], w)
