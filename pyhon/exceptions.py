class HonAuthenticationError(Exception):
    pass


class HonNoAuthenticationNeeded(Exception):
    pass


class NoSessionException(Exception):
    pass


class NoAuthenticationException(Exception):
    pass


class ApiError(Exception):
    pass
