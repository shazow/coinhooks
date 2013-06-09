import jsonrpclib
import json
import time
import requests


def _get_retry_wait(num_attempt=1, MAX_RETRY_WAIT=86400):
    return min(MAX_RETRY_WAIT, 2**num_attempt)

def _prefixer(prefix):
    return lambda s: '%s:%s' % (prefix, s)


class REDIS_KEYS:
    PREFIX_PENDING_WALLET = _prefixer('w')
    CONFIRMATION_QUEUE = 'confirmation_queue'
    CALLBACK_QUEUE = 'callback_queue'
    WALLETS_SET = 'free_wallets'


def _get_bitcoin_rpc(request):
    url = request.registry.settings['bitcoind.url']
    return jsonrpclib.Server(url)


def create_wallet(bitcoin_rpc, redis, payout_wallet, callback_url, account=''):
    new_wallet = redis.spop(WALLETS_SET) or bitcoin_rpc.getnewaddress(account)

    # TODO: Add support for min_amount
    redis.set(
        REDIS_KEYS.PREFIX_PENDING_WALLET(new_wallet),
        json.dumps([payout_wallet, callback_url])
    )


def queue_transaction(redis, tx_id):
    value = json.dumps([tx_id, str(int(time.time()))])
    redis.rpush(REDIS_KEYS.CONFIRMATION_QUEUE, value)


def deque_transaction(bitcoin_rpc, redis, queue_name=REDIS_KEYS.CONFIRMATION_QUEUE, seconds_expire=60*60*24, min_confirmations=5):
    value = redis.rpop(queue_name)
    if not value:
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
        redis.rpush(queue_name, value)
        return

    process_transaction(bitcoin_rpc, redis, t)


def process_transaction(bitcoin_rpc, redis, transaction, min_confirmations=5):
    address = transaction['address']
    amount = transaction['amount']

    key = REDIS_KEYS.PREFIX_PENDING_WALLET(address)
    value = redis.get(key)
    if not value:
        # Transaction already processed.
        return

    payout_wallet, callback_url = json.loads(value)

    # TODO: Log receipt.
    # TODO: Take fee.
    bitcoin_rpc.sendtoaddress(payout_wallet, amount)

    transaction_str = json.dumps(transaction)
    payload = {
        'transaction': transaction_str,
    }

    process_callback(redis, callback_url, payload)
    redis.del(key)
    redis.sadd(REDIS_KEYS.WALLETS_SET, payout_wallet)


def queue_callback(redis, callback_url, payload, num_attempts=0):
    retry_value = json.dumps({
        'num_attempts': num_attempts + 1,
        'time_attempted': int(time.time()),
        'callback_url': callback_url,
        'payload': payload,
    })
    redis.rpush(REDIS_KEYS.CALLBACK_QUEUE, retry_value)


def deque_callback(redis, queue_name=REDIS_KEYS.CALLBACK_QUEUE):
    value = redis.rpop(queue_name)
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
        return # Success
    except requests.RequestException, e:
        # TODO: Log error
        pass

    # Failed, queue to retry later
    queue_callback(redis, callback_url, payload, num_attempts + 1)
