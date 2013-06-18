import json
import time
import datetime
from decimal import Decimal

class FancyEncoder(json.JSONEncoder):
    """Encoder which supports DateTime and Decimal objects."""

    def default(self, obj):
        if isinstance(obj, datetime.date):
            return time.strftime('%Y-%m-%dT%H:%M:%SZ', obj.utctimetuple())
        elif isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


# Convenience wrappers for JSON encoding/decoding.

def dumps(*args, **kw):
    cls = kw.pop('cls', FancyEncoder)
    return json.dumps(*args, cls=cls, **kw)

loads = json.loads
