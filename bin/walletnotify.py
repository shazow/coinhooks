import sys
from pyramid.paster import bootstrap

from coinhooks import api


def main(request, tx_id):
    api.bitcoin.queue_transaction(request.bitcoin, request.redis, tx_id)


if __name__ == '__main__':
    try:
        ini_path, tx_id = sys.argv[1], sys.argv[2]
    except IndexError:
        print 'Usage: %s INI_PATH TX_ID' % sys.argv[0]
        sys.exit(1)

    env = bootstrap(ini_path)
    main(env['request'], tx_id)
