class Error(Exception):
    err_name = "Error"
    status_code = 500
    message = ""

    def __init__(self, message=None):
        if message is not None:
            self.message = message

    def to_dict(self):
        return {"message": self.message,
                "error_name": self.err_name}


class Omitted(Exception):
    """
    Descendants of StorageInterface raise this when a
    particular functionality hasn't been implemented
    deliberately in order to trigger fall through functionalities.
    If you want to completely prevent fall throughs raise something
    that isn't this exception in the method.

    eg:

    class YesFallThroughBehavior(StorageInterface):
        # This class will produce tifs from jpgs
        def __init__(self, config):
            pass

        def get_jpg(self, identifier):
            return "/jpgs/this_one.jpg"

    class NoFallThroughBehavior(StorageInterface):
        # This class wont produce tifs from jpgs
        def __init__(self, config):
            pass

        def get_tif(self, identifier):
            raise NotImplementedError()

        def get_jpg(self, identifier):
            return "/jpgs/this_one.jpg"
    """
    pass


class UnknownIdentifierFormatError(Error):
    err_name = "UnknownIdentifierFormatError"
    message = "No handlers found for that identifier"


class UnsupportedContextError(Error):
    err_name = "UnsupportedContextError"
    message = "That context isn't supported for this endpoint!"


class ContextError(Error):
    err_name = "ContextError"
    message = "Something went wrong trying to access that context!"


class MutuallyExclusiveParametersError(Error):
    err_name = "MutuallyExclusiveParametersError"
