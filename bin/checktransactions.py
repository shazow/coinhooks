# TODO: Port this to CELERYD BEAT
import sys
from pyramid.paster import bootstrap

from coinhooks import api


def main(request):
    api.bitcoin.deque_transaction(request.bitcoin, request.redis)


if __name__ == '__main__':
    try:
        ini_path = sys.argv[1]
    except IndexError:
        print 'Usage: %s INI_PATH' % sys.argv[0]
        sys.exit(1)

    env = bootstrap(ini_path)
    main(env['request'])
