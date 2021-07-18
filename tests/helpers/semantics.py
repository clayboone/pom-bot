import unittest
from contextlib import contextmanager


@contextmanager
def assert_not_raises(testcase: unittest.TestCase = None, msg: str = None):
    """Context manager that does nothing; Semantic sugar for the reader to know
    that purpose of a line is that it does not raise an exception.

    Takes two optional, mutually inclusive arguments. When an exception occurs,
    then `testcase.fail` will be called by passing `msg` as the argument.

    @param testcase The object of the specific test being run.
    @param msg A custom message to send to the output on failure.
    """
    try:
        yield
    except Exception as exc:
        if testcase and msg:
            testcase.fail(msg)

        raise AssertionError("Exception was not expected") from exc
