import jsonrpclib
import json
import time
import requests


class REDIS_KEYS:
    PREFIX_PENDING_WALLET = 'w'
    CONFIRMATION_QUEUE = 'confirmation_queue'


def _get_bitcoin_rpc(request):
    url = request.registry.settings['bitcoind.url']
    return jsonrpclib.Server(url)


def create_wallet(bitcoin_rpc, redis, payout_wallet, callback_url, account=''):
    # TODO: Implement wallet re-use
    new_wallet = bitcoin_rpc.getnewaddress(account)

    redis.set(
        '%s:%s' % (REDIS_KEYS.PREFIX_PENDING_WALLET, new_wallet),
        json.dumps([payout_wallet, callback_url])
    )


def queue_transaction(redis, tx_id, queue_name=REDIS_KEYS.CONFIRMATION_QUEUE):
    value = json.dumps([tx_id, str(int(time.time()))])
    redis.rpush(queue_name, value)


def process_queue(bitcoin_rpc, redis, queue_name=REDIS_KEYS.CONFIRMATION_QUEUE, seconds_expire=60*60*24, min_confirmations=5):
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
        redis.rpush(value)
        return

    process_transaction(bitcoin_rpc, redis, t)


def process_transaction(bitcoin_rpc, redis, transaction, min_confirmations=5):
    address = transaction['address']
    amount = transaction['amount']

    value = redis.get('%s:%s' % (REDIS_KEYS.PREFIX_PENDING_WALLET, address))
    if not value:
        # Transaction already processed.
        return

    payout_wallet, callback_url = json.loads(value)

    # TODO: Log receipt.
    # TODO: Take fee.
    bitcoin_rpc.sendtoaddress(payout_wallet, amount)

    transaction_str = json.dumps(transaction)
    transaction_sig = bitcoin_rpc.signmessage(address, transaction_str)
    payload = {
        'transaction': transaction_str,
        'transaction_sig': transaction_sig,
    }
    requests.post(callback_url, params=payload)
