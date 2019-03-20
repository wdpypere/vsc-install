"""Test raising-string"""


myexc = 'my exception string'
try:
    raise myexc
except myexc:
    pass
