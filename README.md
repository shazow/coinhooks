# coinhooks

A webhooks service for Bitcoin ecommerce.

Currently under development. Ping me if you're interested in being an early easier.


## Code

The frontend is built on Pyramid. It depends on Redis for persistence and a Bitcoin daemon with RPC for Bitcoin-y things.


### Points of interest

* [coinhooks/web/views/wallet.py](https://github.com/shazow/coinhooks/blob/master/coinhooks/web/views/wallet.py):
  Exposed API functions are defined here, using a custom HTTP JSON RPC-like
  API framework defined in
  [coinhooks/web/views/api.py](https://github.com/shazow/coinhooks/blob/master/coinhooks/web/views/wallet.py)

* [coinhooks/api/bitcoin.py](https://github.com/shazow/coinhooks/blob/master/coinhooks/api/bitcoin.py):
  Core functionality of the application is defined in the `coinhooks.api`
  submodule. All non-trivial "business logic" lives here and is decoupled from
  the rest of the web framework where possible, for easy testing and reuse.
  Corresponding tests live in
  [coinhooks/test/api/test_bitcoin.py](https://github.com/shazow/coinhooks/blob/master/coinhooks/test/api/test_bitcoin.py).


## License:

Currently unlicensed. Planning to release under a BSD-like license.
