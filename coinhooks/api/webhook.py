# FIXME: This is in-progress, not used yet.
import json
import requests

from coinhooks.lib.exceptions import APIError


KEY_CALLBACK_QUEUE = 'callback:queue'
KEY_CALLBACK_DIRTY = 'callback:dirty'


def _get_retry_wait(num_attempt=1, MAX_RETRY_WAIT=86400):
    return min(MAX_RETRY_WAIT, 2**num_attempt)

def send(callback_url, payload):
    try:
        r = requests.post(callback_url, params=payload)
    except requests.RequestException:
        raise APIError('Failed webhook request: POST %s' % callback_url)

    if r.status <= 299:
        # Success
        return r

    raise APIError('Invalid webhook response (status %d): POST %s' % (r.status_code, callback_url))


def send_queued(redis, callback_url, payload, num_attempts=10):
    request_id = json.dumps([callback_url, payload])
    is_unique = redis.sadd(KEY_CALLBACK_DIRTY, request_id)
    if not is_unique:
        # Already in-progress
        return

    # TODO: ...
