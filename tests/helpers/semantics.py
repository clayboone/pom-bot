from contextlib import contextmanager


@contextmanager
def assert_not_raises(*, test: object = None, msg: str = None):
    """Context manager that does nothing.

    When an exception occurs, it will be allowed raise.  This is semantic
    sugar for the reader to know that the purpose of a line is to ensure that
    the line does not raise an exception.

    Takes an optional keyword-only `msg` argument. When an exception is raise,
    print msg to stderr.
    """
    try:
        yield
    except Exception:
        if test and msg:
            test.fail(msg)
        raise
