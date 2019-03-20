"""Test arguments_differ"""


class LoremIpsum(object):
    """Class LoremIpsum"""
    def __init__(self):
        """Function init"""
        self.a_a = 2

    def ego(self):
        """Function ego"""
        return self

    def odio(self, elit):
        """Function odio"""
        return self.a_a * elit


class DolorSitAmet(LoremIpsum):
    """Class DolorSitAmet"""
    def odio(self, elit, gloria):
        """Function odio"""
        gloria = elit
        super(DolorSitAmet, self).odio(gloria)
