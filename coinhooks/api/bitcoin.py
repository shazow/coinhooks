import json
import time
import requests


## Helpers
def _key_namespace(prefix):
    return lambda s: '%s:%s' % (prefix, s)


# TODO: Port this to something like https://gist.github.com/shazow/5754021
KEY_PREFIX_PENDING_WALLET = _key_namespace('w')
KEY_CONFIRMATION_QUEUE = 'confirmation:queue'
KEY_CALLBACK_QUEUE = 'callback:queue'
KEY_WALLETS_SET = 'wallet_pool'

# TODO: Make queue-based transactions recoverable by using a dirty-queue with RPOPLPUSH.


## API

def create_wallet(bitcoin_rpc, redis, payout_address=None, callback_url=None, account=''):
    """
    Return a fresh wallet address.

    :param bitcoin_rpc:
        Instance of the Bitcoin JSONRPC client connection.

    :param redis:
        Instance of the Redis client connection.

    :param payout_address:
        If supplied, then payments to the new wallet are automatically relayed
        to the given payout_address.

    :param callback_url:
        If supplied, then a webhook is executed onto callback_url for each
        transaction.
    """
    new_wallet = redis.spop(KEY_WALLETS_SET) or bitcoin_rpc.getnewaddress(account)

    # TODO: Add support for min_amount?
    redis.set(
        KEY_PREFIX_PENDING_WALLET(new_wallet),
        json.dumps([payout_address, callback_url])
    )

    return new_wallet


def discard_wallet(redis, address):
    """
    Mark wallet address as discarded, so it can be re-used (ie. returned in a
    future call to `create_wallet(...)`).

    :param redis:
        Instance of the Redis client connection.

    :param address:
        Wallet address to return to our pool of unused addresses.
    """
    # TODO: Check if wallet belongs to bitcoin_rpc?
    key = KEY_PREFIX_PENDING_WALLET(address)

    redis.delete(key)
    redis.sadd(KEY_WALLETS_SET, address)


def queue_transaction(redis, tx_id):
    """
    Transaction notification received for an address that belongs to us. Used
    by Bitcoind's `walletnotify=` hook through `bin/walletnotify.py`.

    :param redis:
        Instance of the Redis client connection.

    :param tx_id:
        Relevant transaction ID that we just learned about.
    """
    now = str(int(time.time()))
    value = json.dumps([tx_id, now])
    redis.rpush(KEY_CONFIRMATION_QUEUE, value)

    return value


def deque_transaction(bitcoin_rpc, redis, seconds_expire=60*60*24, min_confirmations=5):
    value = redis.rpop(KEY_CONFIRMATION_QUEUE)
    if not value:
        # Nothing to do.
        return

    tx_id, timestamp = json.loads(value)
    if int(timestamp) + seconds_expire < time.time():
        # TODO: Log expired transaction.
        return

    t = bitcoin_rpc.gettransaction(tx_id)
    if t['category'] != u'receive':
        # Don't care about sent transactions.
        return

    if int(t['confirmations']) < min_confirmations:
        # Not ready yet
        redis.rpush(KEY_CONFIRMATION_QUEUE, value)
        return

    return process_transaction(bitcoin_rpc, redis, t)


def process_transaction(bitcoin_rpc, redis, transaction, min_confirmations=5):
    address = transaction['address']
    amount = transaction['amount']

    key = KEY_PREFIX_PENDING_WALLET(address)
    value = redis.get(key)
    if not value:
        # Wallet is discarded.
        return

    payout_address, callback_url = json.loads(value)

    if payout_address:
        # TODO: Log receipt.
        # TODO: Take fee.
        bitcoin_rpc.sendtoaddress(payout_address, amount)

    if callback_url:
        transaction_str = json.dumps(transaction)
        payload = {
            # TODO: Add nonce and signing?
            'state': 'confirmed',
            'transaction': transaction_str,
        }

        process_callback(redis, callback_url, payload)

    return transaction


def queue_callback(redis, callback_url, payload, num_attempts=0):
    retry_value = json.dumps({
        'num_attempts': num_attempts + 1,
        'time_attempted': int(time.time()),
        'callback_url': callback_url,
        'payload': payload,
    })
    redis.rpush(KEY_CALLBACK_QUEUE, retry_value)

    return retry_value


def deque_callback(redis):
    value = redis.rpop(KEY_CALLBACK_QUEUE)
    if not value:
        return

    r = json.loads(value)
    seconds_wait = _get_retry_wait(r['num_attempts'])
    if r['time_attempted'] + seconds_wait < time.time():
        # Too soon
        redis.lpush(value)
        return

    return process_callback(r['callback_url'], r['payload'], r['num_attempts'])


def process_callback(redis, callback_url, payload, num_attempts=0):
    """
    Send webhook callback. If failed, then queue for retry later.
    """
    try:
        r = requests.post(callback_url, params=payload)
        r.raise_for_status()
        return r # Success
    except requests.RequestException, e:
        # TODO: Log error
        pass

    # Failed, queue to retry later
    queue_callback(redis, callback_url, payload, num_attempts+1)
