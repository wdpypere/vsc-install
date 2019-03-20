"""Test indexing-exception"""


try:
    A = 2
except IndexError as err:
    err[0]
