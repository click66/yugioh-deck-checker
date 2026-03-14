from app.exceptions import Error


class InvalidCardCountsError(Error):
    pass


class InsufficientDeckSizeError(Error):
    pass
