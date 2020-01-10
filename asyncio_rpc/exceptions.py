class NotReceived(Exception):
    """
    Message has not been recieved by anyone
    """


class WrappedException(Exception):
    """
    Exception raised when an exception raised
    by RPC call could not be resolved, the innermessage
    shows the exception raised on the RPC server.
    """


class RPCTimeoutError(Exception):
    """
    Timeouterror raised by RPC client if result
    took to long.
    """


class SubscriptionClosed(Exception):
    """
    Raised when the subscription has already been closed
    """
