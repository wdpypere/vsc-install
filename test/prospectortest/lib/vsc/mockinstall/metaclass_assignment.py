"""Test metaclass-assignment"""


class MyMeta(type):
    """Class MyMeta"""
    def __new__(mcs, meta, name, bases, dct):
        """function new"""
        return super(MyMeta, meta).__new__(mcs, meta, name, bases, dct)


    def __init__(cls, name, bases, dct):
        """function init"""
        super(MyMeta, cls).__init__(name, bases, dct)

class MyKlass(object):
    """Class MyKlass"""
    __metaclass__ = MyMeta

    def foo_bar(self, param):
        """Function foo_bar"""
        pass

    def bar_bar(self, param):
        """Function foo_bar"""
        pass

    barattr = 2
