import time
import requests
import logging

from coinhooks.lib import json_ as json

log = logging.getLogger(__name__)


## Helpers
def _key_namespace(prefix):
    return lambda s: '%s:%s' % (prefix, s)

def _get_retry_wait(num_attempt=1, MAX_RETRY_WAIT=86400):
    return min(MAX_RETRY_WAIT, 2**num_attempt)


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


def queue_transaction(bitcoin_rpc, redis, tx_id):
    """
    Transaction notification received for an address that belongs to us. Used
    by Bitcoind's `walletnotify=` hook through `bin/walletnotify.py`.

    :param redis:
        Instance of the Redis client connection.

    :param tx_id:
        Relevant transaction ID that we just learned about.
    """

    t = bitcoin_rpc.gettransaction(tx_id)
    if not t:
        # TODO: Log invalid transaction
        return

    transaction = t.__dict__
    log.debug("Relevant transaction received: %s", transaction['txid'])

    value = json.dumps(transaction)
    redis.rpush(KEY_CONFIRMATION_QUEUE, value)

    log.debug("Processing transaction: %s", transaction['txid'])
    return process_transaction(bitcoin_rpc, redis, transaction)


def deque_transaction(bitcoin_rpc, redis, seconds_expire=60*60*24, min_confirmations=5):
    value = redis.rpop(KEY_CONFIRMATION_QUEUE)
    if not value:
        # Nothing to do.
        return

    transaction = json.loads(value)
    if int(transaction['timereceived']) + seconds_expire < time.time():
        # TODO: Log expired transaction.
        return

    if int(transaction['confirmations']) < min_confirmations:
        # Not ready yet
        redis.rpush(KEY_CONFIRMATION_QUEUE, value)
        return

    log.debug("Processing transaction: %s", transaction['txid'])
    return process_transaction(bitcoin_rpc, redis, transaction, min_confirmations)


def process_transaction(bitcoin_rpc, redis, transaction, min_confirmations=5):
    receive_details = next(d for d in transaction['details'] if d['category'] == u'receive')
    address = receive_details['address']
    amount = receive_details['amount']
    is_confirmed =  int(transaction['confirmations']) >= min_confirmations

    key = KEY_PREFIX_PENDING_WALLET(address)
    value = redis.get(key)
    if not value:
        # Wallet is discarded.
        return

    payout_address, callback_url = json.loads(value)

    if is_confirmed and payout_address:
        # TODO: Log receipt.
        # TODO: Take fee.
        bitcoin_rpc.sendtoaddress(payout_address, amount)

    if callback_url:
        transaction_str = json.dumps(transaction)
        payload = {
            # TODO: Add nonce and signing?
            'state': 'confirmed' if is_confirmed else 'unconfirmed',
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
    log.debug("Sending callback: POST %s", callback_url)
    try:
        r = requests.post(callback_url, params=payload)
        r.raise_for_status()
        return r # Success
    except requests.RequestException:
        # TODO: Log error
        pass

    # Failed, queue to retry later
    queue_callback(redis, callback_url, payload, num_attempts+1)
