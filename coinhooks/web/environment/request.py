from pyramid.request import Request as _Request


__all__ = ['Request']


class Request(_Request):
    DEFAULT_FEATURES = {
    }

    def __init__(self, *args, **kw):
        _Request.__init__(self, *args, **kw)

        self.features = self.DEFAULT_FEATURES.copy()
