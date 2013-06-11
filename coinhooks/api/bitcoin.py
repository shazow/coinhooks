import json
import time
import requests


## Helpers

def _get_retry_wait(num_attempt=1, MAX_RETRY_WAIT=86400):
    return min(MAX_RETRY_WAIT, 2**num_attempt)

def _key_namespace(prefix):
    return lambda s: '%s:%s' % (prefix, s)


# TODO: Port this to something like https://gist.github.com/shazow/5754021
KEY_PREFIX_PENDING_WALLET = _key_namespace('w')
KEY_CONFIRMATION_QUEUE = 'confirmation_queue'
KEY_CALLBACK_QUEUE = 'callback_queue'
KEY_WALLETS_SET = 'free_wallets'


## API

def create_wallet(bitcoin_rpc, redis, payout_address, callback_url, account=''):
    new_wallet = redis.spop(KEY_WALLETS_SET) or bitcoin_rpc.getnewaddress(account)

    # TODO: Add support for min_amount
    redis.set(
        KEY_PREFIX_PENDING_WALLET(new_wallet),
        json.dumps([payout_address, callback_url])
    )

    return new_wallet


def queue_transaction(redis, tx_id):
    value = json.dumps([tx_id, str(int(time.time()))])
    redis.rpush(KEY_CONFIRMATION_QUEUE, value)

    return value


def deque_transaction(bitcoin_rpc, redis, seconds_expire=60*60*24, min_confirmations=5):
    value = redis.rpop(KEY_CONFIRMATION_QUEUE)
    if not value:
        # Nothing to do.
        return

    tx_id, timestamp = value.split(':')
    if int(timestamp) + seconds_expire < time.time():
        # TODO: Log expired transaction.
        return

    t = bitcoin_rpc.gettransaction(tx_id)
    if t['category'] != 'receive':
        # Don't care about sent transactions.
        return

    if int(t['confirmations']) < min_confirmations:
        # Not ready yet
        redis.rpush(KEY_CONFIRMATION_QUEUE, value)
        return

    process_transaction(bitcoin_rpc, redis, t)


def process_transaction(bitcoin_rpc, redis, transaction, min_confirmations=5):
    address = transaction['address']
    amount = transaction['amount']

    key = KEY_PREFIX_PENDING_WALLET(address)
    value = redis.get(key)
    if not value:
        # Transaction already processed.
        return

    payout_address, callback_url = json.loads(value)

    # TODO: Log receipt.
    # TODO: Take fee.
    bitcoin_rpc.sendtoaddress(payout_address, amount)

    transaction_str = json.dumps(transaction)
    payload = {
        # TODO: Add nonce and signing?
        'transaction': transaction_str,
    }

    process_callback(redis, callback_url, payload)
    redis.delete(key)
    redis.sadd(KEY_WALLETS_SET, payout_address)


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

    process_callback(r['callback_url'], r['payload'], r['num_attempts'])


def process_callback(redis, callback_url, payload, num_attempts=0):
    try:
        r = requests.post(callback_url, params=payload)
        r.raise_for_status()
        return r # Success
    except requests.RequestException, e:
        # TODO: Log error
        pass

    # Failed, queue to retry later
    queue_callback(redis, callback_url, payload, num_attempts+1)
