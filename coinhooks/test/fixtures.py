"""
Collection of data and helpers useful for testing.
"""

class BITCOIN_ADDRESSES:
    good = [
        '15VjRaDX9zpbA8LVnbrCAFzrVzN7ixHNsC',
        '1EtqqRFwLYwk3ERbtkVKhsAPGgmSB2sh9E',
    ]

    bad = [
        'asdf',
        '0'*34,
        'n3swQ1Gm1HrNuzA8B4KJtzxqwXt1zEhhNJ',
    ]

    good_testnet = [
        'n3swQ1Gm1HrNuzA8B4KJtzxqwXt1zEhhNJ',
        'mqoyKYSsA4RpoMjunFmqJ1WgXEm6xmvCw3',
    ]

    encoding = [
        ('15VjRaDX9zpbA8LVnbrCAFzrVzN7ixHNsC', '\x001O\x90Eg\x8d2\xfdBj\xa03+\xc1\x86\x9dE\x9a\x86suR\xa5\xe3'),
        ('n3swQ1Gm1HrNuzA8B4KJtzxqwXt1zEhhNJ', 'o\xf5J\xc0\xda\xcd\xb1\x12\x0f3[\x19\xcf\x95\xa9\xb0\x87\xa9\xc2R7R\x9b|\xa3'),
    ]
