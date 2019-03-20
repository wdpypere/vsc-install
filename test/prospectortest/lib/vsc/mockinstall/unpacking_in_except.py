"""Test unpacking-in-except"""


try:
    A = 2
except ValueError, (errno, errstr):
    if errno == errstr:
        A = 4
