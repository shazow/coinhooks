class CoinhooksException(Exception):
    pass


class APIException(CoinhooksException):
    def __init__(self, message, code=400):
        self.message = message
        self.code = 400

    def __repr__(self):
        return '%s("%s", code=%d)' % (self.__class__.__name__, self.message, self.code)

    def __str__(self):
        return self.message


class APIError(APIException):
    pass


class APIControllerError(APIError):
    pass

