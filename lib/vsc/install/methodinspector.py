### External compatible license
#
#  From https://gist.github.com/nyergler/6531048
#     referenced in https://www.eventbrite.com/engineering/tracking-method-calls-during-testing/
#  Comment in gist:
#     In the interest of complete clarity, I waive any copyright over this gist
#     and dedicate to the public domain under the CC0 dedication.
#
"""
Wrap a method and track calls to allow making assertions about them.
"""

import collections
from mock import patch


MethodCall = collections.namedtuple(
    'MethodCall',
    ('args',
     'kwargs',
     'return_value',
     ),
)


class MethodInspector(object):
    """Wrap a method and track calls to allow making assertions about them.

    In some cases mocking a method isn't sufficient: we need to
    inspect calls and their return values to determine that our code
    is operating as expected. For example, the payment service doesn't
    lend itself to mocking, but we can inspect the return value of
    Order.charge_via_payment_service to assert that the right amount
    was charged.

    MethodInspector is a context manager that instruments a method and
    tracks its arguments and return values to allow this sort of testing.

    >>> with MethodInspector(Order, 'charge_via_payment_service') as inspector:
    ...     # do something

    The calls are stored as a sequence of named tuples. Each has three values:

    # args
    # kwargs
    # return_value


    """

    def __init__(self, klass, method_name):

        self.klass = klass
        self.method_name = method_name
        self.orig = getattr(klass, method_name)

    def __enter__(self):

        self.calls = []

        def wrapper(*a, **kw):

            result = self.orig(*a, **kw)
            self.calls.append(
                MethodCall(
                    args=a,
                    kwargs=kw,
                    return_value=result,
                )
            )
            return result

        self._patch = patch.object(self.klass, self.method_name, autospec=True)
        self._patch.start().side_effect = wrapper

        return self

    def __exit__(self, *a):

        self._patch.stop()

    def assertCalledOnce(self, msg=None):

        if len(self.calls) != 1:
            raise AssertionError(msg or '')
