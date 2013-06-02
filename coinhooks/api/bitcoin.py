import jsonrpclib


class REDIS_KEYS:
    PREFIX_PENDING_WALLET = 'w'
    CONFIRMATION_QUEUE = 'confirmation_queue'


def _get_bitcoin_rpc(request):
    url = request.registry.settings['bitcoind.url']
    return jsonrpclib.Server(url)


def _redis_wallet_key(wallet):
    return 


def _redis_wallet_value(payout_wallet, callback_url):
    return payout_wallet, callback_url


def create_wallet(bitcoin_rpc, redis, payout_wallet, callback_url, account=''):
    # TODO: Implement wallet re-use
    new_wallet = bitcoin_rpc.getnewaddress(account)

    redis.set(
        '%s:%s' % (REDIS_KEYS.PREFIX_PENDING_WALLET, new_wallet),
        (payout_wallet, callback_url)
    )


def _handle_transaction(bitcoin_rpc, redis, t):
    # TODO: Handle insufficient confirmations (separate queue?)
    # TODO:
    # - Fetch redis entry
    # - Log receipt
    # - Send payment to payout wallet
    # bitcoinrpc.sendtoaddress(payout_wallet, amount, key)
    # - (Someday) Queue webhook
    # - Send webhook
    pass


def poll_transactions(bitcoin_rpc, redis, epoch_since=None, account='', num_limit=20, min_confirmations=5):
    while True:
        # Keep grabbing more until we find the earliest we haven't seen. We
        # don't use offset to avoid missing some during the gap.
        transactions = bitcoin_rpc.listtransactions(account, num_limit)

        if not transactions:
            return

        if int(next(transactions)['time']) < epoch_since:
            break

        num_limit *= 2

    # TODO: Fetch and append queued transactions.

    for t in transactions:
        if int(t['time']) < epoch_since:
            # Fast forward to the earliest we want
            continue

        if t['category'] == 'send':
            continue

        if int(t['confirmations']) < min_confirmations:
            # TODO: Queue transaction for a later check?
            redis.sadd(REDIS_KEYS.CONFIRMATION_QUEUE, t['txid'])
            continue

        _handle_transaction(bitcoin_rpc, redis, t)
